# app/terms/urls.py
from django.urls import path
from . import views

app_name = "terms"

urlpatterns = [
    path("", views.term_list, name="list"),
    path("<int:term_id>/", views.term_detail, name="detail"),
]
