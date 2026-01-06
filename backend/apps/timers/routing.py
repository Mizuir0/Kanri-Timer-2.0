from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/timer/', consumers.TimerConsumer.as_asgi()),
]
