from django.urls import path
from . import views

app_name = 'timers'

urlpatterns = [
    # タイマー状態
    path('timer-state/', views.get_timer_state, name='get_timer_state'),
    path('timer-state/start/', views.start_timer, name='start_timer'),

    # Step 2以降で追加
    # path('timer-state/pause/', views.pause_timer, name='pause_timer'),
    # path('timer-state/resume/', views.resume_timer, name='resume_timer'),
    # path('timer-state/skip/', views.skip_timer, name='skip_timer'),
]
