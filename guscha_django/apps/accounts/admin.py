from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib import messages

# Django Unfold imports
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    RangeDateFilter,
    ChoicesDropdownFilter,
    RelatedDropdownFilter
)
# Используем стандартные Django виджеты с Unfold стилизацией
from django import forms
from unfold.decorators import display

from .models import (
    User,
    PendingUserRegistration,
    TelegramVerificationCode
)

User = get_user_model()


class TelegramVerificationCodeInline(TabularInline):
    """Инлайн для истории верификации Telegram (без отображения кодов)"""
    model = TelegramVerificationCode
    extra = 0
    readonly_fields = (
        'verification_type', 'created_at', 'expires_at', 
        'is_used', 'attempts_count', 'status_display'
    )
    fields = (
        'verification_type', 'created_at', 'expires_at',
        'is_used', 'attempts_count', 'status_display'
    )
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    @display(description='Статус')
    def status_display(self, obj):
        """Отображение статуса кода с цветовой индикацией"""
        if obj.is_used:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Использован</span>'
            )
        elif obj.is_expired_property:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Истек</span>'
            )
        elif obj.attempts_count >= 3:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠ Заблокирован</span>'
            )
        else:
            return format_html(
                '<span style="color: blue; font-weight: bold;">⏳ Активен</span>'
            )


