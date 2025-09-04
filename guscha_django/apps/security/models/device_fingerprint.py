from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class DeviceFingerprint(models.Model):
    """
    Модель для хранения отпечатков устройств
    """
    
    RISK_LEVELS = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]
    
    # Основная информация
    fingerprint_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='Хеш отпечатка'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    
    # Информация об устройстве
    user_agent = models.TextField(
        verbose_name='User Agent'
    )
    
    screen_resolution = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Разрешение экрана'
    )
    
    timezone_offset = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Смещение часового пояса'
    )
    
    language = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Язык'
    )
    
    platform = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Платформа'
    )
    
    plugins = models.TextField(
        blank=True,
        verbose_name='Плагины браузера'
    )
    
    canvas_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Canvas отпечаток'
    )
    
    webgl_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='WebGL отпечаток'
    )
    
    # Анализ риска
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVELS,
        default='low',
        verbose_name='Уровень риска'
    )
    
    risk_score = models.IntegerField(
        default=0,
        verbose_name='Оценка риска (0-100)'
    )
    
    is_suspicious = models.BooleanField(
        default=False,
        verbose_name='Подозрительный'
    )
    
    # Статистика использования
    usage_count = models.IntegerField(
        default=1,
        verbose_name='Количество использований'
    )
    
    first_seen = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Первое обнаружение'
    )
    
    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name='Последнее обнаружение'
    )
    
    # Дополнительные данные
    additional_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Дополнительные данные'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Заметки'
    )
    
    class Meta:
        db_table = 'security_device_fingerprint'
        verbose_name = 'Отпечаток устройства'
        verbose_name_plural = 'Отпечатки устройств'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['fingerprint_hash']),
            models.Index(fields=['user']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['last_seen']),
        ]
    
    def __str__(self):
        return f"Отпечаток {self.fingerprint_hash[:8]}... ({self.risk_level})"
    
    def update_usage(self):
        """
        Обновляет статистику использования
        """
        self.usage_count += 1
        self.last_seen = timezone.now()
        self.save(update_fields=['usage_count', 'last_seen'])
    
    def mark_suspicious(self, reason=None):
        """
        Помечает отпечаток как подозрительный
        """
        self.is_suspicious = True
        self.risk_level = 'high'
        self.risk_score = max(self.risk_score, 70)
        
        if reason:
            if not self.notes:
                self.notes = reason
            else:
                self.notes += f"\n{timezone.now().strftime('%Y-%m-%d %H:%M')}: {reason}"
        
        self.save()
    
    def calculate_risk_score(self):
        """
        Вычисляет оценку риска на основе характеристик устройства
        """
        score = 0
        
        # Проверка User Agent
        if 'bot' in self.user_agent.lower() or 'crawler' in self.user_agent.lower():
            score += 50
        
        # Проверка частоты использования
        if self.usage_count > 100:
            score += 20
        elif self.usage_count > 50:
            score += 10
        
        # Проверка времени между использованиями
        if self.first_seen and self.last_seen:
            time_diff = self.last_seen - self.first_seen
            if time_diff.total_seconds() < 3600 and self.usage_count > 10:  # Много запросов за час
                score += 30
        
        # Проверка отсутствия важных данных
        if not self.canvas_fingerprint or not self.webgl_fingerprint:
            score += 15
        
        self.risk_score = min(score, 100)
        
        # Обновляем уровень риска
        if self.risk_score >= 80:
            self.risk_level = 'critical'
        elif self.risk_score >= 60:
            self.risk_level = 'high'
        elif self.risk_score >= 40:
            self.risk_level = 'medium'
        else:
            self.risk_level = 'low'
        
        return self.risk_score