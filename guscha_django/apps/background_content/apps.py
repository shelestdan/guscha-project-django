from django.apps import AppConfig


class BackgroundContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.background_content'
    verbose_name = 'Управление фоновым контентом'
    
    def ready(self):
        """Инициализация приложения"""
        pass
