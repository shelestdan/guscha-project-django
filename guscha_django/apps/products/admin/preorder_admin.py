# -*- coding: utf-8 -*-
"""
Администрирование предзаказов.

Содержит классы для управления предзаказами, их размерами и изображениями
в админ-панели. Следует принципу единственной ответственности.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db import transaction
from django.db import models

from django.forms import (
    TextInput,
    Select,
    CheckboxInput,
    FileInput,
    NumberInput,
    Textarea
)
from unfold.widgets import UnfoldAdminImageFieldWidget, UnfoldAdminTextInputWidget, UnfoldAdminTextareaWidget

from .base_admin import BaseProductAdmin, BaseImageInline, BaseSizeInline
from ..models import Preorder, PreorderSize, PreorderImage
from ..forms import PreorderSizeForm, PreorderImageForm


class PreorderSizeAdmin(admin.ModelAdmin):
    """
    Администрирование размеров предзаказов.
    
    Предоставляет отдельный интерфейс для управления размерами предзаказов.
    Каждый размер имеет свой собственный запас и настройки.
    """
    list_display = ['preorder', 'size_name', 'size_label', 'stock_quantity', 'max_quantity', 'is_active', 'is_sold_out']
    list_filter = ['size_name', 'is_active', 'is_sold_out']
    search_fields = ['preorder__name', 'size_name', 'size_label']
    list_editable = ['stock_quantity', 'max_quantity', 'is_active', 'is_sold_out']
    autocomplete_fields = ['preorder']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('preorder', 'size_name', 'size_label'),
            'description': 'Базовые данные размера предзаказа'
        }),
        (_('Управление запасами'), {
            'fields': ('stock_quantity', 'max_quantity'),
            'description': 'Количество на складе и ограничения заказа'
        }),
        (_('Статусы и сортировка'), {
            'fields': ('is_active', 'is_sold_out', 'sort_order'),
            'description': 'Статусы доступности и порядок отображения'
        }),
    )


class PreorderImageAdmin(admin.ModelAdmin):
    """
    Администрирование изображений предзаказов.
    
    Предоставляет отдельный интерфейс для управления изображениями предзаказов.
    Позволяет загружать файлы или указывать URL изображений.
    """
    list_display = ['image_preview', 'preorder', 'alt_text', 'image_type', 'sort_order', 'is_primary']
    list_filter = ['is_primary', 'image_type']
    search_fields = ['preorder__name', 'alt_text']
    list_editable = ['sort_order', 'is_primary']
    autocomplete_fields = ['preorder']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('preorder', 'alt_text'),
            'description': 'Предзаказ и описание изображения для SEO'
        }),
        (_('Изображение'), {
            'fields': ('image', 'image_url', 'image_preview'),
            'description': 'Загрузите файл или укажите URL изображения (приоритет у загруженного файла)'
        }),
        (_('Настройки отображения'), {
            'fields': ('image_type', 'is_primary', 'sort_order'),
            'description': 'Тип изображения, основное изображение и порядок сортировки'
        }),
    )
    
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Предварительный просмотр изображения"""
        image_url = obj.get_image_url if hasattr(obj, 'get_image_url') else (obj.image.url if obj.image else obj.image_url)
        if image_url:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />',
                image_url
            )
        return "Нет изображения"
    image_preview.short_description = "Предварительный просмотр"


class PreorderSizeInline(BaseSizeInline):
    """
    Inline для быстрого управления размерами предзаказов.
    
    Компактный интерфейс для добавления/редактирования размеров.
    Для детального управления используйте отдельный раздел "Размеры предзаказов".
    """
    model = PreorderSize
    form = PreorderSizeForm
    verbose_name = _("Размер")
    verbose_name_plural = _("Размеры")
    extra = 1  # Показывать одну пустую форму для добавления
    min_num = 0
    max_num = 20
    can_delete = True
    show_change_link = True
    tab = True  # Отображать в отдельной вкладке
    fields = ['size_name', 'stock_quantity', 'max_quantity', 'is_active', 'is_sold_out']

class PreorderImageInline(BaseImageInline):
    """
    Inline для быстрого управления изображениями предзаказов.
    
    Компактный интерфейс для добавления/редактирования изображений.
    Для детального управления используйте отдельный раздел "Изображения предзаказов".
    Все поля остаются во вкладке с изображениями согласно требованиям.
    """
    model = PreorderImage
    form = PreorderImageForm  # Используем кастомную форму с Unfold виджетами
    verbose_name = _("Изображение")
    verbose_name_plural = _("Изображения")
    extra = 1  # Показывать одну пустую форму для добавления
    min_num = 0
    max_num = 10
    can_delete = True
    show_change_link = True
    tab = True  # Отображать в отдельной вкладке
    fields = ['image', 'image_url', 'alt_text', 'image_type', 'is_primary', 'sort_order', 'image_preview']
    readonly_fields = ['image_preview']

