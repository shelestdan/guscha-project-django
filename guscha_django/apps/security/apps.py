from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SecurityConfig(AppConfig):
    """
    Конфигурация приложения безопасности Django
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.security'
    verbose_name = 'Security System'
    verbose_name_plural = 'Security Systems'
    
    def ready(self):
        """
        Инициализация приложения при запуске Django
        """
        try:
            # Импортируем сигналы
            from . import signals
            
            # Импортируем задачи Celery
            from . import tasks
            
            # Настраиваем Celery если доступен
            self._setup_celery()
            
            # Инициализируем систему мониторинга
            self._initialize_monitoring()
            
            # Проверяем конфигурацию безопасности
            self._validate_security_config()
            
            logger.info("Security application initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing security application: {e}")
            # Не прерываем запуск Django из-за ошибок в системе безопасности
    
    def _setup_celery(self):
        """
        Настройка Celery для задач безопасности
        """
        try:
            from .celery_config import update_celery_config
            
            # Пытаемся получить экземпляр Celery
            try:
                from celery import current_app as celery_app
                update_celery_config(celery_app)
                logger.info("Celery configuration updated for security tasks")
            except ImportError:
                logger.warning("Celery not available, security tasks will not be scheduled")
            except Exception as e:
                logger.error(f"Error configuring Celery for security: {e}")
                
        except ImportError:
            logger.warning("Celery configuration not available")
    
    def _initialize_monitoring(self):
        """
        Инициализация системы мониторинга безопасности
        """
        try:
            from .settings import is_security_enabled, get_security_setting
            
            if not is_security_enabled():
                logger.info("Security monitoring is disabled")
                return
            
            # Проверяем настройки мониторинга
            monitoring_enabled = get_security_setting('SECURITY_MONITORING_ENABLED', True)
            if monitoring_enabled:
                logger.info("Security monitoring system initialized")
                
                # Инициализируем сервис мониторинга
                from .services.monitoring_service import SecurityMonitoringService
                monitoring_service = SecurityMonitoringService()
                
                # Запускаем начальную проверку (если не в тестовом режиме)
                if not getattr(settings, 'TESTING', False):
                    try:
                        monitoring_service.run_all_checks()
                        logger.info("Initial security check completed")
                    except Exception as e:
                        logger.warning(f"Initial security check failed: {e}")
            else:
                logger.info("Security monitoring is disabled in settings")
                
        except Exception as e:
            logger.error(f"Error initializing security monitoring: {e}")
    
    def _validate_security_config(self):
        """
        Проверка конфигурации системы безопасности
        """
        try:
            from .settings import SECURITY_SETTINGS, get_security_setting
            
            # Проверяем критически важные настройки
            required_settings = [
                'SECURITY_ENABLED',
                'SECURITY_RISK_THRESHOLDS',
                'SECURITY_RATE_LIMITING',
                'SECURITY_BLACKLIST_ENABLED'
            ]
            
            missing_settings = []
            for setting in required_settings:
                if setting not in SECURITY_SETTINGS:
                    missing_settings.append(setting)
            
            if missing_settings:
                logger.warning(f"Missing security settings: {missing_settings}")
            
            # Проверяем настройки уведомлений
            notifications_enabled = get_security_setting('SECURITY_NOTIFICATIONS_ENABLED', False)
            if notifications_enabled:
                email_settings = get_security_setting('SECURITY_NOTIFICATION_EMAILS', [])
                webhook_url = get_security_setting('SECURITY_NOTIFICATION_WEBHOOK_URL', '')
                
                if not email_settings and not webhook_url:
                    logger.warning("Notifications enabled but no email or webhook configured")
            
            # Проверяем настройки базы данных
            self._check_database_config()
            
            logger.info("Security configuration validation completed")
            
        except Exception as e:
            logger.error(f"Error validating security configuration: {e}")
    
    def _check_database_config(self):
        """
        Проверка конфигурации базы данных для системы безопасности
        """
        try:
            from django.db import connection
            from django.core.management.color import no_style
            from django.db import models
            
            # Проверяем доступность базы данных
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Проверяем наличие таблиц безопасности
            table_names = connection.introspection.table_names()
            security_tables = [
                'security_securityreport',
                'security_threatdetection',
                'security_securityblacklist',
                'security_devicefingerprint',
                'security_behavioralanalysis'
            ]
            
            missing_tables = []
            for table in security_tables:
                if table not in table_names:
                    missing_tables.append(table)
            
            if missing_tables:
                logger.warning(f"Security tables not found: {missing_tables}. Run migrations.")
            else:
                logger.info("All security database tables are available")
                
        except Exception as e:
            logger.warning(f"Could not verify database configuration: {e}")
    
    @classmethod
    def get_security_status(cls):
        """
        Возвращает статус системы безопасности
        """
        try:
            from .settings import is_security_enabled, get_security_setting
            
            status = {
                'enabled': is_security_enabled(),
                'monitoring_enabled': get_security_setting('SECURITY_MONITORING_ENABLED', True),
                'blacklist_enabled': get_security_setting('SECURITY_BLACKLIST_ENABLED', True),
                'rate_limiting_enabled': get_security_setting('SECURITY_RATE_LIMITING_ENABLED', True),
                'device_fingerprinting_enabled': get_security_setting('SECURITY_DEVICE_FINGERPRINTING_ENABLED', True),
                'behavioral_analysis_enabled': get_security_setting('SECURITY_BEHAVIORAL_ANALYSIS_ENABLED', True),
                'notifications_enabled': get_security_setting('SECURITY_NOTIFICATIONS_ENABLED', False),
                'version': '1.0.0'
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting security status: {e}")
            return {'enabled': False, 'error': str(e)}