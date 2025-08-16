# -*- coding: utf-8 -*-
"""
Административная панель для коллекций.

Этот модуль содержит настройки административной панели для управления коллекциями.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from django.forms import Textarea
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import ModelAdmin, TabularInline
from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminTextareaWidget
# from unfold.decorators import display
# from unfold.contrib.forms.widgets import WysiwygWidget
from .models import Collection, CollectionImage
import logging

logger = logging.getLogger(__name__)


class CollectionImageInline(TabularInline):
    """
    Инлайн для изображений коллекций.
    
    Позволяет добавлять и редактировать изображения коллекций
    прямо на странице редактирования коллекции.
    """
    model = CollectionImage
    extra = 1
    max_num = 10
    
    fields = ['image', 'alt_text', 'is_primary', 'sort_order', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """
        Отображает превью изображения в админке.
        
        Args:
            obj: Экземпляр CollectionImage
            
        Returns:
            HTML-код с превью изображения или сообщение об отсутствии изображения
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 4px;" />',
                obj.image.url
            )
        return "Нет изображения"
    image_preview.short_description = _("Превью")
    
    class Media:
        css = {
            'all': ('admin/css/collections_admin.css',)
        }
        js = ('admin/js/collections_admin.js',)


@admin.register(Collection)
class CollectionAdmin(ModelAdmin):
    """
    Административная панель для коллекций.
    
    Предоставляет интерфейс для создания, редактирования и управления
    коллекциями в админ-панели Django с использованием django-unfold.
    """
    
    def view_on_site(self, obj):
        """
        Переопределяет стандартную ссылку "Посмотреть на сайте" для Django Unfold.
        Возвращает URL фронтенда React.
        """
        if obj and obj.is_active:
            return f'/collections/{obj.slug}'
        return None
    list_display = (
        'name', 
        'slug', 
        'is_featured_display', 
        'is_active', 
        'images_count', 
        'created_at',
        'view_on_site_link'
    )
    list_filter = (
        'is_active', 
        'featured', 
        'created_at', 
        'updated_at'
    )
    search_fields = ('name', 'description', 'short_description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'images_count',
        'main_image_preview'
    )
    
    def images_count(self, obj):
        """
        Отображает количество изображений коллекции.
        
        Args:
            obj: Экземпляр Collection
            
        Returns:
            Количество изображений с ссылкой на список
        """
        count = obj.images.count()
        if count > 0:
            url = reverse('admin:collections_collectionimage_changelist') + f'?collection__id__exact={obj.id}'
            return format_html(
                '<a href="{}">{} изображений</a>',
                url, count
            )
        return "0 изображений"
    images_count.short_description = _("Изображения")
    
    def main_image_preview(self, obj):
        """
        Отображает превью главного изображения коллекции.
        
        Args:
            obj: Экземпляр Collection
            
        Returns:
            HTML-код с превью главного изображения или сообщение об отсутствии
        """
        primary_image = obj.images.filter(is_primary=True, is_active=True).first()
        if primary_image and primary_image.image:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px; border-radius: 4px;" />',
                primary_image.image.url
            )
        return "Нет изображения"
    inlines = [CollectionImageInline]
    
    # Настройка полей для отображения с использованием вкладок django-unfold
    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'name', 
                'slug', 
                'short_description', 
                'description'
            ),
            'classes': ('tab',)
        }),
        (_('Настройки отображения'), {
            'fields': (
                'is_active', 
                'featured',
                'sort_order',
                'main_image_preview',
                'images_count'
            ),
            'classes': ('tab',)
        }),
        (_('SEO'), {
            'fields': (
                'meta_title', 
                'meta_description'
            ),
            'classes': ('tab',)
        }),
        (_('Системная информация'), {
            'fields': (
                'created_at', 
                'updated_at'
            ),
            'classes': ('tab',)
        })
    )
    
    # Настройки для улучшения производительности
    list_per_page = 25
    list_max_show_all = 100
    
    # Настройки формы
    formfield_overrides = {
        models.TextField: {'widget': UnfoldAdminTextareaWidget(attrs={'rows': 4})},
        models.CharField: {'widget': UnfoldAdminTextInputWidget()},
        models.SlugField: {'widget': UnfoldAdminTextInputWidget()},
    }
    
    def get_queryset(self, request):
        """
        Оптимизированный queryset с prefetch_related.
        """
        return super().get_queryset(request).prefetch_related('images')
    
    def is_featured_display(self, obj):
        """
        Отображение статуса "рекомендуемое" с иконкой.
        """
        if obj.featured:
            return format_html(
                '<span style="color: #ffc107;">★ Рекомендуемое</span>'
            )
        return format_html(
            '<span style="color: #6c757d;">☆ Обычное</span>'
        )
    is_featured_display.short_description = _("Статус")
    is_featured_display.admin_order_field = 'featured'
    

    

    
    def view_on_site_link(self, obj):
        """
        Ссылка для просмотра коллекции на сайте.
        """
        if obj.is_active:
            url = f'/collections/{obj.slug}'
            return format_html(
                '<a href="{}" target="_blank" style="color: #007cba;">Посмотреть на сайте</a>',
                url
            )
        return "Неактивная коллекция"
    view_on_site_link.short_description = _("Просмотр")
    
    def save_model(self, request, obj, form, change):
        """
        Дополнительная логика при сохранении коллекции.
        """
        if change:
            logger.info(f'Администратор {request.user.username} обновил коллекцию: {obj.name} (ID: {obj.id})')
        else:
            logger.info(f'Администратор {request.user.username} создал новую коллекцию: {obj.name}')
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """
        Дополнительная логика при удалении коллекции.
        """
        logger.info(f'Администратор {request.user.username} удалил коллекцию: {obj.name} (ID: {obj.id})')
        super().delete_model(request, obj)
    
    class Media:
        css = {
            'all': ('admin/css/collections_admin.css',)
        }
        js = ('admin/js/collections_admin.js',)


