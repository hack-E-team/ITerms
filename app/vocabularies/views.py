# app/vocabularies/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .models import Vocabulary, VocabularyTerm, Term, UserFavoriteVocabulary
from terms.models import Tag  # Vocabulary.tags (M2M) はこれに紐づける想定


# =========================
# 一覧（公開 or 自分の用語帳）
# =========================
@require_GET
def vocabulary_list_view(request):
    """
    用語帳一覧：公開 or 自分の用語帳
    - ?q=     タイトル / 説明 / 含まれる用語名 / 用語説明 / 用語帳タグ名
    - ?tag=<id>  Vocabulary.tags で絞り込み
    """
    q = (request.GET.get("q") or "").strip()
    tag = (request.GET.get("tag") or "").strip()

    qs = (
        Vocabulary.objects
        .select_related("user")
        .prefetch_related("tags")
        .annotate(term_count=Count("terms", distinct=True))  # VocabularyTerm の件数
        .order_by("-updated_at", "-created_at")
    )

    if request.user.is_authenticated:
        qs = qs.filter(Q(is_public=True) | Q(user=request.user))
    else:
        qs = qs.filter(is_public=True)

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(terms__term__term_name__icontains=q) |
            Q(terms__term__description__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct()

    current_tag_id = None
    if tag.isdigit():
        current_tag_id = int(tag)
        qs = qs.filter(tags__id=current_tag_id).distinct()

    return render(request, "vocabularies/list.html", {
        "q": q,
        "vocab_list": qs,
        "all_tags": Tag.objects.order_by("name"),
        "current_tag_id": current_tag_id,
    })


# ==========
# 詳細表示
# ==========
@require_GET
def vocabulary_detail_view(request, pk: int):
    """
    用語帳詳細：公開は誰でも、非公開は本人のみ
    """
    vocab = get_object_or_404(
        Vocabulary.objects.select_related("user").prefetch_related("tags"),
        pk=pk,
    )

    if not vocab.is_public and (not request.user.is_authenticated or request.user != vocab.user):
        return render(request, "403.html", status=404)

    entries = (
        VocabularyTerm.objects
        .select_related("term")
        .filter(vocabulary=vocab)
        .order_by("order_index", "id")
    )

    return render(request, "vocabularies/detail.html", {
        "vocab": vocab,
        "entries": entries,
    })


# ===============
# 作成フォーム表示
# ===============
@login_required
@require_GET
def vocabulary_create_view(request):
    """
    用語帳作成フォーム
    - 自分の Term（term_name/description）から選択
    - 既存 Tag を選択（新規作成はしない）
    """
    my_terms = Term.objects.filter(user=request.user).order_by("term_name")
    all_tags = Tag.objects.order_by("name")
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


# ==========
# 作成処理
# ==========
@login_required
@require_POST
@transaction.atomic
def vocabulary_create_post(request):
    """
    用語帳作成処理（POST）
    - タイトル必須
    - term_ids は自分の Term のみに制限
    - tag_ids は既存 Tag のみ（作成はしない）
    - VocabularyTerm は受信順に order_index を付けて作成
    """
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    is_public = bool(request.POST.get("is_public"))
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
        all_tags = Tag.objects.order_by("name")
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

    # タグ紐付け（既存のみ）
    if tag_ids:
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


# ==========================
# 他人の用語帳を探す（公開）
# ==========================
@require_GET
def discover_vocabularies_view(request):
    """
    他ユーザーの用語帳（公開のみ）
    - ?q=     タイトル / 説明 / 含まれる用語名 / 用語説明 / 用語帳タグ名
    - ?tag=<id>  Vocabulary.tags で絞り込み
    """
    q = (request.GET.get("q") or "").strip()
    tag = (request.GET.get("tag") or "").strip()

    qs = (
        Vocabulary.objects
        .select_related("user")
        .prefetch_related("tags")
        .annotate(term_count=Count("terms", distinct=True))
        .filter(is_public=True)
        .order_by("-updated_at", "-created_at")
    )

    # 「他人の」に限定したい場合
    if request.user.is_authenticated:
        qs = qs.exclude(user=request.user)

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(terms__term__term_name__icontains=q) |
            Q(terms__term__description__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct()

    current_tag_id = None
    if tag.isdigit():
        current_tag_id = int(tag)
        qs = qs.filter(tags__id=current_tag_id).distinct()

    paginator = Paginator(qs, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "vocabulariesSearch/search.html", {
        "q": q,
        "page_obj": page_obj,
        "all_tags": Tag.objects.order_by("name"),
        "current_tag_id": current_tag_id,
    })


# ======================
# お気に入りに追加（POST）
# ======================
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


# ===========================
# 用語帳ごとの学習ページ & API
# ===========================
@require_GET
def vocabulary_learn_view(request, pk: int):
    """
    用語帳のフラッシュカード画面
    - 非公開は作成者のみ
    """
    vocab = get_object_or_404(Vocabulary.objects.select_related("user"), pk=pk)
    if not vocab.is_public and (not request.user.is_authenticated or request.user != vocab.user):
        return render(request, "403.html", status=404)

    # テンプレへAPIのURLを渡す
    return render(request, "vocabularies/learn.html", {
        "vocab": vocab,
        "api_url": reverse("vocabularies:api_fc", kwargs={"pk": vocab.pk}),
    })


@require_GET
def vocabulary_api_flashcards(request, pk: int):
    """
    用語帳に紐づくフラッシュカードJSON
    - レスポンス: { items: [{id, term, definition, note, order_index}, ...] }
    - ?q= でデッキ内検索（用語名/説明）
    - 並び順は VocabularyTerm.order_index, id
    """
    vocab = get_object_or_404(Vocabulary.objects.select_related("user"), pk=pk)
    if not vocab.is_public and (not request.user.is_authenticated or request.user != vocab.user):
        return JsonResponse({"items": []}, status=404)

    q = (request.GET.get("q") or "").strip()

    qs = (
        VocabularyTerm.objects
        .select_related("term")
        .filter(vocabulary=vocab)
        .order_by("order_index", "id")
    )
    if q:
        qs = qs.filter(
            Q(term__term_name__icontains=q) |
            Q(term__description__icontains=q)
        )

    items = [{
        "id": vt.term_id,
        "term": vt.term.term_name,           # 表
        "definition": vt.term.description,   # 裏
        "note": vt.note or "",
        "order_index": vt.order_index,
    } for vt in qs]

    return JsonResponse({"items": items})
