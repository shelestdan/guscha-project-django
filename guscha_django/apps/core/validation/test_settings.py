# -*- coding: utf-8 -*-
"""
Настройки Django для тестирования системы валидации.

Этот файл содержит специальные настройки для запуска тестов
системы валидации и безопасности.
"""

from django.conf import settings
import os

# Базовые настройки для тестов
TEST_SETTINGS = {
    'DEBUG': True,
    'TESTING': True,
    
    # Базы данных
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    
    # Кеширование
    'CACHES': {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    },
    
    # Логирование для тестов
    'LOGGING': {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
            },
            'test_file': {
                'class': 'logging.FileHandler',
                'filename': 'test_security.log',
                'level': 'WARNING',
            },
        },
        'loggers': {
            'security': {
                'handlers': ['console', 'test_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'validation': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    },
    
    # Middleware для тестов
    'MIDDLEWARE': [
        'django.middleware.security.SecurityMiddleware',
        'apps.core.middleware.validation_middleware.InputValidationMiddleware',
        'apps.core.middleware.validation_middleware.RateLimitMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ],
    
    # Приложения для тестов
    'INSTALLED_APPS': [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'apps.core',
    ],
    
    # Настройки валидации для тестов
    'VALIDATION_CONFIG': {
        'MAX_STRING_LENGTH': 1000,
        'MAX_JSON_SIZE': 10240,
        'ENABLE_ATTACK_DETECTION': True,
        'ENABLE_SANITIZATION': True,
        'ENABLE_SECURITY_LOGGING': True,
        'RATE_LIMIT_ENABLED': True,
        'RATE_LIMIT_REQUESTS': 100,
        'RATE_LIMIT_WINDOW': 3600,
    },
    
    # Секретный ключ для тестов
    'SECRET_KEY': 'test-secret-key-for-validation-tests-only',
    
    # Отключаем CSRF для тестов
    'CSRF_COOKIE_SECURE': False,
    'SESSION_COOKIE_SECURE': False,
    
    # Настройки файлов
    'MEDIA_ROOT': '/tmp/test_media/',
    'STATIC_ROOT': '/tmp/test_static/',
    
    # Часовой пояс
    'TIME_ZONE': 'UTC',
    'USE_TZ': True,
}


def configure_test_settings():
    """
    Конфигурирует Django настройки для тестов.
    
    Эта функция должна быть вызвана перед запуском тестов
    для правильной настройки окружения.
    """
    if not settings.configured:
        settings.configure(**TEST_SETTINGS)
    
    # Создаем необходимые директории
    os.makedirs(TEST_SETTINGS['MEDIA_ROOT'], exist_ok=True)
    os.makedirs(TEST_SETTINGS['STATIC_ROOT'], exist_ok=True)


# Автоматическая конфигурация при импорте
if __name__ == '__main__':
    configure_test_settings()
    print("Test settings configured successfully")