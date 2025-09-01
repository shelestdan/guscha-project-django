# -*- coding: utf-8 -*-
"""
Конфигурация системы валидации и безопасности.

Этот модуль содержит настройки для централизованной системы валидации,
санитизации и мониторинга безопасности Django приложения.
"""

from django.conf import settings
from typing import Dict, List, Any

# Настройки валидации
VALIDATION_SETTINGS = {
    # Максимальные размеры данных
    'MAX_SIZES': {
        'json_body': getattr(settings, 'MAX_JSON_BODY_SIZE', 1024 * 1024),  # 1MB
        'form_field': getattr(settings, 'MAX_FORM_FIELD_SIZE', 10000),
        'file_upload': getattr(settings, 'MAX_FILE_UPLOAD_SIZE', 10 * 1024 * 1024),  # 10MB
        'string_field': getattr(settings, 'MAX_STRING_FIELD_SIZE', 1000),
        'text_field': getattr(settings, 'MAX_TEXT_FIELD_SIZE', 10000),
    },
    
    # Разрешенные типы файлов
    'ALLOWED_FILE_EXTENSIONS': getattr(settings, 'ALLOWED_FILE_EXTENSIONS', [
        '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', 
        '.xls', '.xlsx', '.txt', '.csv', '.zip'
    ]),
    
    # Запрещенные типы файлов
    'FORBIDDEN_FILE_EXTENSIONS': getattr(settings, 'FORBIDDEN_FILE_EXTENSIONS', [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
    ]),
    
    # MIME типы для проверки файлов
    'ALLOWED_MIME_TYPES': getattr(settings, 'ALLOWED_MIME_TYPES', [
        'image/jpeg', 'image/png', 'image/gif', 'application/pdf',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain', 'text/csv', 'application/zip'
    ]),
    
    # Настройки rate limiting
    'RATE_LIMITS': {
        'default': getattr(settings, 'DEFAULT_RATE_LIMIT', 100),  # запросов в минуту
        'auth': getattr(settings, 'AUTH_RATE_LIMIT', 10),  # попыток входа в минуту
        'api': getattr(settings, 'API_RATE_LIMIT', 60),  # API запросов в минуту
        'upload': getattr(settings, 'UPLOAD_RATE_LIMIT', 5),  # загрузок в минуту
        'critical': getattr(settings, 'CRITICAL_RATE_LIMIT', 10),  # критических операций в минуту
    },
    
    # Настройки блокировки IP
    'IP_BLOCKING': {
        'enabled': getattr(settings, 'IP_BLOCKING_ENABLED', True),
        'block_duration': getattr(settings, 'IP_BLOCK_DURATION', 3600),  # секунд
        'max_violations': getattr(settings, 'MAX_SECURITY_VIOLATIONS', 5),
        'whitelist': getattr(settings, 'IP_WHITELIST', ['127.0.0.1', '::1']),
    },
}

# Критические endpoints, требующие дополнительной защиты
CRITICAL_ENDPOINTS = getattr(settings, 'CRITICAL_ENDPOINTS', [
    '/api/auth/login/',
    '/api/auth/register/',
    '/api/auth/password-reset/',
    '/api/payments/',
    '/api/admin/',
    '/api/users/profile/',
    '/api/orders/create/',
])

# Endpoints, исключенные из валидации (например, статические файлы)
EXCLUDED_PATHS = getattr(settings, 'VALIDATION_EXCLUDED_PATHS', [
    '/static/',
    '/media/',
    '/favicon.ico',
    '/robots.txt',
    '/health/',
    '/metrics/',
])

# Настройки логирования безопасности
SECURITY_LOGGING = {
    'enabled': getattr(settings, 'SECURITY_LOGGING_ENABLED', True),
    'log_level': getattr(settings, 'SECURITY_LOG_LEVEL', 'WARNING'),
    'max_log_entries': getattr(settings, 'MAX_SECURITY_LOG_ENTRIES', 10000),
    'alert_threshold': getattr(settings, 'SECURITY_ALERT_THRESHOLD', 10),  # событий для алерта
    'alert_window': getattr(settings, 'SECURITY_ALERT_WINDOW', 300),  # секунд
    
    # Email настройки для алертов
    'email_alerts': {
        'enabled': getattr(settings, 'SECURITY_EMAIL_ALERTS', False),
        'recipients': getattr(settings, 'SECURITY_ALERT_RECIPIENTS', []),
        'from_email': getattr(settings, 'SECURITY_ALERT_FROM_EMAIL', 'security@example.com'),
    },
    
    # Slack настройки для алертов
    'slack_alerts': {
        'enabled': getattr(settings, 'SECURITY_SLACK_ALERTS', False),
        'webhook_url': getattr(settings, 'SECURITY_SLACK_WEBHOOK', ''),
        'channel': getattr(settings, 'SECURITY_SLACK_CHANNEL', '#security'),
    },
}

