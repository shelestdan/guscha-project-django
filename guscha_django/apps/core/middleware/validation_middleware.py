# -*- coding: utf-8 -*-
"""
Middleware для централизованной валидации и санитизации входных данных.

Обеспечивает:
- Валидацию всех входящих данных
- Санитизацию потенциально опасного контента
- Защиту от XSS, SQL injection и других атак
- Логирование подозрительной активности
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ValidationError
from django.utils.html import escape
from apps.accounts.utils.validation_utils import ValidationUtils
from apps.accounts.utils.security_utils import SecurityUtils

# Импортируем наши новые утилиты
from ..validation.advanced_validation import AdvancedValidator
from ..validation.security_logging import log_suspicious_request, log_rate_limit_exceeded

logger = logging.getLogger('security')


class InputValidationMiddleware(MiddlewareMixin):
    """
    Middleware для централизованной валидации и санитизации входных данных.
    
    Применяется ко всем POST, PUT, PATCH запросам.
    """
    
    # Опасные паттерны для обнаружения атак
    DANGEROUS_PATTERNS = [
        # SQL Injection patterns
        re.compile(r"('|(\-\-)|(;)|(\||\|)|(\*|\*))", re.IGNORECASE),
        re.compile(r"(union|select|insert|delete|update|drop|create|alter|exec|execute)", re.IGNORECASE),
        
        # XSS patterns
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<iframe[^>]*>", re.IGNORECASE),
        
        # Command injection patterns
        re.compile(r"(\||&|;|\$|`|\(|\)|\{|\}|\[|\])", re.IGNORECASE),
        re.compile(r"(cat|ls|pwd|whoami|id|uname|wget|curl|nc|netcat)", re.IGNORECASE),
        
        # Path traversal patterns
        re.compile(r"\.\.[\/\\]", re.IGNORECASE),
        re.compile(r"[\/\\]etc[\/\\]passwd", re.IGNORECASE),
    ]
    
    # Максимальные размеры для различных типов данных
    MAX_SIZES = {
        'string': 10000,
        'text': 50000,
        'email': 254,
        'phone': 20,
        'url': 2048,
        'json_depth': 10,
        'array_length': 1000,
    }
    
    # Исключения - пути, которые не требуют валидации
    EXCLUDED_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/api/health/',
    ]
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Обрабатывает входящие запросы для валидации и санитизации.
        """
        # Пропускаем GET запросы и исключенные пути
        if request.method == 'GET' or self._is_excluded_path(request.path):
            return None
            
        # Пропускаем запросы без тела
        if not hasattr(request, 'body') or not request.body:
            return None
            
        try:
            # Валидируем размер запроса
            if len(request.body) > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                logger.warning(
                    f"Request too large: {len(request.body)} bytes from {self._get_client_ip(request)}"
                )
                return JsonResponse(
                    {'error': 'Запрос слишком большой'}, 
                    status=413
                )
            
            # Парсим и валидируем данные
            if request.content_type == 'application/json':
                return self._validate_json_data(request)
            elif request.content_type.startswith('multipart/form-data'):
                return self._validate_form_data(request)
            elif request.content_type == 'application/x-www-form-urlencoded':
                return self._validate_form_data(request)
                
        except Exception as e:
            logger.error(
                f"Validation middleware error: {str(e)} for request from {self._get_client_ip(request)}"
            )
            return JsonResponse(
                {'error': 'Ошибка валидации данных'}, 
                status=400
            )
            
        return None
    
    def _is_excluded_path(self, path: str) -> bool:
        """Проверяет, исключен ли путь из валидации."""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Получает IP адрес клиента."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _validate_json_data(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Валидирует JSON данные."""
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # Проверяем глубину JSON
            if self._get_json_depth(data) > self.MAX_SIZES['json_depth']:
                logger.warning(
                    f"JSON too deep from {self._get_client_ip(request)}"
                )
                return JsonResponse(
                    {'error': 'JSON структура слишком глубокая'}, 
                    status=400
                )
            
            # Валидируем и санитизируем данные
            sanitized_data = self._sanitize_data(data)
            
            # Проверяем на опасные паттерны
            if self._contains_dangerous_patterns(sanitized_data):
                client_ip = self._get_client_ip(request)
                logger.warning(
                    f"Dangerous patterns detected in request from {client_ip}: {request.path}"
                )
                
                # Логируем подозрительный запрос
                log_suspicious_request(
                    request=request,
                    attack_type='DANGEROUS_PATTERNS',
                    details={
                        'client_ip': client_ip,
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'content_type': getattr(request, 'content_type', ''),
                        'method': request.method
                    }
                )
                
                return JsonResponse(
                    {'error': 'Обнаружены потенциально опасные данные'}, 
                    status=400
                )
            
            # Заменяем тело запроса на санитизированные данные
            request._body = json.dumps(sanitized_data).encode('utf-8')
            
        except json.JSONDecodeError:
            logger.warning(
                f"Invalid JSON from {self._get_client_ip(request)}"
            )
            return JsonResponse(
                {'error': 'Некорректный JSON'}, 
                status=400
            )
            
        return None
    
    def _validate_form_data(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Валидирует данные формы."""
        try:
            # Санитизируем POST данные
            if hasattr(request, 'POST'):
                for key, value in request.POST.items():
                    if isinstance(value, str):
                        sanitized_value = self._sanitize_string(value)
                        if self._contains_dangerous_patterns(sanitized_value):
                            logger.warning(
                                f"Dangerous pattern in form field '{key}' from {self._get_client_ip(request)}"
                            )
                            return JsonResponse(
                                {'error': f'Недопустимые данные в поле {key}'}, 
                                status=400
                            )
            
            # Санитизируем файлы
            if hasattr(request, 'FILES'):
                for field_name, uploaded_file in request.FILES.items():
                    if not self._validate_uploaded_file(uploaded_file):
                        logger.warning(
                            f"Dangerous file upload '{uploaded_file.name}' from {self._get_client_ip(request)}"
                        )
                        return JsonResponse(
                            {'error': f'Недопустимый файл: {uploaded_file.name}'}, 
                            status=400
                        )
                        
        except Exception as e:
            logger.error(
                f"Form validation error: {str(e)} from {self._get_client_ip(request)}"
            )
            return JsonResponse(
                {'error': 'Ошибка валидации формы'}, 
                status=400
            )
            
        return None
    
    def _get_json_depth(self, obj: Any, depth: int = 0) -> int:
        """Вычисляет глубину JSON объекта."""
        if isinstance(obj, dict):
            return max([self._get_json_depth(v, depth + 1) for v in obj.values()], default=depth)
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj], default=depth)
        else:
            return depth
    
    def _sanitize_data(self, data: Any) -> Any:
        """Рекурсивно санитизирует данные."""
        if isinstance(data, dict):
            return {key: self._sanitize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            if len(data) > self.MAX_SIZES['array_length']:
                logger.warning("Array too long, truncating")
                data = data[:self.MAX_SIZES['array_length']]
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _sanitize_string(self, value: str) -> str:
        """
        Санитизирует строковое значение используя AdvancedValidator.
        
        Args:
            value: Строка для санитизации
        
        Returns:
            Санитизированная строка
        """
        if not isinstance(value, str):
            return value
        
        return AdvancedValidator.sanitize_string(value)
    
    def _contains_dangerous_patterns(self, data: Any) -> bool:
        """
        Проверяет данные на наличие опасных паттернов используя AdvancedValidator.
        
        Args:
            data: Данные для проверки
        
        Returns:
            True если обнаружены опасные паттерны
        """
        try:
            if isinstance(data, dict):
                return any(self._contains_dangerous_patterns(value) for value in data.values())
            elif isinstance(data, list):
                return any(self._contains_dangerous_patterns(item) for item in data)
            elif isinstance(data, str):
                # Используем AdvancedValidator для проверки
                AdvancedValidator._check_for_attacks(data)
                return False
            else:
                return False
        except ValidationError:
            # AdvancedValidator обнаружил атаку
            return True
    
    def _validate_uploaded_file(self, uploaded_file) -> bool:
        """Валидирует загруженный файл."""
        # Проверяем расширение файла
        allowed_extensions = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', [
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt'
        ])
        
        file_extension = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
        if f'.{file_extension}' not in allowed_extensions:
            return False
            
        # Проверяем размер файла
        max_file_size = getattr(settings, 'MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
        if uploaded_file.size > max_file_size:
            return False
            
        # Проверяем имя файла на опасные символы
        dangerous_chars = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
        if any(char in uploaded_file.name for char in dangerous_chars):
            return False
            
        return True


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware для ограничения частоты запросов.
    
    Предотвращает DDoS атаки и злоупотребления API.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.request_counts = {}  # В продакшене использовать Redis
        self.blocked_ips = set()
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Проверяет лимиты запросов."""
        client_ip = self._get_client_ip(request)
        
        # Проверяем заблокированные IP
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted request: {client_ip}")
            return JsonResponse(
                {'error': 'IP адрес заблокирован'}, 
                status=429
            )
        
        # Проверяем лимиты
        current_time = int(time.time())
        window_start = current_time - 60  # 1 минута
        
        # Очищаем старые записи
        self.request_counts = {
            ip: [(timestamp, path) for timestamp, path in requests 
                 if timestamp > window_start]
            for ip, requests in self.request_counts.items()
        }
        
        # Подсчитываем запросы от данного IP
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
            
        recent_requests = self.request_counts[client_ip]
        
        # Проверяем общий лимит
        if len(recent_requests) >= 100:  # 100 запросов в минуту
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            # Логируем превышение лимита
            log_rate_limit_exceeded(
                request=request,
                limit_type='general',
                current_count=len(recent_requests),
                limit=100
            )
            
            self.blocked_ips.add(client_ip)
            return JsonResponse(
                {'error': 'Превышен лимит запросов'}, 
                status=429
            )
        
        # Проверяем лимит для критических endpoints
        critical_paths = ['/api/auth/login/', '/api/auth/register/', '/api/payment/']
        critical_requests = [
            req for req in recent_requests 
            if any(req[1].startswith(path) for path in critical_paths)
        ]
        
        if len(critical_requests) >= 10:  # 10 критических запросов в минуту
            logger.warning(f"Critical endpoint rate limit exceeded for IP: {client_ip}")
            
            # Логируем превышение лимита для критических операций
            log_rate_limit_exceeded(
                request=request,
                limit_type='critical',
                current_count=len(critical_requests),
                limit=10
            )
            
            return JsonResponse(
                {'error': 'Превышен лимит для критических операций'}, 
                status=429
            )
        
        # Записываем текущий запрос
        self.request_counts[client_ip].append((current_time, request.path))
        
        return None
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Получает IP адрес клиента."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


import time