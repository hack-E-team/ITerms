# app/terms/urls.py
from django.urls import path
from . import views

app_name = "terms"

urlpatterns = [
    # 一覧（termslist.html）
    path("", views.terms_list_view, name="list"),

    # 詳細（カードUI; terms.html） — 1件のTermを起点に表示
    path("<int:pk>/", views.term_detail_page, name="detail"),

    # 用語作成
    path("create/", views.term_create_view, name="create"),
    path("create/submit/", views.term_create_post, name="create_post"),

    # JSON API
    path("api/flashcards/", views.terms_api_flashcards, name="api_flashcards"),  # 学習/カード用データ
    path("api/term/<int:term_id>/", views.term_api_detail, name="api_term_detail"),  # 1件だけ
]
