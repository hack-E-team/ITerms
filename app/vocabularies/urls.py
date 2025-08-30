# app/vocabularies/urls.py
from django.urls import path
from .views import (
    vocabulary_list_view,
    vocabulary_detail_view,
    vocabulary_create_view,
    vocabulary_create_post,
    discover_vocabularies_view,
    discover_add_favorite_view,
    favorite_remove_view,
    vocabulary_learn_view,
    vocabulary_api_flashcards,
    vocabulary_edit_view,
    vocabulary_edit_post,
)

app_name = "vocabularies"

urlpatterns = [
    path("", vocabulary_list_view, name="myvocabularies"),
    path("create/", vocabulary_create_view, name="vocabulariescreate"),
    path("create/submit/", vocabulary_create_post, name="create_post"),

    path("<int:pk>/edit/", vocabulary_edit_view, name="edit"),
    path("<int:pk>/edit/submit/", vocabulary_edit_post, name="edit_post"),

    path("discover/", discover_vocabularies_view, name="vocabulariesSearch"),
    path("discover/favorite/", discover_add_favorite_view, name="discover_favorite"),
    path("favorite/remove/", favorite_remove_view, name="favorite_remove"),

    path("<int:pk>/learn/", vocabulary_learn_view, name="learn"),
    path("<int:pk>/api/flashcards/", vocabulary_api_flashcards, name="api_fc"),

    path("<int:pk>/", vocabulary_detail_view, name="detail"),
]