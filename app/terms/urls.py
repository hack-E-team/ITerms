from django.urls import path
from . import views

app_name = 'terms'

# urlpatterns = [
#     path('index/', views.dummy_terms_view, name='myterms'),
# ]
from django.urls import path
from . import views

app_name = "terms"

urlpatterns = [
    path("api/terms/", views.term_list, name="term_list"),
    path("api/terms/create/", views.term_create, name="term_create"),
    path("api/terms/<int:term_id>/", views.term_detail, name="term_detail"),
    path("api/terms/<int:term_id>/update/", views.term_update, name="term_update"),
    path("api/terms/<int:term_id>/delete/", views.term_delete, name="term_delete"),
]
