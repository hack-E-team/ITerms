# Register your models here.
from django.contrib import admin
from .models import Vocabulary, VocabularyTerm, UserFavoriteVocabulary

@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_public', 'created_at', 'updated_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'description')
    raw_id_fields = ('user',)
#    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(VocabularyTerm)
class VocabularyTermAdmin(admin.ModelAdmin):
    list_display = ('vocabulary', 'term', 'user', 'order_index', 'created_at')
    list_filter = ('vocabulary',)
    search_fields = ('term__term', 'note')
    raw_id_fields = ('vocabulary', 'term', 'user')
    ordering = ('vocabulary', 'order_index')


@admin.register(UserFavoriteVocabulary)
class UserFavoriteVocabularyAdmin(admin.ModelAdmin):
    list_display = ('user', 'vocabulary', 'added_at')
    list_filter = ('added_at',)
    raw_id_fields = ('user', 'vocabulary')
    ordering = ('-added_at',)
