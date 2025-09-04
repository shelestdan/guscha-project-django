"""Вспомогательные функции для Telegram бота."""

import secrets
import string
import hashlib
from typing import Optional
from datetime import datetime, timedelta


def generate_secure_code(length: int = 6) -> str:
    """Генерирует безопасный код верификации."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def generate_random_string(length: int = 32) -> str:
    """Генерирует случайную строку."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def rate_limit_key(chat_id: str, action: str) -> str:
    """Генерирует ключ для rate limiting."""
    return f"rate_limit:{action}:{chat_id}"


def hash_phone_number(phone: str) -> str:
    """Создает хеш номера телефона для логирования."""
    return hashlib.sha256(phone.encode()).hexdigest()[:8]


def format_timedelta(td: timedelta) -> str:
    """Форматирует timedelta в читаемый вид."""
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} сек"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} мин"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if minutes > 0:
            return f"{hours} ч {minutes} мин"
        return f"{hours} ч"


def is_expired(created_at: datetime, timeout_minutes: int) -> bool:
    """Проверяет, истек ли таймаут."""
    expiry_time = created_at + timedelta(minutes=timeout_minutes)
    return datetime.now() > expiry_time


def sanitize_user_input(text: str, max_length: int = 1000) -> str:
    """Очищает пользовательский ввод."""
    if not text:
        return ""
    
    # Убираем лишние пробелы
    text = text.strip()
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def extract_command_args(text: str) -> tuple[str, list[str]]:
    """Извлекает команду и аргументы из текста сообщения."""
    if not text or not text.startswith('/'):
        return "", []
    
    parts = text.split()
    command = parts[0][1:]  # Убираем /
    args = parts[1:] if len(parts) > 1 else []
    
    return command, args


def create_deep_link(bot_username: str, payload: str) -> str:
    """Создает deep link для Telegram бота."""
    return f"https://t.me/{bot_username}?start={payload}"


def parse_callback_data(callback_data: str) -> tuple[str, Optional[str]]:
    """Парсит callback_data на действие и параметр."""
    if '_' in callback_data:
        action, param = callback_data.split('_', 1)
        return action, param
    return callback_data, None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Обрезает текст до указанной длины."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_user_mention(user_id: int, first_name: str) -> str:
    """Форматирует упоминание пользователя."""
    return f"[{first_name}](tg://user?id={user_id})"


def is_valid_telegram_username(username: str) -> bool:
    """Проверяет валидность Telegram username."""
    if not username:
        return False
    
    # Username должен быть от 5 до 32 символов
    if len(username) < 5 or len(username) > 32:
        return False
    
    # Должен содержать только буквы, цифры и подчеркивания
    if not username.replace('_', '').isalnum():
        return False
    
    # Не должен начинаться или заканчиваться подчеркиванием
    if username.startswith('_') or username.endswith('_'):
        return False
    
    # Не должен содержать два подчеркивания подряд
    if '__' in username:
        return False
    
    return True


def get_user_display_name(first_name: str, last_name: Optional[str] = None, username: Optional[str] = None) -> str:
    """Получает отображаемое имя пользователя."""
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif username:
        return f"@{username}"
    else:
        return "Пользователь"