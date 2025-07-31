from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.contrib.admin import SimpleListFilter
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RangeDateFilter, ChoicesDropdownFilter
from unfold.widgets import UnfoldAdminMoneyWidget
from djmoney.models.fields import MoneyField
from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['product', 'name', 'size', 'quantity', 'price', 'item_type', 'created_at']
    tab = True


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    # Переопределяем виджеты для MoneyField
    formfield_overrides = {
        MoneyField: {'widget': UnfoldAdminMoneyWidget},
    }
    list_display = [
        'order_number', 'user', 'email', 'colored_status', 'colored_payment_status', 
        'colored_fulfillment_status', 'formatted_total', 'items_count', 'created_at'
    ]
    list_filter = [
        ('status', ChoicesDropdownFilter),
        ('payment_status', ChoicesDropdownFilter),
        ('fulfillment_status', ChoicesDropdownFilter),
        ('created_at', RangeDateFilter),
        ('updated_at', RangeDateFilter)
    ]
    search_fields = [
        'order_number', 'user__email', 'email', 'user__first_name', 
        'user__last_name'
    ]
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 
        'shipped_at', 'delivered_at', 'order_statistics'
    ]
    save_on_top = False  # Убираем верхние кнопки сохранения
    save_as = False      # Убираем "Сохранить как новый"
    
    actions = [
        'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered',
        'mark_as_cancelled', 'mark_payment_paid', 'mark_fulfillment_fulfilled'
    ]
    
    fieldsets = (
        (_('Основная информация заказа'), {
            'fields': ('order_number', 'user', 'email'),
            'classes': ('tab',)
        }),
        (_('Статусы заказа'), {
            'fields': ('status', 'payment_status', 'fulfillment_status'),
            'classes': ('tab',),
            'description': 'Управление статусами заказа'
        }),
        (_('Адреса доставки и оплаты'), {
            'fields': (
                ('billing_address_obj', 'shipping_address_obj'),
                ('billing_address', 'shipping_address')
            ),
            'classes': ('tab',)
        }),
        (_('Финансовая информация'), {
            'fields': (
                ('subtotal', 'tax'),
                ('shipping', 'discount'),
                'total',
                'order_statistics'
            ),
            'classes': ('tab',)
        }),
        (_('Методы доставки и оплаты'), {
            'fields': (
                ('shipping_method', 'payment_method'),
                ('tracking_number', 'transaction_id')
            ),
            'classes': ('tab',)
        }),
        (_('Временные метки'), {
            'fields': (
                ('created_at', 'updated_at'),
                ('shipped_at', 'delivered_at')
            ),
            'classes': ('tab',)
        }),
        (_('Дополнительная информация'), {
            'fields': ('notes',),
            'classes': ('tab',)
        }),
    )
    
    inlines = [OrderItemInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'billing_address_obj', 'shipping_address_obj'
        ).prefetch_related('items')
    
    # Цветовая индикация статусов
    @display(description=_('Статус заказа'), ordering='status')
    def colored_status(self, obj):
        colors = {
            'pending': '#ffc107',      # желтый
            'processing': '#17a2b8',   # голубой
            'shipped': '#007bff',      # синий
            'delivered': '#28a745',    # зеленый
            'cancelled': '#dc3545',    # красный
            'refunded': '#6c757d',     # серый
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_status_display()
        )
    
    @display(description=_('Статус оплаты'), ordering='payment_status')
    def colored_payment_status(self, obj):
        colors = {
            'pending': '#ffc107',      # желтый
            'paid': '#28a745',         # зеленый
            'failed': '#dc3545',       # красный
            'refunded': '#6c757d',     # серый
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_payment_status_display()
        )
    
    @display(description=_('Статус выполнения'), ordering='fulfillment_status')
    def colored_fulfillment_status(self, obj):
        colors = {
            'unfulfilled': '#ffc107',         # желтый
            'partially_fulfilled': '#fd7e14', # оранжевый
            'fulfilled': '#28a745',           # зеленый
            'restocked': '#6c757d',           # серый
        }
        color = colors.get(obj.fulfillment_status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_fulfillment_status_display()
        )
    
    # Статистические методы для отображения сумм
    @display(description=_('Общая сумма'), ordering='total')
    def formatted_total(self, obj):
        return format_html(
            '<strong style="color: #28a745; font-size: 1.1em;">{} ₽</strong>',
            obj.total
        )
    
    @display(description=_('Товаров'))
    def items_count(self, obj):
        count = obj.items.count()
        return format_html(
            '<span style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">{} шт.</span>',
            count
        )
    
    @display(description=_('Статистика'))
    def order_statistics(self, obj):
        if obj.pk:
            items = obj.items.all()
            total_items = items.count()
            total_quantity = sum(item.quantity for item in items)
            avg_item_price = obj.subtotal / total_quantity if total_quantity > 0 else 0
            
            return format_html(
                '''
                <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 5px 0;">
                    <strong>Статистика заказа:</strong><br>
                    <span style="color: #495057;">• Уникальных товаров: <strong>{}</strong></span><br>
                    <span style="color: #495057;">• Общее количество: <strong>{}</strong></span><br>
                    <span style="color: #495057;">• Средняя цена за единицу: <strong>{:.2f} ₽</strong></span><br>
                    <span style="color: #495057;">• Скидка: <strong>{} ₽</strong></span><br>
                    <span style="color: #495057;">• Доставка: <strong>{} ₽</strong></span>
                </div>
                ''',
                total_items,
                total_quantity,
                avg_item_price,
                obj.discount,
                obj.shipping
            )
        return _('Сохраните заказ для просмотра статистики')
    
    # Кастомные действия для быстрого изменения статусов
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} заказов переведено в статус "Обрабатывается"')
    mark_as_processing.short_description = _('Перевести в статус "Обрабатывается"')
    
    def mark_as_shipped(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for order in queryset:
            order.status = 'shipped'
            if not order.shipped_at:
                order.shipped_at = timezone.now()
            order.save()
            updated += 1
        self.message_user(request, f'{updated} заказов переведено в статус "Отправлен"')
    mark_as_shipped.short_description = _('Перевести в статус "Отправлен"')
    
    def mark_as_delivered(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for order in queryset:
            order.status = 'delivered'
            order.fulfillment_status = 'fulfilled'
            if not order.delivered_at:
                order.delivered_at = timezone.now()
            order.save()
            updated += 1
        self.message_user(request, f'{updated} заказов переведено в статус "Доставлен"')
    mark_as_delivered.short_description = _('Перевести в статус "Доставлен"')
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled', fulfillment_status='restocked')
        self.message_user(request, f'{updated} заказов отменено')
    mark_as_cancelled.short_description = _('Отменить заказы')
    
    def mark_payment_paid(self, request, queryset):
        updated = queryset.update(payment_status='paid')
        self.message_user(request, f'{updated} заказов помечено как оплаченные')
    mark_payment_paid.short_description = _('Пометить как оплаченные')
    
    def mark_fulfillment_fulfilled(self, request, queryset):
        updated = queryset.update(fulfillment_status='fulfilled')
        self.message_user(request, f'{updated} заказов помечено как выполненные')
    mark_fulfillment_fulfilled.short_description = _('Пометить как выполненные')
    

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """Убираем кнопку 'Сохранить и добавить другой объект'"""
        context['show_save_and_add_another'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = [
        'order', 'name', 'size', 'quantity', 'price', 'total', 
        'item_type', 'created_at'
    ]
    list_filter = ['item_type', 'created_at']
    search_fields = ['name', 'order__order_number', 'order__user__email']
    readonly_fields = ['created_at', 'updated_at', 'total']
    
    @display(description=_('Общая сумма'))
    def total(self, obj):
        return obj.total
