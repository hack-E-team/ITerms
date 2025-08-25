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

from .models import Term, Tag
from vocabularies.models import Vocabulary, VocabularyTerm


# =========================
# 一覧（termslist.html）
# =========================
@require_GET
@login_required
def terms_list_view(request):
    """
    /terms/?q=&vocab=&page=
    - デフォルト: Term の全件（所有者フィールドが無いため全体）
    - ?vocab=<id>: 指定用語集に含まれる Term のみに絞り込み
      （非公開デッキは作成者のみ）
    """
    q = (request.GET.get("q") or "").strip()
    vocab = (request.GET.get("vocab") or "").strip()

    qs = Term.objects.all()

    selected_vocab = None
    if vocab.isdigit():
        selected_vocab = get_object_or_404(Vocabulary, id=int(vocab))
        # 権限: 非公開は作成者のみ
        if not (selected_vocab.is_public or selected_vocab.user_id == request.user.id):
            raise Http404()
        qs = qs.filter(vocabulary_entries__vocabulary=selected_vocab).distinct()

    if q:
        qs = qs.filter(
            Q(term__icontains=q) |
            Q(definition__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct()

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
    - initial_term_id をテンプレへ渡し、セット内でその位置にジャンプ
    - 表示権限:
        * その Term が「公開の用語集」に含まれる or
        * ?vocab 指定の用語集が自分のもの
        * （Term自体に所有者が無い前提のため、用語集単位でアクセス制御）
    """
    term = get_object_or_404(Term, pk=pk)

    vocab_id = (request.GET.get("vocab") or "").strip()
    via_vocab = None
    vt = None

    in_public_vocab = VocabularyTerm.objects.filter(
        term=term, vocabulary__is_public=True
    ).exists()

    in_my_vocab = False
    if vocab_id.isdigit():
        via_vocab = get_object_or_404(Vocabulary, id=int(vocab_id))
        if not (via_vocab.is_public or via_vocab.user_id == request.user.id):
            raise Http404()
        vt = VocabularyTerm.objects.filter(vocabulary=via_vocab, term=term).first()
        in_my_vocab = bool(vt) and (via_vocab.user_id == request.user.id)

    if not (in_public_vocab or in_my_vocab or via_vocab is None):
        # 公開にも自分デッキにも無い場合は非許可
        raise Http404()

    return render(request, "terms/terms.html", {
        "initial_term_id": term.id,
        "selected_vocab": via_vocab,  # None の場合もあり
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
@transaction.atomic
@login_required
def term_create_post(request):
    # テンプレのnameに合わせる: term / description(=definitionに保存)
    term_value = (request.POST.get("term") or "").strip()
    definition_value = (request.POST.get("description") or "").strip()
    raw_tag_ids = request.POST.getlist("tag_ids")

    errors = {}
    if not term_value:
        errors["term"] = "必須です。"
    if not definition_value:
        errors["definition"] = "必須です。"

    tag_ids = [int(x) for x in raw_tag_ids if x.isdigit()]

    if errors:
        return render(request, "createterms/createterms.html", {
            "values": {"term": term_value, "definition": definition_value, "tag_ids": tag_ids},
            "errors": errors,
            "all_tags": Tag.objects.order_by("name"),
        }, status=400)

    obj = Term.objects.create(
        term=term_value,
        definition=definition_value,
    )
    if tag_ids:
        selected = list(Tag.objects.filter(id__in=set(tag_ids)))
        if selected:
            obj.tags.add(*selected)

    messages.success(request, f'用語「{obj.term}」を作成しました。')
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
    - 未指定: Term 全体（所有者フィールドが無いため）
    - desc = definition
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
        if not (v.is_public or v.user_id == request.user.id):
            return JsonResponse({"items": [], "count": 0}, status=403)

        qs = VocabularyTerm.objects.select_related("term").filter(vocabulary=v)
        if q:
            qs = qs.filter(Q(term__term__icontains=q) | Q(term__definition__icontains=q) |
                           Q(term__tags__name__icontains=q)).distinct()
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
        qs = Term.objects.all()
        if q:
            qs = qs.filter(Q(term__icontains=q) | Q(definition__icontains=q) |
                           Q(tags__name__icontains=q)).distinct()
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
    t = get_object_or_404(Term, id=term_id)

    # 公開デッキ or 自分のデッキに含まれていれば閲覧可（Termに所有者が無い想定）
    in_public_vocab = VocabularyTerm.objects.filter(term=t, vocabulary__is_public=True).exists()
    in_my_vocab = VocabularyTerm.objects.filter(term=t, vocabulary__user_id=request.user.id).exists()
    if not (in_public_vocab or in_my_vocab):
        # どのデッキにも無い用語をどう扱うかは要件次第。ここでは閲覧OKにしても良い。
        pass

    data = {
        "id": t.id,
        "term": t.term,
        "desc": t.definition,
        "tags": [tg.name for tg in t.tags.all()],
        "updated_at": timezone.localtime(t.updated_at).isoformat(),
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
