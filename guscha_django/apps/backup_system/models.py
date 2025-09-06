from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class BackupLog(models.Model):
    """Простой лог операций резервного копирования"""
    
    OPERATION_CHOICES = [
        ('backup_db', 'Резервное копирование БД'),
        ('backup_media', 'Резервное копирование медиа'),
        ('restore_db', 'Восстановление БД'),
        ('restore_media', 'Восстановление медиа'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
    ]
    
    timestamp = models.DateTimeField('Время операции', auto_now_add=True)
    operation_type = models.CharField('Тип операции', max_length=20, choices=OPERATION_CHOICES, default='backup_db')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='success')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    details = models.TextField('Детали', blank=True)
    
    class Meta:
        verbose_name = 'Лог резервного копирования'
        verbose_name_plural = 'Логи резервного копирования'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f'{self.get_operation_type_display()} - {self.get_status_display()} ({self.timestamp})'
