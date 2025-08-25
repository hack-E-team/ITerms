from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from .models import Vocabulary, VocabularyTerm, UserFavoriteVocabulary
from terms.models import Term
try:
    from terms.models import Tag
except Exception:
    Tag = None

def _has_vocab_tags():
    has_field = any(getattr(f, "many_to_many", False) and f.name == "tags"
                    for f in Vocabulary._meta.get_fields())
    return bool(Tag) and has_field

# =========================
# 一覧（公開 or 自分の用語帳）
# =========================
@require_GET
def vocabulary_list_view(request):
    """
    用語帳一覧：公開 or 自分の用語帳
    - ?q=     タイトル / 説明 / 含まれる用語名 / 用語説明 / 用語帳タグ名
    - ?tag=<id>  Vocabulary.tags で絞り込み（tags がある場合のみ）
    """
    q = (request.GET.get("q") or "").strip()
    tag = (request.GET.get("tag") or "").strip()

    qs = (
        Vocabulary.objects
        .select_related("user")
        .annotate(term_count=Count("terms", distinct=True))  # VocabularyTerm の件数
        .order_by("-updated_at", "-created_at")
    )
    if _has_vocab_tags():
        qs = qs.prefetch_related("tags")

    if request.user.is_authenticated:
        qs = qs.filter(Q(is_public=True) | Q(user=request.user))
    else:
        qs = qs.filter(is_public=True)

    if q:
        base = Q(title__icontains=q) | Q(description__icontains=q) | Q(terms__term__term_name__icontains=q) | Q(terms__term__description__icontains=q)
        if _has_vocab_tags():
            base |= Q(tags__name__icontains=q)
        qs = qs.filter(base).distinct()

    current_tag_id = None
    if tag.isdigit() and _has_vocab_tags():
        current_tag_id = int(tag)
        qs = qs.filter(tags__id=current_tag_id).distinct()

    return render(request, "vocabularies/vocabularies.html", {
        "q": q,
        "vocab_list": qs,
        "all_tags": Tag.objects.order_by("name") if _has_vocab_tags() else [],
        "current_tag_id": current_tag_id,
    })


# ========== 詳細表示 ==========
@require_GET
def vocabulary_detail_view(request, pk: int):
    """
    用語帳詳細：公開は誰でも、非公開は本人のみ。
    """
    vocab = get_object_or_404(Vocabulary.objects.select_related("user"), pk=pk)

    # アクセス権
    if not vocab.is_public and (not request.user.is_authenticated or request.user != vocab.user):
        raise Http404()

    # 用語帳に含まれる Term を、VocabularyTerm.order_index の順に並べる
    qs = (
        Term.objects
        .filter(vocabulary_entries__vocabulary=vocab)
        .order_by('vocabulary_entries__order_index', 'vocabulary_entries__id')
        .distinct()
    )

    # （任意）内部検索対応 ?q=
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(term_name__icontains=q) | Q(description__icontains=q))

    # ページング
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # terms/termslist.html を使う。selected_vocab があれば“用語帳内一覧”として表示される想定
    return render(request, "terms/termslist.html", {
        "page_obj": page_obj,        # ← Term のページング結果
        "q": q,
        "selected_vocab": vocab,     # ← これがあるとテンプレで「用語帳用の見出し・導線」に切替可
    })


# =============== 作成フォーム表示 ===============
@login_required
@require_GET
def vocabulary_create_view(request):
    """
    用語帳作成フォーム
    - 自分の Term（term_name/description）から選択
    - 既存 Tag を選択（新規作成はしない）
    """
    my_terms = Term.objects.filter(user=request.user).order_by("term_name")
    all_tags = Tag.objects.order_by("name") if _has_vocab_tags() else []
    return render(request, "vocabularies/create.html", {
        "values": {
            "title": "",
            "description": "",
            "is_public": False,
            "term_ids": [],
            "tag_ids": [],
        },
        "errors": {},
        "my_terms": my_terms,
        "all_tags": all_tags,
    })


