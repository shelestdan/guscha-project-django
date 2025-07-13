from django.db import models
from apps.products.models import Product, ProductSize, Preorder, PreorderSize
from apps.accounts.models import User
from django.utils.translation import gettext_lazy as _


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
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Цена'))
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='product', 
                              verbose_name=_('Тип элемента'))
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