# Паттерны для обнаружения атак
ATTACK_PATTERNS = {
    'sql_injection': [
        r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
        r"\b(union|select|insert|delete|update|drop|create|alter|exec|execute)\b",
        r"\b(or|and)\s+\d+\s*=\s*\d+",
        r"\b(waitfor|delay)\b",
        r"\b(sp_|xp_)\w+",
    ],
    
    'xss': [
        r"<script[^>]*>.*?</script>",
        r"javascript:\s*",
        r"on\w+\s*=\s*['\"]?[^'\"]*['\"]?",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ],
    
    'command_injection': [
        r"[;&|`$(){}\[\]]",
        r"\b(cat|ls|pwd|whoami|id|uname|wget|curl|nc|netcat|rm|mv|cp)\b",
        r"\.\.[\/\\]",
        r"\b(cmd|powershell|bash|sh)\b",
    ],
    
    'path_traversal': [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"\.\.%2f",
        r"\.\.%5c",
    ],
    
    'ldap_injection': [
        r"[()&|!*]",
        r"\b(objectClass|cn|uid|mail)\b",
    ],
    
    'xpath_injection': [
        r"[\[\]'\"]",
        r"\b(and|or|not)\b.*\b(text|node|position)\b",
    ],
}

# Подозрительные домены и IP адреса
SUSPICIOUS_DOMAINS = getattr(settings, 'SUSPICIOUS_DOMAINS', [
    'tempmail.org',
    '10minutemail.com',
    'guerrillamail.com',
    'mailinator.com',
    'throwaway.email',
])

# Настройки проверки паролей
PASSWORD_VALIDATION = {
    'min_length': getattr(settings, 'PASSWORD_MIN_LENGTH', 8),
    'require_uppercase': getattr(settings, 'PASSWORD_REQUIRE_UPPERCASE', True),
    'require_lowercase': getattr(settings, 'PASSWORD_REQUIRE_LOWERCASE', True),
    'require_digits': getattr(settings, 'PASSWORD_REQUIRE_DIGITS', True),
    'require_special': getattr(settings, 'PASSWORD_REQUIRE_SPECIAL', True),
    'forbidden_passwords_file': getattr(settings, 'FORBIDDEN_PASSWORDS_FILE', None),
    'check_common_passwords': getattr(settings, 'CHECK_COMMON_PASSWORDS', True),
}

# Настройки валидации email
EMAIL_VALIDATION = {
    'check_mx_record': getattr(settings, 'EMAIL_CHECK_MX_RECORD', False),
    'check_disposable': getattr(settings, 'EMAIL_CHECK_DISPOSABLE', True),
    'max_length': getattr(settings, 'EMAIL_MAX_LENGTH', 254),
}

# Настройки валидации телефонов
PHONE_VALIDATION = {
    'allowed_countries': getattr(settings, 'PHONE_ALLOWED_COUNTRIES', ['RU', 'US', 'GB']),
    'require_country_code': getattr(settings, 'PHONE_REQUIRE_COUNTRY_CODE', True),
}

# Функция для получения настроек валидации
def get_validation_setting(key: str, default: Any = None) -> Any:
    """
    Получает настройку валидации.
    
    Args:
        key: Ключ настройки в формате 'section.key'
        default: Значение по умолчанию
    
    Returns:
        Значение настройки
    """
    if '.' in key:
        section, setting_key = key.split('.', 1)
        section_settings = globals().get(section.upper())
        if section_settings and isinstance(section_settings, dict):
            return section_settings.get(setting_key, default)
    
    return getattr(settings, key.upper(), default)

# Функция для проверки критического endpoint
def is_critical_endpoint(path: str) -> bool:
    """
    Проверяет, является ли путь критическим endpoint.
    
    Args:
        path: Путь запроса
    
    Returns:
        True если путь критический
    """
    return any(path.startswith(endpoint) for endpoint in CRITICAL_ENDPOINTS)

# Функция для проверки исключенного пути
def is_excluded_path(path: str) -> bool:
    """
    Проверяет, исключен ли путь из валидации.
    
    Args:
        path: Путь запроса
    
    Returns:
        True если путь исключен
    """
    return any(path.startswith(excluded) for excluded in EXCLUDED_PATHS)

# Функция для получения лимита запросов
def get_rate_limit(endpoint_type: str = 'default') -> int:
    """
    Получает лимит запросов для типа endpoint.
    
    Args:
        endpoint_type: Тип endpoint (default, auth, api, upload, critical)
    
    Returns:
        Лимит запросов в минуту
    """
    return VALIDATION_SETTINGS['RATE_LIMITS'].get(endpoint_type, 100)