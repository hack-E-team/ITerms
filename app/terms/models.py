from django.db import models
from django.conf import settings

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='タグ名')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日')

    def __str__(self):
        return self.name


class Term(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='terms',
        verbose_name='作成者',
    )
    term = models.CharField(max_length=255, verbose_name='用語')
    definition = models.TextField(verbose_name='定義')
    tags = models.ManyToManyField(Tag, related_name='terms', blank=True, verbose_name='タグ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日')

    def __str__(self):
        return self.term
