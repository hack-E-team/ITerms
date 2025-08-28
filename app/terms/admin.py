from django.contrib import admin
from .models import Term, Tag


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('term','user', 'created_at', 'updated_at')  # 一覧表示に出す項目
    search_fields = ('term', 'definition')               # 検索可能なフィールド
    list_filter = ('tags',)                              # 絞り込みフィルター
    filter_horizontal = ('tags',)                        # ManyToMany を横並びで編集


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')                # 一覧表示に出す項目
    search_fields = ('name',)
