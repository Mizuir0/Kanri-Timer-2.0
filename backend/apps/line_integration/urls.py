from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.line_webhook, name='line_webhook'),
    path('test/', views.line_webhook_test, name='line_webhook_test'),  # デバッグ用
]
