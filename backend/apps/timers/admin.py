from django.contrib import admin
from .models import Timer, TimerState


@admin.register(Timer)
class TimerAdmin(admin.ModelAdmin):
    list_display = ('band_name', 'minutes', 'member1', 'member2', 'member3', 'order', 'is_completed', 'actual_seconds', 'created_at')
    list_filter = ('completed_at',)
    search_fields = ('band_name',)
    readonly_fields = ('created_at', 'completed_at', 'actual_seconds')
    ordering = ('order',)


@admin.register(TimerState)
class TimerStateAdmin(admin.ModelAdmin):
    list_display = ('current_timer', 'is_running', 'is_paused', 'started_at', 'updated_at')
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        """追加を禁止（Singleton）"""
        return not TimerState.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """削除を禁止（Singleton）"""
        return False
