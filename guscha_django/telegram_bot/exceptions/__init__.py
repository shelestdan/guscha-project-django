"""Исключения Telegram бота."""

from .bot_exceptions import (
    TelegramBotError,
    VerificationCodeError,
    PhoneValidationError,
    RateLimitError,
    UserNotFoundError,
    ConfigurationError,
    DatabaseError,
    ValidationError,
    MessageSendError,
)

__all__ = [
    'TelegramBotError',
    'VerificationCodeError', 
    'PhoneValidationError',
    'RateLimitError',
    'UserNotFoundError',
    'ConfigurationError',
    'DatabaseError',
    'ValidationError',
    'MessageSendError',
]