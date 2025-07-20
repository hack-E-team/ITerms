from django.urls import path
from . import views

urlpatterns = [
    path('myvocabularies/', views.myvocabularies_view, name='myvocabularies'),
]