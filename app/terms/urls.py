from django.urls import path
from . import views

app_name = 'terms'

urlpatterns = [
    path('index/', views.dummy_terms_view, name='myterms'),
]