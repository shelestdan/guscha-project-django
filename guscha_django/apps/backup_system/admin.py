from django.contrib import admin
from .models import BackupLog


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'operation_type', 'status', 'user', 'details_short']
    list_filter = ['operation_type', 'status', 'timestamp']
    search_fields = ['details', 'user__username']
    readonly_fields = ['timestamp', 'operation_type', 'status', 'user', 'details']
    date_hierarchy = 'timestamp'
    
    def details_short(self, obj):
        if obj.details:
            return obj.details[:50] + '...' if len(obj.details) > 50 else obj.details
        return '-'
    details_short.short_description = 'Детали'
    
    def has_add_permission(self, request):
        # Запрещаем создание логов через админку
        return False
    
    def has_change_permission(self, request, obj=None):
        # Запрещаем изменение логов через админку
        return False