@admin.register(CollectionImage)
class CollectionImageAdmin(ModelAdmin):
    """
    Административная панель для изображений коллекций.
    
    Предоставляет интерфейс для управления изображениями коллекций
    с использованием django-unfold.
    """
    
    list_display = [
        'collection', 
        'image_preview', 
        'alt_text', 
        'is_primary', 
        'sort_order', 
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'collection', 
        'is_primary', 
        'is_active', 
        'created_at'
    ]
    
    search_fields = [
        'collection__name', 
        'alt_text'
    ]
    
    list_editable = [
        'is_primary', 
        'sort_order', 
        'is_active'
    ]
    
    readonly_fields = [
        'image_preview', 
        'created_at', 
        'updated_at'
    ]
    
    ordering = ['collection', 'sort_order']
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'collection', 
                'image', 
                'image_preview',
                'alt_text'
            ),
            'classes': ('tab',)
        }),
        (_('Настройки отображения'), {
            'fields': (
                'is_primary',
                'sort_order', 
                'is_active'
            ),
            'classes': ('tab',)
        }),
        (_('Системная информация'), {
            'fields': (
                'created_at', 
                'updated_at'
            ),
            'classes': ('tab',)
        })
    )
    
    def image_preview(self, obj):
        """
        Отображает превью изображения в списке.
        
        Args:
            obj: Экземпляр CollectionImage
            
        Returns:
            HTML-код с превью изображения или сообщение об отсутствии изображения
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px; border-radius: 4px;" />',
                obj.image.url
            )
        return "Нет изображения"
    
    def save_model(self, request, obj, form, change):
        """
        Дополнительная логика при сохранении изображения.
        """
        if change:
            logger.info(f'Администратор {request.user.username} обновил изображение коллекции: {obj.collection.name}')
        else:
            logger.info(f'Администратор {request.user.username} добавил изображение в коллекцию: {obj.collection.name}')
        
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/collections_admin.css',)
        }
        js = ('admin/js/collections_admin.js',)


# Настройка заголовков админки
admin.site.site_header = "Guscha - Управление коллекциями"
admin.site.site_title = "Guscha Admin"
admin.site.index_title = "Панель управления коллекциями"