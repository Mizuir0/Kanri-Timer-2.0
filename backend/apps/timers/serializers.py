from rest_framework import serializers
from .models import Timer, TimerState
from apps.members.models import Member


class MemberSerializer(serializers.ModelSerializer):
    """メンバーシリアライザー"""

    class Meta:
        model = Member
        fields = ('id', 'name')


class TimerSerializer(serializers.ModelSerializer):
    """タイマーシリアライザー"""
    members = serializers.SerializerMethodField()
    member1 = MemberSerializer(read_only=True)
    member2 = MemberSerializer(read_only=True)
    member3 = MemberSerializer(read_only=True)
    time_difference = serializers.ReadOnlyField()
    time_difference_display = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()

    class Meta:
        model = Timer
        fields = (
            'id',
            'band_name',
            'minutes',
            'members',
            'member1',
            'member2',
            'member3',
            'order',
            'actual_seconds',
            'time_difference',
            'time_difference_display',
            'completed_at',
            'is_completed',
            'created_at'
        )

    def get_members(self, obj):
        """担当者のリストを返す"""
        return [obj.member1.name, obj.member2.name, obj.member3.name]


class TimerStateSerializer(serializers.ModelSerializer):
    """タイマー状態シリアライザー"""
    current_timer = TimerSerializer(read_only=True)
    next_timer = serializers.SerializerMethodField()
    remaining_seconds = serializers.SerializerMethodField()
    total_time_difference = serializers.SerializerMethodField()
    total_time_difference_display = serializers.SerializerMethodField()

    class Meta:
        model = TimerState
        fields = (
            'current_timer',
            'next_timer',
            'started_at',
            'paused_at',
            'elapsed_seconds',
            'remaining_seconds',
            'is_running',
            'is_paused',
            'total_time_difference',
            'total_time_difference_display',
            'updated_at'
        )

    def get_next_timer(self, obj):
        """次のタイマーを返す"""
        if obj.current_timer:
            next_timer = Timer.objects.filter(
                order__gt=obj.current_timer.order,
                completed_at__isnull=True
            ).first()
            if next_timer:
                return TimerSerializer(next_timer).data
        return None

    def get_remaining_seconds(self, obj):
        """残り時間（秒）を計算（表示用に切り上げ）"""
        if not obj.current_timer:
            return 0

        total_seconds = obj.current_timer.minutes * 60

        # 開始前（started_atがnull）の場合は予定時間を返す
        if not obj.started_at:
            return total_seconds

        from django.utils import timezone
        import math

        if obj.is_paused:
            # 一時停止中は elapsed_seconds から計算
            return total_seconds - obj.elapsed_seconds
        else:
            # 実行中は現在時刻から計算（切り上げで表示用に調整）
            elapsed = (timezone.now() - obj.started_at).total_seconds()
            remaining = total_seconds - elapsed
            # 0より大きい場合は切り上げ、0以下の場合は0
            return max(0, math.ceil(remaining))

    def get_total_time_difference(self, obj):
        """全体の押し巻き（秒）をリアルタイム計算"""
        from django.utils import timezone

        # 完了済みタイマーの時間差を合計
        completed_timers = Timer.objects.filter(actual_seconds__isnull=False)
        total_diff = sum(timer.time_difference for timer in completed_timers)

        # 実行中のタイマーがある場合、累積一時停止時間を加算
        if obj.current_timer and obj.is_running:
            # 既に累積された一時停止時間を加算
            total_diff += obj.total_paused_seconds

            # さらに一時停止中の場合、現在の一時停止時間も暫定的に加算
            if obj.is_paused and obj.paused_at:
                current_pause_duration = int((timezone.now() - obj.paused_at).total_seconds())
                total_diff += current_pause_duration

        return total_diff

    def get_total_time_difference_display(self, obj):
        """全体の押し巻きを表示用フォーマットで返す（リアルタイム）"""
        diff = self.get_total_time_difference(obj)
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
