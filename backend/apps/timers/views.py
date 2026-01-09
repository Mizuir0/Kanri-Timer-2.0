from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db import models, transaction
from datetime import timedelta
from .models import Timer, TimerState
from .serializers import TimerStateSerializer, TimerSerializer
from .utils import broadcast_timer_state, broadcast_timer_list
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
        timer_state.total_paused_seconds = 0
        timer_state.is_running = True
        timer_state.is_paused = False
        timer_state.save()

        logger.info(f'タイマー開始: {timer.band_name}')

        # WebSocketで配信
        broadcast_timer_state()

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
    実行中タイマーの暫定時間差を含めてリアルタイム更新

    GET /api/timers/
    """
    try:
        timers = Timer.objects.all().order_by('order')
        serializer = TimerSerializer(timers, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'get_timers error: {e}', exc_info=True)
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

        # 表示される残り時間を基準に経過時間を保存（表示の一貫性を保つ）
        import math
        elapsed = (timezone.now() - timer_state.started_at).total_seconds()
        total_seconds = timer_state.current_timer.minutes * 60
        remaining = total_seconds - elapsed
        display_remaining = max(0, math.ceil(remaining))
        timer_state.elapsed_seconds = total_seconds - display_remaining
        timer_state.paused_at = timezone.now()
        timer_state.is_paused = True
        timer_state.save()

        logger.info(f'タイマー一時停止: {timer_state.current_timer.band_name if timer_state.current_timer else "None"}')

        # WebSocketで配信
        broadcast_timer_state()

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

        # 一時停止していた時間を累積
        paused_duration = int((timezone.now() - timer_state.paused_at).total_seconds())
        timer_state.total_paused_seconds += paused_duration

        # started_at を調整（経過時間を考慮）
        timer_state.started_at = timezone.now() - timedelta(seconds=timer_state.elapsed_seconds)
        timer_state.paused_at = None
        timer_state.is_paused = False
        timer_state.save()

        logger.info(f'タイマー再開: {timer_state.current_timer.band_name if timer_state.current_timer else "None"}')

        # WebSocketで配信
        broadcast_timer_state()

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

        # タイマーの経過時間を計算
        if timer_state.is_paused:
            timer_elapsed = timer_state.elapsed_seconds
            # 現在の一時停止時間も加算
            current_pause = int((timezone.now() - timer_state.paused_at).total_seconds())
            total_paused = timer_state.total_paused_seconds + current_pause
        elif timer_state.is_running:
            timer_elapsed = int((timezone.now() - timer_state.started_at).total_seconds())
            total_paused = timer_state.total_paused_seconds
        else:
            timer_elapsed = 0
            total_paused = 0

        # actual_seconds = タイマー経過時間 + 累積一時停止時間
        actual_seconds = timer_elapsed + total_paused

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
            timer_state.total_paused_seconds = 0
            timer_state.is_running = True
            timer_state.is_paused = False
            timer_state.save()

            logger.info(f'次のタイマー自動開始: {next_timer.band_name}')

            # WebSocketで配信（状態とリストの両方）
            broadcast_timer_state()
            broadcast_timer_list()

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
            timer_state.total_paused_seconds = 0
            timer_state.is_running = False
            timer_state.is_paused = False
            timer_state.save()

            logger.info('全タイマー完了')

            # WebSocketで配信（状態とリストの両方）
            broadcast_timer_state()
            broadcast_timer_list()

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


# ============================================================================
# CRUD Operations (MVP Step 3)
# ============================================================================


def _validate_timer_data(data):
    """
    タイマーデータのバリデーション

    Args:
        data: リクエストデータ

    Returns:
        tuple: (error_response, validated_data)
        - error_response: バリデーションエラー時はResponse、成功時はNone
        - validated_data: バリデーション成功時は検証済みデータのdict
    """
    from apps.members.models import Member

    band_name = data.get('band_name', '').strip()
    minutes = data.get('minutes')
    member1_id = data.get('member1_id')
    member2_id = data.get('member2_id')
    member3_id = data.get('member3_id')

    # 必須フィールドチェック
    if not band_name:
        return Response(
            {'detail': 'バンド名は必須です。'},
            status=status.HTTP_400_BAD_REQUEST
        ), None

    if not minutes or minutes <= 0:
        return Response(
            {'detail': '予定時間は1分以上で指定してください。'},
            status=status.HTTP_400_BAD_REQUEST
        ), None

    if not all([member1_id, member2_id, member3_id]):
        return Response(
            {'detail': '担当者3名を全て選択してください。'},
            status=status.HTTP_400_BAD_REQUEST
        ), None

    # 重複チェック
    if len(set([member1_id, member2_id, member3_id])) != 3:
        return Response(
            {'detail': '同じメンバーを複数回選択することはできません。'},
            status=status.HTTP_400_BAD_REQUEST
        ), None

    # メンバーの存在確認
    try:
        member1 = Member.objects.get(id=member1_id, is_active=True)
        member2 = Member.objects.get(id=member2_id, is_active=True)
        member3 = Member.objects.get(id=member3_id, is_active=True)
    except Member.DoesNotExist:
        return Response(
            {'detail': '指定されたメンバーが見つかりません。'},
            status=status.HTTP_404_NOT_FOUND
        ), None

    return None, {
        'band_name': band_name,
        'minutes': minutes,
        'member1': member1,
        'member2': member2,
        'member3': member3,
    }

@api_view(['POST'])
def create_timer(request):
    """
    新しいタイマーを作成

    POST /api/timers/create/
    Body: {
        "band_name": "Band Name",
        "minutes": 15,
        "member1_id": 1,
        "member2_id": 2,
        "member3_id": 3
    }
    """
    try:
        # バリデーション
        error_response, validated_data = _validate_timer_data(request.data)
        if error_response:
            return error_response

        # 順序の自動割り当て（最大値 + 1）
        max_order = Timer.objects.aggregate(models.Max('order'))['order__max'] or 0
        new_order = max_order + 1

        # タイマー作成
        timer = Timer.objects.create(
            band_name=validated_data['band_name'],
            minutes=validated_data['minutes'],
            member1=validated_data['member1'],
            member2=validated_data['member2'],
            member3=validated_data['member3'],
            order=new_order
        )

        logger.info(f'タイマー作成: {timer.band_name} (order: {timer.order})')

        # current_timerがnullの場合、新規作成したタイマーを自動セット
        timer_state = TimerState.load()
        if not timer_state.current_timer:
            timer_state.current_timer = timer
            timer_state.save()
            logger.info(f'current_timerを自動設定: {timer.band_name}')
            # タイマー状態も配信
            broadcast_timer_state()

        # WebSocketで配信
        broadcast_timer_list()

        serializer = TimerSerializer(timer)
        return Response({
            'detail': 'タイマーを作成しました。',
            'timer': serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f'create_timer error: {e}', exc_info=True)
        return Response(
            {'detail': 'タイマーの作成に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
def update_timer(request, timer_id):
    """
    タイマーを更新

    PUT /api/timers/{timer_id}/
    Body: {
        "band_name": "New Band Name",
        "minutes": 20,
        "member1_id": 1,
        "member2_id": 2,
        "member3_id": 3
    }
    """
    try:
        # タイマー取得
        try:
            timer = Timer.objects.get(id=timer_id)
        except Timer.DoesNotExist:
            return Response(
                {'detail': '指定されたタイマーが見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 編集制限チェック
        timer_state = TimerState.load()

        # 完了済みタイマーは編集不可
        if timer.is_completed:
            return Response(
                {'detail': '完了済みのタイマーは編集できません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 実行中のタイマーは編集不可
        if timer_state.is_running and timer_state.current_timer and timer_state.current_timer.id == timer.id:
            return Response(
                {'detail': '実行中のタイマーは編集できません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # バリデーション
        error_response, validated_data = _validate_timer_data(request.data)
        if error_response:
            return error_response

        # タイマー更新
        timer.band_name = validated_data['band_name']
        timer.minutes = validated_data['minutes']
        timer.member1 = validated_data['member1']
        timer.member2 = validated_data['member2']
        timer.member3 = validated_data['member3']
        timer.save()

        logger.info(f'タイマー更新: {timer.band_name} (id: {timer.id})')

        # WebSocketで配信
        broadcast_timer_list()

        serializer = TimerSerializer(timer)
        return Response({
            'detail': 'タイマーを更新しました。',
            'timer': serializer.data
        })

    except Exception as e:
        logger.error(f'update_timer error: {e}', exc_info=True)
        return Response(
            {'detail': 'タイマーの更新に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_timer(request, timer_id):
    """
    タイマーを削除

    DELETE /api/timers/{timer_id}/delete/
    """
    try:
        # タイマー取得
        try:
            timer = Timer.objects.get(id=timer_id)
        except Timer.DoesNotExist:
            return Response(
                {'detail': '指定されたタイマーが見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 削除制限チェック
        timer_state = TimerState.load()

        # 完了済みタイマーは削除不可
        if timer.is_completed:
            return Response(
                {'detail': '完了済みのタイマーは削除できません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 実行中のタイマーは削除不可
        if timer_state.is_running and timer_state.current_timer and timer_state.current_timer.id == timer.id:
            return Response(
                {'detail': '実行中のタイマーは削除できません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 削除するタイマーのorder値を保存
        deleted_order = timer.order
        band_name = timer.band_name

        # タイマー削除
        timer.delete()

        # 残りのタイマーのorderを詰める（deleted_orderより大きいorderを-1する）
        Timer.objects.filter(order__gt=deleted_order).update(
            order=models.F('order') - 1
        )

        logger.info(f'タイマー削除: {band_name} (order: {deleted_order})')

        # WebSocketで配信
        broadcast_timer_list()

        return Response({
            'detail': 'タイマーを削除しました。'
        })

    except Exception as e:
        logger.error(f'delete_timer error: {e}', exc_info=True)
        return Response(
            {'detail': 'タイマーの削除に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def reorder_timers(request):
    """
    タイマーの順序を変更

    POST /api/timers/reorder/
    Body: {
        "timer_ids": [3, 1, 2, 4, 5]  // 新しい順序のタイマーID配列
    }
    """
    try:
        timer_ids = request.data.get('timer_ids', [])

        if not timer_ids or not isinstance(timer_ids, list):
            return Response(
                {'detail': 'timer_idsは配列で指定してください。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 全タイマーIDを取得
        all_timer_ids = set(Timer.objects.values_list('id', flat=True))
        requested_timer_ids = set(timer_ids)

        # IDの整合性チェック
        if requested_timer_ids != all_timer_ids:
            return Response(
                {'detail': 'タイマーIDが不正です。全てのタイマーを指定してください。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 順序を更新（トランザクション）
        with transaction.atomic():
            for index, timer_id in enumerate(timer_ids):
                Timer.objects.filter(id=timer_id).update(order=index + 1)

        logger.info(f'タイマー順序変更: {timer_ids}')

        # WebSocketで配信
        broadcast_timer_list()

        return Response({
            'detail': 'タイマーの順序を変更しました。'
        })

    except Exception as e:
        logger.error(f'reorder_timers error: {e}', exc_info=True)
        return Response(
            {'detail': 'タイマーの順序変更に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def update_settings(request):
    """
    設定を更新

    POST /api/settings/
    Body: {
        "line_notifications_enabled": true/false
    }
    """
    try:
        timer_state = TimerState.load()

        # LINE通知設定の更新
        if 'line_notifications_enabled' in request.data:
            timer_state.line_notifications_enabled = request.data['line_notifications_enabled']
            timer_state.save()

            status_text = '有効' if timer_state.line_notifications_enabled else '無効'
            logger.info(f'LINE通知設定を{status_text}に変更')

        serializer = TimerStateSerializer(timer_state)
        return Response({
            'detail': '設定を更新しました。',
            'state': serializer.data
        })

    except Exception as e:
        logger.error(f'update_settings error: {e}', exc_info=True)
        return Response(
            {'detail': '設定の更新に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def delete_all_timers(request):
    """
    全てのタイマーを削除（全タイマー完了時のみ可能）

    POST /api/timers/delete-all/
    """
    try:
        # タイマーが存在するかチェック
        timer_count = Timer.objects.count()
        if timer_count == 0:
            return Response(
                {'detail': 'タイマーが存在しません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 全タイマーが完了しているかチェック
        incomplete_count = Timer.objects.filter(completed_at__isnull=True).count()
        if incomplete_count > 0:
            return Response(
                {'detail': '未完了のタイマーが存在するため、全削除できません。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # トランザクション内で全削除とTimerStateリセット
        with transaction.atomic():
            # LINE通知履歴を削除
            from apps.line_integration.models import LineNotification
            notification_count = LineNotification.objects.all().delete()[0]

            # 全タイマーを削除
            deleted_count = Timer.objects.all().delete()[0]

            # TimerStateをリセット
            timer_state = TimerState.load()
            timer_state.current_timer = None
            timer_state.started_at = None
            timer_state.paused_at = None
            timer_state.elapsed_seconds = 0
            timer_state.total_paused_seconds = 0
            timer_state.is_running = False
            timer_state.is_paused = False
            timer_state.save()

        logger.info(f'全タイマー削除: {deleted_count}件, LINE通知履歴削除: {notification_count}件')

        # WebSocketで配信（状態とリストの両方）
        broadcast_timer_state()
        broadcast_timer_list()

        return Response({
            'detail': f'{deleted_count}件のタイマーと{notification_count}件の通知履歴を削除しました。',
            'deleted_count': deleted_count,
            'notification_deleted_count': notification_count
        })

    except Exception as e:
        logger.error(f'delete_all_timers error: {e}', exc_info=True)
        return Response(
            {'detail': '全タイマーの削除に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
