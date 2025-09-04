"""Настройки Telegram бота."""

import os
from dataclasses import dataclass
from typing import Optional
from django.conf import settings


@dataclass(frozen=True)
class BotSettings:
    """Настройки Telegram бота."""
    
    # Токен бота
    token: str
    
    # Настройки таймаутов
    verification_code_timeout_minutes: int = 10
    registration_rate_limit_minutes: int = 5
    max_registration_attempts: int = 3
    
    # Настройки логирования
    log_level: str = 'INFO'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Настройки безопасности
    max_phone_validation_attempts: int = 3
    phone_validation_timeout_minutes: int = 1
    
    @classmethod
    def from_django_settings(cls) -> 'BotSettings':
        """Создает настройки из Django settings."""
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN не настроен в Django settings")
        
        return cls(
            token=token,
            verification_code_timeout_minutes=getattr(
                settings, 'TELEGRAM_VERIFICATION_TIMEOUT_MINUTES', 10
            ),
            registration_rate_limit_minutes=getattr(
                settings, 'TELEGRAM_REGISTRATION_RATE_LIMIT_MINUTES', 5
            ),
            max_registration_attempts=getattr(
                settings, 'TELEGRAM_MAX_REGISTRATION_ATTEMPTS', 3
            ),
            log_level=getattr(settings, 'TELEGRAM_LOG_LEVEL', 'INFO'),
            max_phone_validation_attempts=getattr(
                settings, 'TELEGRAM_MAX_PHONE_VALIDATION_ATTEMPTS', 3
            ),
            phone_validation_timeout_minutes=getattr(
                settings, 'TELEGRAM_PHONE_VALIDATION_TIMEOUT_MINUTES', 1
            ),
        )


# Глобальный экземпляр настроек
bot_settings = BotSettings.from_django_settings()