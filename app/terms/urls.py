# app/terms/urls.py
from django.urls import path
from . import views

app_name = "terms"

urlpatterns = [
    path("list/", views.terms_list_view, name="list"),

    # 用語作成
    path("myterms/", views.term_create_view, name="createterms"),
    path("create/submit/", views.term_create_post, name="create_post"),
    
    
    path("<int:pk>/edit/", views.term_edit_view, name="edit"),
    path("<int:pk>/edit/submit/", views.term_edit_post, name="edit_post"),

    # JSON API
    path("api/flashcards/", views.terms_api_flashcards, name="api_flashcards"),
    path("api/term/<int:term_id>/", views.term_api_detail, name="api_term_detail"),

    # 詳細（動的パスは最後に）
    path("<int:pk>/", views.term_detail_page, name="detail"),
]
