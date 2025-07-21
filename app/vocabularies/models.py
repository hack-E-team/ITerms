# from django.db import models
# from django.conf import settings


# class Vocabulary(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vocabularies', verbose_name='作成者')
#     title = models.CharField(max_length=255, verbose_name='用語集名')
#     description = models.TextField(blank=True, verbose_name='説明')
#     is_public = models.BooleanField(default=False, verbose_name='公開/非公開')
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日')
#     updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日')

#     def __str__(self):
#         return self.title


# class VocabularyTerm(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vocabulary_terms', verbose_name='ユーザー')
#     vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='terms', verbose_name='用語集')
#     term = models.ForeignKey('Term', on_delete=models.CASCADE, related_name='vocabulary_entries', verbose_name='用語')
#     note = models.TextField(blank=True, verbose_name='補足・メモ')
#     order_index = models.PositiveIntegerField(default=0, verbose_name='並び順')
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日')
#     updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日')

#     class Meta:
#         unique_together = ('vocabulary', 'term')  # 同じ用語を重複登録できないようにする（組み合わせユニーク）
#         ordering = ['order_index']  # 並び順指定

#     def __str__(self):
#         return f'{self.vocabulary.title} - {self.term.term}'


# class UserFavoriteVocabulary(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_vocabularies', verbose_name='ユーザー')
#     vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='用語集')
#     added_at = models.DateTimeField(auto_now_add=True, verbose_name='追加日')

#     class Meta:
#         unique_together = ('user', 'vocabulary') # 同じ用語集を重複登録できないようにする（組み合わせユニーク）

#     def __str__(self):
#         return f'{self.user.username} のお気に入り: {self.vocabulary.title}'