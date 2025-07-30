from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Заказы'
    
    def ready(self):
        """
        Импортируем сигналы при запуске приложения
        """
        # Временно отключаем импорт сигналов для диагностики
        # import apps.orders.signals
        pass
