from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class SecurityReport(models.Model):
    """
    Модель для хранения отчетов о безопасности от клиентов
    """
    
    RISK_LEVELS = [
        ('minimal', 'Минимальный'),
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]
    
    RECOMMENDED_ACTIONS = [
        ('allow', 'Разрешить'),
        ('monitor', 'Мониторить'),
        ('challenge', 'Дополнительная проверка'),
        ('block', 'Заблокировать'),
        ('ban', 'Забанить'),
    ]
    
    # Основная информация
    session_id = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='ID сессии'
    )
    ip_address = models.GenericIPAddressField(
        db_index=True,
        verbose_name='IP адрес'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    
    # Device Fingerprinting данные
    fingerprint_hash = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        verbose_name='Хэш отпечатка устройства'
    )
    fingerprint_confidence = models.FloatField(
        default=0,
        verbose_name='Уверенность в отпечатке'
    )
    browser_info = models.JSONField(
        default=dict,
        verbose_name='Информация о браузере'
    )
    screen_info = models.JSONField(
        default=dict,
        verbose_name='Информация об экране'
    )
    timezone_info = models.JSONField(
        default=dict,
        verbose_name='Информация о часовом поясе'
    )
    automation_detected = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Обнаружена автоматизация'
    )
    
    # Поведенческий анализ
    behavior_is_human = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='Поведение человека'
    )
    behavior_confidence = models.FloatField(
        default=0,
        verbose_name='Уверенность в поведении'
    )
    behavior_risk_score = models.FloatField(
        default=0,
        verbose_name='Риск-скор поведения'
    )
    total_interactions = models.IntegerField(
        default=0,
        verbose_name='Общее количество взаимодействий'
    )
    suspicious_patterns_count = models.IntegerField(
        default=0,
        verbose_name='Количество подозрительных паттернов'
    )
    high_risk_patterns_count = models.IntegerField(
        default=0,
        verbose_name='Количество высокорисковых паттернов'
    )
    
    # Общий анализ риска
    overall_risk_score = models.FloatField(
        default=0,
        db_index=True,
        verbose_name='Общий риск-скор'
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVELS,
        default='minimal',
        db_index=True,
        verbose_name='Уровень риска'
    )
    
    # Результаты анализа
    threat_detected = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Угроза обнаружена'
    )
    recommended_action = models.CharField(
        max_length=20,
        choices=RECOMMENDED_ACTIONS,
        default='allow',
        verbose_name='Рекомендуемое действие'
    )
    analysis_confidence = models.FloatField(
        default=0,
        verbose_name='Уверенность в анализе'
    )
    
    # Дополнительные данные
    raw_data = models.JSONField(
        default=dict,
        verbose_name='Сырые данные'
    )
    request_metadata = models.JSONField(
        default=dict,
        verbose_name='Метаданные запроса'
    )
    
    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        db_table = 'security_reports'
        verbose_name = 'Отчет о безопасности'
        verbose_name_plural = 'Отчеты о безопасности'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['risk_level', 'created_at']),
            models.Index(fields=['threat_detected', 'created_at']),
            models.Index(fields=['automation_detected', 'created_at']),
            models.Index(fields=['overall_risk_score', 'created_at']),
        ]
    
    def __str__(self):
        return f'Security Report {self.id} - {self.ip_address} ({self.risk_level})'
    
    @property
    def is_high_risk(self):
        """Проверяет, является ли отчет высокорисковым"""
        return self.risk_level in ['high', 'critical']
    
    @property
    def is_bot_suspected(self):
        """Проверяет, подозревается ли бот"""
        return (
            self.automation_detected or
            self.behavior_is_human is False or
            self.behavior_risk_score > 70 or
            self.overall_risk_score > 60
        )
    
    def get_risk_factors(self):
        """Возвращает факторы риска"""
        factors = []
        
        if self.automation_detected:
            factors.append('Обнаружена автоматизация')
        
        if self.behavior_is_human is False:
            factors.append('Поведение не человека')
        
        if self.behavior_risk_score > 70:
            factors.append('Высокий риск поведения')
        
        if self.high_risk_patterns_count > 0:
            factors.append(f'Высокорисковых паттернов: {self.high_risk_patterns_count}')
        
        if self.total_interactions == 0:
            factors.append('Отсутствие взаимодействий')
        
        if self.fingerprint_confidence < 50:
            factors.append('Низкая уверенность в отпечатке')
        
        return factors
    
    def to_dict(self):
        """Преобразует объект в словарь для API"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ip_address': str(self.ip_address),
            'user_id': self.user_id,
            'fingerprint_hash': self.fingerprint_hash,
            'fingerprint_confidence': self.fingerprint_confidence,
            'automation_detected': self.automation_detected,
            'behavior_is_human': self.behavior_is_human,
            'behavior_confidence': self.behavior_confidence,
            'behavior_risk_score': self.behavior_risk_score,
            'total_interactions': self.total_interactions,
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level,
            'threat_detected': self.threat_detected,
            'recommended_action': self.recommended_action,
            'analysis_confidence': self.analysis_confidence,
            'risk_factors': self.get_risk_factors(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class ThreatDetection(models.Model):
    """
    Модель для хранения информации об обнаруженных угрозах
    """
    
    THREAT_TYPES = [
        ('bot', 'Бот'),
        ('automation', 'Автоматизация'),
        ('suspicious_behavior', 'Подозрительное поведение'),
        ('high_risk_fingerprint', 'Высокорисковый отпечаток'),
        ('rate_limiting', 'Превышение лимитов'),
        ('malicious_patterns', 'Вредоносные паттерны'),
        ('fraud_attempt', 'Попытка мошенничества'),
        ('other', 'Другое'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Низкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая'),
        ('critical', 'Критическая'),
    ]
    
    STATUSES = [
        ('new', 'Новая'),
        ('investigating', 'Расследуется'),
        ('confirmed', 'Подтверждена'),
        ('false_positive', 'Ложное срабатывание'),
        ('resolved', 'Решена'),
        ('ignored', 'Игнорируется'),
    ]
    
    security_report = models.ForeignKey(
        SecurityReport,
        on_delete=models.CASCADE,
        related_name='threat_detections',
        verbose_name='Отчет о безопасности'
    )
    
    threat_type = models.CharField(
        max_length=50,
        choices=THREAT_TYPES,
        db_index=True,
        verbose_name='Тип угрозы'
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='medium',
        db_index=True,
        verbose_name='Серьезность'
    )
    
    confidence = models.FloatField(
        default=0,
        verbose_name='Уверенность в обнаружении'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Описание угрозы'
    )
    
    recommended_action = models.CharField(
        max_length=20,
        choices=SecurityReport.RECOMMENDED_ACTIONS,
        default='monitor',
        verbose_name='Рекомендуемое действие'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default='new',
        db_index=True,
        verbose_name='Статус'
    )
    
    metadata = models.JSONField(
        default=dict,
        verbose_name='Дополнительные данные'
    )
    
    # Обработка угрозы
    investigated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investigated_threats',
        verbose_name='Расследовал'
    )
    
    investigation_notes = models.TextField(
        blank=True,
        verbose_name='Заметки по расследованию'
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата решения'
    )
    
    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        db_table = 'threat_detections'
        verbose_name = 'Обнаружение угрозы'
        verbose_name_plural = 'Обнаружения угроз'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['threat_type', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['security_report', 'created_at']),
        ]
    
    def __str__(self):
        return f'Threat {self.id} - {self.threat_type} ({self.severity})'
    
    @property
    def is_critical(self):
        """Проверяет, является ли угроза критической"""
        return self.severity == 'critical'
    
    @property
    def is_active(self):
        """Проверяет, является ли угроза активной"""
        return self.status in ['new', 'investigating', 'confirmed']
    
    def mark_as_resolved(self, user=None, notes=''):
        """Помечает угрозу как решенную"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if user:
            self.investigated_by = user
        if notes:
            self.investigation_notes = notes
        self.save()
    
    def mark_as_false_positive(self, user=None, notes=''):
        """Помечает угрозу как ложное срабатывание"""
        self.status = 'false_positive'
        self.resolved_at = timezone.now()
        if user:
            self.investigated_by = user
        if notes:
            self.investigation_notes = notes
        self.save()
    
    def to_dict(self):
        """Преобразует объект в словарь для API"""
        return {
            'id': self.id,
            'security_report_id': self.security_report_id,
            'threat_type': self.threat_type,
            'severity': self.severity,
            'confidence': self.confidence,
            'description': self.description,
            'recommended_action': self.recommended_action,
            'status': self.status,
            'investigated_by': self.investigated_by.username if self.investigated_by else None,
            'investigation_notes': self.investigation_notes,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class SecurityBlacklist(models.Model):
    """
    Модель для хранения черного списка IP адресов и отпечатков
    """
    
    BLACKLIST_TYPES = [
        ('ip', 'IP адрес'),
        ('fingerprint', 'Отпечаток устройства'),
        ('user_agent', 'User Agent'),
        ('session', 'Сессия'),
    ]
    
    REASONS = [
        ('automated_behavior', 'Автоматизированное поведение'),
        ('malicious_activity', 'Вредоносная активность'),
        ('fraud_attempt', 'Попытка мошенничества'),
        ('rate_limit_exceeded', 'Превышение лимитов'),
        ('manual_block', 'Ручная блокировка'),
        ('other', 'Другое'),
    ]
    
    blacklist_type = models.CharField(
        max_length=20,
        choices=BLACKLIST_TYPES,
        db_index=True,
        verbose_name='Тип блокировки'
    )
    
    value = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Значение'
    )
    
    reason = models.CharField(
        max_length=50,
        choices=REASONS,
        verbose_name='Причина блокировки'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Активна'
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Истекает'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создал'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        db_table = 'security_blacklist'
        verbose_name = 'Запись черного списка'
        verbose_name_plural = 'Черный список безопасности'
        ordering = ['-created_at']
        unique_together = ['blacklist_type', 'value']
        indexes = [
            models.Index(fields=['blacklist_type', 'value']),
            models.Index(fields=['is_active', 'expires_at']),
        ]
    
    def __str__(self):
        return f'{self.blacklist_type}: {self.value}'
    
    @property
    def is_expired(self):
        """Проверяет, истекла ли блокировка"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Проверяет, действительна ли блокировка"""
        return self.is_active and not self.is_expired
    
    def deactivate(self):
        """Деактивирует блокировку"""
        self.is_active = False
        self.save()
    
    @classmethod
    def is_blocked(cls, blacklist_type, value):
        """Проверяет, заблокировано ли значение"""
        return cls.objects.filter(
            blacklist_type=blacklist_type,
            value=value,
            is_active=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).exists()