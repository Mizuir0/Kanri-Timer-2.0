from django.db import models
from django.db.models import Sum, F
from apps.members.models import Member


class Timer(models.Model):
    """タイマー（バンドごと）"""

    band_name = models.CharField('バンド名', max_length=50)
    minutes = models.IntegerField('予定時間（分）', default=15)
    member1 = models.ForeignKey(
        Member,
        related_name='timer_member1',
        on_delete=models.PROTECT,
        verbose_name='担当者1'
    )
    member2 = models.ForeignKey(
        Member,
        related_name='timer_member2',
        on_delete=models.PROTECT,
        verbose_name='担当者2'
    )
    member3 = models.ForeignKey(
        Member,
        related_name='timer_member3',
        on_delete=models.PROTECT,
        verbose_name='担当者3'
    )
    order = models.IntegerField('実行順序')
    actual_seconds = models.IntegerField('実際にかかった時間（秒）', null=True, blank=True)
    completed_at = models.DateTimeField('完了時刻', null=True, blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'タイマー'
        verbose_name_plural = 'タイマー'

    def __str__(self):
        return f'{self.band_name} (順序: {self.order})'

    @property
    def is_completed(self):
        """完了済みかどうか"""
        return self.completed_at is not None

    @property
    def time_difference(self):
        """予定時間との差分（秒）"""
        if self.actual_seconds is None:
            return 0
        return self.actual_seconds - (self.minutes * 60)

    @property
    def time_difference_display(self):
        """予定時間との差分を表示用フォーマットで返す"""
        diff = self.time_difference
        if diff == 0:
            return '±0:00'

        sign = '+' if diff > 0 else '-'
        abs_diff = abs(diff)
        minutes = abs_diff // 60
        seconds = abs_diff % 60
        return f'{sign}{minutes}:{seconds:02d}'


class TimerState(models.Model):
    """タイマー状態（Singleton）"""

    current_timer = models.ForeignKey(
        Timer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='現在のタイマー'
    )
    started_at = models.DateTimeField('開始時刻', null=True, blank=True)
    paused_at = models.DateTimeField('一時停止時刻', null=True, blank=True)
    elapsed_seconds = models.IntegerField('経過時間（秒）', default=0)
    is_running = models.BooleanField('実行中', default=False)
    is_paused = models.BooleanField('一時停止中', default=False)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        verbose_name = 'タイマー状態'
        verbose_name_plural = 'タイマー状態'

    def __str__(self):
        if self.current_timer:
            return f'タイマー状態: {self.current_timer.band_name}'
        return 'タイマー状態: なし'

    @property
    def total_time_difference(self):
        """全体の押し巻き（秒）"""
        completed_timers = Timer.objects.filter(actual_seconds__isnull=False)
        return sum(timer.time_difference for timer in completed_timers)

    @property
    def total_time_difference_display(self):
        """全体の押し巻きを表示用フォーマットで返す"""
        diff = self.total_time_difference
        sign = '+' if diff >= 0 else '-'
        abs_diff = abs(diff)
        minutes = abs_diff // 60
        seconds = abs_diff % 60

        if diff > 0:
            status = '押し🔴'
        elif diff < 0:
            status = '巻き🟢'
        else:
            status = '定刻通り⚪'

        return f'{sign}{minutes}:{seconds:02d} {status}'

    def save(self, *args, **kwargs):
        """Singleton パターン: 1件のみ保存"""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """削除を禁止"""
        pass

    @classmethod
    def load(cls):
        """Singletonインスタンスを取得"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
