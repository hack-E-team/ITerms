# app/terms/views.py
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse

from .models import Vocabulary, VocabularyTerm, Term, UserFavoriteVocabulary  # noqa: F401


# =========================
# 一覧（termslist.html）
# =========================
@require_GET
@login_required
def terms_list_view(request):
    """
    /terms/?q=&vocab=&page=
    - 基本は「自分の Term」を一覧表示（ページング）
    - ?vocab=<id> があれば“自分の”用語集に含まれる Term のみ
    """
    q = (request.GET.get("q") or "").strip()
    vocab = (request.GET.get("vocab") or "").strip()

    qs = Term.objects.filter(user=request.user)

    selected_vocab = None
    if vocab.isdigit():
        selected_vocab = get_object_or_404(Vocabulary, id=int(vocab), user=request.user)
        qs = qs.filter(vocabulary_entries__vocabulary=selected_vocab).distinct()

    if q:
        qs = qs.filter(Q(term_name__icontains=q) | Q(description__icontains=q))

    qs = qs.order_by("-updated_at", "-created_at")

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "terms/termslist.html", {
        "page_obj": page_obj,
        "q": q,
        "selected_vocab": selected_vocab,
    })


# =========================
# 詳細ページ（カードUI; terms.html）
# =========================
@require_GET
@login_required
def term_detail_page(request, pk: int):
    """
    /terms/<pk>/?vocab=&q=&order=
    - terms.html を描画（JSが /terms/api/flashcards/ を叩く）
    - initial_term_id をテンプレへ渡し、JSがセット内でその位置にジャンプ
    - 表示権限:
        * 自分のTerm もしくは
        * 公開Vocabularyに含まれているTerm もしくは
        * 自分のVocabularyに含まれている（?vocab 指定時）
    """
    term = get_object_or_404(Term, pk=pk)

    vocab_id = (request.GET.get("vocab") or "").strip()
    via_vocab = None
    vt = None

    owned = (term.user_id == request.user.id)
    in_public_vocab = VocabularyTerm.objects.filter(term=term, vocabulary__is_public=True).exists()

    in_my_vocab = False
    if vocab_id.isdigit():
        via_vocab = get_object_or_404(Vocabulary, id=int(vocab_id))
        # 非公開の他人デッキは不可
        if not (via_vocab.is_public or via_vocab.user_id == request.user.id):
            raise Http404()
        vt = VocabularyTerm.objects.filter(vocabulary=via_vocab, term=term).first()
        in_my_vocab = bool(vt) and (via_vocab.user_id == request.user.id)

    if not (owned or in_public_vocab or in_my_vocab):
        raise Http404()

    # terms.html へ最低限の情報を渡す（データ本体はAPIから取得）
    return render(request, "terms/terms.html", {
        "initial_term_id": term.id,
        "selected_vocab": via_vocab,  # None の場合もあり
        "q": (request.GET.get("q") or "").strip(),
        "order": (request.GET.get("order") or "").strip(),
    })


# =========================
# 用語作成（GET/POST）
# =========================
@require_GET
@login_required
def term_create_view(request):
    return render(request, "createterms/createterms.html", {
        "values": {"term_name": "", "description": ""},
        "errors": {},
    })

@require_POST
@transaction.atomic
@login_required
def term_create_post(request):
    term_name = (request.POST.get("term_name") or "").strip()
    description = (request.POST.get("description") or "").strip()

    errors = {}
    if not term_name:
        errors["term_name"] = "必須です。"

    if errors:
        return render(request, "createterms/createterms.html", {
            "values": {"term_name": term_name, "description": description},
            "errors": errors,
        }, status=400)

    obj = Term.objects.create(
        user=request.user,
        term_name=term_name,
        description=description,
    )
    messages.success(request, f'用語「{obj.term_name}」を作成しました。')
    return redirect("terms:list")


# =========================
# JSON: 学習/カード用データ
# =========================
@require_GET
@login_required
def terms_api_flashcards(request):
    """
    GET /terms/api/flashcards/?vocab=&q=&order=random&limit=
    - vocab 指定: その用語集の用語（公開 or 自分）
    - 未指定: 自分の全Term
    - desc（= description）で統一
    """
    q = (request.GET.get("q") or "").strip()
    vocab = (request.GET.get("vocab") or "").strip()
    order = (request.GET.get("order") or "").strip().lower()
    try:
        limit = int(request.GET.get("limit") or 500)
    except ValueError:
        limit = 500
    limit = max(1, min(limit, 2000))

    if vocab.isdigit():
        v = get_object_or_404(Vocabulary, id=int(vocab))
        if not (v.user_id == request.user.id or v.is_public):
            return JsonResponse({"items": [], "count": 0}, status=403)

        qs = VocabularyTerm.objects.select_related("term").filter(vocabulary=v)
        if q:
            qs = qs.filter(Q(term__term_name__icontains=q) | Q(term__description__icontains=q))
        qs = qs.order_by("?") if order == "random" else qs.order_by("order_index", "id")
        qs = qs[:limit]

        items = [{
            "id": vt.term_id,
            "term": vt.term.term_name,
            "desc": vt.term.description,
            "updated_at": timezone.localtime(vt.term.updated_at).isoformat(),
        } for vt in qs]

    else:
        qs = Term.objects.filter(user=request.user)
        if q:
            qs = qs.filter(Q(term_name__icontains=q) | Q(description__icontains=q))
        qs = qs.order_by("?") if order == "random" else qs.order_by("-updated_at", "-created_at")
        qs = qs[:limit]

        items = [{
            "id": t.id,
            "term": t.term_name,
            "desc": t.description,
            "updated_at": timezone.localtime(t.updated_at).isoformat(),
        } for t in qs]

    return JsonResponse({"items": items, "count": len(items)}, json_dumps_params={"ensure_ascii": False})


# =========================
# JSON: 1件だけ（任意：モーダル等で使う）
# =========================
@require_GET
@login_required
def term_api_detail(request, term_id: int):
    t = get_object_or_404(Term, id=term_id)

    if t.user_id != request.user.id:
        in_public_vocab = VocabularyTerm.objects.filter(term=t, vocabulary__is_public=True).exists()
        if not in_public_vocab:
            return JsonResponse({"detail": "権限がありません。"}, status=403)

    data = {
        "id": t.id,
        "term": t.term_name,
        "desc": t.description,
        "updated_at": timezone.localtime(t.updated_at).isoformat(),
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
