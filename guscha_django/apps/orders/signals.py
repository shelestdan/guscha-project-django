from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Order, OrderItem


@receiver(post_save, sender=OrderItem)
def update_order_totals_on_item_save(sender, instance, created, **kwargs):
    """
    Обновляем общую сумму и количество заказа при сохранении элемента
    """
    order = instance.order
    order.update_totals()


@receiver(post_delete, sender=OrderItem)
def update_order_totals_on_item_delete(sender, instance, **kwargs):
    """
    Обновляем общую сумму и количество заказа при удалении элемента
    """
    order = instance.order
    order.update_totals()


@receiver(post_save, sender=Order)
def update_product_sales_on_order_status_change(sender, instance, created, **kwargs):
    """
    Обновляем статистику продаж товаров при изменении статуса заказа
    """
    if instance.status == 'delivered':
        # Увеличиваем количество проданных товаров
        for item in instance.items.all():
            product = item.product
            product.sold_count += item.quantity
            product.save()
    elif instance.status == 'cancelled':
        # Уменьшаем количество проданных товаров при отмене
        for item in instance.items.all():
            product = item.product
            product.sold_count = max(0, product.sold_count - item.quantity)
            product.save()