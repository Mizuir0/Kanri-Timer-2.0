"""
URLルーティング設定
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from apps.timers.views import update_settings


def health_check(request):
    """ヘルスチェック用エンドポイント（HEAD/GET対応）"""
    return HttpResponse("OK", status=200)


urlpatterns = [
    # ヘルスチェック（UptimeRobot用）
    path('health/', health_check, name='health_check'),

    # Django管理画面
    path('admin/', admin.site.urls),

    # API
    path('api/members/', include('apps.members.urls')),  # Step 3で追加
    path('api/timers/', include('apps.timers.urls')),
    path('api/line/', include('apps.line_integration.urls')),  # Step 5で追加
    path('api/settings/', update_settings, name='update_settings'),
]
