# urlpatterns = [
#    path('index/', views.dummy_quizzes_view, name='quizzes'),
#]

from django.urls import path
from . import views

app_name = "quizzes"

urlpatterns = [
    path("play/<int:term_id>/<str:qtype>/", views.play, name="play"),  # qtype: DT or TD
    path("play/<int:term_id>/", views.play, {"qtype": "DT"}, name="play_default"),
]
