from django.db import models
from django.utils.translation import gettext_lazy as _


class Background(models.Model):
    """Модель фоновых изображений и видео"""
    FILE_TYPE_CHOICES = (
        ('image', _('Изображение')),
        ('video', _('Видео')),
    )
    
    file_url = models.URLField(max_length=255, verbose_name=_('URL файла'))
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='image', 
                              verbose_name=_('Тип файла'))
    is_active = models.BooleanField(default=True, verbose_name=_('Активно'))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Порядок сортировки'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    
    class Meta:
        verbose_name = _('Фоновое изображение/видео')
        verbose_name_plural = _('Фоновые изображения/видео')
        ordering = ['sort_order', 'id']
    
    def __str__(self):
        return f"{self.get_file_type_display()} #{self.id}"
