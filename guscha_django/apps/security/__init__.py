# Security application for Django
# Provides comprehensive anti-spam and security features

__version__ = '1.0.0'
__author__ = 'Security Team'
__description__ = 'Comprehensive security and anti-spam system for Django applications'

# Импорты будут выполнены при необходимости, чтобы избежать AppRegistryNotReady
default_app_config = 'apps.security.apps.SecurityConfig'

# Экспорт основных классов и функций будет доступен через прямые импорты
__all__ = []