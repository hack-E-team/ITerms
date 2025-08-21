from django.urls import path
from . import views

app_name = 'vocabularies'

urlpatterns = [
    path('index/', views.dummy_vocabularies_view, name='myvocabularies'),
    path('vocabulariesSearch/', views.dummy_vocabularies_search_view, name='vocabulariesSearch'),  # 用語帳検索
]