# app/accounts/views.py
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

UserModel = get_user_model()

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""

        # authenticate は引数名が username 固定だが、UserModel.USERNAME_FIELD を見てくれる
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next") or "dashboard:dashboard"
            return redirect(next_url)

        messages.error(request, "メールアドレスまたはパスワードが正しくありません。")

    return render(request, "accounts/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        password_confirm = request.POST.get("password_confirm") or ""
        nickname = (request.POST.get("nickname") or "").strip()

        errs = []
        if not email:
            errs.append("メールアドレスを入力してください。")
        if not password:
            errs.append("パスワードを入力してください。")
        if password != password_confirm:
            errs.append("パスワードが一致しません。")
        if UserModel.objects.filter(**{f"{UserModel.USERNAME_FIELD}__iexact": email}).exists():
            errs.append("このメールアドレスは既に登録されています。")

        # パスワードバリデーション
        try:
            validate_password(password)
        except ValidationError as e:
            errs.extend(e.messages)

        if errs:
            for m in errs:
                messages.error(request, m)
            return render(request, "sign_up/sign_up.html")

        # 作成（Manager の create_user が nickname を受けない場合に備えて安全に）
        user = UserModel(**{UserModel.USERNAME_FIELD: email})
        if hasattr(user, "email") and not getattr(user, "email"):
            user.email = email
        if hasattr(user, "nickname"):
            user.nickname = nickname
        user.set_password(password)
        user.save()

        login(request, user)
        return redirect("dashboard:dashboard")

    return render(request, "sign_up/sign_up.html")


@login_required
def profile_view(request):
    # 以前のテンプレが user_obj を使っていたので合わせます
    return render(request, "accounts/profile.html", {"user_obj": request.user})