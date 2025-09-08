# -*- coding: utf-8 -*-
"""
CSRF Debug Middleware для мониторинга CSRF токенов в режиме разработки.

Обеспечивает:
- Логирование CSRF токенов из cookies и заголовков
- Мониторинг проблем с CSRF валидацией
- Debug информацию для разработчиков
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.middleware.csrf import get_token

logger = logging.getLogger('csrf_debug')


class CSRFDebugMiddleware(MiddlewareMixin):
    """
    Middleware для debug логирования CSRF токенов.
    Работает только в DEBUG режиме.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.debug_enabled = getattr(settings, 'DEBUG', False)
    
    def process_request(self, request):
        """Логируем CSRF информацию для входящих запросов."""
        if not self.debug_enabled:
            return None
            
        # Получаем CSRF токен из cookies
        csrf_cookie = request.COOKIES.get(settings.CSRF_COOKIE_NAME, 'NOT_FOUND')
        
        # Получаем CSRF токен из заголовков
        csrf_header = request.META.get('HTTP_X_CSRFTOKEN', 'NOT_FOUND')
        
        # Получаем метод и путь запроса
        method = request.method
        path = request.path
        
        # Логируем только для небезопасных методов или если есть проблемы
        if method in ['POST', 'PUT', 'DELETE', 'PATCH'] or csrf_cookie == 'NOT_FOUND':
            logger.debug(
                f"CSRF Debug - Method: {method}, Path: {path}, "
                f"Cookie Token: {csrf_cookie[:10]}{'...' if len(csrf_cookie) > 10 else ''}, "
                f"Header Token: {csrf_header[:10]}{'...' if len(csrf_header) > 10 else ''}, "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'UNKNOWN')[:50]}"
            )
            
            # Дополнительная проверка на совпадение токенов
            if csrf_cookie != 'NOT_FOUND' and csrf_header != 'NOT_FOUND':
                if csrf_cookie != csrf_header:
                    logger.warning(
                        f"CSRF Token Mismatch - Path: {path}, "
                        f"Cookie: {csrf_cookie[:10]}..., Header: {csrf_header[:10]}..."
                    )
                else:
                    logger.debug(f"CSRF Tokens Match - Path: {path}")
        
        return None
    
    def process_response(self, request, response):
        """Логируем CSRF информацию для исходящих ответов."""
        if not self.debug_enabled:
            return response
            
        # Проверяем, установлен ли CSRF cookie в ответе
        csrf_cookie_set = settings.CSRF_COOKIE_NAME in [cookie.key for cookie in response.cookies.values()]
        
        if csrf_cookie_set:
            logger.debug(f"CSRF Cookie Set in Response - Path: {request.path}")
        
        # Логируем ошибки CSRF
        if response.status_code == 403 and 'CSRF' in str(response.content):
            logger.error(
                f"CSRF Validation Failed - Path: {request.path}, "
                f"Method: {request.method}, Status: {response.status_code}"
            )
        
        return response