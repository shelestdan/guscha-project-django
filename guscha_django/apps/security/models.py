from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class SecurityReport(models.Model):
    """
    Модель для хранения отчетов о безопасности
    """
    REPORT_TYPES = [
        ('suspicious_activity', 'Подозрительная активность'),
        ('registration_attempt', 'Попытка регистрации'),
        ('form_submission', 'Отправка формы'),
        ('honeypot_triggered', 'Сработал honeypot'),
        ('fast_form_submission', 'Быстрая отправка формы'),
        ('automation_detected', 'Обнаружена автоматизация'),
        ('behavioral_anomaly', 'Поведенческая аномалия'),
    ]
    
    ip_address = models.GenericIPAddressField('IP адрес')
    user_agent = models.TextField('User Agent', blank=True)
    device_fingerprint = models.CharField('Отпечаток устройства', max_length=255, blank=True)
    report_type = models.CharField('Тип отчета', max_length=50, choices=REPORT_TYPES)
    risk_score = models.IntegerField(
        'Оценка риска',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    metadata = models.JSONField('Метаданные', default=dict, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        db_table = 'security_reports'
        verbose_name = 'Отчет о безопасности'
        verbose_name_plural = 'Отчеты о безопасности'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['report_type', 'created_at']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return f'{self.get_report_type_display()} - {self.ip_address} ({self.risk_score})'


class ThreatDetection(models.Model):
    """
    Модель для хранения обнаруженных угроз
    """
    THREAT_TYPES = [
        ('bot_activity', 'Активность бота'),
        ('automation_detected', 'Обнаружена автоматизация'),
        ('suspicious_pattern', 'Подозрительный паттерн'),
        ('mass_registration', 'Массовая регистрация'),
        ('brute_force', 'Брутфорс атака'),
        ('honeypot_trigger', 'Срабатывание honeypot'),
        ('behavioral_anomaly', 'Поведенческая аномалия'),
    ]
    
    security_report = models.ForeignKey(
        SecurityReport,
        on_delete=models.CASCADE,
        related_name='threats',
        verbose_name='Отчет о безопасности'
    )
    threat_type = models.CharField('Тип угрозы', max_length=50, choices=THREAT_TYPES)
    risk_score = models.IntegerField(
        'Оценка риска',
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    description = models.TextField('Описание', blank=True)
    is_resolved = models.BooleanField('Решено', default=False)
    resolved_at = models.DateTimeField('Решено в', null=True, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        db_table = 'threat_detections'
        verbose_name = 'Обнаружение угрозы'
        verbose_name_plural = 'Обнаружения угроз'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['threat_type', 'created_at']),
            models.Index(fields=['is_resolved']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return f'{self.get_threat_type_display()} - {self.risk_score}'


class SecurityBlacklist(models.Model):
    """
    Модель для хранения черного списка
    """
    BLACKLIST_TYPES = [
        ('ip', 'IP адрес'),
        ('user_agent', 'User Agent'),
        ('fingerprint', 'Отпечаток устройства'),
        ('email', 'Email'),
        ('phone', 'Телефон'),
    ]
    
    blacklist_type = models.CharField('Тип', max_length=20, choices=BLACKLIST_TYPES)
    value = models.CharField('Значение', max_length=500)
    reason = models.TextField('Причина')
    is_active = models.BooleanField('Активно', default=True)
    expires_at = models.DateTimeField('Истекает', null=True, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        db_table = 'security_blacklist'
        verbose_name = 'Запись черного списка'
        verbose_name_plural = 'Черный список'
        ordering = ['-created_at']
        unique_together = ['blacklist_type', 'value']
        indexes = [
            models.Index(fields=['blacklist_type', 'value']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f'{self.get_blacklist_type_display()}: {self.value}'
    
    def is_expired(self):
        """Проверяет, истекла ли запись"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class DeviceFingerprint(models.Model):
    """
    Модель для хранения отпечатков устройств
    """
    fingerprint_hash = models.CharField('Хеш отпечатка', max_length=255, unique=True)
    ip_address = models.GenericIPAddressField('IP адрес')
    fingerprint_data = models.JSONField('Данные отпечатка', default=dict)
    first_seen = models.DateTimeField('Первое обнаружение', auto_now_add=True)
    last_seen = models.DateTimeField('Последнее обнаружение', auto_now=True)
    usage_count = models.PositiveIntegerField('Количество использований', default=1)
    is_suspicious = models.BooleanField('Подозрительный', default=False)
    
    class Meta:
        db_table = 'security_device_fingerprint'
        verbose_name = 'Отпечаток устройства'
        verbose_name_plural = 'Отпечатки устройств'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['ip_address', 'last_seen']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['usage_count']),
        ]
    
    def __str__(self):
        return f'Отпечаток {self.fingerprint_hash[:16]}... - {self.ip_address}'


class BehavioralAnalysis(models.Model):
    """
    Модель для хранения поведенческого анализа
    """
    session_key = models.CharField('Ключ сессии', max_length=255)
    ip_address = models.GenericIPAddressField('IP адрес')
    events_per_minute = models.FloatField('События в минуту', default=0)
    mouse_movements = models.IntegerField('Движения мыши', default=0)
    keystroke_patterns = models.JSONField('Паттерны нажатий', default=dict)
    scroll_behavior = models.JSONField('Поведение прокрутки', default=dict)
    focus_events = models.IntegerField('События фокуса', default=0)
    form_interaction_time = models.FloatField('Время взаимодействия с формой', default=0)
    is_human_like = models.BooleanField('Похоже на человека', default=True)
    risk_score = models.IntegerField(
        'Оценка риска',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        db_table = 'security_behavioral_analysis'
        verbose_name = 'Поведенческий анализ'
        verbose_name_plural = 'Поведенческие анализы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['is_human_like']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return f'Анализ {self.session_key[:16]}... - {self.ip_address} ({self.risk_score})'


class SecuritySettings(models.Model):
    """
    Модель для хранения настроек безопасности
    """
    key = models.CharField('Ключ', max_length=100, unique=True)
    value = models.TextField('Значение')
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активно', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        db_table = 'security_settings'
        verbose_name = 'Настройка безопасности'
        verbose_name_plural = 'Настройки безопасности'
        ordering = ['key']
    
    def __str__(self):
        return f'{self.key}: {self.value[:50]}'
    
    def get_value(self):
        """Возвращает значение с правильным типом"""
        try:
            return json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            return self.value


class SecurityLog(models.Model):
    """
    Модель для логирования событий безопасности
    """
    LOG_LEVELS = [
        ('DEBUG', 'Отладка'),
        ('INFO', 'Информация'),
        ('WARNING', 'Предупреждение'),
        ('ERROR', 'Ошибка'),
        ('CRITICAL', 'Критическая'),
    ]
    
    level = models.CharField('Уровень', max_length=10, choices=LOG_LEVELS)
    message = models.TextField('Сообщение')
    ip_address = models.GenericIPAddressField('IP адрес', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    extra_data = models.JSONField('Дополнительные данные', default=dict, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        db_table = 'security_log'
        verbose_name = 'Лог безопасности'
        verbose_name_plural = 'Логи безопасности'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', 'created_at']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f'[{self.level}] {self.message[:100]}'