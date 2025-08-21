from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # CSRF 取得（必要なら）
    path("api/csrf/", views.csrf, name="csrf"),

    # 認証系
    path("api/signup/", views.signup, name="signup"),
    path("api/login/", views.login_view, name="login"),
    path("api/logout/", views.logout_view, name="logout"),

    # プロフィール
    path("api/me/", views.me, name="me"),
    path("api/profile/update/", views.profile_update, name="profile_update"),
    path("api/password/change/", views.password_change, name="password_change"),
]
