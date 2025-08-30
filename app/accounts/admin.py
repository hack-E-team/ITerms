from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()

# モデルに存在するフィールド名一覧
_field_names = {f.name for f in User._meta.get_fields()}

def _pick(*names):
    """候補の中から、モデルに存在するものだけを返す"""
    return [n for n in names if n in _field_names]

@admin.register(User)
class SimpleUserAdmin(admin.ModelAdmin):
    """存在するフィールドだけで構成した安全な管理画面"""
    list_display = _pick(
        "id", "username", "email", "nickname",
        "is_staff", "is_superuser", "is_active",
        "last_login", "date_joined"
    ) or _pick("id", "email")

    search_fields = _pick("username", "email", "nickname")
    list_filter = _pick("is_staff", "is_superuser", "is_active")
    readonly_fields = _pick("last_login", "date_joined")
    ordering = _pick("id")

    fields = _pick(
        "username", "email", "nickname", "password",
        "is_active", "is_staff", "is_superuser",
        "last_login", "date_joined"
    ) or _pick("email", "password")
