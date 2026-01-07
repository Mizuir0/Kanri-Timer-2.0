"""
URLルーティング設定
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django管理画面
    path('admin/', admin.site.urls),

    # API
    path('api/members/', include('apps.members.urls')),  # Step 3で追加
    path('api/timers/', include('apps.timers.urls')),
    # path('api/line/', include('apps.line_integration.urls')),  # Step 5で追加
]
