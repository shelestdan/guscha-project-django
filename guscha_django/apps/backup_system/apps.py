from django.apps import AppConfig


class BackupSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.backup_system'
    verbose_name = 'Система резервного копирования'
    
    def ready(self):
        """Инициализация приложения при запуске Django"""
        # Импортируем сигналы при инициализации приложения
        try:
            from . import signals
        except ImportError:
            pass
        
        # Регистрируем задачи Celery, если Celery доступен
        try:
            from . import tasks
        except ImportError:
            pass
