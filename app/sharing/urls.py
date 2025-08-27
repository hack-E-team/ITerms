from django.urls import path
from . import views

app_name = 'sharing'

urlpatterns = [
    
    path('ping/', views.ping, name='ping'),


    path('create/', views.create_share, name='create'),
    path('<str:token>/revoke/', views.revoke_share, name='revoke'),

    
    path('<str:token>/', views.open_share, name='open'),
]
