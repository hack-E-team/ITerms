# app/vocabularies/urls.py
from django.urls import path
from .views import (
    vocabulary_list_view,
    vocabulary_detail_view,
    vocabulary_create_view,
    vocabulary_create_post,
    discover_vocabularies_view,
    discover_add_favorite_view,
    vocabulary_learn_view,
    vocabulary_api_flashcards,
)

app_name = "vocabularies"

urlpatterns = [
    # 一覧・作成
    path("", vocabulary_list_view, name="list"),
    path("create/", vocabulary_create_view, name="create"),
    path("create/submit/", vocabulary_create_post, name="create_post"),

    # 他人の用語帳を探す & お気に入り追加
    path("discover/", discover_vocabularies_view, name="discover"),
    path("discover/favorite/", discover_add_favorite_view, name="discover_favorite"),

    # 学習ページ & API（用語帳に紐づく）
    path("<int:pk>/learn/", vocabulary_learn_view, name="learn"),
    path("<int:pk>/api/flashcards/", vocabulary_api_flashcards, name="api_fc"),

    # 詳細
    path("<int:pk>/", vocabulary_detail_view, name="detail"),
]