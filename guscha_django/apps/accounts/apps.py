from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    """Конфигурация приложения для управления аккаунтами."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Управление аккаунтами'
    
    def ready(self):
        """Инициализация приложения при запуске Django."""
        try:
            # Импорт admin.py для регистрации моделей в админке
            from . import admin
            logger.info("Admin модуль успешно импортирован")
            
            # Временно отключаем импорт сигналов для диагностики
            # from . import signals
            logger.info("Приложение accounts успешно инициализировано (без сигналов)")
        except ImportError as e:
            logger.warning(f"Не удалось импортировать модули: {e}")
        except Exception as e:
            logger.error(f"Ошибка при инициализации приложения accounts: {e}")
            
        # Проверка настроек безопасности
        self._check_security_settings()
    
    def _check_security_settings(self):
        """Проверка критически важных настроек безопасности."""
        from django.conf import settings
        
        # Проверка наличия SECRET_KEY
        if not getattr(settings, 'SECRET_KEY', None):
            logger.error("SECRET_KEY не установлен!")
            
        # Проверка настроек JWT
        if not getattr(settings, 'JWT_SECRET_KEY', None):
            logger.warning("JWT_SECRET_KEY не установлен, используется SECRET_KEY")
            
        # Проверка настроек email
        if not getattr(settings, 'EMAIL_HOST', None):
            logger.warning("EMAIL_HOST не настроен, отправка email может не работать")
            
        # Проверка настроек Telegram
        if not getattr(settings, 'TELEGRAM_BOT_TOKEN', None):
            logger.warning("TELEGRAM_BOT_TOKEN не установлен, Telegram интеграция недоступна")
            
        logger.info("Проверка настроек безопасности завершена")
