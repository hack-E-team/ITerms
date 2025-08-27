# app/vocabularies/views.py
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

def _get_term_tags():
    # 用語( Term )のタグ一覧。Tag が無い構成でも落ちないように。
    try:
        from terms.models import Tag
        return Tag.objects.order_by("name")
    except Exception:
        return []


# =========================
# 一覧（公開 or 自分の用語帳）
# =========================
@require_GET
@login_required
def vocabulary_list_view(request):
    """
    用語帳一覧：自分の用語帳 + お気に入り登録した他人の用語帳のみ
    - ?q=     タイトル / 説明 / 含まれる用語名 / 用語説明 / 用語帳タグ名
    - ?tag=<id>  Vocabulary.tags で絞り込み（tags がある場合のみ）
    """
    q   = (request.GET.get("q") or "").strip()
    tag = (request.GET.get("tag") or "").strip()

    fav_ids_qs = UserFavoriteVocabulary.objects.filter(
        user=request.user
    ).values_list("vocabulary_id", flat=True)
    fav_ids = set(fav_ids_qs)

    qs = (
        Vocabulary.objects
        .select_related("user")
        .annotate(term_count=Count("terms", distinct=True))
        .filter(Q(user=request.user) | Q(id__in=fav_ids_qs, is_public=True))
        .order_by("-updated_at", "-created_at")
    )
    if _has_vocab_tags():
        qs = qs.prefetch_related("tags")

    if q:
        base = (Q(title__icontains=q) | Q(description__icontains=q) |
                Q(terms__term__term__icontains=q) | Q(terms__term__definition__icontains=q))
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
        "favorite_ids": fav_ids,
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
        .prefetch_related("tags")
        .order_by('vocabulary_entries__order_index', 'vocabulary_entries__id')
        .distinct()
    )

    # 内部検索とタグ絞り込み（任意）
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(term__icontains=q) | Q(definition__icontains=q))

    tag_id = (request.GET.get("tag") or "").strip()
    if tag_id.isdigit():
        qs = qs.filter(tags__id=int(tag_id)).distinct()

    terms = list(qs)

    return render(request, "termslist/termslist.html", {
        "terms": terms,
        "q": q,
        "selected_vocab": vocab,
        "all_tags": Tag.objects.order_by("name") if Tag else [],
        "current_tag_id": int(tag_id) if tag_id.isdigit() else None,
    })

# =============== 作成フォーム表示 ===============
@login_required
@require_GET
def vocabulary_create_view(request):
    my_terms = (Term.objects
                .filter(user=request.user)
                .prefetch_related("tags")
                .order_by("term"))
    term_tags = list(_get_term_tags())

    return render(request, "vocabulariescreate/vocabulariescreate.html", {
        "mode": "create",
        "values": {"title": "", "description": "", "is_public": False,
                   "term_ids": [], "tag_ids": []},
        "errors": {},
        "my_terms": my_terms,
        "term_tags": term_tags,
        "action_url": reverse("vocabularies:create_post"),
        "submit_label": "作成完了",
    })


# =============== 作成処理 ===============
@login_required
@require_POST
@transaction.atomic
def vocabulary_create_post(request):
    """
    用語帳作成処理（POST）
    - タイトル必須
    - term_ids は **自分の** Term のみに制限
    - tag_ids は既存 Tag のみ（作成はしない）※ tags がある場合のみ
    - VocabularyTerm は受信順に order_index を付けて作成
    """
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()

    raw_is_public = (request.POST.get("is_public") or "").strip().lower()
    is_public = raw_is_public in ("1", "true", "on")

    raw_term_ids = request.POST.getlist("term_ids")
    raw_tag_ids = request.POST.getlist("tag_ids")

    errors = {}
    if not title:
        errors["title"] = "必須です。"

    ordered_term_ids, seen_terms = [], set()
    for x in raw_term_ids:
        if x.isdigit():
            i = int(x)
            if i not in seen_terms:
                ordered_term_ids.append(i)
                seen_terms.add(i)

    tag_ids = [int(x) for x in raw_tag_ids if x.isdigit()]

    if errors:
        my_terms = Term.objects.filter(user=request.user).order_by("term").prefetch_related("tags")
        term_tags = Tag.objects.order_by("name") if Tag else []
        return render(request, "vocabulariescreate/vocabulariescreate.html", {
            "mode": "create",
            "action_url": reverse("vocabularies:create_post"),
            "submit_label": "作成完了",
            "values": {
                "title": title,
                "description": description,
                "is_public": is_public,
                "term_ids": ordered_term_ids,
                "tag_ids": tag_ids,
            },
            "errors": errors,
            "my_terms": my_terms,
            "term_tags": term_tags,
        }, status=400)

    vocab = Vocabulary.objects.create(
        user=request.user,
        title=title,
        description=description,
        is_public=is_public,
    )

    if _has_vocab_tags() and tag_ids:
        selected_tags = list(Tag.objects.filter(id__in=set(tag_ids)))
        if selected_tags:
            vocab.tags.add(*selected_tags)

    my_terms_by_id = {t.id: t for t in Term.objects.filter(user=request.user, id__in=ordered_term_ids)}
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

