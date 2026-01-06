from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import Timer, TimerState
from .serializers import TimerStateSerializer
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


# Step 2以降で追加する機能
# @api_view(['POST'])
# def pause_timer(request):
#     """タイマーを一時停止"""
#     pass

# @api_view(['POST'])
# def resume_timer(request):
#     """タイマーを再開"""
#     pass

# @api_view(['POST'])
# def skip_timer(request):
#     """タイマーをスキップ"""
#     pass
