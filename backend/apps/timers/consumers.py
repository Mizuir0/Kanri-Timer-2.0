from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import TimerState, Timer
from .serializers import TimerStateSerializer, TimerSerializer


class TimerConsumer(AsyncWebsocketConsumer):
    """
    WebSocketコンシューマー（タイマー更新用）

    グループ: 'timer_updates'
    受信メッセージタイプ:
      - timer.state.updated (タイマー状態更新)
      - timer.list.updated (タイマーリスト更新)
    """

    async def connect(self):
        # グループに参加
        self.group_name = 'timer_updates'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # 接続時に現在の状態を送信（状態復元）
        await self.send_current_state()

        # 接続確立メッセージ
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket接続が確立されました'
        }))

    async def disconnect(self, close_code):
        # グループから離脱
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_current_state(self):
        """接続時に現在のタイマー状態とリストを送信"""
        timer_state = await self.get_timer_state()
        timer_list = await self.get_timer_list()

        # タイマー状態を送信
        await self.send(text_data=json.dumps({
            'type': 'timer_state_updated',
            'data': timer_state
        }))

        # タイマーリストを送信
        await self.send(text_data=json.dumps({
            'type': 'timer_list_updated',
            'data': timer_list
        }))

    async def timer_state_updated(self, event):
        """タイマー状態更新を受信して送信"""
        await self.send(text_data=json.dumps({
            'type': 'timer_state_updated',
            'data': event['data']
        }))

    async def timer_list_updated(self, event):
        """タイマーリスト更新を受信して送信"""
        await self.send(text_data=json.dumps({
            'type': 'timer_list_updated',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_timer_state(self):
        """タイマー状態を取得（非同期対応）"""
        timer_state = TimerState.load()
        serializer = TimerStateSerializer(timer_state)
        return serializer.data

    @database_sync_to_async
    def get_timer_list(self):
        """タイマーリストを取得（非同期対応）"""
        timers = Timer.objects.all().order_by('order')
        serializer = TimerSerializer(timers, many=True)
        return serializer.data