# =============== 作成処理 ===============
@login_required
@require_POST
@transaction.atomic
def vocabulary_create_post(request):
    """
    用語帳作成処理（POST）
    - タイトル必須
    - term_ids は自分の Term のみに制限
    - tag_ids は既存 Tag のみ（作成はしない）※ tags がある場合のみ
    - VocabularyTerm は受信順に order_index を付けて作成
    """
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()

    raw_is_public = (request.POST.get("is_public") or "").strip().lower()
    is_public = raw_is_public in ("1", "true", "on")  # 厳密化

    raw_term_ids = request.POST.getlist("term_ids")
    raw_tag_ids = request.POST.getlist("tag_ids")

    errors = {}
    if not title:
        errors["title"] = "必須です。"

    # term_ids: 数値のみ抽出・順序維持（重複除去）
    ordered_term_ids, seen_terms = [], set()
    for x in raw_term_ids:
        if x.isdigit():
            i = int(x)
            if i not in seen_terms:
                ordered_term_ids.append(i)
                seen_terms.add(i)

    # tag_ids: 数値のみ
    tag_ids = [int(x) for x in raw_tag_ids if x.isdigit()]

    if errors:
        my_terms = Term.objects.filter(user=request.user).order_by("term_name")
        all_tags = Tag.objects.order_by("name") if _has_vocab_tags() else []
        return render(request, "vocabularies/create.html", {
            "values": {
                "title": title,
                "description": description,
                "is_public": is_public,
                "term_ids": ordered_term_ids,
                "tag_ids": tag_ids,
            },
            "errors": errors,
            "my_terms": my_terms,
            "all_tags": all_tags,
        }, status=400)

    # 用語帳作成
    vocab = Vocabulary.objects.create(
        user=request.user,
        title=title,
        description=description,
        is_public=is_public,
    )

    # タグ紐付け（既存のみ / tags がある場合のみ）
    if _has_vocab_tags() and tag_ids:
        selected_tags = list(Tag.objects.filter(id__in=set(tag_ids)))
        if selected_tags:
            vocab.tags.add(*selected_tags)

    # 自分の用語だけを順番通りに登録（unique_together(vocabulary, term) に配慮）
    my_terms_by_id = {
        t.id: t for t in Term.objects.filter(user=request.user, id__in=ordered_term_ids)
    }
    for idx, tid in enumerate(ordered_term_ids):
        term = my_terms_by_id.get(tid)
        if term:
            VocabularyTerm.objects.get_or_create(
                user=request.user,
                vocabulary=vocab,
                term=term,
                defaults={"order_index": idx},
            )

    messages.success(request, f"用語集「{vocab.title}」を作成しました。")
    return redirect("vocabularies:detail", pk=vocab.pk)


# ========================== 他人の用語帳を探す（公開） ==========================
@require_GET
def discover_vocabularies_view(request):
    """
    他ユーザーの用語帳（公開のみ）
    - ?q=     タイトル / 説明 / 含まれる用語名 / 用語説明 / 用語帳タグ名
    - ?tag=<id>  Vocabulary.tags で絞り込み（tags がある場合のみ）
    """
    q = (request.GET.get("q") or "").strip()
    tag = (request.GET.get("tag") or "").strip()

    qs = (
        Vocabulary.objects
        .select_related("user")
        .annotate(term_count=Count("terms", distinct=True))
        .filter(is_public=True)
        .order_by("-updated_at", "-created_at")
    )
    if _has_vocab_tags():
        qs = qs.prefetch_related("tags")

    # 「他人の」に限定
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)

    if q:
        base = Q(title__icontains=q) | Q(description__icontains=q) | Q(terms__term__term_name__icontains=q) | Q(terms__term__description__icontains=q)
        if _has_vocab_tags():
            base |= Q(tags__name__icontains=q)
        qs = qs.filter(base).distinct()

    current_tag_id = None
    if tag.isdigit() and _has_vocab_tags():
        current_tag_id = int(tag)
        qs = qs.filter(tags__id=current_tag_id).distinct()

    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "vocabulariesSearch/vocabulariesSearch.html", {
        "q": q,
        "page_obj": page_obj,
        "all_tags": Tag.objects.order_by("name") if _has_vocab_tags() else [],
        "current_tag_id": current_tag_id,
    })


