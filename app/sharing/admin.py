from django.contrib import admin
from .models import ShareLink

@admin.register(ShareLink)
class ShareLinkAdmin(admin.ModelAdmin):
    list_display = ('token', 'content_type', 'object_id', 'creator', 'is_active', 'expires_at', 'created_at', 'last_accessed_at')
    list_filter = ('is_active', 'content_type')
    search_fields = ('token',)
    readonly_fields = ('token', 'created_at', 'last_accessed_at')