@admin.register(Preorder)
class PreorderAdmin(BaseProductAdmin):
    """
    Администрирование предзаказов.
    
    Предоставляет полный интерфейс для управления предзаказами,
    включая их размеры и изображения.
    """
    
    # Кастомный шаблон для улучшения UI inline форм
    change_form_template = 'admin/products/preorder/change_form.html'
    
    # Настройки формы - официальные Unfold виджеты для всех полей
    formfield_overrides = {
        # Основная информация - используем официальные Unfold виджеты для текстовых полей
        models.CharField: {'widget': UnfoldAdminTextInputWidget()},
        models.SlugField: {'widget': UnfoldAdminTextInputWidget()},
        models.TextField: {'widget': UnfoldAdminTextareaWidget(attrs={'rows': 4})},
        models.BooleanField: {'widget': CheckboxInput()},
        models.ForeignKey: {'widget': Select()},
        
        # Ценообразование
        models.DecimalField: {'widget': NumberInput(attrs={'step': '0.01'})},
        models.PositiveIntegerField: {'widget': NumberInput(attrs={'min': '0'})},
        
        # Изображения
        models.ImageField: {'widget': UnfoldAdminImageFieldWidget()},
        models.URLField: {'widget': UnfoldAdminTextInputWidget(attrs={'type': 'url'})},
    }

    
    list_display = [
        'image_preview', 'name', 'formatted_price', 
        'status_badges', 'rating_display', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_featured', 'created_at', 'updated_at'
    ]
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = [
        'image_preview', 'created_at', 'updated_at', 
        'rating_display', 'formatted_price', 'status_badges'
    ]
    
    # Четкое разделение функций по вкладкам - каждая вкладка отвечает только за свою область
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'slug', 'sku', 'description', 'is_active', 'is_featured', 'created_at', 'updated_at'),
            'classes': ('tab',),
            'description': 'Основные данные предзаказа, артикул, описание, статус публикации и системная информация'
        }),
        (_('Ценообразование'), {
            'fields': ('price', 'formatted_price'),
            'classes': ('tab',),
            'description': 'Управление ценами предзаказа'
        }),
        (_('SEO метаданные'), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('tab',),
            'description': 'Данные для поисковых систем'
        })
    )
    
    # Размеры и изображения управляются через inline-формы в отдельных вкладках
    inlines = [PreorderSizeInline, PreorderImageInline]
    
    def image_preview(self, obj):
        """Предварительный просмотр изображения предзаказа"""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        return "Нет изображения"
    image_preview.short_description = "Изображение"
    
    def formatted_price(self, obj):
        """Форматированная цена предзаказа"""
        return format_html(
            '<span style="font-weight: bold; color: #2c3e50;">{} ₽</span>',
            obj.price.amount
        )
    formatted_price.short_description = "Цена"
    
    def rating_display(self, obj):
        """Отображение рейтинга (заглушка для предзаказов)"""
        return format_html(
            '<span style="color: #95a5a6; font-style: italic;">Предзаказ</span>'
        )
    rating_display.short_description = "Рейтинг"
    
    def status_badges(self, obj):
        """Бейджи статусов предзаказа"""
        badges = []
        
        # Добавляем бейдж предзаказа
        badges.append('<span style="background: #9b59b6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Предзаказ</span>')
        
        if obj.is_featured:
            badges.append('<span style="background: #3498db; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Рекомендуем</span>')
        if not obj.is_active:
            badges.append('<span style="background: #95a5a6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Неактивен</span>')
        
        return format_html(' '.join(badges))
    status_badges.short_description = "Статусы"
    
    def get_queryset(self, request):
        """Оптимизированный queryset для списка предзаказов"""
        return super().get_queryset(request).prefetch_related('sizes')
    
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """Сохранение предзаказа с дополнительной логикой"""
        super().save_model(request, obj, form, change)
        
        # Обновляем основное изображение из первого изображения, если оно не задано
        if not obj.image_url:
            first_image = obj.preorder_images.first()
            if first_image:
                obj.image_url = first_image.get_image_url
                obj.save(update_fields=['image_url'])
        
        # Добавляем предупреждение, если нет размеров
        if not obj.sizes.exists():
            messages.warning(
                request,
                f'Предзаказ "{obj.name}" сохранен, но у него нет размеров. '
                'Добавьте размеры для корректного отображения в каталоге.'
            )
    

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """Убираем кнопку 'Сохранить и добавить другой объект'"""
        context['show_save_and_add_another'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)


# Регистрируем отдельные админ-классы для размеров и изображений предзаказов
admin.site.register(PreorderSize, PreorderSizeAdmin)
admin.site.register(PreorderImage, PreorderImageAdmin)