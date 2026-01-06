"""
ASGI config for backend project.

WebSocket対応のため、Django Channelsを使用
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')

# Django ASGIアプリケーションを先に初期化
django_asgi_app = get_asgi_application()

# Channelsのルーティングをインポート（Djangoアプリ初期化後）
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
# from apps.timers.routing import websocket_urlpatterns  # Step 4で追加

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # "websocket": AuthMiddlewareStack(  # Step 4で追加
    #     URLRouter(
    #         websocket_urlpatterns
    #     )
    # ),
})