@admin.register(User)
class UserAdmin(ModelAdmin):
    """Админка пользователей с Django Unfold"""
    
    # Основные настройки отображения
    list_display = (
        'email', 'full_name_display', 'telegram_status_display',
        'phone_display', 'is_active', 'date_joined_display', 'last_login_display'
    )
    
    list_filter = (
        ('date_joined', RangeDateFilter),
        ('last_login', RangeDateFilter),
        ('is_active', ChoicesDropdownFilter),
        ('is_staff', ChoicesDropdownFilter),
        ('is_telegram_verified', ChoicesDropdownFilter),
    )
    
    search_fields = (
        'email', 'first_name', 'last_name', 
        'telegram_username', 'phone'
    )
    
    ordering = ('-date_joined',)
    
    readonly_fields = (
        'telegram_chat_id', 'phone', 'last_login', 
        'date_joined', 'telegram_info_display'
    )
    
    # Инлайны
    inlines = [TelegramVerificationCodeInline]
    
    # Группировка полей в табы
    fieldsets = (
        ('Основная информация', {
            'fields': ('email', 'first_name', 'last_name'),
            'classes': ('tab',)
        }),
        ('Контактная информация', {
            'fields': ('phone', 'address'),
            'classes': ('tab',)
        }),
        ('Telegram интеграция', {
            'fields': (
                'telegram_username', 'telegram_chat_id', 
                'is_telegram_verified', 'telegram_info_display'
            ),
            'classes': ('tab',)
        }),
        ('Права доступа', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 
                'groups', 'user_permissions'
            ),
            'classes': ('tab',)
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('tab',)
        })
    )
    
    # Кастомные методы отображения
    @display(description='Полное имя')
    def full_name_display(self, obj):
        """Отображение полного имени"""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.email.split('@')[0]
    
    @display(description='Telegram статус')
    def telegram_status_display(self, obj):
        """Отображение статуса Telegram с цветовой индикацией"""
        if obj.is_telegram_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Подтвержден</span><br>'
                '<small>@{}</small>',
                obj.telegram_username or 'Не указан'
            )
        elif obj.telegram_username:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ Ожидает</span><br>'
                '<small>@{}</small>',
                obj.telegram_username
            )
        else:
            return format_html(
                '<span style="color: gray;">✗ Не настроен</span>'
            )
    
    @display(description='Телефон')
    def phone_display(self, obj):
        """Отображение телефона"""
        return obj.phone if obj.phone else '—'
    
    @display(description='Дата регистрации')
    def date_joined_display(self, obj):
        """Отображение даты регистрации"""
        return obj.date_joined.strftime('%d.%m.%Y %H:%M')
    
    @display(description='Последний вход')
    def last_login_display(self, obj):
        """Отображение последнего входа"""
        if obj.last_login:
            return obj.last_login.strftime('%d.%m.%Y %H:%M')
        return 'Никогда'
    
    @display(description='Информация о Telegram')
    def telegram_info_display(self, obj):
        """Подробная информация о Telegram интеграции"""
        info = []
        
        if obj.telegram_chat_id:
            info.append(f'Chat ID: {obj.telegram_chat_id}')
        
        # Количество верификаций
        verification_count = obj.telegram_verification_codes.count()
        info.append(f'Верификаций: {verification_count}')
        
        # Последняя верификация
        last_verification = obj.telegram_verification_codes.first()
        if last_verification:
            info.append(
                f'Последняя: {last_verification.created_at.strftime("%d.%m.%Y %H:%M")}'
            )
        
        return format_html('<br>'.join(info)) if info else '—'
    
    # Настройка формы с кастомными виджетами
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Кастомные виджеты для полей формы"""
        if db_field.name in ['phone']:
            kwargs['widget'] = forms.TextInput(attrs={'readonly': True, 'class': 'readonly-field'})
        elif db_field.name == 'address':
            kwargs['widget'] = forms.Textarea(attrs={'rows': 3})
        
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    def has_delete_permission(self, request, obj=None):
        """Запрет удаления суперпользователей"""
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(TelegramVerificationCode)
class TelegramVerificationCodeAdmin(ModelAdmin):
    """Админка кодов верификации Telegram"""
    
    list_display = (
        'user_email', 'verification_type', 'created_at',
        'status_display', 'attempts_count', 'ip_address'
    )
    
    list_filter = (
        ('verification_type', ChoicesDropdownFilter),
        ('is_used', ChoicesDropdownFilter),
        ('created_at', RangeDateFilter),
        ('expires_at', RangeDateFilter),
    )
    
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 'ip_address'
    )
    
    readonly_fields = (
        'code_hash', 'salt', 'user', 'pending_registration',
        'telegram_chat_id', 'verification_type', 'created_at',
        'expires_at', 'is_used', 'used_at', 'attempts_count', 'ip_address'
    )
    
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        """Запрет создания кодов через админку"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрет изменения кодов"""
        return False
    
    @display(description='Email пользователя')
    def user_email(self, obj):
        """Email пользователя"""
        if obj.user:
            return obj.user.email
        elif obj.pending_registration:
            return f"{obj.pending_registration.email} (ожидает)"
        return '—'
    
    @display(description='Статус')
    def status_display(self, obj):
        """Отображение статуса кода"""
        if obj.is_used:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Использован</span>'
            )
        elif obj.is_expired_property:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Истек</span>'
            )
        elif obj.attempts_count >= 3:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠ Заблокирован</span>'
            )
        else:
            return format_html(
                '<span style="color: blue; font-weight: bold;">⏳ Активен</span>'
            )


@admin.register(PendingUserRegistration)
class PendingUserRegistrationAdmin(ModelAdmin):
    """Админка ожидающих регистрации пользователей"""
    
    list_display = (
        'email', 'full_name_display', 'created_at', 
        'expires_at', 'status_display'
    )
    
    list_filter = (
        ('created_at', RangeDateFilter),
        ('expires_at', RangeDateFilter),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    
    readonly_fields = (
        'email', 'first_name', 'last_name', 'phone', 
        'address', 'password_hash', 'created_at', 'expires_at'
    )
    
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        """Запрет создания через админку"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрет изменения"""
        return False
    
    @display(description='Полное имя')
    def full_name_display(self, obj):
        """Отображение полного имени"""
        return f"{obj.first_name} {obj.last_name}".strip()
    
    @display(description='Статус')
    def status_display(self, obj):
        """Отображение статуса регистрации"""
        if obj.is_expired():
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Истек</span>'
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">⏳ Активен</span>'
            )
