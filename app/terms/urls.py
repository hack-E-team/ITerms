# app/terms/urls.py
from django.urls import path
from . import views

app_name = "terms"

urlpatterns = [
    # 一覧（= terms.html の listモード）
    path("", views.terms_list_view, name="list"),

    # 作成（既存を維持）
    path("create/", views.term_create_view, name="create"),
    path("create/submit/", views.term_create_post, name="create_post"),

    # 学習（= terms.html の learnモード。?vocab=<id> で用語集単位）
    path("learn/", views.terms_learn_view, name="learn"),

    # 学習用API（?vocab=<id>&q=&order=random&limit=...）
    path("api/flashcards/", views.terms_api_flashcards, name="api_flashcards"),

    # モーダル詳細API（1件）
    path("api/term/<int:term_id>/", views.term_api_detail, name="api_term_detail"),
]
