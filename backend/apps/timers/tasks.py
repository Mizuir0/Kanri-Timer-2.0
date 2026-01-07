from celery import shared_task
from django.utils import timezone
from .models import TimerState, Timer
from .utils import broadcast_timer_state, broadcast_timer_list
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
            complete_current_timer(timer_state)

    except Exception as e:
        logger.error(f'update_timer_state error: {e}', exc_info=True)


def complete_current_timer(timer_state):
    """
    現在のタイマーを完了し、次のタイマーを自動開始

    Args:
        timer_state: TimerState インスタンス
    """
    try:
        current_timer = timer_state.current_timer

        # 実経過時間を計算
        actual_seconds = int((timezone.now() - timer_state.started_at).total_seconds())

        # 現在のタイマーを完了マーク
        current_timer.actual_seconds = actual_seconds
        current_timer.completed_at = timezone.now()
        current_timer.save()

        logger.info(f'タイマー完了: {current_timer.band_name} ({actual_seconds}秒)')

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
        else:
            # すべてのタイマーが完了
            timer_state.current_timer = None
            timer_state.started_at = None
            timer_state.paused_at = None
            timer_state.elapsed_seconds = 0
            timer_state.is_running = False
            timer_state.is_paused = False
            timer_state.save()

            logger.info('すべてのタイマーが完了しました')

        # WebSocketで配信（状態とリストの両方）
        broadcast_timer_state()
        broadcast_timer_list()

    except Exception as e:
        logger.error(f'complete_current_timer error: {e}', exc_info=True)
