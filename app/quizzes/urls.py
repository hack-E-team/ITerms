from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.dummy_quizzes_view, name='quizzes'),
]