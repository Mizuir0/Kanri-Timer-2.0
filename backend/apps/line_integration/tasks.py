"""LINE通知 Celery タスク"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from apps.timers.models import Timer, TimerState
from apps.members.models import Member
from .models import LineNotification
from .line_client import send_line_message_bulk
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_and_send_notifications():
    """
    5分前通知チェック - Celery Beatで1秒ごとに実行

    ロジック:
    1. 実行中かつ未一時停止のタイマーがあるか確認
    2. 次のタイマーを取得
    3. 次のタイマー開始まで残り時間を計算
    4. 297〜303秒の範囲なら通知送信
    5. 重複送信防止（LineNotificationで確認）
    """
    try:
        timer_state = TimerState.load()

        # 実行中でない、または一時停止中の場合はスキップ
        if not timer_state.is_running or not timer_state.current_timer:
            return
        if timer_state.is_paused:
            return

        # 次のタイマーを取得
        next_timer = Timer.objects.filter(
            completed_at__isnull=True,
            order__gt=timer_state.current_timer.order
        ).order_by('order').first()

        if not next_timer:
            logger.debug('次のタイマーなし - 5分前通知スキップ')
            return

        # 次のタイマー開始までの残り時間を計算
        elapsed = (timezone.now() - timer_state.started_at).total_seconds()
        total_seconds = timer_state.current_timer.minutes * 60
        remaining = total_seconds - elapsed

        time_until_next = remaining

        # 5分前（300秒）±3秒の範囲でトリガー
        TARGET_SECONDS = 300
        TOLERANCE = 3

        if not (TARGET_SECONDS - TOLERANCE <= time_until_next <= TARGET_SECONDS + TOLERANCE):
            return  # まだ5分前でない、または既に過ぎている

        # 重複送信チェック
        already_sent = LineNotification.objects.filter(
            timer=next_timer,
            notification_type='5min_before'
        ).exists()

        if already_sent:
            logger.debug(f'既に送信済み: {next_timer.band_name} | タイプ=5min_before')
            return

        # 担当者のLINE User IDを取得
        members = [next_timer.member1, next_timer.member2, next_timer.member3]
        line_user_ids = [
            member.line_user_id
            for member in members
            if member and member.line_user_id
        ]

        if not line_user_ids:
            logger.warning(f'LINE連携済みメンバーなし: {next_timer.band_name}')
            return

        # メッセージ作成
        message_text = (
            f'【KanriTimer】\n'
            f'次は「{next_timer.band_name}」の担当です。\n'
            f'あと5分で開始します🎵\n\n'
            f'担当: {", ".join([m.name for m in members])}'
        )

        # トランザクション内で送信+記録
        with transaction.atomic():
            # 送信
            success_count, failure_count = send_line_message_bulk(line_user_ids, message_text)

            # 履歴記録
            LineNotification.objects.create(
                timer=next_timer,
                notification_type='5min_before',
                line_user_ids=line_user_ids,
                message=message_text
            )

            logger.info(
                f'5分前通知完了: {next_timer.band_name} | '
                f'送信={success_count}, 失敗={failure_count}'
            )

    except Exception as e:
        logger.error(f'5分前通知エラー: {e}', exc_info=True)


@shared_task
def send_rehearsal_start_notification():
    """
    リハーサル開始通知

    トリガー: 最初のタイマーが開始された瞬間（is_running=True, started_at設定直後）
    送信先: 全てのLINE連携済みメンバー
    """
    try:
        timer_state = TimerState.load()

        # 実行中でない場合はスキップ
        if not timer_state.is_running or not timer_state.started_at:
            return

        # 既に送信済みかチェック（timer=null, notification_type='rehearsal_start'）
        already_sent = LineNotification.objects.filter(
            timer__isnull=True,
            notification_type='rehearsal_start'
        ).exists()

        if already_sent:
            logger.debug('リハーサル開始通知: 既に送信済み')
            return

        # 全LINE連携済みメンバーを取得
        line_user_ids = list(
            Member.objects.filter(
                is_active=True,
                line_user_id__isnull=False
            ).exclude(line_user_id='').values_list('line_user_id', flat=True)
        )

        if not line_user_ids:
            logger.warning('LINE連携済みメンバーなし - リハーサル開始通知スキップ')
            return

        # メッセージ作成
        message_text = (
            f'【KanriTimer】\n'
            f'🎤 リハーサルを開始しました！\n\n'
            f'全員頑張りましょう🔥'
        )

        # トランザクション内で送信+記録
        with transaction.atomic():
            success_count, failure_count = send_line_message_bulk(line_user_ids, message_text)

            LineNotification.objects.create(
                timer=None,  # システム通知
                notification_type='rehearsal_start',
                line_user_ids=line_user_ids,
                message=message_text
            )

            logger.info(f'リハーサル開始通知完了: 送信={success_count}, 失敗={failure_count}')

    except Exception as e:
        logger.error(f'リハーサル開始通知エラー: {e}', exc_info=True)


@shared_task
def send_rehearsal_end_notification():
    """
    リハーサル終了通知

    トリガー: 最後のタイマーが完了した瞬間（全タイマーcompleted_at設定済み）
    送信先: 全てのLINE連携済みメンバー
    """
    try:
        # タイマーの総数を取得
        total_timers = Timer.objects.count()

        # タイマーが存在しない場合はスキップ
        if total_timers == 0:
            logger.debug('リハーサル終了通知: タイマーが存在しないためスキップ')
            return

        # 全タイマーが完了しているか確認
        incomplete_timers = Timer.objects.filter(completed_at__isnull=True).count()

        if incomplete_timers > 0:
            return  # まだ未完了タイマーがある

        # 既に送信済みかチェック
        already_sent = LineNotification.objects.filter(
            timer__isnull=True,
            notification_type='rehearsal_end'
        ).exists()

        if already_sent:
            logger.debug('リハーサル終了通知: 既に送信済み')
            return

        # 全LINE連携済みメンバーを取得
        line_user_ids = list(
            Member.objects.filter(
                is_active=True,
                line_user_id__isnull=False
            ).exclude(line_user_id='').values_list('line_user_id', flat=True)
        )

        if not line_user_ids:
            logger.warning('LINE連携済みメンバーなし - リハーサル終了通知スキップ')
            return

        # 累計押し巻きを取得
        timer_state = TimerState.load()

        # 全体の時間差を計算
        completed_timers = Timer.objects.filter(actual_seconds__isnull=False)
        total_diff = sum(timer.time_difference for timer in completed_timers)

        # 累積一時停止時間を加算
        total_diff += timer_state.total_paused_seconds

        # 表示用フォーマット
        sign = '+' if total_diff >= 0 else '-'
        abs_diff = abs(total_diff)
        minutes = abs_diff // 60
        seconds = abs_diff % 60

        if total_diff > 0:
            status = '押し🔴'
        elif total_diff < 0:
            status = '巻き🟢'
        else:
            status = '定刻通り⚪'

        total_diff_display = f'{sign}{minutes}:{seconds:02d} {status}'

        # メッセージ作成
        message_text = (
            f'【KanriTimer】\n'
            f'🎉 リハーサルが終了しました！\n\n'
            f'お疲れ様でした👏\n'
            f'全体の進行状況: {total_diff_display}'
        )

        # トランザクション内で送信+記録
        with transaction.atomic():
            success_count, failure_count = send_line_message_bulk(line_user_ids, message_text)

            LineNotification.objects.create(
                timer=None,  # システム通知
                notification_type='rehearsal_end',
                line_user_ids=line_user_ids,
                message=message_text
            )

            logger.info(f'リハーサル終了通知完了: 送信={success_count}, 失敗={failure_count}')

    except Exception as e:
        logger.error(f'リハーサル終了通知エラー: {e}', exc_info=True)
