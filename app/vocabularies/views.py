from django.shortcuts import render

# def dummy_vocabularies_view(request):
#     return render(request, 'vocabularies/index.html')

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Vocabulary
from terms.models import Term
import json


def _json_bad_request():
    return JsonResponse({"error": "Invalid JSON"}, status=400)


# ------- 一覧 -------
@login_required
@require_http_methods(["GET"])
def vocab_list(request):
    """ログインユーザーの単語帳一覧"""
    vocabs = Vocabulary.objects.filter(user=request.user)
    data = [
        {
            "id": v.id,
            "name": v.name,
            "description": getattr(v, "description", "") or "",
        }
        for v in vocabs
    ]
    return JsonResponse({"results": data})


# ------- 詳細 -------
@login_required
@require_http_methods(["GET"])
def vocab_detail(request, vocab_id):
    """単語帳の詳細"""
    v = get_object_or_404(Vocabulary, id=vocab_id, user=request.user)
    data = {
        "id": v.id,
        "name": v.name,
        "description": getattr(v, "description", "") or "",
    }
    return JsonResponse(data)


# ------- 作成 -------
@login_required
@require_http_methods(["POST"])
def vocab_create(request):
    """単語帳の作成"""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return _json_bad_request()

    name = (payload.get("name") or "").strip()
    description = (payload.get("description") or "").strip()

    if not name:
        return JsonResponse({"error": "name is required"}, status=400)

    v = Vocabulary.objects.create(
        user=request.user,
        name=name,
        description=description,
    )
    return JsonResponse({"id": v.id, "message": "created"}, status=201)


# ------- 更新 -------
@login_required
@require_http_methods(["PUT", "PATCH"])
def vocab_update(request, vocab_id):
    """単語帳の更新"""
    v = get_object_or_404(Vocabulary, id=vocab_id, user=request.user)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return _json_bad_request()

    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            return JsonResponse({"error": "name must not be empty"}, status=400)
        v.name = name
    if "description" in payload:
        v.description = (payload.get("description") or "").strip()
    v.save()

    return JsonResponse({"id": v.id, "message": "updated"})


# ------- 削除 -------
@login_required
@require_http_methods(["DELETE"])
def vocab_delete(request, vocab_id):
    """単語帳の削除"""
    v = get_object_or_404(Vocabulary, id=vocab_id, user=request.user)
    v.delete()
    return JsonResponse({"id": vocab_id, "message": "deleted"})


# ------- 付録：ある単語帳の用語一覧 -------
@login_required
@require_http_methods(["GET"])
def vocab_terms(request, vocab_id):
    """単語帳に属する Term 一覧（軽量）"""
    v = get_object_or_404(Vocabulary, id=vocab_id, user=request.user)
    terms = Term.objects.filter(user=request.user, vocabulary=v).only("id", "word", "meaning")
    data = [
        {"id": t.id, "word": t.word, "meaning": t.meaning}
        for t in terms
    ]
    return JsonResponse({"vocabulary_id": v.id, "vocabulary_name": v.name, "results": data})
