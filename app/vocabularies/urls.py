from django.urls import path
from . import views

app_name = 'vocabularies'

urlpatterns = [
    path('index/', views.dummy_vocabularies_view, name='myvocabularies'),
]