# app/quizzes/urls.py
from django.urls import path
from . import views

app_name = "quizzes"

urlpatterns = [
    path("", views.index, name="index"),
    path("play/<int:term_id>/<str:qtype>/", views.play, name="play"),
    path("play/<int:term_id>/", views.play, name="play-default"),
]
