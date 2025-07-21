from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dummy_dashboard_view, name='dashboard'),
]
