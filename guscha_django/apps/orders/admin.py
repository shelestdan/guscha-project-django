from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['product', 'name', 'size', 'quantity', 'price', 'item_type', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'email', 'status', 'payment_status', 
        'fulfillment_status', 'total', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'fulfillment_status', 
        'created_at', 'updated_at'
    ]
    search_fields = [
        'order_number', 'user__email', 'email', 'user__first_name', 
        'user__last_name'
    ]
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 
        'shipped_at', 'delivered_at'
    ]
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('order_number', 'user', 'email', 'status', 
                      'payment_status', 'fulfillment_status')
        }),
        (_('Адреса'), {
            'fields': (
                'billing_address_obj', 'shipping_address_obj',
                'billing_address', 'shipping_address'
            )
        }),
        (_('Суммы'), {
            'fields': ('subtotal', 'tax', 'shipping', 'discount', 'total')
        }),
        (_('Методы'), {
            'fields': ('shipping_method', 'payment_method')
        }),
        (_('Идентификаторы'), {
            'fields': ('tracking_number', 'transaction_id')
        }),
        (_('Дополнительно'), {
            'fields': ('notes', 'created_at', 'updated_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderItemInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'billing_address_obj', 'shipping_address_obj'
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'name', 'size', 'quantity', 'price', 'total', 
        'item_type', 'created_at'
    ]
    list_filter = ['item_type', 'created_at']
    search_fields = ['name', 'order__order_number', 'order__user__email']
    readonly_fields = ['created_at', 'updated_at', 'total']
    
    def total(self, obj):
        return obj.total
    total.short_description = _('Общая сумма')
