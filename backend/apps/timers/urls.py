from django.urls import path
from . import views

app_name = 'timers'

urlpatterns = [
    # タイマー一覧
    path('', views.get_timers, name='get_timers'),

    # タイマーCRUD（MVP Step 3）
    # 注意: 具体的なパスを動的パターン(<int:timer_id>/)より先に配置
    path('create/', views.create_timer, name='create_timer'),
    path('reorder/', views.reorder_timers, name='reorder_timers'),
    path('delete-all/', views.delete_all_timers, name='delete_all_timers'),
    path('<int:timer_id>/', views.update_timer, name='update_timer'),
    path('<int:timer_id>/delete/', views.delete_timer, name='delete_timer'),

    # タイマー状態
    path('timer-state/', views.get_timer_state, name='get_timer_state'),
    path('timer-state/start/', views.start_timer, name='start_timer'),
    path('timer-state/pause/', views.pause_timer, name='pause_timer'),
    path('timer-state/resume/', views.resume_timer, name='resume_timer'),
    path('timer-state/skip/', views.skip_timer, name='skip_timer'),
]
