"""LINE Messaging API クライアント"""
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_messaging_api():
    """LINE Messaging API クライアントを取得"""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        raise ValueError('LINE_CHANNEL_ACCESS_TOKEN が設定されていません。')

    configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
    return MessagingApi(ApiClient(configuration))


def get_webhook_handler():
    """LINE Webhook ハンドラーを取得"""
    if not settings.LINE_CHANNEL_SECRET:
        raise ValueError('LINE_CHANNEL_SECRET が設定されていません。')

    return WebhookHandler(settings.LINE_CHANNEL_SECRET)


def send_line_message(line_user_id, message_text):
    """
    LINEメッセージを送信

    Args:
        line_user_id (str): LINE User ID
        message_text (str): 送信するメッセージ

    Returns:
        bool: 送信成功時True、失敗時False
    """
    try:
        messaging_api = get_messaging_api()
        messaging_api.push_message(
            PushMessageRequest(
                to=line_user_id,
                messages=[TextMessage(text=message_text)]
            )
        )
        logger.info(f'LINE送信成功: {line_user_id[:8]}... | メッセージ: {message_text[:30]}...')
        return True
    except Exception as e:
        logger.error(f'LINE送信エラー ({line_user_id[:8]}...): {e}', exc_info=True)
        return False


def send_line_message_bulk(line_user_ids, message_text):
    """
    複数のユーザーに同じメッセージを一括送信

    Args:
        line_user_ids (list): LINE User IDのリスト
        message_text (str): 送信するメッセージ

    Returns:
        tuple: (成功数, 失敗数)
    """
    if not line_user_ids:
        logger.warning('送信先LINE User IDが0件です。')
        return 0, 0

    success_count = 0
    failure_count = 0

    for line_user_id in line_user_ids:
        if send_line_message(line_user_id, message_text):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f'一括送信完了: 成功={success_count}, 失敗={failure_count}')
    return success_count, failure_count
