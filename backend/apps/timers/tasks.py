from celery import shared_task
from django.utils import timezone
from .models import TimerState
from .utils import broadcast_timer_state
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_timer_state():
    """
    タイマー状態を更新し、WebSocketで配信する
    Celery Beatで1秒ごとに実行される
    """
    try:
        timer_state = TimerState.load()

        # タイマーが実行中でない、または一時停止中の場合は何もしない
        if not timer_state.is_running or timer_state.is_paused:
            return

        # 現在のタイマーがない場合は何もしない
        if not timer_state.current_timer:
            return

        # 経過時間を計算
        elapsed = (timezone.now() - timer_state.started_at).total_seconds()
        total_seconds = timer_state.current_timer.minutes * 60
        remaining = total_seconds - elapsed

        # ログ出力（デバッグ用）
        logger.debug(
            f'タイマー更新: {timer_state.current_timer.band_name} '
            f'経過={int(elapsed)}秒 残り={int(remaining)}秒'
        )

        # WebSocketで配信
        broadcast_timer_state()

        # タイマー完了チェック（0:00になった？）
        if remaining <= 0:
            logger.info(f'タイマー完了: {timer_state.current_timer.band_name}')
            # TODO: Step 2でタイマー完了処理を実装
            # complete_current_timer(timer_state)

    except Exception as e:
        logger.error(f'update_timer_state error: {e}', exc_info=True)


# Step 2で実装
# def complete_current_timer(timer_state):
#     """現在のタイマーを完了し、次のタイマーを自動開始"""
#     pass
