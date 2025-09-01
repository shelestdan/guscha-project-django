# -*- coding: utf-8 -*-
"""
Декораторы для валидации и санитизации входных данных.

Обеспечивает:
- Валидацию параметров функций
- Санитизацию входных данных
- Проверку типов данных
- Валидацию бизнес-логики
"""

import json
import logging
import functools
from typing import Dict, Any, List, Optional, Callable, Union
from django.http import JsonResponse, HttpRequest
from django.core.exceptions import ValidationError
from django.utils.html import escape
from apps.accounts.utils.validation_utils import ValidationUtils
from apps.accounts.utils.security_utils import SecurityUtils
from ..validation.advanced_validation import AdvancedValidator
from ..validation.security_logging import log_security_event, SecurityEvent

logger = logging.getLogger('security')


def validate_json_input(required_fields: Optional[List[str]] = None,
                       optional_fields: Optional[List[str]] = None,
                       field_validators: Optional[Dict[str, Callable]] = None,
                       max_payload_size: int = 1024 * 1024):
    """
    Декоратор для валидации JSON входных данных.
    
    Args:
        required_fields: Список обязательных полей
        optional_fields: Список опциональных полей
        field_validators: Словарь валидаторов для полей {field_name: validator_func}
        max_payload_size: Максимальный размер payload в байтах
    
    Example:
        @validate_json_input(
            required_fields=['email', 'password'],
            optional_fields=['remember_me'],
            field_validators={
                'email': ValidationUtils.validate_email,
                'password': ValidationUtils.validate_password
            }
        )
        def login_view(request):
            # request.validated_data содержит валидированные данные
            pass
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Проверяем метод запроса
            if request.method not in ['POST', 'PUT', 'PATCH']:
                return JsonResponse(
                    {'error': 'Метод не поддерживается'}, 
                    status=405
                )
            
            # Проверяем размер payload
            if len(request.body) > max_payload_size:
                logger.warning(
                    f"Payload too large: {len(request.body)} bytes from {_get_client_ip(request)}"
                )
                return JsonResponse(
                    {'error': 'Данные слишком большие'}, 
                    status=413
                )
            
            try:
                # Парсим JSON
                data = json.loads(request.body.decode('utf-8'))
                
                # Санитизируем данные
                sanitized_data = _sanitize_data_recursive(data)
                
                # Валидируем обязательные поля
                if required_fields:
                    missing_fields = [field for field in required_fields 
                                    if field not in sanitized_data]
                    if missing_fields:
                        return JsonResponse(
                            {'error': f'Отсутствуют обязательные поля: {", ".join(missing_fields)}'}, 
                            status=400
                        )
                
                # Проверяем лишние поля
                allowed_fields = set((required_fields or []) + (optional_fields or []))
                if allowed_fields:
                    extra_fields = set(sanitized_data.keys()) - allowed_fields
                    if extra_fields:
                        return JsonResponse(
                            {'error': f'Недопустимые поля: {", ".join(extra_fields)}'}, 
                            status=400
                        )
                
                # Применяем валидаторы полей
                if field_validators:
                    for field_name, validator in field_validators.items():
                        if field_name in sanitized_data:
                            try:
                                validator(sanitized_data[field_name])
                            except ValidationError as e:
                                return JsonResponse(
                                    {'error': f'Ошибка валидации поля {field_name}: {str(e)}'}, 
                                    status=400
                                )
                            except Exception as e:
                                logger.error(f"Validator error for field {field_name}: {str(e)}")
                                return JsonResponse(
                                    {'error': f'Ошибка валидации поля {field_name}'}, 
                                    status=400
                                )
                
                # Добавляем валидированные данные к запросу
                request.validated_data = sanitized_data
                
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Некорректный JSON'}, 
                    status=400
                )
            except Exception as e:
                logger.error(f"JSON validation error: {str(e)}")
                return JsonResponse(
                    {'error': 'Ошибка валидации данных'}, 
                    status=400
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def validate_query_params(required_params: Optional[List[str]] = None,
                         optional_params: Optional[List[str]] = None,
                         param_validators: Optional[Dict[str, Callable]] = None):
    """
    Декоратор для валидации query параметров.
    
    Args:
        required_params: Список обязательных параметров
        optional_params: Список опциональных параметров
        param_validators: Словарь валидаторов для параметров
    
    Example:
        @validate_query_params(
            required_params=['page'],
            optional_params=['limit', 'search'],
            param_validators={
                'page': lambda x: int(x) > 0,
                'limit': lambda x: 1 <= int(x) <= 100
            }
        )
        def list_view(request):
            # request.validated_params содержит валидированные параметры
            pass
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            try:
                # Получаем параметры
                params = dict(request.GET.items())
                
                # Санитизируем параметры
                sanitized_params = {}
                for key, value in params.items():
                    sanitized_key = SecurityUtils.sanitize_input(str(key))
                    sanitized_value = SecurityUtils.sanitize_input(str(value))
                    sanitized_params[sanitized_key] = sanitized_value
                
                # Валидируем обязательные параметры
                if required_params:
                    missing_params = [param for param in required_params 
                                    if param not in sanitized_params]
                    if missing_params:
                        return JsonResponse(
                            {'error': f'Отсутствуют обязательные параметры: {", ".join(missing_params)}'}, 
                            status=400
                        )
                
                # Проверяем лишние параметры
                allowed_params = set((required_params or []) + (optional_params or []))
                if allowed_params:
                    extra_params = set(sanitized_params.keys()) - allowed_params
                    if extra_params:
                        return JsonResponse(
                            {'error': f'Недопустимые параметры: {", ".join(extra_params)}'}, 
                            status=400
                        )
                
                # Применяем валидаторы параметров
                if param_validators:
                    for param_name, validator in param_validators.items():
                        if param_name in sanitized_params:
                            try:
                                validator(sanitized_params[param_name])
                            except Exception as e:
                                return JsonResponse(
                                    {'error': f'Ошибка валидации параметра {param_name}: {str(e)}'}, 
                                    status=400
                                )
                
                # Добавляем валидированные параметры к запросу
                request.validated_params = sanitized_params
                
            except Exception as e:
                logger.error(f"Query params validation error: {str(e)}")
                return JsonResponse(
                    {'error': 'Ошибка валидации параметров'}, 
                    status=400
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def sanitize_input_data(sanitize_html: bool = True,
                       sanitize_sql: bool = True,
                       sanitize_xss: bool = True,
                       max_string_length: int = 10000):
    """
    Декоратор для санитизации входных данных.
    
    Args:
        sanitize_html: Экранировать HTML теги
        sanitize_sql: Удалять SQL injection паттерны
        sanitize_xss: Удалять XSS паттерны
        max_string_length: Максимальная длина строки
    
    Example:
        @sanitize_input_data(sanitize_html=True, sanitize_xss=True)
        def create_post(request):
            # Все входные данные будут санитизированы
            pass
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            try:
                # Санитизируем POST данные
                if hasattr(request, 'POST') and request.POST:
                    sanitized_post = {}
                    for key, value in request.POST.items():
                        sanitized_key = _sanitize_string(
                            key, sanitize_html, sanitize_sql, sanitize_xss, max_string_length
                        )
                        sanitized_value = _sanitize_string(
                            value, sanitize_html, sanitize_sql, sanitize_xss, max_string_length
                        )
                        sanitized_post[sanitized_key] = sanitized_value
                    request._post = sanitized_post
                
                # Санитизируем GET параметры
                if hasattr(request, 'GET') and request.GET:
                    sanitized_get = {}
                    for key, value in request.GET.items():
                        sanitized_key = _sanitize_string(
                            key, sanitize_html, sanitize_sql, sanitize_xss, max_string_length
                        )
                        sanitized_value = _sanitize_string(
                            value, sanitize_html, sanitize_sql, sanitize_xss, max_string_length
                        )
                        sanitized_get[sanitized_key] = sanitized_value
                    request._get = sanitized_get
                
                # Санитизируем JSON данные
                if hasattr(request, 'body') and request.body:
                    try:
                        data = json.loads(request.body.decode('utf-8'))
                        sanitized_data = _sanitize_data_recursive(
                            data, sanitize_html, sanitize_sql, sanitize_xss, max_string_length
                        )
                        request._body = json.dumps(sanitized_data).encode('utf-8')
                        request.sanitized_json = sanitized_data
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass  # Не JSON данные, пропускаем
                
            except Exception as e:
                logger.error(f"Input sanitization error: {str(e)}")
                return JsonResponse(
                    {'error': 'Ошибка обработки данных'}, 
                    status=400
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def validate_file_upload(allowed_extensions: Optional[List[str]] = None,
                        max_file_size: int = 10 * 1024 * 1024,  # 10MB
                        required_files: Optional[List[str]] = None,
                        scan_for_malware: bool = True):
    """
    Декоратор для валидации загружаемых файлов.
    
    Args:
        allowed_extensions: Разрешенные расширения файлов
        max_file_size: Максимальный размер файла в байтах
        required_files: Список обязательных полей файлов
        scan_for_malware: Сканировать файлы на вредоносное ПО
    
    Example:
        @validate_file_upload(
            allowed_extensions=['.jpg', '.png', '.pdf'],
            max_file_size=5*1024*1024,  # 5MB
            required_files=['avatar']
        )
        def upload_avatar(request):
            # Файлы валидированы и безопасны
            pass
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            try:
                # Проверяем наличие файлов
                if not hasattr(request, 'FILES') or not request.FILES:
                    if required_files:
                        return JsonResponse(
                            {'error': 'Отсутствуют обязательные файлы'}, 
                            status=400
                        )
                    return view_func(request, *args, **kwargs)
                
                # Проверяем обязательные файлы
                if required_files:
                    missing_files = [field for field in required_files 
                                   if field not in request.FILES]
                    if missing_files:
                        return JsonResponse(
                            {'error': f'Отсутствуют обязательные файлы: {", ".join(missing_files)}'}, 
                            status=400
                        )
                
                # Валидируем каждый файл
                for field_name, uploaded_file in request.FILES.items():
                    # Проверяем размер файла
                    if uploaded_file.size > max_file_size:
                        return JsonResponse(
                            {'error': f'Файл {uploaded_file.name} слишком большой'}, 
                            status=400
                        )
                    
                    # Проверяем расширение
                    if allowed_extensions:
                        file_extension = f".{uploaded_file.name.lower().split('.')[-1]}" if '.' in uploaded_file.name else ''
                        if file_extension not in allowed_extensions:
                            return JsonResponse(
                                {'error': f'Недопустимое расширение файла: {file_extension}'}, 
                                status=400
                            )
                    
                    # Проверяем имя файла
                    if not _validate_filename(uploaded_file.name):
                        return JsonResponse(
                            {'error': f'Недопустимое имя файла: {uploaded_file.name}'}, 
                            status=400
                        )
                    
                    # Сканируем на вредоносное ПО (базовая проверка)
                    if scan_for_malware and not _scan_file_content(uploaded_file):
                        logger.warning(
                            f"Potentially malicious file upload: {uploaded_file.name} from {_get_client_ip(request)}"
                        )
                        return JsonResponse(
                            {'error': 'Файл содержит потенциально опасный контент'}, 
                            status=400
                        )
                
            except Exception as e:
                logger.error(f"File upload validation error: {str(e)}")
                return JsonResponse(
                    {'error': 'Ошибка валидации файлов'}, 
                    status=400
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_authentication(check_permissions: Optional[List[str]] = None):
    """
    Декоратор для проверки аутентификации и авторизации.
    
    Args:
        check_permissions: Список требуемых разрешений
    
    Example:
        @require_authentication(check_permissions=['can_edit_posts'])
        def edit_post(request):
            # Пользователь аутентифицирован и имеет права
            pass
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Проверяем аутентификацию
            if not request.user.is_authenticated:
                return JsonResponse(
                    {'error': 'Требуется аутентификация'}, 
                    status=401
                )
            
            # Проверяем разрешения
            if check_permissions:
                missing_permissions = [
                    perm for perm in check_permissions 
                    if not request.user.has_perm(perm)
                ]
                if missing_permissions:
                    logger.warning(
                        f"Access denied for user {request.user.id}: missing permissions {missing_permissions}"
                    )
                    return JsonResponse(
                        {'error': 'Недостаточно прав доступа'}, 
                        status=403
                    )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Вспомогательные функции

def _get_client_ip(request: HttpRequest) -> str:
    """Получает IP адрес клиента."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _sanitize_data_recursive(data: Any, 
                            sanitize_html: bool = True,
                            sanitize_sql: bool = True,
                            sanitize_xss: bool = True,
                            max_string_length: int = 10000) -> Any:
    """Рекурсивно санитизирует данные."""
    if isinstance(data, dict):
        return {key: _sanitize_data_recursive(value, sanitize_html, sanitize_sql, sanitize_xss, max_string_length) 
                for key, value in data.items()}
    elif isinstance(data, list):
        return [_sanitize_data_recursive(item, sanitize_html, sanitize_sql, sanitize_xss, max_string_length) 
                for item in data]
    elif isinstance(data, str):
        return _sanitize_string(data, sanitize_html, sanitize_sql, sanitize_xss, max_string_length)
    else:
        return data


def _sanitize_string(value: str,
                    sanitize_html: bool = True,
                    sanitize_sql: bool = True,
                    sanitize_xss: bool = True,
                    max_string_length: int = 10000) -> str:
    """Санитизирует строковое значение."""
    if not isinstance(value, str):
        return value
    
    # Ограничиваем длину
    if len(value) > max_string_length:
        value = value[:max_string_length]
    
    # Удаляем null байты
    value = value.replace('\x00', '')
    
    # HTML санитизация
    if sanitize_html:
        value = escape(value)
    
    # Используем встроенную санитизацию
    value = SecurityUtils.sanitize_input(value)
    
    return value


def _validate_filename(filename: str) -> bool:
    """Валидирует имя файла."""
    # Проверяем на опасные символы
    dangerous_chars = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"', '\x00']
    if any(char in filename for char in dangerous_chars):
        return False
    
    # Проверяем длину
    if len(filename) > 255:
        return False
    
    # Проверяем на зарезервированные имена Windows
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
    if filename.upper().split('.')[0] in reserved_names:
        return False
    
    return True


def _scan_file_content(uploaded_file) -> bool:
    """Базовое сканирование файла на вредоносный контент."""
    try:
        # Читаем первые 1024 байта для проверки
        content = uploaded_file.read(1024)
        uploaded_file.seek(0)  # Возвращаем указатель в начало
        
        # Проверяем на подозрительные сигнатуры
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'<?php',
            b'<%',
            b'#!/bin/sh',
            b'#!/bin/bash',
        ]
        
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"File content scan error: {str(e)}")
        return False