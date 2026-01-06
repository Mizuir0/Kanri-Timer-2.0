from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Timer, TimerState
from .serializers import TimerStateSerializer, TimerSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_timer_state(request):
    """
    タイマー状態を取得

    GET /api/timer-state/
    """
    try:
        timer_state = TimerState.load()
        serializer = TimerStateSerializer(timer_state)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'get_timer_state error: {e}')
        return Response(
            {'detail': 'タイマー状態の取得に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def start_timer(request):
    """
    タイマーを開始

    POST /api/timer-state/start/
    Body: { "timer_id": 1 }  # オプション
    """
    try:
        timer_state = TimerState.load()

        # 既に実行中の場合はエラー
        if timer_state.is_running and not timer_state.is_paused:
            return Response(
                {'detail': '既にタイマーが実行中です。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # timer_idが指定されていれば、そのタイマーを開始
        timer_id = request.data.get('timer_id')
        if timer_id:
            try:
                timer = Timer.objects.get(id=timer_id)
            except Timer.DoesNotExist:
                return Response(
                    {'detail': '指定されたタイマーが見つかりません。'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # 最初の未完了タイマーを取得
            timer = Timer.objects.filter(completed_at__isnull=True).first()
            if not timer:
                return Response(
                    {'detail': 'タイマーがありません。'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # タイマーを開始
        timer_state.current_timer = timer
        timer_state.started_at = timezone.now()
        timer_state.paused_at = None
        timer_state.elapsed_seconds = 0
        timer_state.is_running = True
        timer_state.is_paused = False
        timer_state.save()

        logger.info(f'タイマー開始: {timer.band_name}')

        serializer = TimerStateSerializer(timer_state)
        return Response({
            'detail': 'タイマーを開始しました。',
            'state': serializer.data
        })

    except Exception as e:
        logger.error(f'start_timer error: {e}')
        return Response(
            {'detail': 'タイマーの開始に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_timers(request):
    """
    全タイマー一覧を取得

    GET /api/timers/
    """
    try:
        timers = Timer.objects.all().order_by('order')
        serializer = TimerSerializer(timers, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'get_timers error: {e}')
        return Response(
            {'detail': 'タイマー一覧の取得に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def pause_timer(request):
    """
    タイマーを一時停止

    POST /api/timers/timer-state/pause/
    """
    try:
        timer_state = TimerState.load()

        # バリデーション: 実行中でないと一時停止できない
        if not timer_state.is_running:
            return Response(
                {'detail': 'タイマーが実行中ではありません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # バリデーション: 既に一時停止中
        if timer_state.is_paused:
            return Response(
                {'detail': 'タイマーは既に一時停止中です。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 経過時間を計算
        elapsed = (timezone.now() - timer_state.started_at).total_seconds()
        timer_state.elapsed_seconds = int(elapsed)
        timer_state.paused_at = timezone.now()
        timer_state.is_paused = True
        timer_state.save()

        logger.info(f'タイマー一時停止: {timer_state.current_timer.band_name if timer_state.current_timer else "None"}')

        serializer = TimerStateSerializer(timer_state)
        return Response({
            'detail': 'タイマーを一時停止しました。',
            'state': serializer.data
        })

    except Exception as e:
        logger.error(f'pause_timer error: {e}')
        return Response(
            {'detail': 'タイマーの一時停止に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def resume_timer(request):
    """
    タイマーを再開

    POST /api/timers/timer-state/resume/
    """
    try:
        timer_state = TimerState.load()

        # バリデーション: 実行中でないと再開できない
        if not timer_state.is_running:
            return Response(
                {'detail': 'タイマーが実行中ではありません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # バリデーション: 一時停止中でないと再開できない
        if not timer_state.is_paused:
            return Response(
                {'detail': 'タイマーは一時停止中ではありません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # started_at を調整（経過時間を考慮）
        timer_state.started_at = timezone.now() - timedelta(seconds=timer_state.elapsed_seconds)
        timer_state.paused_at = None
        timer_state.is_paused = False
        timer_state.save()

        logger.info(f'タイマー再開: {timer_state.current_timer.band_name if timer_state.current_timer else "None"}')

        serializer = TimerStateSerializer(timer_state)
        return Response({
            'detail': 'タイマーを再開しました。',
            'state': serializer.data
        })

    except Exception as e:
        logger.error(f'resume_timer error: {e}')
        return Response(
            {'detail': 'タイマーの再開に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def skip_timer(request):
    """
    タイマーをスキップして次に進む

    POST /api/timers/timer-state/skip/
    """
    try:
        timer_state = TimerState.load()

        # バリデーション: 現在のタイマーが存在するか
        if not timer_state.current_timer:
            return Response(
                {'detail': '現在実行中のタイマーがありません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_timer = timer_state.current_timer

        # 実経過時間を計算
        if timer_state.is_paused:
            actual_seconds = timer_state.elapsed_seconds
        elif timer_state.is_running:
            actual_seconds = int((timezone.now() - timer_state.started_at).total_seconds())
        else:
            actual_seconds = 0

        # 現在のタイマーを完了マーク
        current_timer.actual_seconds = actual_seconds
        current_timer.completed_at = timezone.now()
        current_timer.save()

        logger.info(f'タイマースキップ: {current_timer.band_name} ({actual_seconds}秒)')

        # 次の未完了タイマーを取得
        next_timer = Timer.objects.filter(
            completed_at__isnull=True
        ).order_by('order').first()

        if next_timer:
            # 次のタイマーを自動開始
            timer_state.current_timer = next_timer
            timer_state.started_at = timezone.now()
            timer_state.paused_at = None
            timer_state.elapsed_seconds = 0
            timer_state.is_running = True
            timer_state.is_paused = False
            timer_state.save()

            logger.info(f'次のタイマー自動開始: {next_timer.band_name}')

            serializer = TimerStateSerializer(timer_state)
            return Response({
                'detail': 'タイマーをスキップして次に進みました。',
                'skipped_timer': TimerSerializer(current_timer).data,
                'state': serializer.data
            })
        else:
            # 全タイマー完了
            timer_state.current_timer = None
            timer_state.started_at = None
            timer_state.paused_at = None
            timer_state.elapsed_seconds = 0
            timer_state.is_running = False
            timer_state.is_paused = False
            timer_state.save()

            logger.info('全タイマー完了')

            serializer = TimerStateSerializer(timer_state)
            return Response({
                'detail': '全てのタイマーが完了しました。',
                'skipped_timer': TimerSerializer(current_timer).data,
                'state': serializer.data
            })

    except Exception as e:
        logger.error(f'skip_timer error: {e}')
        return Response(
            {'detail': 'タイマーのスキップに失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
