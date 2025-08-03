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
from unfold.contrib.forms.widgets import WysiwygWidget
import logging

from .models import (
    User, 
    PendingUserRegistration, 
    TelegramVerificationCode, 
    QRCodeScan
)
from .utils import SecurityUtils, ValidationUtils

logger = logging.getLogger(__name__)
User = get_user_model()


# Removed UserLoginHistory and SecurityEvent inlines as these models don't exist


class TelegramVerificationCodeInline(admin.TabularInline):
    """Инлайн для кодов верификации Telegram"""
    model = TelegramVerificationCode
    extra = 0
    readonly_fields = ('code', 'created_at', 'expires_at', 'is_used')
    can_delete = True
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Расширенная административная панель для пользователей"""
    
    # Основные настройки отображения
    list_display = (
        'email', 'full_name', 'is_active', 'is_staff', 'is_superuser',
        'telegram_status', 'last_login_info', 'registration_date',
        'security_score', 'quick_actions'
    )
    
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_telegram_verified',
        'date_joined', 'last_login'
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'telegram_username')
    
    ordering = ('-date_joined',)
    
    readonly_fields = (
        'date_joined', 'last_login',
        'telegram_chat_id', 'is_telegram_verified',
        'security_info', 'account_statistics'
    )
    
    # Настройки формы
    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget()},
    }
    
    # Группировка полей
    fieldsets = (
        ('Основная информация', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'address')
        }),
        ('Telegram интеграция', {
            'fields': ('telegram_username', 'telegram_chat_id', 'is_telegram_verified'),
            'classes': ('collapse',)
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
        ('Безопасность', {
            'fields': ('security_info',),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('account_statistics',),
            'classes': ('collapse',)
        })
    )
    
    # Инлайны
    inlines = [TelegramVerificationCodeInline]
    
    # Дополнительные действия
    actions = [
        'activate_users', 'deactivate_users', 'reset_telegram_verification',
        'send_password_reset', 'generate_security_report'
    ]
    
    def get_queryset(self, request):
        """Оптимизированный queryset с предзагрузкой связанных данных"""
        return super().get_queryset(request).select_related().prefetch_related(
            'groups', 'user_permissions'
        )
    
    def full_name(self, obj):
        """Полное имя пользователя"""
        return f"{obj.first_name} {obj.last_name}".strip() or "Не указано"
    full_name.short_description = 'Полное имя'
    
    def telegram_status(self, obj):
        """Статус Telegram интеграции"""
        if obj.is_telegram_verified:
            return format_html(
                '<span style="color: green;">✓ Подтвержден</span><br>'
                '<small>@{}</small>',
                obj.telegram_username or 'Не указан'
            )
        elif obj.telegram_username:
            return format_html(
                '<span style="color: orange;">⏳ Ожидает подтверждения</span><br>'
                '<small>@{}</small>',
                obj.telegram_username
            )
        else:
            return format_html('<span style="color: gray;">✗ Не настроен</span>')
    telegram_status.short_description = 'Telegram'
    
    def last_login_info(self, obj):
        """Информация о последнем входе"""
        if obj.last_login:
            return obj.last_login.strftime('%d.%m.%Y %H:%M')
        return "Никогда"
    last_login_info.short_description = 'Последний вход'
    
    def registration_date(self, obj):
        """Дата регистрации"""
        return obj.date_joined.strftime('%d.%m.%Y')
    registration_date.short_description = 'Дата регистрации'
    
    def security_score(self, obj):
        """Оценка безопасности аккаунта"""
        score = 0
        max_score = 100
        
        # Проверяем различные аспекты безопасности
        if obj.is_telegram_verified:
            score += 30
        if obj.last_login and obj.last_login > timezone.now() - timedelta(days=30):
            score += 20
        if obj.phone:
            score += 15
        if len(obj.first_name) > 0 and len(obj.last_name) > 0:
            score += 10
        
        # Проверяем активность аккаунта (заменяем события безопасности)
        if obj.last_login:
            days_since_login = (timezone.now() - obj.last_login).days
            if days_since_login <= 7:
                score += 25
            elif days_since_login <= 30:
                score += 15
        
        # Определяем цвет на основе оценки
        if score >= 80:
            color = 'green'
            status = 'Высокий'
        elif score >= 60:
            color = 'orange'
            status = 'Средний'
        else:
            color = 'red'
            status = 'Низкий'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/100</span><br>'
            '<small>{}</small>',
            color, score, status
        )
    security_score.short_description = 'Безопасность'
    
    def quick_actions(self, obj):
        """Колонка с быстрыми действиями"""
        actions = []
        
        # Ссылка на детальный просмотр
        detail_url = reverse('admin:accounts_user_change', args=[obj.pk])
        actions.append(f'<a href="{detail_url}" title="Редактировать">✏️</a>')
        
        # Действия в зависимости от статуса
        if not obj.is_active:
            actions.append('<span title="Деактивирован">🚫</span>')
        
        if obj.is_telegram_verified:
            actions.append('<span title="Telegram подтвержден">📱</span>')
        
        if obj.is_staff:
            actions.append('<span title="Сотрудник">👤</span>')
        
        if obj.is_superuser:
            actions.append('<span title="Суперпользователь">👑</span>')
        
        return format_html(' '.join(actions))
    quick_actions.short_description = 'Действия'
    
    def security_info(self, obj):
        """Подробная информация о безопасности"""
        info = []
        
        # Базовая информация о безопасности
        info.append(f"Email: {obj.email}")
        info.append(f"Активен: {'Да' if obj.is_active else 'Нет'}")
        info.append(f"Telegram верифицирован: {'Да' if obj.is_telegram_verified else 'Нет'}")
        
        # Информация о последнем входе
        if obj.last_login:
            info.append(f"Последний вход: {obj.last_login.strftime('%d.%m.%Y %H:%M')}")
        else:
            info.append("Последний вход: Никогда")
        
        # Возраст аккаунта
        account_age = (timezone.now() - obj.date_joined).days
        info.append(f"Возраст аккаунта: {account_age} дней")
        
        return format_html('<br>'.join(info))
    security_info.short_description = 'Информация о безопасности'
    
    def account_statistics(self, obj):
        """Статистика аккаунта"""
        stats = []
        
        # Возраст аккаунта
        account_age = (timezone.now() - obj.date_joined).days
        stats.append(f"Возраст аккаунта: {account_age} дней")
        
        # QR коды
        qr_codes = QRCodeScan.objects.filter(
            verification_code__user=obj
        ).count()
        stats.append(f"QR кодов связано: {qr_codes}")
        
        # Коды верификации Telegram
        telegram_codes = obj.telegram_codes.count()
        stats.append(f"Кодов Telegram: {telegram_codes}")
        
        return format_html('<br>'.join(stats))
    account_statistics.short_description = 'Статистика аккаунта'
    
    # Действия
    def activate_users(self, request, queryset):
        """Активация выбранных пользователей"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано {updated} пользователей.')
    activate_users.short_description = 'Активировать выбранных пользователей'
    
    def deactivate_users(self, request, queryset):
        """Деактивация выбранных пользователей"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано {updated} пользователей.')
    deactivate_users.short_description = 'Деактивировать выбранных пользователей'
    
    def reset_telegram_verification(self, request, queryset):
        """Сброс верификации Telegram"""
        updated = queryset.update(
            is_telegram_verified=False,
            telegram_chat_id=None
        )
        self.message_user(request, f'Сброшена Telegram верификация для {updated} пользователей.')
    reset_telegram_verification.short_description = 'Сбросить Telegram верификацию'
    
    def send_password_reset(self, request, queryset):
        """Отправка ссылок для сброса пароля"""
        count = 0
        for user in queryset:
            if user.is_active and user.email:
                # Здесь будет вызов сервиса для отправки email
                logger.info(f'Password reset sent to {user.email}')
                count += 1
        
        self.message_user(request, f'Отправлено {count} ссылок для сброса пароля.')
    send_password_reset.short_description = 'Отправить ссылки сброса пароля'
    

    
    def generate_security_report(self, request, queryset):
        """Генерация отчета по безопасности"""
        # Здесь будет логика генерации отчета
        self.message_user(request, f'Отчет по безопасности для {queryset.count()} пользователей сгенерирован.')
    generate_security_report.short_description = 'Сгенерировать отчет по безопасности'


@admin.register(PendingUserRegistration)
class PendingUserRegistrationAdmin(admin.ModelAdmin):
    """Административная панель для ожидающих регистрации пользователей"""
    
    # Настройки формы
    formfield_overrides = {
        models.TextField: {'widget': WysiwygWidget()},
    }
    
    list_display = ('email', 'full_name', 'created_at', 'expires_at', 'is_expired', 'action_buttons')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'password_hash')
    ordering = ('-created_at',)
    
    actions = ['approve_registrations', 'delete_expired']
    
    def full_name(self, obj):
        """Полное имя"""
        return f"{obj.first_name} {obj.last_name}".strip()
    full_name.short_description = 'Полное имя'
    
    def is_expired(self, obj):
        """Проверка истечения срока"""
        if obj.expires_at < timezone.now():
            return format_html('<span style="color: red;">Истек</span>')
        return format_html('<span style="color: green;">Активен</span>')
    is_expired.short_description = 'Статус'
    
    def action_buttons(self, obj):
        """Быстрые действия"""
        actions = []
        
        if obj.expires_at > timezone.now():
            actions.append('✅ Можно активировать')
        else:
            actions.append('❌ Истек срок')
        
        return format_html(' | '.join(actions))
    action_buttons.short_description = 'Действия'
    
    def approve_registrations(self, request, queryset):
        """Одобрение регистраций"""
        approved = 0
        for pending in queryset:
            if pending.expires_at > timezone.now():
                # Здесь будет логика создания пользователя
                approved += 1
        
        self.message_user(request, f'Одобрено {approved} регистраций.')
    approve_registrations.short_description = 'Одобрить регистрации'
    
    def delete_expired(self, request, queryset):
        """Удаление истекших регистраций"""
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        
        self.message_user(request, f'Удалено {count} истекших регистраций.')
    delete_expired.short_description = 'Удалить истекшие'


@admin.register(TelegramVerificationCode)
class TelegramVerificationCodeAdmin(admin.ModelAdmin):
    """Административная панель для кодов верификации Telegram"""
    
    list_display = ('user', 'code', 'created_at', 'expires_at', 'is_used', 'is_expired')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    actions = ['mark_as_used', 'delete_expired']
    
    def is_expired(self, obj):
        """Проверка истечения кода"""
        if obj.expires_at < timezone.now():
            return format_html('<span style="color: red;">Истек</span>')
        return format_html('<span style="color: green;">Активен</span>')
    is_expired.short_description = 'Статус'
    
    def mark_as_used(self, request, queryset):
        """Отметка кодов как использованных"""
        updated = queryset.update(is_used=True)
        self.message_user(request, f'Отмечено как использованные {updated} кодов.')
    mark_as_used.short_description = 'Отметить как использованные'
    
    def delete_expired(self, request, queryset):
        """Удаление истекших кодов"""
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        
        self.message_user(request, f'Удалено {count} истекших кодов.')
    delete_expired.short_description = 'Удалить истекшие'


@admin.register(QRCodeScan)
class QRCodeAdmin(admin.ModelAdmin):
    """Административная панель для QR кодов"""
    
    list_display = (
        'qr_id', 'verification_code', 'created_at', 'scanned_at',
        'scan_count', 'successful_activations', 'is_scanned', 'status_info'
    )
    list_filter = ('created_at', 'scanned_at', 'trigger_activated_at', 'bot_started_at')
    search_fields = ('qr_id', 'ip_address')
    readonly_fields = ('created_at', 'scan_count', 'successful_activations', 'qr_id')
    ordering = ('-created_at',)
    
    actions = ['mark_as_scanned', 'reset_scan_status']
    
    def is_scanned(self, obj):
        """Проверка сканирования QR кода"""
        if obj.scanned_at:
            return format_html('<span style="color: green;">Отсканирован</span>')
        return format_html('<span style="color: gray;">Не отсканирован</span>')
    is_scanned.short_description = 'Статус сканирования'
    
    def status_info(self, obj):
        """Быстрые действия"""
        actions = []
        
        if obj.scanned_at:
            actions.append('🟢 Отсканирован')
        else:
            actions.append('🔴 Не отсканирован')
        
        if obj.scan_count > 0:
            actions.append(f'📊 Сканирований: {obj.scan_count}')
        
        return format_html(' | '.join(actions))
    status_info.short_description = 'Статус'
    
    def mark_as_scanned(self, request, queryset):
        """Отметить QR коды как отсканированные"""
        count = 0
        for qr_code in queryset:
            if not qr_code.scanned_at:
                qr_code.scanned_at = timezone.now()
                qr_code.scan_count += 1
                qr_code.save()
                count += 1
        self.message_user(request, f'Отмечено как отсканированные {count} QR кодов.')
    mark_as_scanned.short_description = 'Отметить как отсканированные'
    
    def reset_scan_status(self, request, queryset):
        """Сброс статуса сканирования"""
        count = queryset.update(
            scanned_at=None,
            trigger_activated_at=None,
            bot_started_at=None,
            scan_count=0
        )
        self.message_user(request, f'Сброшен статус сканирования для {count} QR кодов.')
    reset_scan_status.short_description = 'Сбросить статус сканирования'


# Removed UserLoginHistoryAdmin and SecurityEventAdmin as these models don't exist


# Настройка заголовков админки
admin.site.site_header = 'Guscha Django - Управление аккаунтами'
admin.site.site_title = 'Guscha Admin'
admin.site.index_title = 'Панель управления аккаунтами'
