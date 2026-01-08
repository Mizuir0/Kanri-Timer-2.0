from django.contrib import admin
from .models import LineNotification


@admin.register(LineNotification)
class LineNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'notification_type', 'timer', 'sent_at', 'recipient_count']
    list_filter = ['notification_type', 'sent_at']
    readonly_fields = ['sent_at', 'line_user_ids', 'message']
    search_fields = ['timer__band_name', 'message']

    def recipient_count(self, obj):
        return obj.recipient_count()
    recipient_count.short_description = '送信先人数'
