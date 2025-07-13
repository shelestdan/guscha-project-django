from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import uuid
from apps.accounts.models import User
from apps.products.models import Product, ProductSize, Preorder, PreorderSize
from apps.addresses.models import Address


class Order(models.Model):
    """Модель заказа"""
    STATUS_CHOICES = (
        ('pending', _('В обработке')),
        ('processing', _('Обрабатывается')),
        ('shipped', _('Отправлен')),
        ('delivered', _('Доставлен')),
        ('cancelled', _('Отменен')),
        ('refunded', _('Возвращен')),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Ожидает оплаты')),
        ('paid', _('Оплачен')),
        ('failed', _('Ошибка оплаты')),
        ('refunded', _('Возвращен')),
    )
    
    FULFILLMENT_STATUS_CHOICES = (
        ('unfulfilled', _('Не выполнен')),
        ('partially_fulfilled', _('Частично выполнен')),
        ('fulfilled', _('Выполнен')),
        ('restocked', _('Возвращен на склад')),
    )
    
    order_number = models.CharField(max_length=50, unique=True, verbose_name=_('Номер заказа'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                           related_name='orders', verbose_name=_('Пользователь'))
    email = models.EmailField(verbose_name=_('Email'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', 
                           verbose_name=_('Статус заказа'))
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, 
                                   default='pending', verbose_name=_('Статус оплаты'))
    fulfillment_status = models.CharField(max_length=20, choices=FULFILLMENT_STATUS_CHOICES, 
                                       default='unfulfilled', verbose_name=_('Статус выполнения'))
    
    # Суммы
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                 verbose_name=_('Промежуточная сумма'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                            verbose_name=_('Налог'))
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                 verbose_name=_('Стоимость доставки'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                 verbose_name=_('Скидка'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                              verbose_name=_('Общая сумма'))
    
    # Адреса - новые поля для связи с моделью Address
    billing_address_obj = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='billing_orders',
        verbose_name=_('Адрес оплаты (объект)')
    )
    shipping_address_obj = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='shipping_orders',
        verbose_name=_('Адрес доставки (объект)')
    )
    
    # Старые текстовые поля для обратной совместимости
    billing_address = models.TextField(null=True, blank=True, verbose_name=_('Адрес оплаты (текст)'))
    shipping_address = models.TextField(null=True, blank=True, verbose_name=_('Адрес доставки (текст)'))
    
    # Методы
    shipping_method = models.CharField(max_length=100, null=True, blank=True, 
                                     verbose_name=_('Метод доставки'))
    payment_method = models.CharField(max_length=100, null=True, blank=True, 
                                    verbose_name=_('Метод оплаты'))
    
    # Идентификаторы
    tracking_number = models.CharField(max_length=100, null=True, blank=True, 
                                     verbose_name=_('Номер отслеживания'))
    transaction_id = models.CharField(max_length=100, null=True, blank=True, 
                                    verbose_name=_('ID транзакции'))
    
    # Примечания
    notes = models.TextField(null=True, blank=True, verbose_name=_('Примечания'))
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Дата отправки'))
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Дата доставки'))
    
    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Синхронизация текстовых полей с объектами адресов
        if self.billing_address_obj:
            self.billing_address = self.billing_address_obj.full_address
        if self.shipping_address_obj:
            self.shipping_address = self.shipping_address_obj.full_address
            
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_order_number():
        """Генерация уникального номера заказа"""
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    def get_billing_address_display(self):
        """Получение адреса оплаты для отображения"""
        if self.billing_address_obj:
            return self.billing_address_obj.full_address
        return self.billing_address
    
    def get_shipping_address_display(self):
        """Получение адреса доставки для отображения"""
        if self.shipping_address_obj:
            return self.shipping_address_obj.full_address
        return self.shipping_address
    
    def to_dict(self):
        """Преобразование заказа в словарь"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'payment_status': self.payment_status,
            'fulfillment_status': self.fulfillment_status,
            'subtotal': float(self.subtotal),
            'tax': float(self.tax),
            'shipping': float(self.shipping),
            'discount': float(self.discount),
            'total': float(self.total),
            'billing_address': self.get_billing_address_display(),
            'shipping_address': self.get_shipping_address_display(),
            'billing_address_obj': self.billing_address_obj.to_dict() if self.billing_address_obj else null,
            'shipping_address_obj': self.shipping_address_obj.to_dict() if self.shipping_address_obj else null,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items.all()],
        }


class OrderItem(models.Model):
    """Модель элемента заказа"""
    ITEM_TYPES = (
        ('product', _('Товар')),
        ('preorder', _('Предзаказ')),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', 
                            verbose_name=_('Заказ'))
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, 
                              verbose_name=_('Товар'))
    product_size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name=_('Размер товара'))
    preorder = models.ForeignKey(Preorder, on_delete=models.SET_NULL, null=True, blank=True, 
                                verbose_name=_('Предзаказ'))
    preorder_size = models.ForeignKey(PreorderSize, on_delete=models.SET_NULL, null=True, blank=True, 
                                    verbose_name=_('Размер предзаказа'))
    
    name = models.CharField(max_length=255, verbose_name=_('Название'))
    size = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Размер'))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Количество'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Цена'))
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='product', 
                               verbose_name=_('Тип элемента'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    
    class Meta:
        verbose_name = _('Элемент заказа')
        verbose_name_plural = _('Элементы заказа')
        ordering = ['id']
    
    def __str__(self):
        return f"{self.name} x {self.quantity}"
    
    @property
    def total(self):
        """Расчет общей стоимости элемента заказа"""
        return self.price * self.quantity
    
    def to_dict(self):
        """Преобразование элемента заказа в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'size': self.size,
            'quantity': self.quantity,
            'price': float(self.price),
            'total': float(self.total),
            'item_type': self.item_type,
        }
