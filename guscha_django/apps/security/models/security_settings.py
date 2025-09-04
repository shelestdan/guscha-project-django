from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class SecuritySettings(models.Model):
    """
    Модель для хранения настроек системы безопасности
    """
    
    # Основные настройки
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название настройки'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    
    # Настройки блокировки
    max_failed_attempts = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Максимальное количество неудачных попыток'
    )
    
    lockout_duration = models.IntegerField(
        default=300,  # 5 минут в секундах
        validators=[MinValueValidator(60), MaxValueValidator(86400)],  # от 1 минуты до 24 часов
        verbose_name='Длительность блокировки (секунды)'
    )
    
    # Настройки мониторинга
    enable_ip_monitoring = models.BooleanField(
        default=True,
        verbose_name='Включить мониторинг IP адресов'
    )
    
    enable_device_fingerprinting = models.BooleanField(
        default=True,
        verbose_name='Включить отпечатки устройств'
    )
    
    enable_behavioral_analysis = models.BooleanField(
        default=True,
        verbose_name='Включить поведенческий анализ'
    )
    
    # Настройки риска
    risk_threshold_low = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Порог низкого риска'
    )
    
    risk_threshold_medium = models.IntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Порог среднего риска'
    )
    
    risk_threshold_high = models.IntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Порог высокого риска'
    )
    
    # Настройки автоматических действий
    auto_block_high_risk = models.BooleanField(
        default=False,
        verbose_name='Автоматически блокировать высокий риск'
    )
    
    auto_challenge_medium_risk = models.BooleanField(
        default=True,
        verbose_name='Автоматически требовать дополнительную проверку для среднего риска'
    )
    
    # Настройки уведомлений
    enable_email_alerts = models.BooleanField(
        default=True,
        verbose_name='Включить email уведомления'
    )
    
    alert_email = models.EmailField(
        blank=True,
        verbose_name='Email для уведомлений'
    )
    
    # Настройки очистки данных
    data_retention_days = models.IntegerField(
        default=90,
        validators=[MinValueValidator(1), MaxValueValidator(3650)],  # от 1 дня до 10 лет
        verbose_name='Срок хранения данных (дни)'
    )
    
    auto_cleanup_enabled = models.BooleanField(
        default=True,
        verbose_name='Включить автоматическую очистку'
    )
    
    # Настройки API
    api_rate_limit = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        verbose_name='Лимит запросов API в минуту'
    )
    
    api_key_required = models.BooleanField(
        default=False,
        verbose_name='Требовать API ключ'
    )
    
    # Дополнительные настройки
    additional_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Дополнительные настройки'
    )
    
    # Метаданные
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )
    
    class Meta:
        db_table = 'security_settings'
        verbose_name = 'Настройка безопасности'
        verbose_name_plural = 'Настройки безопасности'
        ordering = ['name']
    
    def __str__(self):
        return f"Настройки: {self.name}"
    
    @classmethod
    def get_active_settings(cls):
        """
        Возвращает активные настройки безопасности
        """
        try:
            return cls.objects.filter(is_active=True).first()
        except cls.DoesNotExist:
            return cls.get_default_settings()
    
    @classmethod
    def get_default_settings(cls):
        """
        Создает и возвращает настройки по умолчанию
        """
        defaults, created = cls.objects.get_or_create(
            name='default',
            defaults={
                'description': 'Настройки безопасности по умолчанию',
                'max_failed_attempts': 5,
                'lockout_duration': 300,
                'enable_ip_monitoring': True,
                'enable_device_fingerprinting': True,
                'enable_behavioral_analysis': True,
                'risk_threshold_low': 30,
                'risk_threshold_medium': 60,
                'risk_threshold_high': 80,
                'auto_block_high_risk': False,
                'auto_challenge_medium_risk': True,
                'enable_email_alerts': True,
                'data_retention_days': 90,
                'auto_cleanup_enabled': True,
                'api_rate_limit': 100,
                'api_key_required': False,
                'is_active': True
            }
        )
        return defaults
    
    def get_risk_level(self, score):
        """
        Определяет уровень риска на основе оценки
        """
        if score >= self.risk_threshold_high:
            return 'high'
        elif score >= self.risk_threshold_medium:
            return 'medium'
        elif score >= self.risk_threshold_low:
            return 'low'
        else:
            return 'minimal'
    
    def should_block_request(self, risk_score):
        """
        Определяет, нужно ли блокировать запрос
        """
        if self.auto_block_high_risk and risk_score >= self.risk_threshold_high:
            return True
        return False
    
    def should_challenge_request(self, risk_score):
        """
        Определяет, нужна ли дополнительная проверка
        """
        if self.auto_challenge_medium_risk and risk_score >= self.risk_threshold_medium:
            return True
        return False
    
    def clean(self):
        """
        Валидация настроек
        """
        from django.core.exceptions import ValidationError
        
        # Проверяем, что пороги риска идут по возрастанию
        if self.risk_threshold_low >= self.risk_threshold_medium:
            raise ValidationError('Порог низкого риска должен быть меньше среднего')
        
        if self.risk_threshold_medium >= self.risk_threshold_high:
            raise ValidationError('Порог среднего риска должен быть меньше высокого')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)