# ====================== お気に入りに追加（POST） ======================
@login_required
@require_POST
def discover_add_favorite_view(request):
    """
    お気に入り追加（UserFavoriteVocabulary）
    POST: vocabulary_id, next(任意)
    """
    vocab_id = (request.POST.get("vocabulary_id") or "").strip()
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("vocabularies:list")

    if not vocab_id.isdigit():
        messages.error(request, "不正なリクエストです。")
        return redirect(next_url)

    vocab = get_object_or_404(Vocabulary, pk=int(vocab_id), is_public=True)

    if vocab.user_id == request.user.id:
        messages.info(request, "自分の用語帳は追加対象外です。")
        return redirect(next_url)

    UserFavoriteVocabulary.objects.get_or_create(
        user=request.user,
        vocabulary=vocab,
    )
    messages.success(request, f"「{vocab.title}」をお気に入りに追加しました。")
    return redirect(next_url)


# =========================== 用語帳ごとの学習ページ & API ===========================
@require_GET
def vocabulary_learn_view(request, pk: int):
    """
    用語帳の学習ページ。テンプレは terms/terms.html を流用。
    - 非公開は作成者のみ
    - terms.html 側のJSが /terms/api/flashcards/?vocab=<id> を叩く
    """
    vocab = get_object_or_404(Vocabulary.objects.select_related("user"), pk=pk)
    if not vocab.is_public and (not request.user.is_authenticated or request.user != vocab.user):
        raise Http404()

    # 初期表示カード（任意：デッキの先頭を開く）
    first_term_id = (
        VocabularyTerm.objects
        .filter(vocabulary=vocab)
        .order_by("order_index", "id")
        .values_list("term_id", flat=True)
        .first()
    )

    return render(request, "terms/terms.html", {
        "selected_vocab": vocab,                        # ← デッキ文脈
        "initial_term_id": first_term_id,               # ← 先頭カード（無ければ None）
        "q": (request.GET.get("q") or "").strip(),      # ← 検索を引き継ぎたい場合
        "order": (request.GET.get("order") or "").strip().lower(),  # ← random 等
    })


@require_GET
def vocabulary_api_flashcards(request, pk: int):
    """
    用語帳に紐づくフラッシュカードJSON
    - レスポンス: { items: [{id, term, desc, note, order_index, updated_at}], count }
    - ?q= デッキ内検索（用語名/説明）
    - ?order=random でランダム（既定は order_index, id）
    - ?limit= 上限件数（既定1000, 1..5000）
    """
    vocab = get_object_or_404(Vocabulary.objects.select_related("user"), pk=pk)
    if not vocab.is_public and (not request.user.is_authenticated or request.user != vocab.user):
        # 存在秘匿の観点で 404
        return JsonResponse({"items": [], "count": 0}, status=404)

    q = (request.GET.get("q") or "").strip()
    order = (request.GET.get("order") or "").strip().lower()
    try:
        limit = int(request.GET.get("limit") or 1000)
    except ValueError:
        limit = 1000
    limit = max(1, min(limit, 5000))

    qs = (
        VocabularyTerm.objects
        .select_related("term")
        .filter(vocabulary=vocab)
    )

    if q:
        qs = qs.filter(
            Q(term__term_name__icontains=q) |
            Q(term__description__icontains=q)
        )

    if order == "random":
        qs = qs.order_by("?")
    else:
        qs = qs.order_by("order_index", "id")

    qs = qs[:limit]

    items = [{
        "id": vt.term_id,
        "term": vt.term.term_name,          # 表
        "desc": vt.term.description,        # 裏は desc に統一
        "note": vt.note or "",
        "order_index": vt.order_index,
        "updated_at": timezone.localtime(vt.term.updated_at).isoformat(),
    } for vt in qs]

    return JsonResponse({"items": items, "count": len(items)}, json_dumps_params={"ensure_ascii": False})
