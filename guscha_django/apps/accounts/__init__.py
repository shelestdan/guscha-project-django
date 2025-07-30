# -*- coding: utf-8 -*-
"""
Приложение для управления аккаунтами пользователей.

Это приложение предоставляет:
- Управление пользователями и аутентификацией
- Интеграцию с Telegram
- Функциональность QR кодов
- Систему безопасности и валидации
- Утилиты для работы с токенами и email
"""

default_app_config = 'apps.accounts.apps.AccountsConfig'

__version__ = '1.0.0'
__author__ = 'Guscha Django Team'

# Экспорт основных компонентов
# Временно отключаем импорты для диагностики AppRegistryNotReady
# from .models import (
#     PendingUserRegistration,
#     TelegramVerificationCode,
#     QRCode,
#     UserLoginHistory,
#     SecurityEvent
# )

# from .services import (
#     UserService,
#     AuthService,
#     TelegramService,
#     QRService
# )

# from .utils import (
#     EmailUtils,
#     TokenUtils,
#     SecurityUtils,
#     ValidationUtils
# )

# Временно отключаем __all__ для диагностики
# __all__ = [
#     # Модели
#     'PendingUserRegistration',
#     'TelegramVerificationCode',
#     'QRCode',
#     'UserLoginHistory',
#     'SecurityEvent',
#     
#     # Сервисы
#     'UserService',
#     'AuthService',
#     'TelegramService',
#     'QRService',
#     
#     # Утилиты
#     'EmailUtils',
#     'TokenUtils',
#     'SecurityUtils',
#     'ValidationUtils',
# ]