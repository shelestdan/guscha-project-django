# -*- coding: utf-8 -*-
"""
Администрирование товаров.

Содержит классы для управления товарами, их размерами и изображениями
в админ-панели. Следует принципу единственной ответственности.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db import transaction

from .base_admin import BaseProductAdmin, BaseImageInline, BaseSizeInline
from ..models import Product, ProductSize, ProductImage
from ..services.product_service import ProductService
from ..forms import ProductSizeForm, ProductImageForm

# Создаем экземпляр сервиса
product_service = ProductService()


class ProductSizeAdmin(admin.ModelAdmin):
    """
    Администрирование размеров товаров.
    
    Предоставляет отдельный интерфейс для управления размерами товаров.
    Каждый размер имеет свой собственный запас и настройки.
    """
    list_display = ['product', 'size_name', 'size_label', 'stock_quantity', 'limit', 'is_active', 'is_sold_out']
    list_filter = ['size_name', 'is_active', 'is_sold_out', 'product__category']
    search_fields = ['product__name', 'size_name', 'size_label']
    list_editable = ['stock_quantity', 'limit', 'is_active', 'is_sold_out']
    autocomplete_fields = ['product']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('product', 'size_name', 'size_label'),
            'description': 'Базовые данные размера товара'
        }),
        (_('Управление запасами'), {
            'fields': ('stock_quantity', 'limit'),
            'description': 'Количество на складе и ограничения корзины'
        }),
        (_('Статусы и сортировка'), {
            'fields': ('is_active', 'is_sold_out', 'sort_order'),
            'description': 'Статусы доступности и порядок отображения'
        }),
    )


class ProductImageAdmin(admin.ModelAdmin):
    """
    Администрирование изображений товаров.
    
    Предоставляет отдельный интерфейс для управления изображениями товаров.
    Позволяет загружать файлы или указывать URL изображений.
    """
    list_display = ['image_preview', 'product', 'alt_text', 'sort_order', 'is_primary']
    list_filter = ['is_primary', 'product__category']
    search_fields = ['product__name', 'alt_text']
    list_editable = ['sort_order', 'is_primary']
    autocomplete_fields = ['product']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('product', 'alt_text'),
            'description': 'Товар и описание изображения для SEO'
        }),
        (_('Изображение'), {
            'fields': ('image', 'image_url', 'image_preview'),
            'description': 'Загрузите файл или укажите URL изображения (приоритет у загруженного файла)'
        }),
        (_('Настройки отображения'), {
            'fields': ('is_primary', 'sort_order'),
            'description': 'Основное изображение и порядок сортировки'
        }),
    )
    
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Предварительный просмотр изображения"""
        image_url = obj.get_image_url
        if image_url:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />',
                image_url
            )
        return "Нет изображения"
    image_preview.short_description = "Предпросмотр"


class ProductSizeInline(BaseSizeInline):
    """
    Inline для быстрого управления размерами товаров.
    
    Компактный интерфейс для добавления/редактирования размеров.
    Для детального управления используйте отдельный раздел "Размеры товаров".
    """
    model = ProductSize
    # form = ProductSizeForm  # Временно отключаем кастомную форму
    verbose_name = _("Размер")
    verbose_name_plural = _("Размеры")
    extra = 1  # Показывать одну пустую форму для добавления
    min_num = 0  # Минимальное количество форм
    max_num = 20  # Максимальное количество форм
    tab = True  # Отображать в отдельной вкладке
    fields = ['size_name', 'stock_quantity', 'limit', 'is_active', 'is_sold_out']
    show_change_link = True  # Показывать ссылку для редактирования
    can_delete = True  # Разрешить удаление
    

class ProductImageInline(BaseImageInline):
    """
    Inline для быстрого управления изображениями товаров.
    
    Компактный интерфейс для добавления/редактирования изображений.
    Для детального управления используйте отдельный раздел "Изображения товаров".
    """
    model = ProductImage
    # form = ProductImageForm  # Временно отключаем кастомную форму
    verbose_name = _("Изображение")
    verbose_name_plural = _("Изображения")
    extra = 1  # Показывать одну пустую форму для добавления
    min_num = 0  # Минимальное количество форм
    max_num = 10  # Максимальное количество форм  
    tab = True  # Отображать в отдельной вкладке
    fields = ['image', 'image_url', 'alt_text', 'is_primary', 'sort_order', 'image_preview']
    show_change_link = True  # Показывать ссылку для редактирования
    can_delete = True  # Разрешить удаление