# ===== 編集フォーム（表示） =====
@login_required
@require_GET
def vocabulary_edit_view(request, pk: int):
    vocab = get_object_or_404(Vocabulary, pk=pk, user=request.user)

    my_terms = (Term.objects
                .filter(user=request.user)
                .prefetch_related("tags")
                .order_by("term"))

    selected_term_ids = list(
        VocabularyTerm.objects
        .filter(vocabulary=vocab)
        .order_by("order_index", "id")
        .values_list("term_id", flat=True)
    )

    term_tags = list(_get_term_tags())

    # 用語帳タグ（もし Vocabulary に tags がある場合）
    try:
        vocab_tag_ids = list(vocab.tags.values_list("id", flat=True))
    except Exception:
        vocab_tag_ids = []

    return render(request, "vocabulariescreate/vocabulariescreate.html", {
        "mode": "edit",
        "values": {"title": vocab.title,
                   "description": vocab.description,
                   "is_public": vocab.is_public,
                   "term_ids": selected_term_ids,
                   "tag_ids": vocab_tag_ids},
        "errors": {},
        "my_terms": my_terms,
        "term_tags": term_tags,   # ← ★必ず渡す
        "all_tags": term_tags,    # 互換
        "action_url": reverse("vocabularies:edit_post", args=[vocab.pk]),
        "submit_label": "保存する",
    })


