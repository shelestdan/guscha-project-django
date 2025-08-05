# -*- coding: utf-8 -*-
"""
Сигналы для приложения accounts.

Обрабатывает события создания, изменения и удаления пользователей,
а также другие важные события в системе.
"""

from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver('django.db.models.signals.post_save', sender='accounts.User')
def user_post_save_handler(sender, instance, created, **kwargs):
    """
    Обработчик сигнала после сохранения пользователя.
    
    Args:
        sender: Модель User
        instance: Экземпляр пользователя
        created: True если пользователь был создан
    """
    try:
        from django.db.models.signals import post_save
        from django.conf import settings
        from .models import SecurityEvent
        
        if created:
            # Логирование создания нового пользователя
            logger.info(f"Создан новый пользователь: {instance.email}")
            
            # Создание события безопасности
            SecurityEvent.objects.create(
                user=instance,
                event_type='user_created',
                details=f'Пользователь {instance.email} был создан',
                severity='info'
            )
            
            # Отправка приветственного email (если настроен)
            if hasattr(settings, 'SEND_WELCOME_EMAIL') and settings.SEND_WELCOME_EMAIL:
                try:
                    from .utils import EmailUtils
                    EmailUtils.send_welcome_email(instance.email, {
                        'user_name': instance.get_full_name() or instance.email,
                        'login_url': getattr(settings, 'FRONTEND_URL', '') + '/login'
                    })
                except Exception as e:
                    logger.error(f"Ошибка отправки приветственного email: {e}")
        else:
            # Логирование обновления пользователя
            logger.info(f"Обновлен пользователь: {instance.email}")
            
            # Создание события безопасности для изменения профиля
            SecurityEvent.objects.create(
                user=instance,
                event_type='user_updated',
                details=f'Профиль пользователя {instance.email} был обновлен',
                severity='info'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике post_save для пользователя: {e}")


@receiver('django.db.models.signals.pre_save', sender='accounts.User')
def user_pre_save_handler(sender, instance, **kwargs):
    """
    Обработчик сигнала перед сохранением пользователя.
    
    Args:
        sender: Модель User
        instance: Экземпляр пользователя
    """
    try:
        from django.contrib.auth import get_user_model
        from .models import SecurityEvent
        
        User = get_user_model()
        
        # Проверка на изменение критически важных полей
        if instance.pk:  # Если это обновление существующего пользователя
            try:
                old_instance = User.objects.get(pk=instance.pk)
                
                # Проверка изменения email
                if old_instance.email != instance.email:
                    logger.warning(f"Изменение email пользователя: {old_instance.email} -> {instance.email}")
                    
                    # Создание события безопасности
                    SecurityEvent.objects.create(
                        user=instance,
                        event_type='email_changed',
                        details=f'Email изменен с {old_instance.email} на {instance.email}',
                        severity='warning'
                    )
                    
                # Проверка изменения статуса активности
                if old_instance.is_active != instance.is_active:
                    status = 'активирован' if instance.is_active else 'деактивирован'
                    logger.info(f"Пользователь {instance.email} {status}")
                    
                    SecurityEvent.objects.create(
                        user=instance,
                        event_type='status_changed',
                        details=f'Пользователь {status}',
                        severity='info'
                    )
                    
            except User.DoesNotExist:
                logger.debug(f"Новый пользователь создается: {instance.email}")
                
    except Exception as e:
        logger.error(f"Ошибка в обработчике pre_save для User: {e}")


@receiver('django.db.models.signals.post_delete', sender='accounts.User')
def user_post_delete_handler(sender, instance, **kwargs):
    """
    Обработчик сигнала после удаления пользователя.
    
    Args:
        sender: Модель User
        instance: Экземпляр пользователя
    """
    try:
        from .models import SecurityEvent
        
        logger.info(f"Удален пользователь: {instance.email}")
        
        # Создание события безопасности (если возможно)
        try:
            SecurityEvent.objects.create(
                user=None,  # Пользователь уже удален
                event_type='user_deleted',
                details=f'Пользователь {instance.email} был удален',
                severity='warning'
            )
        except Exception as e:
            logger.error(f"Ошибка при создании события безопасности для удаления пользователя: {e}")
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике post_delete для пользователя: {e}")


@receiver('django.contrib.auth.signals.user_logged_in')
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Обработчик сигнала успешного входа пользователя.
    
    Args:
        sender: Класс пользователя
        request: HTTP запрос
        user: Экземпляр пользователя
    """
    try:
        from .models import SecurityEvent, UserLoginHistory
        from .utils import SecurityUtils
        
        # Получение информации о клиенте
        ip_address = SecurityUtils.get_client_ip(request)
        user_agent = SecurityUtils.get_user_agent(request)
        
        # Создание записи в истории входов
        UserLoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        # Создание события безопасности
        SecurityEvent.objects.create(
            user=user,
            event_type='login_success',
            ip_address=ip_address,
            user_agent=user_agent,
            details=f'Успешный вход с IP: {ip_address}',
            severity='info'
        )
        
        # Сброс счетчика неудачных попыток
        SecurityUtils.reset_rate_limit(f"login_attempts_{ip_address}")
        
        logger.info(f"Успешный вход пользователя: {user.email} с IP: {ip_address}")
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике user_logged_in: {e}")


@receiver('django.contrib.auth.signals.user_logged_out')
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    Обработчик сигнала выхода пользователя.
    
    Args:
        sender: Класс пользователя
        request: HTTP запрос
        user: Экземпляр пользователя
    """
    try:
        if user:
            from .models import SecurityEvent
            from .utils import SecurityUtils
            
            # Получение информации о клиенте
            ip_address = SecurityUtils.get_client_ip(request)
            user_agent = SecurityUtils.get_user_agent(request)
            
            # Создание события безопасности
            SecurityEvent.objects.create(
                user=user,
                event_type='logout',
                ip_address=ip_address,
                user_agent=user_agent,
                details=f'Выход с IP: {ip_address}',
                severity='info'
            )
            
            logger.info(f"Выход пользователя: {user.email} с IP: {ip_address}")
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике user_logged_out: {e}")


@receiver('django.contrib.auth.signals.user_login_failed')
def user_login_failed_handler(sender, credentials, request, **kwargs):
    """
    Обработчик сигнала неудачной попытки входа.
    
    Args:
        sender: Класс пользователя
        credentials: Учетные данные
        request: HTTP запрос
    """
    try:
        from django.contrib.auth import get_user_model
        from .models import SecurityEvent, UserLoginHistory
        from .utils import SecurityUtils
        
        User = get_user_model()
        
        # Получение информации о клиенте
        ip_address = SecurityUtils.get_client_ip(request)
        user_agent = SecurityUtils.get_user_agent(request)
        email = credentials.get('email', 'unknown')
        
        # Попытка найти пользователя
        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.debug(f"Пользователь с email {email} не найден при неудачной попытке входа")
        
        # Создание записи в истории входов
        UserLoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
        
        # Создание события безопасности
        SecurityEvent.objects.create(
            user=user,
            event_type='login_failed',
            ip_address=ip_address,
            user_agent=user_agent,
            details=f'Неудачная попытка входа для {email} с IP: {ip_address}',
            severity='warning'
        )
        
        # Увеличение счетчика неудачных попыток
        SecurityUtils.record_failed_attempt(f"login_attempts_{ip_address}")
        
        logger.warning(f"Неудачная попытка входа для {email} с IP: {ip_address}")
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике user_login_failed: {e}")


@receiver('django.db.models.signals.post_save', sender='accounts.PendingUserRegistration')
def pending_registration_post_save_handler(sender, instance, created, **kwargs):
    """
    Обработчик сигнала после сохранения ожидающей регистрации.
    
    Args:
        sender: Модель PendingUserRegistration
        instance: Экземпляр ожидающей регистрации
        created: True если запись была создана
    """
    try:
        if created:
            logger.info(f"Создана ожидающая регистрация для: {instance.email}")
            
            # Отправка email с подтверждением (если настроено)
            from django.conf import settings
            if hasattr(settings, 'SEND_ACTIVATION_EMAIL') and settings.SEND_ACTIVATION_EMAIL:
                try:
                    from .utils import EmailUtils
                    # Здесь можно добавить логику отправки email активации
                    logger.info(f"Email активации должен быть отправлен для {instance.email}")
                except Exception as e:
                    logger.error(f"Ошибка отправки email активации: {e}")
                    
    except Exception as e:
        logger.error(f"Ошибка в обработчике post_save для PendingUserRegistration: {e}")


@receiver('django.db.models.signals.post_save', sender='accounts.TelegramVerificationCode')
def telegram_code_post_save_handler(sender, instance, created, **kwargs):
    """
    Обработчик сигнала после сохранения кода верификации Telegram.
    
    Args:
        sender: Модель TelegramVerificationCode
        instance: Экземпляр кода верификации
        created: True если код был создан
    """
    try:
        if created:
            from .models import SecurityEvent
            
            logger.info(f"Создан код верификации Telegram для пользователя: {instance.user.email}")
            
            # Создание события безопасности
            SecurityEvent.objects.create(
                user=instance.user,
                event_type='telegram_code_generated',
                details=f'Сгенерирован код верификации Telegram',
                severity='info'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике post_save для TelegramVerificationCode: {e}")