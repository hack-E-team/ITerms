from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import secrets

User = get_user_model()

def _gen_token() -> str:
    # URL安全な短めトークン
    return secrets.token_urlsafe(16)

class ShareLink(models.Model):
    """
    任意のオブジェクト（Vocabulary / Term / Quiz など）をトークンで共有するためのリンク
    """
    token = models.CharField(max_length=64, unique=True, default=_gen_token, db_index=True)

    # 共有対象（Generic FK）
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')

    # 作成者・状態
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='share_links')
    is_active = models.BooleanField(default=True)

    # 期限（null=期限なし）
    expires_at = models.DateTimeField(null=True, blank=True)

    # 監査
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.token} -> {self.target}"

    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def touch(self):
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['last_accessed_at'])
