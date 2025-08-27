from django.urls import path
from . import views

app_name = 'dashboard'

# urlpatterns = [
#     path('', views.dummy_dashboard_view, name='dashboard'),
# ]

urlpatterns = [
    path("", views.home, name="home"),
    path('summary', views.summary, name='summary'),          # ?days=30
    path('recent', views.recent, name='recent'),             # ?days=30&limit=20&offset=0
    path('vocabs', views.vocabs, name='vocabs'),             # ?days=90
    path('daily', views.daily, name='daily'),                # ?days=30
]
