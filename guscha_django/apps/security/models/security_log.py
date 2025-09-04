from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class SecurityLog(models.Model):
    """
    Модель для логирования событий безопасности
    """
    
    # Типы событий
    EVENT_TYPES = [
        ('login_attempt', 'Попытка входа'),
        ('login_success', 'Успешный вход'),
        ('login_failed', 'Неудачный вход'),
        ('logout', 'Выход'),
        ('password_change', 'Смена пароля'),
        ('password_reset', 'Сброс пароля'),
        ('account_locked', 'Блокировка аккаунта'),
        ('account_unlocked', 'Разблокировка аккаунта'),
        ('suspicious_activity', 'Подозрительная активность'),
        ('security_violation', 'Нарушение безопасности'),
        ('ip_blocked', 'Блокировка IP'),
        ('ip_unblocked', 'Разблокировка IP'),
        ('device_registered', 'Регистрация устройства'),
        ('device_blocked', 'Блокировка устройства'),
        ('api_access', 'Доступ к API'),
        ('api_violation', 'Нарушение API'),
        ('data_breach_attempt', 'Попытка утечки данных'),
        ('brute_force_attack', 'Атака перебора'),
        ('sql_injection_attempt', 'Попытка SQL инъекции'),
        ('xss_attempt', 'Попытка XSS атаки'),
        ('csrf_violation', 'Нарушение CSRF'),
        ('rate_limit_exceeded', 'Превышение лимита запросов'),
        ('honeypot_triggered', 'Срабатывание honeypot'),
        ('bot_detected', 'Обнаружен бот'),
        ('captcha_failed', 'Неудачная капча'),
        ('captcha_success', 'Успешная капча'),
        ('two_factor_enabled', 'Включена двухфакторная аутентификация'),
        ('two_factor_disabled', 'Отключена двухфакторная аутентификация'),
        ('two_factor_failed', 'Неудачная двухфакторная аутентификация'),
        ('session_hijack_attempt', 'Попытка перехвата сессии'),
        ('privilege_escalation', 'Попытка повышения привилегий'),
        ('file_upload_violation', 'Нарушение при загрузке файла'),
        ('admin_access', 'Доступ к админ панели'),
        ('config_change', 'Изменение конфигурации'),
        ('backup_created', 'Создание резервной копии'),
        ('backup_restored', 'Восстановление из резервной копии'),
        ('maintenance_mode', 'Режим обслуживания'),
        ('system_alert', 'Системное предупреждение'),
        ('other', 'Другое')
    ]
    
    # Уровни серьезности
    SEVERITY_LEVELS = [
        ('info', 'Информация'),
        ('warning', 'Предупреждение'),
        ('error', 'Ошибка'),
        ('critical', 'Критическое')
    ]
    
    # Статусы
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('investigating', 'Расследуется'),
        ('resolved', 'Решено'),
        ('false_positive', 'Ложное срабатывание'),
        ('ignored', 'Игнорируется')
    ]
    
    # Основная информация
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        verbose_name='Тип события'
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='info',
        verbose_name='Уровень серьезности'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус'
    )
    
    # Информация о пользователе
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    
    username = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Имя пользователя'
    )
    
    # Сетевая информация
    ip_address = models.GenericIPAddressField(
        verbose_name='IP адрес'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    session_id = models.CharField(
        max_length=40,
        blank=True,
        verbose_name='ID сессии'
    )
    
    # Информация о запросе
    request_method = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='HTTP метод'
    )
    
    request_path = models.TextField(
        blank=True,
        verbose_name='Путь запроса'
    )
    
    request_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Параметры запроса'
    )
    
    # Описание события
    message = models.TextField(
        verbose_name='Сообщение'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Подробное описание'
    )
    
    # Дополнительные данные
    additional_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Дополнительные данные'
    )
    
    # Оценка риска
    risk_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Оценка риска'
    )
    
    # Геолокация
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Страна'
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Город'
    )
    
    # Информация об устройстве
    device_fingerprint = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Отпечаток устройства'
    )
    
    device_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Тип устройства'
    )
    
    # Связанные объекты
    related_security_report = models.ForeignKey(
        'SecurityReport',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Связанный отчет безопасности'
    )
    
    # Обработка
    processed = models.BooleanField(
        default=False,
        verbose_name='Обработано'
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время обработки'
    )
    
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_security_logs',
        verbose_name='Обработано пользователем'
    )
    
    # Автоматические действия
    auto_action_taken = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Автоматическое действие'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
        db_index=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )
    
    class Meta:
        db_table = 'security_log'
        verbose_name = 'Лог безопасности'
        verbose_name_plural = 'Логи безопасности'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['risk_score']),
            models.Index(fields=['processed', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.ip_address} ({self.created_at})"
    
    @classmethod
    def log_event(cls, event_type, ip_address, message, **kwargs):
        """
        Создает новую запись в логе безопасности
        """
        return cls.objects.create(
            event_type=event_type,
            ip_address=ip_address,
            message=message,
            **kwargs
        )
    
    @classmethod
    def log_login_attempt(cls, username, ip_address, success=False, **kwargs):
        """
        Логирует попытку входа
        """
        event_type = 'login_success' if success else 'login_failed'
        severity = 'info' if success else 'warning'
        
        return cls.log_event(
            event_type=event_type,
            ip_address=ip_address,
            message=f"Попытка входа пользователя {username}",
            username=username,
            severity=severity,
            **kwargs
        )
    
    @classmethod
    def log_suspicious_activity(cls, ip_address, message, risk_score=50, **kwargs):
        """
        Логирует подозрительную активность
        """
        return cls.log_event(
            event_type='suspicious_activity',
            ip_address=ip_address,
            message=message,
            severity='warning',
            risk_score=risk_score,
            **kwargs
        )
    
    @classmethod
    def log_security_violation(cls, ip_address, message, risk_score=80, **kwargs):
        """
        Логирует нарушение безопасности
        """
        return cls.log_event(
            event_type='security_violation',
            ip_address=ip_address,
            message=message,
            severity='error',
            risk_score=risk_score,
            **kwargs
        )
    
    @classmethod
    def get_recent_events(cls, hours=24, event_types=None):
        """
        Возвращает недавние события
        """
        since = timezone.now() - timezone.timedelta(hours=hours)
        queryset = cls.objects.filter(created_at__gte=since)
        
        if event_types:
            queryset = queryset.filter(event_type__in=event_types)
        
        return queryset.order_by('-created_at')
    
    @classmethod
    def get_events_by_ip(cls, ip_address, hours=24):
        """
        Возвращает события для конкретного IP
        """
        since = timezone.now() - timezone.timedelta(hours=hours)
        return cls.objects.filter(
            ip_address=ip_address,
            created_at__gte=since
        ).order_by('-created_at')
    
    @classmethod
    def get_high_risk_events(cls, min_risk_score=70, hours=24):
        """
        Возвращает события с высоким риском
        """
        since = timezone.now() - timezone.timedelta(hours=hours)
        return cls.objects.filter(
            risk_score__gte=min_risk_score,
            created_at__gte=since
        ).order_by('-risk_score', '-created_at')
    
    @classmethod
    def get_unprocessed_events(cls):
        """
        Возвращает необработанные события
        """
        return cls.objects.filter(
            processed=False,
            severity__in=['warning', 'error', 'critical']
        ).order_by('-created_at')
    
    def mark_as_processed(self, user=None, action_taken=None):
        """
        Отмечает событие как обработанное
        """
        self.processed = True
        self.processed_at = timezone.now()
        self.processed_by = user
        if action_taken:
            self.auto_action_taken = action_taken
        self.save()
    
    def get_risk_level(self):
        """
        Возвращает уровень риска на основе оценки
        """
        if self.risk_score >= 80:
            return 'high'
        elif self.risk_score >= 50:
        	return 'medium'
        elif self.risk_score >= 20:
            return 'low'
        else:
            return 'minimal'
    
    def is_critical(self):
        """
        Проверяет, является ли событие критическим
        """
        return self.severity == 'critical' or self.risk_score >= 90
    
    def requires_immediate_attention(self):
        """
        Проверяет, требует ли событие немедленного внимания
        """
        critical_events = [
            'data_breach_attempt',
            'sql_injection_attempt',
            'privilege_escalation',
            'session_hijack_attempt'
        ]
        
        return (
            self.event_type in critical_events or
            self.severity == 'critical' or
            self.risk_score >= 85
        )