@admin.register(Product)
class ProductAdmin(BaseProductAdmin):
    """
    Администрирование товаров.
    
    Предоставляет полный интерфейс для управления товарами,
    включая их размеры и изображения.
    """
    
    # Кастомный шаблон для улучшения UI inline форм
    change_form_template = 'admin/products/product/change_form.html'
    
    list_display = [
        'image_preview', 'name', 'sku', 'category', 'formatted_price', 
        'stock_status', 'status_badges', 'rating_display', 'created_at'
    ]
    list_filter = [
        'category', 'is_active', 'track_inventory',
        'is_digital', 'requires_shipping', 'created_at', 'updated_at'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = [
        'image_preview', 'created_at', 'updated_at', 
        'rating_display', 'formatted_price', 'stock_status', 'status_badges'
    ]
    
    # Четкое разделение функций по вкладкам - каждая вкладка отвечает только за свою область
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'slug', 'sku', 'category', 'description', 'track_inventory', 'is_active', 'created_at', 'updated_at'),
            'classes': ('tab',),
            'description': 'Основные данные товара, артикул, описание, статус публикации и системная информация'
        }),
        (_('Ценообразование'), {
            'fields': ('price', 'formatted_price'),
            'classes': ('tab',),
            'description': 'Управление ценами товара'
        }),
        (_('SEO метаданные'), {
            'fields': ('meta_title', 'meta_description', 'search_keywords'),
            'classes': ('tab',),
            'description': 'Данные для поисковых систем'
        })
    )
    
    # Размеры и изображения управляются через inline-формы в отдельных вкладках
    inlines = [ProductSizeInline, ProductImageInline]
    
    def image_preview(self, obj):
        """Предварительный просмотр изображения товара"""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        return "Нет изображения"
    image_preview.short_description = "Изображение"
    
    def formatted_price(self, obj):
        """Форматированная цена товара"""
        return format_html(
            '<span style="font-weight: bold;">{} ₽</span>',
            obj.price.amount
        )
    formatted_price.short_description = "Цена"
    
    def stock_status(self, obj):
        """Статус наличия товара"""
        total_stock = sum(size.stock_quantity for size in obj.sizes.all())
        if total_stock > 10:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">В наличии ({})</span>',
                total_stock
            )
        elif total_stock > 0:
            return format_html(
                '<span style="color: #f39c12; font-weight: bold;">Мало ({})</span>',
                total_stock
            )
        return format_html(
            '<span style="color: #e74c3c; font-weight: bold;">Нет в наличии</span>'
        )
    stock_status.short_description = "Наличие"
    
    def status_badges(self, obj):
        """Бейджи статусов товара"""
        badges = []
        if not obj.is_active:
            badges.append('<span style="background: #95a5a6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Неактивен</span>')
        
        return format_html(' '.join(badges)) if badges else "—"
    status_badges.short_description = "Статусы"
    
    def rating_display(self, obj):
        """Отображение рейтинга товара"""
        if hasattr(obj, 'average_rating') and obj.average_rating:
            stars = '★' * int(obj.average_rating) + '☆' * (5 - int(obj.average_rating))
            return format_html(
                '<span style="color: #f39c12;">{}</span> ({:.1f})',
                stars, obj.average_rating
            )
        return "Нет оценок"
    rating_display.short_description = "Рейтинг"
    
    def get_queryset(self, request):
        """Оптимизированный queryset для списка товаров"""
        return super().get_queryset(request).select_related('category').prefetch_related('sizes')
    
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """Сохранение товара через сервис"""
        super().save_model(request, obj, form, change)
        
        # Используем сервис для обработки логики после сохранения
        warnings = product_service.post_save_processing(obj)
        
        # Отображаем предупреждения пользователю
        for warning in warnings:
            messages.warning(request, warning)
    

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """Убираем кнопку 'Сохранить и добавить другой объект'"""
        context['show_save_and_add_another'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)


# Регистрация дополнительных админ-классов
admin.site.register(ProductSize, ProductSizeAdmin)
admin.site.register(ProductImage, ProductImageAdmin)