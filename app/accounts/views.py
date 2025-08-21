from __future__ import annotations
from typing import Dict, Any

from django.contrib.auth import get_user_model, authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

User = get_user_model()
HAS_NICK = hasattr(User, "nickname")


def _vals(request) -> Dict[str, Any]:
    """テンプレートへ返す共通値（入力値の保持など）"""
    d = {
        "username": (request.POST.get("username") or "").strip(),
        "email": (request.POST.get("email") or "").strip(),
    }
    if HAS_NICK:
        d["nickname"] = (request.POST.get("nickname") or "").strip()
    return d


@require_http_methods(["GET", "POST"])
@csrf_protect
def signup_view(request):
    if request.method == "GET":
        return render(request, "accounts/signup.html")

    values = _vals(request)
    password = request.POST.get("password") or ""
    errors: Dict[str, str] = {}

    if not values["username"]:
        errors["username"] = "ユーザー名は必須です。"
    if not password:
        errors["password"] = "パスワードは必須です。"
    if values["username"] and User.objects.filter(username=values["username"]).exists():
        errors["username"] = "このユーザー名は既に使用されています。"

    if errors:
        return render(request, "accounts/signup.html", {"errors": errors, "values": values}, status=400)

    kwargs = {"email": values["email"] or None}
    if HAS_NICK:
        kwargs["nickname"] = (values.get("nickname") or "").strip()

    user = User.objects.create_user(values["username"], password=password, **kwargs)
    login(request, user)
    return redirect("accounts:me")


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    if request.method == "GET":
        return render(request, "accounts/login.html")

    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    errors: Dict[str, str] = {}

    if not username:
        errors["username"] = "ユーザー名は必須です。"
    if not password:
        errors["password"] = "パスワードは必須です。"

    if not errors:
        user = authenticate(request, username=username, password=password)
        if user is None:
            errors["non_field"] = "ユーザー名またはパスワードが違います。"
        else:
            login(request, user)
            return redirect("accounts:me")

    return render(request, "accounts/login.html", {"errors": errors, "values": {"username": username}}, status=401)


@require_http_methods(["POST"])
@csrf_protect
@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@require_http_methods(["GET"])
@login_required
def me_view(request):
    return render(request, "accounts/me.html", {"u": request.user})


@require_http_methods(["GET", "POST"])
@csrf_protect
@login_required
def profile_view(request):
    if request.method == "GET":
        init = {"email": request.user.email or ""}
        if HAS_NICK:
            init["nickname"] = getattr(request.user, "nickname", "") or ""
        return render(request, "accounts/profile.html", {"values": init})

    email = (request.POST.get("email") or "").strip()
    nickname = (request.POST.get("nickname") or "").strip() if HAS_NICK else ""

    errors: Dict[str, str] = {}
    # 必要なら email の簡易バリデーションを追加
    # if email and "@" not in email: errors["email"] = "メール形式が不正です。"

    if errors:
        values = {"email": email}
        if HAS_NICK:
            values["nickname"] = nickname or ""
        return render(request, "accounts/profile.html", {"errors": errors, "values": values}, status=400)

    u: User = request.user
    u.email = email or None
    if HAS_NICK:
        u.nickname = nickname
    u.save(update_fields=["email"] + (["nickname"] if HAS_NICK else []))
    return redirect("accounts:me")


@require_http_methods(["GET", "POST"])
@csrf_protect
@login_required
def password_change_view(request):
    if request.method == "GET":
        return render(request, "accounts/password_change.html")

    old_pw = request.POST.get("old_password") or ""
    new_pw = request.POST.get("new_password") or ""
    errors: Dict[str, str] = {}

    if not old_pw:
        errors["old_password"] = "現在のパスワードを入力してください。"
    if not new_pw:
        errors["new_password"] = "新しいパスワードを入力してください。"

    if not errors and not request.user.check_password(old_pw):
        errors["old_password"] = "現在のパスワードが違います。"

    if errors:
        return render(request, "accounts/password_change.html", {"errors": errors}, status=400)

    request.user.set_password(new_pw)
    request.user.save(update_fields=["password"])
    update_session_auth_hash(request, request.user)  # セッション維持
    return redirect("accounts:me")
