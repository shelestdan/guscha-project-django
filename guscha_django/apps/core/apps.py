from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Основные настройки'
    
    def ready(self):
        """
        Выполняется когда приложение готово к работе
        """
        # Временно отключаем импорт admin.py для диагностики
        # from . import admin
        pass
