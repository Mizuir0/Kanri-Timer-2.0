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
    total_time_difference = serializers.ReadOnlyField()
    total_time_difference_display = serializers.ReadOnlyField()

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
        """残り時間（秒）を計算"""
        if not obj.current_timer or not obj.started_at:
            return 0

        from django.utils import timezone

        if obj.is_paused:
            # 一時停止中は elapsed_seconds から計算
            total_seconds = obj.current_timer.minutes * 60
            return total_seconds - obj.elapsed_seconds
        else:
            # 実行中は現在時刻から計算
            elapsed = (timezone.now() - obj.started_at).total_seconds()
            total_seconds = obj.current_timer.minutes * 60
            remaining = total_seconds - elapsed
            return max(0, int(remaining))
