from django.urls import path
from . import views

app_name = 'terms'

urlpatterns = [
    path('', views.dummy_terms_view, name='terms'),
    path('createterms/', views.dummy_create_terms_view, name='createterms'),  # 用語作成
]