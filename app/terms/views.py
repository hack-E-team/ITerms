from django.shortcuts import render

# def dummy_terms_view(request):
#     return render(request, 'terms/index.html')

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Term
import json


# ------- 一覧 -------
@login_required
@require_http_methods(["GET"])
def term_list(request):
    terms = Term.objects.filter(user=request.user).select_related("vocabulary")
    data = [
        {
            "id": t.id,
            "word": t.word,
            "meaning": t.meaning,
            "vocabulary_id": t.vocabulary.id if t.vocabulary else None,
            "vocabulary_name": getattr(t.vocabulary, "name", None),
        }
        for t in terms
    ]
    return JsonResponse({"results": data})


# ------- 詳細 -------
@login_required
@require_http_methods(["GET"])
def term_detail(request, term_id):
    term = get_object_or_404(Term, id=term_id, user=request.user)
    data = {
        "id": term.id,
        "word": term.word,
        "meaning": term.meaning,
        "vocabulary_id": term.vocabulary.id if term.vocabulary else None,
        "vocabulary_name": getattr(term.vocabulary, "name", None),
    }
    return JsonResponse(data)


# ------- 作成 -------
@login_required
@require_http_methods(["POST"])
def term_create(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    word = payload.get("word")
    meaning = payload.get("meaning")
    vocab_id = payload.get("vocabulary_id")

    term = Term.objects.create(
        user=request.user,
        word=word,
        meaning=meaning,
        vocabulary_id=vocab_id,
    )
    return JsonResponse({"id": term.id, "message": "created"}, status=201)


# ------- 更新 -------
@login_required
@require_http_methods(["PUT", "PATCH"])
def term_update(request, term_id):
    term = get_object_or_404(Term, id=term_id, user=request.user)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if "word" in payload:
        term.word = payload["word"]
    if "meaning" in payload:
        term.meaning = payload["meaning"]
    if "vocabulary_id" in payload:
        term.vocabulary_id = payload["vocabulary_id"]
    term.save()

    return JsonResponse({"id": term.id, "message": "updated"})


# ------- 削除 -------
@login_required
@require_http_methods(["DELETE"])
def term_delete(request, term_id):
    term = get_object_or_404(Term, id=term_id, user=request.user)
    term.delete()
    return JsonResponse({"id": term_id, "message": "deleted"})
