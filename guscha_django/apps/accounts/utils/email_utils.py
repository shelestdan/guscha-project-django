from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EmailUtils:
    """Утилиты для работы с email"""
    
    @staticmethod
    def send_password_reset_email(user_email: str, reset_link: str, user_name: str = '') -> bool:
        """Отправка email для сброса пароля"""
        try:
            subject = _('Сброс пароля')
            
            # Контекст для шаблона
            context = {
                'user_name': user_name or user_email,
                'reset_link': reset_link,
                'site_name': getattr(settings, 'SITE_NAME', 'Наш сайт'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            }
            
            # Рендерим HTML шаблон
            html_message = render_to_string('accounts/emails/password_reset.html', context)
            
            # Создаем текстовую версию
            plain_message = strip_tags(html_message)
            
            # Отправляем email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            logger.info(f'Password reset email sent to {user_email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send password reset email to {user_email}: {str(e)}')
            return False
    
    @staticmethod
    def send_account_activation_email(user_email: str, activation_link: str, user_name: str = '') -> bool:
        """Отправка email для активации аккаунта"""
        try:
            subject = _('Активация аккаунта')
            
            context = {
                'user_name': user_name or user_email,
                'activation_link': activation_link,
                'site_name': getattr(settings, 'SITE_NAME', 'Наш сайт'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            }
            
            html_message = render_to_string('accounts/emails/account_activation.html', context)
            plain_message = strip_tags(html_message)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            logger.info(f'Account activation email sent to {user_email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send account activation email to {user_email}: {str(e)}')
            return False
    
    @staticmethod
    def send_welcome_email(user_email: str, user_name: str = '') -> bool:
        """Отправка приветственного email"""
        try:
            subject = _('Добро пожаловать!')
            
            context = {
                'user_name': user_name or user_email,
                'site_name': getattr(settings, 'SITE_NAME', 'Наш сайт'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL),
                'login_url': getattr(settings, 'FRONTEND_URL', '') + '/login'
            }
            
            html_message = render_to_string('accounts/emails/welcome.html', context)
            plain_message = strip_tags(html_message)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            logger.info(f'Welcome email sent to {user_email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send welcome email to {user_email}: {str(e)}')
            return False
    
    @staticmethod
    def send_password_changed_notification(user_email: str, user_name: str = '') -> bool:
        """Отправка уведомления об изменении пароля"""
        try:
            subject = _('Пароль изменен')
            
            context = {
                'user_name': user_name or user_email,
                'site_name': getattr(settings, 'SITE_NAME', 'Наш сайт'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            }
            
            html_message = render_to_string('accounts/emails/password_changed.html', context)
            plain_message = strip_tags(html_message)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            logger.info(f'Password changed notification sent to {user_email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send password changed notification to {user_email}: {str(e)}')
            return False
    
    @staticmethod
    def send_login_notification(user_email: str, user_name: str = '', ip_address: str = '', user_agent: str = '') -> bool:
        """Отправка уведомления о входе в систему"""
        try:
            subject = _('Новый вход в аккаунт')
            
            context = {
                'user_name': user_name or user_email,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'site_name': getattr(settings, 'SITE_NAME', 'Наш сайт'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            }
            
            html_message = render_to_string('accounts/emails/login_notification.html', context)
            plain_message = strip_tags(html_message)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            logger.info(f'Login notification sent to {user_email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send login notification to {user_email}: {str(e)}')
            return False
    
    @staticmethod
    def send_security_alert_email(user_email: str, alert_type: str, details: Dict[str, Any], user_name: str = '') -> bool:
        """Отправка уведомления о безопасности"""
        try:
            subject = _('Предупреждение безопасности')
            
            context = {
                'user_name': user_name or user_email,
                'alert_type': alert_type,
                'details': details,
                'site_name': getattr(settings, 'SITE_NAME', 'Наш сайт'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            }
            
            html_message = render_to_string('accounts/emails/security_alert.html', context)
            plain_message = strip_tags(html_message)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            logger.info(f'Security alert email sent to {user_email} for {alert_type}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send security alert email to {user_email}: {str(e)}')
            return False
    
    @staticmethod
    def send_bulk_email(recipients: List[str], subject: str, template_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Массовая отправка email"""
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Рендерим шаблон один раз
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            for recipient in recipients:
                try:
                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[recipient]
                    )
                    msg.attach_alternative(html_message, "text/html")
                    msg.send()
                    
                    results['sent'] += 1
                    logger.info(f'Bulk email sent to {recipient}')
                    
                except Exception as e:
                    results['failed'] += 1
                    error_msg = f'Failed to send to {recipient}: {str(e)}'
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
        except Exception as e:
            logger.error(f'Failed to render email template {template_name}: {str(e)}')
            results['errors'].append(f'Template rendering failed: {str(e)}')
        
        return results
    
    @staticmethod
    def send_custom_email(recipient: str, subject: str, message: str, html_message: str = None) -> bool:
        """Отправка произвольного email"""
        try:
            if html_message:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient]
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send()
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False
                )
            
            logger.info(f'Custom email sent to {recipient}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send custom email to {recipient}: {str(e)}')
            return False
    
    @staticmethod
    def send_verification_code_email(user_email: str, verification_code: str, user_name: str = '') -> bool:
        """Отправка email с кодом верификации"""
        try:
            subject = _('Код верификации')
            
            context = {
                'user_name': user_name or user_email,
                'verification_code': verification_code,
                'site_name': getattr(settings, 'SITE_NAME', 'Наш сайт'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            }
            
            html_message = render_to_string('accounts/emails/verification_code.html', context)
            plain_message = strip_tags(html_message)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            logger.info(f'Verification code email sent to {user_email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send verification code email to {user_email}: {str(e)}')
            return False
    
    @staticmethod
    def send_account_locked_email(user_email: str, unlock_time: str, user_name: str = '') -> bool:
        """Отправка уведомления о блокировке аккаунта"""
        try:
            subject = _('Аккаунт заблокирован')
            
            context = {
                'user_name': user_name or user_email,
                'unlock_time': unlock_time,
                'site_name': getattr(settings, 'SITE_NAME', 'Наш сайт'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            }
            
            html_message = render_to_string('accounts/emails/account_locked.html', context)
            plain_message = strip_tags(html_message)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            logger.info(f'Account locked email sent to {user_email}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to send account locked email to {user_email}: {str(e)}')
            return False
    
    @staticmethod
    def validate_email_settings() -> Dict[str, Any]:
        """Проверка настроек email"""
        issues = []
        
        # Проверяем обязательные настройки
        if not hasattr(settings, 'EMAIL_BACKEND'):
            issues.append('EMAIL_BACKEND not configured')
        
        if not hasattr(settings, 'DEFAULT_FROM_EMAIL'):
            issues.append('DEFAULT_FROM_EMAIL not configured')
        
        # Проверяем SMTP настройки если используется SMTP backend
        if getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.smtp.EmailBackend':
            if not getattr(settings, 'EMAIL_HOST', ''):
                issues.append('EMAIL_HOST not configured for SMTP backend')
            
            if not getattr(settings, 'EMAIL_PORT', None):
                issues.append('EMAIL_PORT not configured for SMTP backend')
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'backend': getattr(settings, 'EMAIL_BACKEND', 'Not configured'),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')
        }
    
    @staticmethod
    def test_email_connection() -> bool:
        """Тестирование подключения к email серверу"""
        try:
            from django.core.mail import get_connection
            
            connection = get_connection()
            connection.open()
            connection.close()
            
            logger.info('Email connection test successful')
            return True
            
        except Exception as e:
            logger.error(f'Email connection test failed: {str(e)}')
            return False
    
    @staticmethod
    def get_email_statistics() -> Dict[str, Any]:
        """Получение статистики отправки email (заглушка для будущей реализации)"""
        # Здесь можно реализовать логику сбора статистики
        # например, из логов или базы данных
        return {
            'total_sent': 0,
            'total_failed': 0,
            'last_sent': None,
            'most_common_errors': []
        }