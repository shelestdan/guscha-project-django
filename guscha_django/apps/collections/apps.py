import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CollectionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.collections'
    verbose_name = 'Коллекции'
    
    def ready(self):
        """Инициализация приложения"""
        try:
            import apps.collections.signals  # noqa F401
        except ImportError:
            logger.debug("Модуль signals не найден в apps.collections")