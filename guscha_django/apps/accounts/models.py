from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import secrets  # Заменяем random на secrets
import string
import uuid
from simple_history.models import HistoricalRecords
import hashlib
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    """Менеджер для пользовательской модели User"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Создает и сохраняет пользователя с указанным email и паролем"""
        if not email:
            raise ValueError(_('Email должен быть указан'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создает и сохраняет суперпользователя с указанным email и паролем"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Суперпользователь должен иметь is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Суперпользователь должен иметь is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Расширенная модель пользователя с Telegram интеграцией"""
    
    username = None  # Убираем username, используем email
    email = models.EmailField(
        _('Адрес электронной почты'),
        unique=True,
        help_text=_('Обязательное поле. Введите действующий email адрес.')
    )
    
    # Основная информация
    first_name = models.CharField(
        _('Имя'), 
        max_length=150, 
        blank=True,
        help_text=_('Имя пользователя')
    )
    last_name = models.CharField(
        _('Фамилия'), 
        max_length=150, 
        blank=True,
        help_text=_('Фамилия пользователя')
    )
    
    # Контактная информация
    phone = models.CharField(
        _('Номер телефона'),
        max_length=20,
        blank=True,
        help_text=_('Номер телефона в международном формате')
    )
    address = models.TextField(
        _('Адрес'),
        blank=True,
        help_text=_('Полный почтовый адрес')
    )
    
    # Telegram интеграция
    telegram_chat_id = models.BigIntegerField(
        _('Telegram Chat ID'),
        null=True,
        blank=True,
        unique=True,
        help_text=_('Уникальный ID чата в Telegram')
    )
    telegram_username = models.CharField(
        _('Telegram Username'),
        max_length=100,
        blank=True,
        help_text=_('Username пользователя в Telegram (без @)')
    )
    is_telegram_verified = models.BooleanField(
        _('Telegram верифицирован'),
        default=False,
        help_text=_('Подтверждена ли связь с Telegram аккаунтом')
    )
    
    # История изменений
    history = HistoricalRecords()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['telegram_chat_id']),
            models.Index(fields=['is_telegram_verified']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Возвращает полное имя пользователя"""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_short_name(self):
        """Возвращает короткое имя пользователя"""
        return self.first_name or self.email.split('@')[0]


class PendingUserRegistration(models.Model):
    """Модель для временного хранения данных регистрации до подтверждения Telegram"""
    email = models.EmailField(_('Email'), unique=True)
    first_name = models.CharField(_('First Name'), max_length=150)
    last_name = models.CharField(_('Last Name'), max_length=150)
    phone = models.CharField(_('Phone'), max_length=20, blank=True)
    address = models.TextField(_('Address'), blank=True)
    password_hash = models.CharField(_('Password Hash'), max_length=128)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'))
    
    class Meta:
        verbose_name = _('Pending User Registration')
        verbose_name_plural = _('Pending User Registrations')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)  # Данные действуют 24 часа
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Проверяет, истекли ли данные регистрации"""
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f'Pending registration for {self.email}'


class TelegramVerificationCode(models.Model):
    """Безопасная модель для хранения кодов верификации Telegram"""
    
    VERIFICATION_TYPES = [
        ('registration', _('Регистрация')),
        ('login', _('Вход в систему')),
        ('password_reset', _('Сброс пароля')),
        ('qr_registration', _('QR регистрация')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='telegram_verification_codes',
        verbose_name=_('Пользователь'),
        null=True,
        blank=True
    )
    
    pending_registration = models.ForeignKey(
        PendingUserRegistration,
        on_delete=models.CASCADE,
        related_name='telegram_verification_codes',
        null=True,
        blank=True
    )
    
    # Код верификации (временно для совместимости)
    code = models.CharField(
        _('Код верификации'),
        max_length=6,
        null=True,
        blank=True,
        help_text=_('6-значный код верификации')
    )
    
    # Безопасное хранение кода (только хеш)
    code_hash = models.CharField(
        _('Хеш кода'),
        max_length=64,
        null=True,
        blank=True,
        help_text=_('SHA-256 хеш кода верификации')
    )
    
    # Соль для дополнительной безопасности
    salt = models.CharField(
        _('Соль'),
        max_length=64,
        null=True,
        blank=True,
        help_text=_('Случайная соль для хеширования')
    )
    
    telegram_chat_id = models.BigIntegerField(_('Telegram Chat ID'), null=True, blank=True)
    
    verification_type = models.CharField(
        _('Тип верификации'),
        max_length=20,
        choices=VERIFICATION_TYPES,
        default='registration'
    )
    
    created_at = models.DateTimeField(
        _('Создан'),
        auto_now_add=True
    )
    
    expires_at = models.DateTimeField(
        _('Истекает')
    )
    
    is_used = models.BooleanField(
        _('Использован'),
        default=False
    )
    
    used_at = models.DateTimeField(_('Использован в'), null=True, blank=True)
    
    attempts_count = models.PositiveIntegerField(
        _('Количество попыток'),
        default=0
    )
    
    ip_address = models.GenericIPAddressField(
        _('IP адрес'),
        null=True,
        blank=True
    )
    
    telegram_phone = models.CharField(_('Telegram Phone'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('Код верификации Telegram')
        verbose_name_plural = _('Коды верификации Telegram')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'verification_type']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_used', 'created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Время жизни кода теперь устанавливается в telegram_service.py
        # в зависимости от типа верификации
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_secure_code(cls, user=None, pending_registration=None, verification_type='registration', ip_address=None):
        """Генерирует безопасный код верификации"""
        # Генерируем 6-значный код
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Генерируем соль
        salt = secrets.token_hex(32)
        
        # Создаем хеш
        code_hash = hashlib.sha256((code + salt).encode()).hexdigest()
        
        # Создаем запись
        verification_code = cls.objects.create(
            user=user,
            pending_registration=pending_registration,
            code=code,
            code_hash=code_hash,
            salt=salt,
            verification_type=verification_type,
            ip_address=ip_address,
            telegram_chat_id=user.telegram_chat_id if user and hasattr(user, 'telegram_chat_id') and user.telegram_chat_id else None
        )
        
        return code, verification_code
    
    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического хеширования кода"""
        # Если код есть, но еще не хеширован
        if self.code and not self.code_hash:
            # Генерируем salt если его нет
            if not self.salt:
                self.salt = secrets.token_hex(32)
            
            # Создаем хеш кода
            self.code_hash = hashlib.sha256((self.code + self.salt).encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    def check_code_match(self, input_code):
        """Проверяет соответствие кода без изменения статуса is_used"""
        if self.is_used or timezone.now() > self.expires_at:
            return False
        
        # Проверяем и инициализируем salt если он None
        if not self.salt:
            return False  # Не можем проверить код без salt
        
        # Проверяем хеш
        input_hash = hashlib.sha256((input_code + self.salt).encode()).hexdigest()
        return input_hash == self.code_hash
    
    def verify_code(self, input_code):
        """Проверяет введенный код и помечает как использованный при успехе"""
        if self.is_used or timezone.now() > self.expires_at:
            return False
        
        # Увеличиваем счетчик попыток
        self.attempts_count += 1
        # Сохраняем только если нет связанного pending_registration или он еще существует
        if not self.pending_registration_id or PendingUserRegistration.objects.filter(id=self.pending_registration_id).exists():
            self.save()
        
        # Проверяем максимальное количество попыток
        if self.attempts_count > 3:
            return False
        
        # Проверяем и инициализируем salt если он None
        if not self.salt:
            self.salt = secrets.token_hex(32)
            # Сохраняем только если нет связанного pending_registration или он еще существует
            if not self.pending_registration_id or PendingUserRegistration.objects.filter(id=self.pending_registration_id).exists():
                self.save()
        
        # Проверяем хеш
        input_hash = hashlib.sha256((input_code + self.salt).encode()).hexdigest()
        
        if input_hash == self.code_hash:
            self.is_used = True
            self.used_at = timezone.now()
            # Сохраняем только если нет связанного pending_registration или он еще существует
            if not self.pending_registration_id or PendingUserRegistration.objects.filter(id=self.pending_registration_id).exists():
                self.save()
            return True
        
        return False
    
    @staticmethod
    def generate_code():
        """Генерирует криптографически стойкий 6-значный код (устаревший метод)"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_expired(self):
        """Проверяет, истек ли код"""
        return timezone.now() > self.expires_at
    
    @property
    def is_expired_property(self):
        """Свойство для проверки истечения кода"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Проверяет, действителен ли код"""
        return not self.is_used and not self.is_expired()
    
    def generate_secure_code(self):
        """Возвращает код для отображения пользователю"""
        if hasattr(self, 'code') and self.code:
            return self.code
        else:
            # Если код не сохранен, генерируем новый и сохраняем
            code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            self.code = code
            # Проверяем и инициализируем salt если он None
            if not self.salt:
                self.salt = secrets.token_hex(32)
            # Обновляем хеш с новым кодом
            self.code_hash = hashlib.sha256((code + self.salt).encode()).hexdigest()
            self.save()
            return code

    def __str__(self):
        user_info = self.user.email if self.user else f"Pending: {self.pending_registration.email if self.pending_registration else 'Unknown'}"
        return f"Код для {user_info} ({self.get_verification_type_display()})"


class QRCodeScan(models.Model):
    """Модель для отслеживания сканирований QR-кодов"""
    qr_id = models.UUIDField(_('QR Code ID'), default=uuid.uuid4, unique=True, editable=False)
    verification_code = models.ForeignKey(
        TelegramVerificationCode, 
        on_delete=models.CASCADE, 
        related_name='qr_scans',
        null=True, 
        blank=True
    )
    pending_registration = models.ForeignKey(
        PendingUserRegistration,
        on_delete=models.CASCADE,
        related_name='qr_scans',
        null=True,
        blank=True
    )
    trigger_url = models.URLField(_('Trigger URL'), max_length=500)
    telegram_bot_url = models.URLField(_('Telegram Bot URL'), max_length=500)
    scanned_at = models.DateTimeField(_('Scanned At'), null=True, blank=True)
    trigger_activated_at = models.DateTimeField(_('Trigger Activated At'), null=True, blank=True)
    bot_started_at = models.DateTimeField(_('Bot Started At'), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    # Статистика
    scan_count = models.PositiveIntegerField(_('Scan Count'), default=0)
    successful_activations = models.PositiveIntegerField(_('Successful Activations'), default=0)
    
    class Meta:
        verbose_name = _('QR Code Scan')
        verbose_name_plural = _('QR Code Scans')
        ordering = ['-created_at']
    
    def generate_trigger_url(self, base_url=''):
        """Генерирует триггер-ссылку для QR-кода"""
        if base_url:
            return f"{base_url}/qr-trigger/{self.qr_id}/"
        else:
            # Если base_url пустой, используем относительный путь
            return f"/qr-trigger/{self.qr_id}/"
    
    def generate_telegram_url(self, bot_username, verification_id=None):
        """Генерирует ссылку на Telegram-бота"""
        # Используем verification_id или qr_id как параметр запуска
        start_param = verification_id or str(self.qr_id)
        return f"https://t.me/{bot_username}?start={start_param}"
    
    def mark_scanned(self, ip_address=None, user_agent=None):
        """Отмечает QR-код как отсканированный"""
        if not self.scanned_at:
            self.scanned_at = timezone.now()
            self.scan_count += 1
            if ip_address:
                self.ip_address = ip_address
            if user_agent:
                self.user_agent = user_agent
            self.save()
    
    def mark_trigger_activated(self):
        """Отмечает активацию триггера"""
        if not self.trigger_activated_at:
            self.trigger_activated_at = timezone.now()
            self.save()
    
    def mark_bot_started(self):
        """Отмечает запуск бота"""
        if not self.bot_started_at:
            self.bot_started_at = timezone.now()
            self.successful_activations += 1
            self.save()
    
    def is_complete_flow(self):
        """Проверяет, завершен ли полный флоу"""
        return all([
            self.scanned_at,
            self.trigger_activated_at,
            self.bot_started_at
        ])
    
    def __str__(self):
        return f'QR {self.qr_id} - Scans: {self.scan_count}, Success: {self.successful_activations}'


class PasswordResetToken(models.Model):
    """Модель для безопасных токенов сброса пароля"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(_('Reset Token'), default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'))
    is_used = models.BooleanField(_('Is Used'), default=False)
    used_at = models.DateTimeField(_('Used At'), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    class Meta:
        verbose_name = _('Password Reset Token')
        verbose_name_plural = _('Password Reset Tokens')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)  # Токен действует 1 час
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Проверяет, истек ли токен"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Проверяет, действителен ли токен"""
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self, ip_address=None, user_agent=None):
        """Отмечает токен как использованный"""
        self.is_used = True
        self.used_at = timezone.now()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        self.save()
    
    def __str__(self):
        return f'Password reset token for {self.user.email} - {self.token}'
