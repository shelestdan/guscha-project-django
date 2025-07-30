from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import random
import string
import uuid
from simple_history.models import HistoricalRecords


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
    """Пользовательская модель User"""
    username = None  # Отключаем поле username
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=15, blank=True, null=True)
    address = models.TextField(_('address'), blank=True, null=True)
    telegram_chat_id = models.CharField(_('Telegram Chat ID'), max_length=50, blank=True, null=True)
    telegram_username = models.CharField(_('Telegram Username'), max_length=50, blank=True, null=True)
    is_telegram_verified = models.BooleanField(_('Telegram Verified'), default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()
    history = HistoricalRecords()  # Добавляем отслеживание истории

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email


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
    """Модель для хранения кодов подтверждения Telegram"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telegram_codes', null=True, blank=True)
    pending_registration = models.ForeignKey(PendingUserRegistration, on_delete=models.CASCADE, related_name='telegram_codes', null=True, blank=True)
    code = models.CharField(_('Verification Code'), max_length=6)
    telegram_chat_id = models.CharField(_('Telegram Chat ID'), max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'))
    is_used = models.BooleanField(_('Is Used'), default=False)
    used_at = models.DateTimeField(_('Used At'), null=True, blank=True)
    telegram_phone = models.CharField(_('Telegram Phone Number'), max_length=20, null=True, blank=True)
    verification_type = models.CharField(
        _('Verification Type'),
        max_length=20,
        choices=[
            ('registration', _('Registration')),
            ('password_reset', _('Password Reset')),
            ('login', _('Login')),
            ('qr_registration', _('QR Registration')),
        ],
        default='registration'
    )

    class Meta:
        verbose_name = _('Telegram Verification Code')
        verbose_name_plural = _('Telegram Verification Codes')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # Код действует 10 минут
        super().save(*args, **kwargs)

    @staticmethod
    def generate_code():
        """Генерирует 6-значный код"""
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self):
        """Проверяет, истек ли код"""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Проверяет, действителен ли код"""
        return not self.is_used and not self.is_expired()

    def __str__(self):
        if self.user:
            email = self.user.email
        elif self.pending_registration:
            email = self.pending_registration.email
        else:
            email = 'Unknown'
        return f'Code {self.code} for {email} ({self.verification_type})'


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
        # Используем код верификации если есть, иначе qr_id
        if self.verification_code and self.verification_code.code:
            start_param = self.verification_code.code
        else:
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
