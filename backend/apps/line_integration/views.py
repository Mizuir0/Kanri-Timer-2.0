"""LINE Webhook ハンドラー - 名前による会員マッチング"""
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from apps.members.models import Member
from .line_client import get_webhook_handler, send_line_message
import logging
import json

logger = logging.getLogger(__name__)


@csrf_exempt
def line_webhook_test(request):
    """デバッグ用：設定確認エンドポイント"""
    return JsonResponse({
        'status': 'ok',
        'channel_secret_configured': bool(settings.LINE_CHANNEL_SECRET),
        'channel_token_configured': bool(settings.LINE_CHANNEL_ACCESS_TOKEN),
        'allowed_hosts': settings.ALLOWED_HOSTS,
    })


@csrf_exempt
@require_POST
def line_webhook(request):
    """
    LINE Webhook エンドポイント

    名前ベース連携フロー:
    1. ユーザーが名前を送信
    2. Memberテーブルから名前で検索
    3. 一致したらline_user_idを更新
    4. 結果メッセージを返信
    """
    try:
        signature = request.headers.get('X-Line-Signature', '')
        body = request.body.decode('utf-8')

        logger.info(f'LINE Webhook受信: signature={signature[:20] if signature else "なし"}...')

        # 環境変数チェック
        if not settings.LINE_CHANNEL_SECRET:
            logger.error('LINE_CHANNEL_SECRET が設定されていません')
            return JsonResponse({'error': 'LINE_CHANNEL_SECRET not configured'}, status=500)

        handler = get_webhook_handler()

        # 署名検証
        try:
            events = handler.parser.parse(body, signature)
        except InvalidSignatureError as e:
            logger.error(f'LINE Webhook: 署名検証エラー - {e}')
            return HttpResponseBadRequest('Invalid signature')
        except Exception as e:
            logger.error(f'LINE Webhook: パースエラー - {e}', exc_info=True)
            return JsonResponse({'error': str(e)}, status=400)

        # イベント処理
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                handle_text_message(event)

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        logger.error(f'LINE Webhook: 予期しないエラー - {e}', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


def handle_text_message(event):
    """
    テキストメッセージイベントを処理（名前マッチング）

    Args:
        event: LINE MessageEvent
    """
    line_user_id = event.source.user_id
    received_text = event.message.text.strip()

    logger.info(f'テキスト受信: {line_user_id[:8]}... | メッセージ: {received_text}')

    # 名前でメンバー検索
    try:
        member = Member.objects.get(name=received_text, is_active=True)

        # 既に別のLINEアカウントと連携済みかチェック
        if member.line_user_id and member.line_user_id != line_user_id:
            response_message = f'❌ 「{member.name}」さんは既に別のLINEアカウントと連携されています。'
            send_line_message(line_user_id, response_message)
            logger.warning(f'連携失敗（既存連携あり）: {member.name} | 既存ID={member.line_user_id[:8]}...')
            return

        # 既に同じLINEアカウントと連携済みかチェック
        if member.line_user_id == line_user_id:
            response_message = f'✅ 「{member.name}」さんは既に連携済みです！\n通知を受け取る準備ができています🎵'
            send_line_message(line_user_id, response_message)
            logger.info(f'連携確認: {member.name} | LINE ID={line_user_id[:8]}... (既に連携済み)')
            return

        # このLINEアカウントが他のメンバーと連携されているかチェック
        previous_member = Member.objects.filter(line_user_id=line_user_id, is_active=True).first()

        # line_user_idを更新（新規連携または上書き）
        member.line_user_id = line_user_id
        member.save()

        # 以前の連携があった場合は解除
        if previous_member and previous_member.id != member.id:
            previous_member.line_user_id = None
            previous_member.save()
            response_message = (
                f'✅ 「{member.name}」さんとして連携しました！\n'
                f'（以前の「{previous_member.name}」の連携は解除されました）\n\n'
                f'これから5分前通知が届きます🎵'
            )
            logger.info(f'連携上書き: {previous_member.name} → {member.name} | LINE ID={line_user_id[:8]}...')
        else:
            response_message = f'✅ 「{member.name}」さんとして連携しました！\nこれから5分前通知が届きます🎵'
            logger.info(f'連携成功: {member.name} | LINE ID={line_user_id[:8]}...')

        send_line_message(line_user_id, response_message)

    except Member.DoesNotExist:
        response_message = (
            f'❌ 「{received_text}」という名前のメンバーが見つかりませんでした。\n\n'
            '登録されている名前を正確に入力してください。'
        )
        send_line_message(line_user_id, response_message)
        logger.warning(f'メンバー未検出: {received_text}')

    except Exception as e:
        logger.error(f'連携エラー: {e}', exc_info=True)
        response_message = '⚠️ システムエラーが発生しました。しばらく待ってから再度お試しください。'
        send_line_message(line_user_id, response_message)
