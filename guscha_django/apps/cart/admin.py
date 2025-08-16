from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
# Импорты для django-eventstream теперь в tasks.py

from django.contrib.admin import ModelAdmin
# from unfold.decorators import display
# from unfold.contrib.filters.admin import RangeDateFilter, ChoicesDropdownFilter
from unfold.widgets import UnfoldAdminMoneyWidget
from djmoney.models.fields import MoneyField
from .models import CartItem, Reservation


@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    """Административная панель для элементов корзины"""
    
    # Переопределяем виджеты для MoneyField
    formfield_overrides = {
        MoneyField: {'widget': UnfoldAdminMoneyWidget()},
    }
    list_display = [
        'user_or_session', 'item_name', 'item_type', 'quantity', 
        'formatted_price', 'formatted_total', 'created_at'
    ]
    list_filter = [
        'item_type',
        'created_at',
        'updated_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'session_id', 'product__name', 'preorder__name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'total']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('user', 'session_id', 'item_type'),
            'classes': ('tab',)
        }),
        (_('Товар/Предзаказ'), {
            'fields': ('product', 'product_size', 'preorder', 'preorder_size'),
            'classes': ('tab',)
        }),
        (_('Детали заказа'), {
            'fields': ('quantity', 'price', 'total'),
            'classes': ('tab',)
        }),
        (_('Временные метки'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('tab',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'product', 'product_size', 'preorder', 'preorder_size'
        )
    
    def user_or_session(self, obj):
        if obj.user:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.user.get_full_name() or obj.user.email,
                obj.user.email
            )
        return format_html(
            '<span style="color: #6c757d;">Сессия: {}</span>',
            obj.session_id[:8] + '...' if obj.session_id else 'N/A'
        )
    user_or_session.short_description = _('Пользователь/Сессия')
    
    def item_name(self, obj):
        if obj.item_type == 'product' and obj.product:
            size_info = f' ({obj.product_size.size_name})' if obj.product_size else ''
            return format_html(
                '<strong>{}</strong>{}',
                obj.product.name,
                size_info
            )
        elif obj.item_type == 'preorder' and obj.preorder:
            size_info = f' ({obj.preorder_size.size_name})' if obj.preorder_size else ''
            return format_html(
                '<strong style="color: #fd7e14;">{}</strong>{}',
                obj.preorder.name,
                size_info
            )
        return _('Не указано')
    item_name.short_description = _('Название товара')
    
    def formatted_price(self, obj):
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">{} ₽</span>',
            obj.price
        )
    formatted_price.short_description = _('Цена')
    formatted_price.admin_order_field = 'price'
    
    def formatted_total(self, obj):
        return format_html(
            '<strong style="color: #007bff; font-size: 1.1em;">{} ₽</strong>',
            obj.total
        )
    
    def total(self, obj):
        return obj.total
    total.short_description = _('Общая сумма')


@admin.register(Reservation)
class ReservationAdmin(ModelAdmin):
    """Административная панель для резервирований товаров с live-обновлениями"""
    
    list_display = [
        'id', 'item_info', 'quantity', 'status_display', 
        'expires_at', 'time_remaining', 'created_at'
    ]
    list_filter = [
        'status',
        'created_at',
        'expires_at',
    ]
    search_fields = [
        'product__name', 'preorder__name', 
        'product_size__size_name', 'preorder_size__size_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('status', 'quantity', 'expires_at'),
            'classes': ('tab',)
        }),
        (_('Товар/Предзаказ'), {
            'fields': ('product', 'product_size', 'preorder', 'preorder_size'),
            'classes': ('tab',)
        }),
        (_('Пользователь'), {
            'fields': ('user', 'session_id'),
            'classes': ('tab',)
        }),
        (_('Временные метки'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('tab',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'product', 'product_size', 'preorder', 'preorder_size', 'user'
        )
    
    # URL для SSE обновлений больше не нужен - используется django-eventstream
    

    
    def changelist_view(self, request, extra_context=None):
        """Стандартное представление списка резервирований"""
        return super().changelist_view(request, extra_context)
    
    def item_info(self, obj):
        if obj.product:
            size_info = f' ({obj.product_size.size_name})' if obj.product_size else ''
            return format_html(
                '<strong>{}</strong>{}',
                obj.product.name,
                size_info
            )
        elif obj.preorder:
            size_info = f' ({obj.preorder_size.size_name})' if obj.preorder_size else ''
            return format_html(
                '<strong style="color: #fd7e14;">{}</strong>{}',
                obj.preorder.name,
                size_info
            )
        return _('Не указано')
    item_info.short_description = _('Товар/Предзаказ')
    
    def status_display(self, obj):
        colors = {
            'active': '#28a745',
            'expired': '#dc3545',
            'cancelled': '#6c757d'
        }
        status_names = {
            'active': 'Активно',
            'expired': 'Истекло',
            'cancelled': 'Отменено'
        }
        color = colors.get(obj.status, '#6c757d')
        name = status_names.get(obj.status, obj.status)
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, name
        )
    status_display.short_description = _('Статус')
    
    def time_remaining(self, obj):
        if obj.status != 'active':
            return '-'
        
        now = timezone.now()
        if obj.expires_at <= now:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">Истекло</span>'
            )
        
        remaining = obj.expires_at - now
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        
        if minutes > 0:
            time_str = f'{minutes}м {seconds}с'
        else:
            time_str = f'{seconds}с'
        
        color = '#dc3545' if minutes < 5 else '#ffc107' if minutes < 15 else '#28a745'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, time_str
        )
    time_remaining.short_description = _('Осталось времени')
