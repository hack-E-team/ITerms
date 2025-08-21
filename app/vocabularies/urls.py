from django.urls import path
from . import views

app_name = 'vocabularies'

# urlpatterns = [
#     path('index/', views.dummy_vocabularies_view, name='myvocabularies'),
# ]

from django.urls import path
from . import views

app_name = "vocabularies"

urlpatterns = [
    # CRUD
    path("api/vocabularies/", views.vocab_list, name="vocab_list"),
    path("api/vocabularies/create/", views.vocab_create, name="vocab_create"),
    path("api/vocabularies/<int:vocab_id>/", views.vocab_detail, name="vocab_detail"),
    path("api/vocabularies/<int:vocab_id>/update/", views.vocab_update, name="vocab_update"),
    path("api/vocabularies/<int:vocab_id>/delete/", views.vocab_delete, name="vocab_delete"),

    # 付録：その単語帳の用語一覧
    path("api/vocabularies/<int:vocab_id>/terms/", views.vocab_terms, name="vocab_terms"),
]