# ===== 編集処理（POST） =====
@login_required
@require_POST
@transaction.atomic
def vocabulary_edit_post(request, pk: int):
    vocab = get_object_or_404(Vocabulary.objects.select_related("user"), pk=pk, user=request.user)

    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    raw_is_public = (request.POST.get("is_public") or "").strip().lower()
    is_public = raw_is_public in ("1", "true", "on")

    raw_term_ids = request.POST.getlist("term_ids")
    raw_tag_ids = request.POST.getlist("tag_ids")

    errors = {}
    if not title:
        errors["title"] = "必須です。"

    # 重複除去しつつ並びは維持
    ordered_term_ids, seen = [], set()
    for x in raw_term_ids:
        if x.isdigit():
            i = int(x)
            if i not in seen:
                ordered_term_ids.append(i)
                seen.add(i)

    # 安全のため「自分のTermのみ」を許可
    valid_term_ids = set(
        Term.objects.filter(user=request.user, id__in=ordered_term_ids).values_list("id", flat=True)
    )
    ordered_term_ids = [i for i in ordered_term_ids if i in valid_term_ids]

    tag_ids = [int(x) for x in raw_tag_ids if x.isdigit()]

    if errors:
        my_terms = Term.objects.filter(user=request.user).order_by("term").prefetch_related("tags")
        all_tags = Tag.objects.order_by("name") if _has_vocab_tags() else []
        return render(request, "vocabulariescreate/vocabulariescreate.html", {
            "mode": "edit",
            "action_url": reverse("vocabularies:edit_post", args=[vocab.pk]),
            "submit_label": "更新する",
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

    # 見出し更新
    vocab.title = title
    vocab.description = description
    vocab.is_public = is_public
    vocab.save(update_fields=["title", "description", "is_public", "updated_at"])

    # 用語帳タグ（あれば）
    if _has_vocab_tags():
        selected_tags = list(Tag.objects.filter(id__in=set(tag_ids)))
        vocab.tags.set(selected_tags)  # setで置き換え

    # VocabularyTerm の差分更新
    existing = {vt.term_id: vt for vt in VocabularyTerm.objects.filter(vocabulary=vocab)}

    # なくなったTermを削除
    keep_set = set(ordered_term_ids)
    for term_id, vt in list(existing.items()):
        if term_id not in keep_set:
            vt.delete()

    # 追加/順序更新
    for idx, term_id in enumerate(ordered_term_ids):
        vt = existing.get(term_id)
        if vt:
            if vt.order_index != idx or vt.user_id != request.user.id:
                vt.order_index = idx
                vt.user_id = request.user.id
                vt.save(update_fields=["order_index", "user", "updated_at"])
        else:
            VocabularyTerm.objects.create(
                user=request.user,
                vocabulary=vocab,
                term_id=term_id,
                order_index=idx,
            )

    messages.success(request, "用語帳を更新しました。")
    return redirect("vocabularies:detail", pk=vocab.pk)

# ========================== 他人の用語帳を探す（公開） ==========================
@require_GET
def discover_vocabularies_view(request):
    q   = (request.GET.get("q") or "").strip()
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

    # 自分の用語帳は除外
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)

    if q:
        base = (
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(terms__term__term__icontains=q) |
            Q(terms__term__definition__icontains=q)
        )
        if _has_vocab_tags():
            base |= Q(tags__name__icontains=q)
        qs = qs.filter(base).distinct()

    current_tag_id = None
    if tag.isdigit() and _has_vocab_tags():
        current_tag_id = int(tag)
        qs = qs.filter(tags__id=current_tag_id).distinct()

    vocab_list = qs

    fav_ids = set()
    if request.user.is_authenticated:
        fav_ids = set(
            UserFavoriteVocabulary.objects
            .filter(user=request.user)
            .values_list("vocabulary_id", flat=True)
        )

    return render(request, "vocabulariesSearch/vocabulariesSearch.html", {
        "q": q,
        "vocab_list": vocab_list,   # ← page_obj ではなく vocab_list
        "all_tags": Tag.objects.order_by("name") if _has_vocab_tags() else [],
        "current_tag_id": current_tag_id,
        "favorite_ids": fav_ids,
    })


# ====================== お気に入りに追加（POST） ======================
@login_required
@require_POST
def discover_add_favorite_view(request):
    vocab_id = (request.POST.get("vocabulary_id") or "").strip()
    next_url = (request.POST.get("next")
                or request.META.get("HTTP_REFERER")
                or reverse("vocabularies:vocabulariesSearch"))
    
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

# 解除（unfavorite）
@login_required
@require_POST
def favorite_remove_view(request):
    vocab_id = (request.POST.get("vocabulary_id") or "").strip()
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("vocabularies:myvocabularies")

    if not vocab_id.isdigit():
        messages.error(request, "不正なリクエストです。")
        return redirect(next_url)

    UserFavoriteVocabulary.objects.filter(
        user=request.user,
        vocabulary_id=int(vocab_id),
    ).delete()

    messages.success(request, "お気に入りを解除しました。")
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

    first_term_id = (
        VocabularyTerm.objects
        .filter(vocabulary=vocab)
        .order_by("order_index", "id")
        .values_list("term_id", flat=True)
        .first()
    )

    return render(request, "terms/terms.html", {
        "selected_vocab": vocab,
        "initial_term_id": first_term_id,
        "q": (request.GET.get("q") or "").strip(),
        "order": (request.GET.get("order") or "").strip().lower(),
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
        return JsonResponse({"items": [], "count": 0}, status=404)

    q = (request.GET.get("q") or "").strip()
    order = (request.GET.get("order") or "").strip().lower()
    try:
        limit = int(request.GET.get("limit") or 1000)
    except ValueError:
        limit = 1000
    limit = max(1, min(limit, 5000))

    tag_id = (request.GET.get("tag") or "").strip()
    qs = VocabularyTerm.objects.select_related("term").prefetch_related("term__tags").filter(vocabulary=vocab)

    if q:
        qs = qs.filter(
            Q(term__term__icontains=q) |            # ← term_name → term
            Q(term__definition__icontains=q)        # ← description → definition
        )
    if tag_id.isdigit():
        qs = qs.filter(term__tags__id=int(tag_id)).distinct()
    if order == "random":
        qs = qs.order_by("?")
    else:
        qs = qs.order_by("order_index", "id")

    qs = qs[:limit]

    items = [{
        "id": vt.term_id,
        "term": vt.term.term,                 # 表
        "desc": vt.term.definition,           # 裏（desc に統一）
        "note": vt.note or "",
        "tags": [tg.name for tg in vt.term.tags.all()],
        "order_index": vt.order_index,
        "updated_at": timezone.localtime(vt.term.updated_at).isoformat(),
    } for vt in qs]

    return JsonResponse({"items": items, "count": len(items)}, json_dumps_params={"ensure_ascii": False})
