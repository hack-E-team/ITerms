# app/terms/urls.py
from django.urls import path
from .views import terms_api_flashcards, terms_learn_view, terms_list_view, term_create_view, term_create_post

app_name = "terms"

urlpatterns = [
    path("", terms_list_view, name="list"),
    path("create/", term_create_view, name="create"),
    path("create/submit/", term_create_post, name="create_post"),
    path("learn/", terms_learn_view, name="learn"),  # ← 学習ページ
    path("api/flashcards/", terms_api_flashcards, name="api_flashcards"),  # ← JSON API
]
