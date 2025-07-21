from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.dummy_login_view, name='login'),
]