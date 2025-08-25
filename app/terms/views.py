# app/terms/views.py
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages

from .models import Vocabulary, VocabularyTerm, Term, UserFavoriteVocabulary

# ------------------------------------------------------------
# 一覧（terms.html を listモードで表示）
# ------------------------------------------------------------
@require_GET
@login_required
def terms_list_view(request):
    """
    ?q= 検索 / ?vocab=<id> 用語集で絞り込み / ?page=
    self-owned の用語 or 指定 vocabulary の用語を一覧表示
    """
    q = (request.GET.get("q") or "").strip()
    vocab = (request.GET.get("vocab") or "").strip()

    # 自分の用語（Term）
    qs = Term.objects.filter(user=request.user).order_by("-updated_at", "-created_at")

    # 用語集指定があれば、その用語集に含まれる用語だけに絞る
    selected_vocab = None
    if vocab.isdigit():
        selected_vocab = get_object_or_404(
            Vocabulary,
            id=int(vocab),
            # 自分の用語集 or 公開の用語集（自分以外でも閲覧OK）
            # 学習は公開でもOKだが、一覧は自分用語の管理視点が多いので owner優先
            # 必要なら is_public=True も許可に切替可
            user=request.user
        )
        qs = qs.filter(vocabulary_entries__vocabulary=selected_vocab).distinct()

    if q:
        qs = qs.filter(
            Q(term_name__icontains=q) |
            Q(description__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "terms/terms.html", {
        "mode": "list",
        "page_obj": page_obj,
        "q": q,
        "selected_vocab": selected_vocab,
    })


# ------------------------------------------------------------
# 学習（terms.html を learnモードで表示）
# ------------------------------------------------------------
@require_GET
@login_required
def terms_learn_view(request):
    """
    学習モード。?vocab=<id> を渡すと、その用語集だけが学習対象。
    データ本体は /terms/api/flashcards/ をフロントJSが叩く。
    """
    q = (request.GET.get("q") or "").strip()
    vocab = (request.GET.get("vocab") or "").strip()

    selected_vocab = None
    if vocab.isdigit():
        # 公開用語集は閲覧可、自分の用語集もOK
        selected_vocab = get_object_or_404(
            Vocabulary,
            id=int(vocab),
        )
        if not (selected_vocab.user_id == request.user.id or selected_vocab.is_public):
            # 非公開の他人用語集はNG
            return render(request, "terms/terms.html", {
                "mode": "learn",
                "q": q,
                "selected_vocab": None,
                "error": "この用語集は閲覧できません。"
            }, status=403)

    return render(request, "terms/terms.html", {
        "mode": "learn",
        "q": q,
        "selected_vocab": selected_vocab,
    })


# ------------------------------------------------------------
# 用語作成（GET/POST） — フィールド名に合わせて修正
# ------------------------------------------------------------
@require_GET
@login_required
def term_create_view(request):
    return render(request, "createterms/createterms.html", {
        "values": {"term_name": "", "description": ""},
        "errors": {},
        # 用語作成時点では Vocabulary は紐付けない（後でVocabularyTerm作成）
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


# ------------------------------------------------------------
# 学習用 API（JSON） — ?vocab= で用語集単位の学習
# ------------------------------------------------------------
@require_GET
@login_required
def terms_api_flashcards(request):
    """
    GET /terms/api/flashcards/?vocab=&q=&order=random&limit=
    - vocab: 指定があれば、その用語集の用語だけ（公開 or 自分の用語集）
             無ければ「自分の用語」全体
    - q: term_name / description の部分一致
    - order=random でランダム
    """
    q = (request.GET.get("q") or "").strip()
    vocab = (request.GET.get("vocab") or "").strip()
    order = (request.GET.get("order") or "").strip().lower()
    try:
        limit = int(request.GET.get("limit") or 500)
    except ValueError:
        limit = 500
    limit = max(1, min(limit, 2000))

    # ベースクエリ
    if vocab.isdigit():
        v = get_object_or_404(Vocabulary, id=int(vocab))
        # 権限：自分の用語集 or 公開
        if not (v.user_id == request.user.id or v.is_public):
            return JsonResponse({"items": [], "count": 0}, status=403)
        # 用語集に含まれる Term を join で取得
        qs = Term.objects.filter(vocabulary_entries__vocabulary=v).distinct()
    else:
        # 自分の全Term
        qs = Term.objects.filter(user=request.user)

    qs = qs.order_by("-updated_at", "-created_at")

    if q:
        qs = qs.filter(Q(term_name__icontains=q) | Q(description__icontains=q))

    if order == "random":
        qs = qs.order_by("?")

    qs = qs[:limit]

    items = [{
        "id": t.id,
        "term": t.term_name,           # ← フロント既存キーに合わせる
        "desc": t.description,         # ← desc にマップ
        "tags": [],                    # タグ無しモデルなので空配列
        "updated_at": t.updated_at.astimezone(timezone.get_current_timezone()).isoformat(),
    } for t in qs]

    return JsonResponse({"items": items, "count": len(items)}, json_dumps_params={"ensure_ascii": False})


# ------------------------------------------------------------
# 詳細モーダル API（1件）
# ------------------------------------------------------------
@require_GET
@login_required
def term_api_detail(request, term_id: int):
    t = get_object_or_404(Term, id=term_id)

    # 自分の用語 もしくは、（もし用語集経由で見る場合を想定するなら）公開用語集に含まれていれば閲覧可
    owned = (t.user_id == request.user.id)
    if not owned:
        # 公開用語集経由の閲覧許可（必要な場合）
        in_public_vocab = VocabularyTerm.objects.filter(
            term=t, vocabulary__is_public=True
        ).exists()
        if not in_public_vocab:
            return JsonResponse({"detail": "権限がありません。"}, status=403)

    data = {
        "id": t.id,
        "term": t.term_name,
        "desc": t.description,
        "tags": [],
        "updated_at": t.updated_at.astimezone(timezone.get_current_timezone()).isoformat(),
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
