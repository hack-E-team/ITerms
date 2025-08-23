# app/accounts/views.py
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get("next") or "dashboard:home"
        return redirect(next_url)
    return render(request, "accounts/login.html", {"form": form})

@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")

@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"user_obj": request.user})

@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()  # ユーザー作成
        login(request, user)  # そのままログイン
        return redirect("dashboard:home")

    return render(request, "accounts/signup.html", {"form": form})
