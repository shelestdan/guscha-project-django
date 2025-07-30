from django.db import models
from djmoney.models.fields import MoneyField
from apps.products.models import Product, ProductSize, Preorder, PreorderSize
from apps.accounts.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


class CartItem(models.Model):
    """Модель элемента корзины"""
    ITEM_TYPES = (
        ('product', 'Товар'),
        ('preorder', 'Предзаказ'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items', 
                            null=True, blank=True, verbose_name=_('Пользователь'))
    session_id = models.CharField(max_length=100, null=True, blank=True, 
                                verbose_name=_('ID сессии'), db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, 
                              null=True, blank=True, verbose_name=_('Товар'))
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, 
                                   null=True, blank=True, verbose_name=_('Размер товара'))
    preorder = models.ForeignKey(Preorder, on_delete=models.CASCADE, 
                               null=True, blank=True, verbose_name=_('Предзаказ'))
    preorder_size = models.ForeignKey(PreorderSize, on_delete=models.CASCADE, 
                                    null=True, blank=True, verbose_name=_('Размер предзаказа'))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Количество'))
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='RUB', 
                      verbose_name='Цена')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='product', 
                              verbose_name=_('Тип элемента'))
    reservation = models.OneToOneField('Reservation', on_delete=models.SET_NULL, 
                                     null=True, blank=True, 
                                     verbose_name=_('Резервирование'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    
    class Meta:
        verbose_name = _('Элемент корзины')
        verbose_name_plural = _('Элементы корзины')
        ordering = ['-created_at']
    
    def __str__(self):
        if self.item_type == 'product' and self.product:
            return f"{self.user or self.session_id} - {self.product.name} x {self.quantity}"
        elif self.item_type == 'preorder' and self.preorder:
            return f"{self.user or self.session_id} - {self.preorder.name} x {self.quantity}"
        return f"{self.user or self.session_id} - {self.item_type} x {self.quantity}"
    
    @property
    def total(self):
        """Расчет общей стоимости элемента корзины"""
        return self.price * self.quantity


class Reservation(models.Model):
    """Модель резервирования товаров"""
    STATUS_CHOICES = (
        ('active', 'Активно'),
        ('expired', 'Истекло'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations',
                            null=True, blank=True, verbose_name=_('Пользователь'))
    session_id = models.CharField(max_length=100, null=True, blank=True,
                                verbose_name=_('ID сессии'), db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                              null=True, blank=True, verbose_name=_('Товар'))
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE,
                                   null=True, blank=True, verbose_name=_('Размер товара'))
    preorder = models.ForeignKey(Preorder, on_delete=models.CASCADE,
                               null=True, blank=True, verbose_name=_('Предзаказ'))
    preorder_size = models.ForeignKey(PreorderSize, on_delete=models.CASCADE,
                                    null=True, blank=True, verbose_name=_('Размер предзаказа'))
    quantity = models.PositiveIntegerField(verbose_name=_('Зарезервированное количество'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active',
                            verbose_name=_('Статус резервирования'))
    expires_at = models.DateTimeField(verbose_name=_('Время истечения резервирования'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    
    class Meta:
        verbose_name = _('Резервирование')
        verbose_name_plural = _('Резервирования')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['expires_at', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['session_id', 'status']),
        ]
    
    def __str__(self):
        item_name = ''
        if self.product:
            item_name = f"{self.product.name}"
            if self.product_size:
                item_name += f" ({self.product_size.size_name})"
        elif self.preorder:
            item_name = f"{self.preorder.name}"
            if self.preorder_size:
                item_name += f" ({self.preorder_size.size_name})"
        
        user_info = self.user.email if self.user else self.session_id
        return f"{user_info} - {item_name} x {self.quantity} ({self.get_status_display()})"
    
    @property
    def is_expired(self):
        """Проверка истечения резервирования"""
        return timezone.now() > self.expires_at
    
    @property
    def time_left(self):
        """Оставшееся время резервирования"""
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - timezone.now()
    
    def extend_reservation(self, minutes=30):
        """Продление резервирования"""
        if self.status == 'active':
            self.expires_at = timezone.now() + timedelta(minutes=minutes)
            self.save()
    
    def cancel(self):
        """Отмена резервирования"""
        self.status = 'cancelled'
        self.save()
    
    def complete(self):
        """Завершение резервирования (при оформлении заказа)"""
        self.status = 'completed'
        self.save()
    
    @classmethod
    def cleanup_expired(cls):
        """Очистка истекших резервирований"""
        expired_reservations = cls.objects.filter(
            status='active',
            expires_at__lt=timezone.now()
        )
        count = expired_reservations.count()
        expired_reservations.update(status='expired')
        return count
