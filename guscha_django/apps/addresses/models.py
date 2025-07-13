from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User


class Address(models.Model):
    """Модель адреса доставки для пользователей"""
    
    ADDRESS_TYPES = (
        ('billing', _('Адрес оплаты')),
        ('shipping', _('Адрес доставки')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses',
                           verbose_name=_('Пользователь'))
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='shipping',
                                  verbose_name=_('Тип адреса'))
    
    # Основная информация
    first_name = models.CharField(max_length=50, verbose_name=_('Имя'))
    last_name = models.CharField(max_length=50, verbose_name=_('Фамилия'))
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Компания'))
    
    # Адрес
    address_line1 = models.CharField(max_length=255, verbose_name=_('Адрес строка 1'))
    address_line2 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Адрес строка 2'))
    city = models.CharField(max_length=100, verbose_name=_('Город'))
    state = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Регион/Область'))
    postal_code = models.CharField(max_length=20, verbose_name=_('Почтовый индекс'))
    country = models.CharField(max_length=100, default='Russia', verbose_name=_('Страна'))
    
    # Контактная информация
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Телефон'))
    
    # Настройки
    is_default = models.BooleanField(default=False, verbose_name=_('Адрес по умолчанию'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активен'))
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    
    class Meta:
        verbose_name = _('Адрес')
        verbose_name_plural = _('Адреса')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'address_type']),
            models.Index(fields=['is_default', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.address_line1}, {self.city}"
    
    def save(self, *args, **kwargs):
        """При сохранении адреса по умолчанию отключаем другие адреса по умолчанию"""
        if self.is_default:
            # Отключаем другие адреса по умолчанию для этого пользователя и типа
            Address.objects.filter(
                user=self.user,
                address_type=self.address_type,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        """Полное имя"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self):
        """Полный адрес в одну строку"""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join(filter(None, parts))
    
    def to_dict(self):
        """Преобразование адреса в словарь"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company': self.company,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'phone': self.phone,
            'is_default': self.is_default,
            'full_address': self.full_address,
            'full_name': self.full_name,
        }