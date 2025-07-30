# -*- coding: utf-8 -*-
"""
Администрирование категорий товаров.

Содержит класс CategoryAdmin для управления категориями в админ-панели.
Следует принципу единственной ответственности (Single Responsibility Principle).
"""

from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from .base_admin import BaseProductAdmin
from ..models import Category


@admin.register(Category)
class CategoryAdmin(BaseProductAdmin):
    """
    Администрирование категорий товаров.
    
    Предоставляет интерфейс для создания, редактирования и управления
    категориями товаров в админ-панели Django.
    """
    
    # Django Unfold автоматически применяет правильные виджеты при наследовании от ModelAdmin
    list_display = ['name', 'parent', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'sort_order']
    readonly_fields = ['created_at', 'updated_at']
    
    # Используем вкладки django-unfold с обводкой как у пользователей
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'slug', 'description', 'parent'),
            'classes': ('tab',)
        }),
        (_('Изображение'), {
            'fields': ('image_url',),
            'classes': ('tab',)
        }),
        (_('Настройки'), {
            'fields': ('is_active', 'sort_order'),
            'classes': ('tab',)
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('tab',)
        })
    )
    
    def response_add(self, request, obj, post_url_continue=None):
        """Переопределяем поведение после добавления категории"""
        return HttpResponseRedirect(reverse('admin:products_category_changelist'))
    
    def response_change(self, request, obj):
        """Переопределяем поведение после изменения категории"""
        return HttpResponseRedirect(reverse('admin:products_category_changelist'))
    
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """Убираем кнопки 'Сохранить и добавить другой объект' и 'Сохранить и продолжить редактирование'"""
        context['show_save_and_add_another'] = False
        context['show_save_and_continue'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)