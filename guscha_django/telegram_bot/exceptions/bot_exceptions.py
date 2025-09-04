"""Кастомные исключения для Telegram бота."""

from typing import Optional, Any, Dict


class TelegramBotError(Exception):
    """Базовое исключение для всех ошибок Telegram бота."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class VerificationCodeError(TelegramBotError):
    """Ошибки связанные с кодами верификации."""
    pass


class PhoneValidationError(TelegramBotError):
    """Ошибки валидации номера телефона."""
    pass


class RateLimitError(TelegramBotError):
    """Ошибка превышения лимита запросов."""
    
    def __init__(
        self, 
        message: str, 
        retry_after_seconds: int,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, context)
        self.retry_after_seconds = retry_after_seconds


class UserNotFoundError(TelegramBotError):
    """Ошибка когда пользователь не найден."""
    pass


class ConfigurationError(TelegramBotError):
    """Ошибки конфигурации бота."""
    pass


class ValidationError(TelegramBotError):
    """Ошибки валидации данных."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, context)
        self.field = field
        self.value = value


class DatabaseError(TelegramBotError):
    """Ошибки работы с базой данных."""
    pass


class MessageSendError(TelegramBotError):
    """Ошибки отправки сообщений в Telegram."""
    
    def __init__(
        self,
        message: str,
        chat_id: Optional[str] = None,
        telegram_error: Optional[Exception] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, context)
        self.chat_id = chat_id
        self.telegram_error = telegram_error