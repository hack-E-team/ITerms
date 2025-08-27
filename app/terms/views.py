import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages

from .models import Term, Tag
from vocabularies.models import Vocabulary, VocabularyTerm


# =========================
# 一覧（termslist.html）
# =========================
@require_GET
@login_required
def terms_list_view(request):
    """
    /terms/?q=&vocab=&tag=&page=
    - デフォルト: 自分の Term を一覧表示（ページング）
    - ?vocab=<id>: 指定用語集の Term を一覧（公開 or 自分の用語集）
    """
    q = (request.GET.get("q") or "").strip()
    vocab = (request.GET.get("vocab") or "").strip()
    tag_id = (request.GET.get("tag") or "").strip()

    selected_vocab = None

    if vocab.isdigit():
        # デッキ内一覧モード（公開 or 自分の用語集のみ許可）
        selected_vocab = get_object_or_404(Vocabulary, id=int(vocab))
        if not (selected_vocab.is_public or selected_vocab.user_id == request.user.id):
            raise Http404()
        qs = (
            Term.objects
            .filter(vocabulary_entries__vocabulary=selected_vocab)
            .prefetch_related("tags")
            .distinct()
        )
    else:
        # 自分の用語一覧モード
        qs = Term.objects.filter(user=request.user).prefetch_related("tags")

    if q:
        qs = qs.filter(
            Q(term__icontains=q) |
            Q(definition__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct()

    if tag_id.isdigit():
        qs = qs.filter(tags__id=int(tag_id)).distinct()

    qs = qs.order_by("-updated_at", "-created_at")
    terms = list(qs)

    return render(request, "termslist/termslist.html", {
        "terms": terms,
        "q": q,
        "selected_vocab": selected_vocab,
        "all_tags": Tag.objects.order_by("name"),
        "current_tag_id": int(tag_id) if tag_id.isdigit() else None,
    })


# =========================
# 詳細ページ（カードUI; terms.html）
# =========================
@require_GET
@login_required
def term_detail_page(request, pk: int):
    term = get_object_or_404(Term, pk=pk)

    vocab_id = (request.GET.get("vocab") or "").strip()
    via_vocab = None

    # ★ ここを先に処理：?vocab= が来ていたら、所有者に関係なく採用
    if vocab_id.isdigit():
        via_vocab = get_object_or_404(Vocabulary, id=int(vocab_id))
        # アクセス権（公開 or 自分の用語帳）
        if not (via_vocab.is_public or via_vocab.user_id == request.user.id):
            raise Http404()
        # その用語帳にこの用語が含まれているか
        in_this_vocab = VocabularyTerm.objects.filter(
            vocabulary=via_vocab, term=term
        ).exists()
        if not in_this_vocab:
            raise Http404()

    else:
        # ?vocab が無いときだけ、他人Termのアクセス制御を行う
        if term.user_id != request.user.id:
            in_public_vocab = VocabularyTerm.objects.filter(
                term=term, vocabulary__is_public=True
            ).exists()
            if not in_public_vocab:
                raise Http404()

    return render(request, "terms/terms.html", {
        "initial_term_id": term.id,
        "selected_vocab": via_vocab,  # ← ?vocab= があれば必ず入る
        "q": (request.GET.get("q") or "").strip(),
        "order": (request.GET.get("order") or "").strip(),
    })


# =========================
# 用語作成（GET/POST）— タグを紐づける
# =========================
@require_GET
@login_required
def term_create_view(request):
    return render(request, "createterms/createterms.html", {
        "values": {"term": "", "definition": "", "tag_ids": []},
        "errors": {},
        "all_tags": Tag.objects.order_by("name"),
    })


@require_POST
@login_required
def term_create_post(request):
    """
    JSON配列: [{ "term": "...", "description": "...", "tag_ids": [1,2,3] }, ...]
    を受け取り、1回のリクエストでまとめて作成します。
    各要素は個別に検証・保存（片方失敗しても他は続行）。
    """
    # 受け口を配列専用にする（不要なら外してOK）
    if "application/json" not in (request.content_type or "").lower():
        return JsonResponse({"ok": False, "error": "Content-Type must be application/json"}, status=415)

    try:
        payload = json.loads(request.body.decode("utf-8") or "[]")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    if not isinstance(payload, list):
        return JsonResponse({"ok": False, "error": "Array expected"}, status=400)

    MAX_ITEMS = 1000
    if len(payload) > MAX_ITEMS:
        return JsonResponse({"ok": False, "error": f"Too many items (>{MAX_ITEMS})"}, status=413)

    created, errors = [], []

    for i, item in enumerate(payload):
        term_value = (item.get("term") or "").strip()
        definition_value = (item.get("description") or item.get("definition") or "").strip()

        tag_ids = []
        for x in (item.get("tag_ids") or []):
            try:
                tag_ids.append(int(x))
            except (TypeError, ValueError):
                continue

        if not term_value or not definition_value:
            errors.append({"index": i, "error": "term/description は必須です"})
            continue

        with transaction.atomic():
            obj = Term.objects.create(
                user=request.user,
                term=term_value,
                definition=definition_value,
            )
            if tag_ids:
                tags = list(Tag.objects.filter(id__in=set(tag_ids)))
                if tags:
                    obj.tags.add(*tags)

            created.append({"id": obj.id, "term": obj.term})

    return JsonResponse(
        {"ok": len(errors) == 0, "created": created, "errors": errors},
        status=200 if not errors else 207,
        json_dumps_params={"ensure_ascii": False},
    )


# =========================
# 用語編集（GET/POST)
# =========================
@require_GET
@login_required
def term_edit_view(request, pk: int):
    """
    自分の用語のみ編集可能。単一レコード編集ページ（GET）
    """
    t = get_object_or_404(Term.objects.prefetch_related("tags"), pk=pk, user=request.user)
    tag_ids = list(t.tags.values_list("id", flat=True))

    return render(request, "editterms/editterms.html", {
        "values": {"term": t.term, "definition": t.definition, "tag_ids": tag_ids},
        "errors": {},
        "all_tags": Tag.objects.order_by("name"),
        "action_url": reverse("terms:edit_post", args=[t.id]),
        "submit_label": "保存する",
        "term_obj": t,
    })


@require_POST
@login_required
def term_edit_post(request, pk: int):
    """
    自分の用語のみ編集可能。単一レコード編集の保存（POST）
    """
    t = get_object_or_404(Term.objects.select_related("user"), pk=pk, user=request.user)

    term_value = (request.POST.get("term") or "").strip()
    definition_value = (request.POST.get("definition") or "").strip()
    raw_tag_ids = request.POST.getlist("tag_ids")
    tag_ids = [int(x) for x in raw_tag_ids if x.isdigit()]

    errors = {}
    if not term_value:
        errors["term"] = "必須です。"
    if not definition_value:
        errors["definition"] = "必須です。"

    if errors:
        return render(request, "editterms/editterms.html", {
            "values": {"term": term_value, "definition": definition_value, "tag_ids": tag_ids},
            "errors": errors,
            "all_tags": Tag.objects.order_by("name"),
            "action_url": reverse("terms:edit_post", args=[t.id]),
            "submit_label": "保存する",
            "term_obj": t,
        }, status=400)

    # 更新
    t.term = term_value
    t.definition = definition_value
    t.save(update_fields=["term", "definition", "updated_at"])

    # タグ更新
    if tag_ids:
        tags = list(Tag.objects.filter(id__in=set(tag_ids)))
        t.tags.set(tags)
    else:
        t.tags.clear()

    messages.success(request, "用語を更新しました。")
    return redirect("terms:detail", pk=t.pk)

# =========================
# JSON: 学習/カード用データ
# =========================
@require_GET
@login_required
def terms_api_flashcards(request):
    """
    GET /terms/api/flashcards/?vocab=&q=&tag=&order=random&limit=
    - vocab 指定: その用語集の用語（公開 or 自分）
    - 未指定: 自分の Term のみ
    - desc = definition
    """
    q = (request.GET.get("q") or "").strip()
    vocab = (request.GET.get("vocab") or "").strip()
    tag_id = (request.GET.get("tag") or "").strip()
    order = (request.GET.get("order") or "").strip().lower()
    try:
        limit = int(request.GET.get("limit") or 500)
    except ValueError:
        limit = 500
    limit = max(1, min(limit, 2000))

    if vocab.isdigit():
        v = get_object_or_404(Vocabulary, id=int(vocab))
        if not (v.is_public or v.user_id == request.user.id):
            return JsonResponse({"items": [], "count": 0}, status=403)

        qs = VocabularyTerm.objects.select_related("term").filter(vocabulary=v)\
                                   .prefetch_related("term__tags")
        if q:
            qs = qs.filter(
                Q(term__term__icontains=q) |
                Q(term__definition__icontains=q) |
                Q(term__tags__name__icontains=q)
            ).distinct()
        if tag_id.isdigit():
            qs = qs.filter(term__tags__id=int(tag_id)).distinct()

        qs = qs.order_by("?") if order == "random" else qs.order_by("order_index", "id")
        qs = qs[:limit]

        items = [{
            "id": vt.term_id,
            "term": vt.term.term,
            "desc": vt.term.definition,
            "tags": [tg.name for tg in vt.term.tags.all()],
            "updated_at": timezone.localtime(vt.term.updated_at).isoformat(),
        } for vt in qs]

    else:
        qs = Term.objects.filter(user=request.user).prefetch_related("tags")
        if q:
            qs = qs.filter(
                Q(term__icontains=q) |
                Q(definition__icontains=q) |
                Q(tags__name__icontains=q)
            ).distinct()
        if tag_id.isdigit():
            qs = qs.filter(tags__id=int(tag_id)).distinct()

        qs = qs.order_by("?") if order == "random" else qs.order_by("-updated_at", "-created_at")
        qs = qs[:limit]

        items = [{
            "id": t.id,
            "term": t.term,
            "desc": t.definition,
            "tags": [tg.name for tg in t.tags.all()],
            "updated_at": timezone.localtime(t.updated_at).isoformat(),
        } for t in qs]

    return JsonResponse({"items": items, "count": len(items)}, json_dumps_params={"ensure_ascii": False})


# =========================
# JSON: 1件だけ（モーダル等）
# =========================
@require_GET
@login_required
def term_api_detail(request, term_id: int):
    t = get_object_or_404(Term.objects.prefetch_related("tags"), id=term_id)

    # 自分のTermはOK。 他人Termは公開デッキ or 自分デッキに含まれていればOK
    if t.user_id != request.user.id:
        in_public_vocab = VocabularyTerm.objects.filter(term=t, vocabulary__is_public=True).exists()
        in_my_vocab = VocabularyTerm.objects.filter(term=t, vocabulary__user_id=request.user.id).exists()
        if not (in_public_vocab or in_my_vocab):
            return JsonResponse({"detail": "権限がありません。"}, status=403)

    data = {
        "id": t.id,
        "term": t.term,
        "desc": t.definition,
        "tags": [tg.name for tg in t.tags.all()],
        "updated_at": timezone.localtime(t.updated_at).isoformat(),
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
