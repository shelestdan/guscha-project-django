# -*- coding: utf-8 -*-
"""
Модуль централизованной валидации и безопасности.

Этот модуль предоставляет комплексную систему валидации, санитизации
и мониторинга безопасности для Django приложения.
"""

from .advanced_validation import AdvancedValidator, DataIntegrityValidator
from .security_logging import (
    SecurityEvent, SecurityLogger, log_security_event,
    log_suspicious_request, log_rate_limit_exceeded,
    log_login_attempt, log_permission_denied
)
# Decorators and middleware imports will be added when those modules are created
# from ..decorators.validation_decorators import (
#     validate_json_input, validate_query_params, sanitize_input_data,
#     validate_file_upload, require_authentication
# )
# from ..middleware.validation_middleware import (
#     InputValidationMiddleware, RateLimitMiddleware
# )
from ..validation_config import (
    VALIDATION_SETTINGS, CRITICAL_ENDPOINTS, EXCLUDED_PATHS,
    SECURITY_LOGGING, ATTACK_PATTERNS, get_validation_setting,
    is_critical_endpoint, is_excluded_path, get_rate_limit
)

__version__ = '1.0.0'
__author__ = 'Security Team'

__all__ = [
    # Валидаторы
    'AdvancedValidator',
    'DataIntegrityValidator',
    
    # Логирование безопасности
    'SecurityEvent',
    'SecurityLogger',
    'log_security_event',
    'log_suspicious_request',
    'log_rate_limit_exceeded',
    'log_authentication_attempt',
    'log_access_denied',
    
    # Декораторы
    'validate_json_input',
    'validate_query_params',
    'sanitize_input_data',
    'validate_file_upload',
    'require_authentication',
    
    # Middleware
    'InputValidationMiddleware',
    'RateLimitMiddleware',
    
    # Конфигурация
    'VALIDATION_SETTINGS',
    'CRITICAL_ENDPOINTS',
    'EXCLUDED_PATHS',
    'SECURITY_LOGGING',
    'ATTACK_PATTERNS',
    'get_validation_setting',
    'is_critical_endpoint',
    'is_excluded_path',
    'get_rate_limit',
]

# Быстрые импорты для удобства
from .advanced_validation import AdvancedValidator as Validator
from .security_logging import log_security_event as log_event

# Функции-хелперы для быстрого использования
def validate_string(value: str, max_length: int = None) -> str:
    """
    Быстрая валидация и санитизация строки.
    
    Args:
        value: Строка для валидации
        max_length: Максимальная длина
    
    Returns:
        Валидированная строка
    
    Raises:
        ValidationError: При обнаружении проблем
    """
    return AdvancedValidator.validate_string(value, max_length)

def validate_email(email: str) -> str:
    """
    Быстрая валидация email адреса.
    
    Args:
        email: Email для валидации
    
    Returns:
        Валидированный email
    
    Raises:
        ValidationError: При невалидном email
    """
    return AdvancedValidator.validate_email(email)

def sanitize_html(html: str) -> str:
    """
    Быстрая санитизация HTML контента.
    
    Args:
        html: HTML для санитизации
    
    Returns:
        Санитизированный HTML
    """
    return AdvancedValidator.sanitize_string(html)

def check_password_strength(password: str) -> dict:
    """
    Быстрая проверка силы пароля.
    
    Args:
        password: Пароль для проверки
    
    Returns:
        Словарь с результатами проверки
    """
    try:
        AdvancedValidator.validate_password(password)
        return {'valid': True, 'score': 100, 'message': 'Пароль соответствует требованиям'}
    except Exception as e:
        return {'valid': False, 'score': 0, 'message': str(e)}

# Константы для удобства
MAX_STRING_LENGTH = VALIDATION_SETTINGS['MAX_SIZES']['string_field']
MAX_TEXT_LENGTH = VALIDATION_SETTINGS['MAX_SIZES']['text_field']
MAX_FILE_SIZE = VALIDATION_SETTINGS['MAX_SIZES']['file_upload']
DEFAULT_RATE_LIMIT = VALIDATION_SETTINGS['RATE_LIMITS']['default']

# Информация о модуле
MODULE_INFO = {
    'name': 'Django Security Validation Module',
    'version': __version__,
    'description': 'Комплексная система валидации и безопасности для Django',
    'features': [
        'Централизованная валидация входных данных',
        'Санитизация и защита от XSS/SQL инъекций',
        'Rate limiting и защита от DDoS',
        'Мониторинг и логирование событий безопасности',
        'Валидация файлов и проверка на вредоносное ПО',
        'Проверка силы паролей и email адресов',
        'Интеграция с Django middleware и декораторами',
    ],
    'components': {
        'validators': 'Классы для валидации различных типов данных',
        'middleware': 'Middleware для автоматической валидации запросов',
        'decorators': 'Декораторы для валидации на уровне view функций',
        'logging': 'Система логирования событий безопасности',
        'config': 'Конфигурационные настройки и константы',
    }
}

def get_module_info() -> dict:
    """
    Возвращает информацию о модуле валидации.
    
    Returns:
        Словарь с информацией о модуле
    """
    return MODULE_INFO.copy()

def get_security_status() -> dict:
    """
    Возвращает текущий статус системы безопасности.
    
    Returns:
        Словарь со статусом безопасности
    """
    return {
        'validation_enabled': True,
        'logging_enabled': SECURITY_LOGGING['enabled'],
        'rate_limiting_enabled': True,
        'ip_blocking_enabled': VALIDATION_SETTINGS['IP_BLOCKING']['enabled'],
        'critical_endpoints_count': len(CRITICAL_ENDPOINTS),
        'excluded_paths_count': len(EXCLUDED_PATHS),
        'attack_patterns_count': sum(len(patterns) for patterns in ATTACK_PATTERNS.values()),
    }