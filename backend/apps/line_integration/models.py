from django.db import models
from apps.timers.models import Timer


class LineNotification(models.Model):
    """LINE通知履歴（重複防止用）"""

    NOTIFICATION_TYPE_CHOICES = [
        ('5min_before', '5分前通知'),
        ('rehearsal_start', 'リハーサル開始通知'),
        ('rehearsal_end', 'リハーサル終了通知'),
    ]

    timer = models.ForeignKey(
        Timer,
        on_delete=models.CASCADE,
        related_name='line_notifications',
        verbose_name='タイマー',
        null=True,
        blank=True  # rehearsal_start/endはtimerがnull
    )
    notification_type = models.CharField(
        '通知種別',
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    sent_at = models.DateTimeField('送信日時', auto_now_add=True)
    line_user_ids = models.JSONField('送信先LINE User IDs', default=list)
    message = models.TextField('送信メッセージ', blank=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'LINE通知履歴'
        verbose_name_plural = 'LINE通知履歴'
        unique_together = [['timer', 'notification_type']]  # 重複防止

    def __str__(self):
        timer_name = self.timer.band_name if self.timer else 'システム通知'
        return f'{self.get_notification_type_display()} - {timer_name} ({self.sent_at.strftime("%m/%d %H:%M")})'

    def recipient_count(self):
        """送信先人数"""
        return len(self.line_user_ids)
    recipient_count.short_description = '送信先人数'
