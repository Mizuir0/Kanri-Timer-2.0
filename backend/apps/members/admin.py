from django.contrib import admin
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'line_user_id', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'line_user_id')
    readonly_fields = ('created_at',)
