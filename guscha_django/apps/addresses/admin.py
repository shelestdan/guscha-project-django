from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'full_name', 'address_line1', 'city', 
        'postal_code', 'address_type', 'is_default', 'is_active'
    ]
    list_filter = [
        'address_type', 'is_default', 'is_active', 
        'country', 'created_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'address_line1', 
        'city', 'postal_code', 'user__email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('user', 'address_type', 'is_default', 'is_active')
        }),
        (_('Контактная информация'), {
            'fields': ('first_name', 'last_name', 'company', 'phone')
        }),
        (_('Адрес'), {
            'fields': (
                'address_line1', 'address_line2', 'city', 
                'state', 'postal_code', 'country'
            )
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')