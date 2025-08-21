from __future__ import annotations

import json
from typing import Any, Dict

from django.contrib import auth
from django.contrib.auth import get_user_model, authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token

User = get_user_model()


def _json(request: HttpRequest) -> Dict[str, Any]:
    """Request.body を JSON で安全に読む小ヘルパー。"""
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON")


def _ok(payload: Dict[str, Any] | None = None, status: int = 200) -> JsonResponse:
    data = {"ok": True}
    if payload:
        data.update(payload)
    return JsonResponse(data, status=status)


def _err(message: str, *, status: int = 400, fields: Dict[str, Any] | None = None) -> JsonResponse:
    data = {"ok": False, "error": message}
    if fields:
        data["fields"] = fields
    return JsonResponse(data, status=status)


@require_http_methods(["GET"])
def csrf(request: HttpRequest):
    """

    """
    token = get_token(request)
    return _ok({"csrfToken": token})


@csrf_exempt 
@require_http_methods(["POST"])
def signup(request: HttpRequest):
    """
    POST /accounts/api/signup
    Body(JSON):
      { "username": "...", "password": "...", "email": "...", "nickname": "..." }
    """
    try:
        data = _json(request)
    except ValueError:
        return _err("Invalid JSON")

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "")
    email = (data.get("email") or "").strip()
    nickname = (data.get("nickname") or "").strip()

    if not username or not password:
        return _err("username and password are required.", fields={"username": bool(username), "password": bool(password)})

    if User.objects.filter(username=username).exists():
        return _err("Username already taken.", fields={"username": "taken"})

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email or None,
        nickname=nickname or None,
    )
    # サインアップ後に即ログイン
    login(request, user)
    return _ok({"user": {"id": user.id, "username": user.username, "email": user.email, "nickname": getattr(user, "nickname", None)}} , status=201)


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request: HttpRequest):
    """
    POST /accounts/api/login
    Body(JSON): { "username": "...", "password": "..." }
    """
    try:
        data = _json(request)
    except ValueError:
        return _err("Invalid JSON")

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "")

    if not username or not password:
        return _err("username and password are required.")

    user = authenticate(request, username=username, password=password)
    if user is None:
        return _err("Invalid credentials.", status=401)

    login(request, user)
    return _ok({"user": {"id": user.id, "username": user.username, "email": user.email, "nickname": getattr(user, "nickname", None)}})


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request: HttpRequest):
    """
    POST /accounts/api/logout
    """
    if request.user.is_authenticated:
        logout(request)
    return _ok({})


@require_http_methods(["GET"])
@login_required
def me(request: HttpRequest):
    """
    GET /accounts/api/me
    """
    u = request.user
    return _ok({
        "user": {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "nickname": getattr(u, "nickname", None),
            "is_staff": u.is_staff,
            "is_superuser": u.is_superuser,
        }
    })


@csrf_exempt
@require_http_methods(["PATCH", "POST"])  
@login_required
def profile_update(request: HttpRequest):
    """
    PATCH/POST /accounts/api/profile/update
    Body(JSON): 任意 {"email": "...", "nickname": "..."}
    """
    try:
        data = _json(request)
    except ValueError:
        return _err("Invalid JSON")

    email = data.get("email")
    nickname = data.get("nickname")

    u: User = request.user
    if email is not None:
        u.email = (email or "").strip() or None
    if nickname is not None and hasattr(u, "nickname"):
        u.nickname = (nickname or "").strip() or None

    u.save(update_fields=["email"] + (["nickname"] if hasattr(u, "nickname") else []))
    return _ok({
        "user": {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "nickname": getattr(u, "nickname", None),
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def password_change(request: HttpRequest):
    """
    POST /accounts/api/password/change
    Body(JSON): { "old_password": "...", "new_password": "..." }
    """
    try:
        data = _json(request)
    except ValueError:
        return _err("Invalid JSON")

    old_pw = data.get("old_password") or ""
    new_pw = data.get("new_password") or ""

    if not old_pw or not new_pw:
        return _err("old_password and new_password are required.")

    if not request.user.check_password(old_pw):
        return _err("Old password is incorrect.", status=401)

    request.user.set_password(new_pw)
    request.user.save(update_fields=["password"])
    # パスワード変更後もセッションを切らさない
    update_session_auth_hash(request, request.user)
    return _ok({})
