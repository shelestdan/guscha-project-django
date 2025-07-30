# -*- coding: utf-8 -*-
"""
Базовые классы для администрирования товаров и предзаказов.

Содержит общие импорты и базовые классы для соблюдения принципа DRY.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class BaseProductAdmin(ModelAdmin):
    """
    Базовый класс для администрирования товаров и предзаказов.
    
    Наследует от unfold.admin.ModelAdmin для использования
    современного интерфейса django-unfold.
    """
    
    # Общие настройки для всех админ-классов товаров
    list_per_page = 25
    save_on_top = True
    
    # Общие действия
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        """Активировать выбранные объекты"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} объект(ов) успешно активировано.'
        )
    make_active.short_description = "Активировать выбранные объекты"
    
    def make_inactive(self, request, queryset):
        """Деактивировать выбранные объекты"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} объект(ов) успешно деактивировано.'
        )
    make_inactive.short_description = "Деактивировать выбранные объекты"


class BaseImageInline(TabularInline):
    """
    Базовый inline класс для изображений.
    
    Содержит общие настройки для inline-редактирования изображений
    товаров и предзаказов.
    """
    extra = 1
    min_num = 0
    max_num = 10
    can_delete = True
    show_change_link = True
    fields = ['image', 'image_url', 'alt_text', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Предварительный просмотр изображения"""
        # Приоритет у загруженного файла
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        elif obj.image_url:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        return "Нет изображения"
    image_preview.short_description = "Предпросмотр"


class BaseSizeInline(TabularInline):
    """
    Базовый inline класс для размеров.
    
    Содержит общие настройки для inline-редактирования размеров
    товаров и предзаказов.
    """
    extra = 1
    min_num = 0
    max_num = 20
    can_delete = True
    show_change_link = True
    fields = ['size_name', 'stock_quantity', 'is_active', 'is_sold_out']
    list_editable = ['stock_quantity', 'is_active', 'is_sold_out']
