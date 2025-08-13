from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta

from .models import ShareLink

def ping(request):
    return JsonResponse({"ok": True})

def _serialize_target(obj):
    """
    簡易シリアライズ（フロントが後で置き換え可能）
    対応: Vocabulary / Term / Quiz
    """
    model = obj.__class__.__name__.lower()
    data = {"model": model, "id": obj.id}

    # ざっくり代表項目
    if model == "vocabulary":
        data.update({"name": getattr(obj, "name", None)})
    elif model == "term":
        data.update({"word": getattr(obj, "word", None), "meaning": getattr(obj, "meaning", None)})
    elif model == "quiz":
        data.update({"question": getattr(obj, "question_text", None)})
    return data

@require_http_methods(["GET"])
def open_share(request, token: str):
    """
    公開（認証不要）。トークンが有効なら対象の軽量データを返す。
    """
    link = get_object_or_404(ShareLink, token=token)
    if not link.is_valid():
        raise Http404("Link invalid or expired")

    link.touch()
    return JsonResponse({
        "token": link.token,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "data": _serialize_target(link.target),
    })

@login_required
@require_http_methods(["POST"])
def create_share(request):
    """
    共有リンクを作る（POST）。
    パラメータ: model, object_id, days(optional)
    例: model=terms.term, object_id=1, days=7
    """
    model_label = request.POST.get("model")  # 例 "terms.term"
    object_id = request.POST.get("object_id")
    days = request.POST.get("days")

    if not model_label or not object_id:
        return JsonResponse({"error": "model and object_id are required"}, status=400)

    try:
        ct = ContentType.objects.get_by_natural_key(*model_label.split("."))
    except Exception:
        return JsonResponse({"error": "invalid model"}, status=400)

    target = ct.get_object_for_this_type(pk=object_id)

    expires_at = None
    if days:
        try:
            d = int(days)
            if d > 0:
                expires_at = timezone.now() + timedelta(days=d)
        except ValueError:
            pass

    link = ShareLink.objects.create(
        content_type=ct,
        object_id=target.id,
        creator=request.user,
        expires_at=expires_at,
    )
    return JsonResponse({"token": link.token, "url": f"/sharing/{link.token}/", "expires_at": expires_at.isoformat() if expires_at else None})

@login_required
@require_http_methods(["POST"])
def revoke_share(request, token: str):
    link = get_object_or_404(ShareLink, token=token, creator=request.user)
    link.is_active = False
    link.save(update_fields=["is_active"])
    return JsonResponse({"revoked": True, "token": token})
