from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import TimerState, Timer
from .serializers import TimerStateSerializer, TimerSerializer
import logging

logger = logging.getLogger(__name__)


def broadcast_timer_state():
    """
    タイマー状態をWebSocketで配信

    使用箇所:
      - views.py (start, pause, resume, skip)
      - tasks.py (update_timer_state)
    """
    try:
        channel_layer = get_channel_layer()
        timer_state = TimerState.load()
        serializer = TimerStateSerializer(timer_state)

        async_to_sync(channel_layer.group_send)(
            'timer_updates',
            {
                'type': 'timer.state.updated',
                'data': serializer.data
            }
        )
        logger.debug('WebSocket配信: timer_state_updated')
    except Exception as e:
        logger.error(f'broadcast_timer_state error: {e}', exc_info=True)


def broadcast_timer_list():
    """
    タイマーリストをWebSocketで配信

    使用箇所:
      - views.py (skip)
    """
    try:
        channel_layer = get_channel_layer()
        timers = Timer.objects.all().order_by('order')
        serializer = TimerSerializer(timers, many=True)

        async_to_sync(channel_layer.group_send)(
            'timer_updates',
            {
                'type': 'timer.list.updated',
                'data': serializer.data
            }
        )
        logger.debug('WebSocket配信: timer_list_updated')
    except Exception as e:
        logger.error(f'broadcast_timer_list error: {e}', exc_info=True)
