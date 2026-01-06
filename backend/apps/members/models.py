from django.db import models


class Member(models.Model):
    """メンバーマスタ"""

    name = models.CharField('名前', max_length=20, unique=True)
    line_user_id = models.CharField('LINE User ID', max_length=100, blank=True, null=True)
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'メンバー'
        verbose_name_plural = 'メンバー'

    def __str__(self):
        return self.name

    @property
    def has_line_linked(self):
        """LINE連携済みかどうか"""
        return bool(self.line_user_id)
