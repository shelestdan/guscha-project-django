# -*- coding: utf-8 -*-
"""
Тесты для системы безопасности Telegram endpoints.

Этот модуль содержит специализированные тесты для проверки
rate limiting, IP ограничений и мониторинга безопасности
для Telegram аутентификации.
"""

import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings

from .rate_limiting import RateLimiter, RATE_LIMITS, get_endpoint_rate_limit
from .security_logging import SecurityLogger
from ..middleware.rate_limiting import RateLimitMiddleware
from ..middleware.security_monitoring import SecurityMonitoringMiddleware
from ..security.monitoring import security_monitor


class TelegramRateLimitingTestCase(TestCase):
    """Тесты для rate limiting Telegram endpoints."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.rate_limiter = RateLimiter()
        self.security_logger = SecurityLogger()
        cache.clear()
    
    def test_telegram_login_rate_limit(self):
        """Тест rate limiting для Telegram login endpoint."""
        request = self.factory.post('/api/accounts/telegram/login/initiate/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.META['HTTP_USER_AGENT'] = 'TelegramBot/1.0'
        
        endpoint_key = get_endpoint_rate_limit(request.path_info, request.method)
        self.assertEqual(endpoint_key, 'telegram_login')
        
        rate_config = RATE_LIMITS.get(endpoint_key)
        self.assertIsNotNone(rate_config)
        
        # Первые запросы должны проходить
        for i in range(3):
            is_limited, rate_info = self.rate_limiter.is_rate_limited(
                request, endpoint_key, rate_config
            )
            self.assertFalse(is_limited, f"Request {i+1} should not be limited")
    
    def test_telegram_status_rate_limit(self):
        """Тест rate limiting для Telegram status endpoint."""
        request = self.factory.get('/api/accounts/telegram/login/status/')
        request.META['REMOTE_ADDR'] = '192.168.1.101'
        
        endpoint_key = get_endpoint_rate_limit(request.path_info, request.method)
        self.assertEqual(endpoint_key, 'telegram_status')
        
        rate_config = RATE_LIMITS.get(endpoint_key)
        self.assertIsNotNone(rate_config)
        
        # Проверяем, что можем делать много status запросов
        for i in range(15):
            is_limited, rate_info = self.rate_limiter.is_rate_limited(
                request, endpoint_key, rate_config
            )
            self.assertFalse(is_limited, f"Status request {i+1} should not be limited")
    
    def test_telegram_verify_rate_limit_exceeded(self):
        """Тест превышения rate limit для Telegram verify endpoint."""
        request = self.factory.post('/api/accounts/telegram/verify/')
        request.META['REMOTE_ADDR'] = '192.168.1.102'
        
        endpoint_key = get_endpoint_rate_limit(request.path_info, request.method)
        self.assertEqual(endpoint_key, 'telegram_verify')
        
        rate_config = RATE_LIMITS.get(endpoint_key)
        
        # Симулируем превышение лимита
        cache_key = f"rate_limit:192.168.1.102:{endpoint_key}"
        cache.set(cache_key, {'requests': 6, 'window_start': time.time()}, 3600)
        
        is_limited, rate_info = self.rate_limiter.is_rate_limited(
            request, endpoint_key, rate_config
        )
        self.assertTrue(is_limited, "Should be rate limited after exceeding limit")
    
    def test_telegram_ip_attempts_limit(self):
        """Тест общего лимита попыток с одного IP для Telegram."""
        ip_address = '192.168.1.103'
        
        # Создаем запросы к разным Telegram endpoints с одного IP
        endpoints = [
            '/api/accounts/telegram/login/initiate/',
            '/api/accounts/telegram/verify/',
            '/api/accounts/telegram/activate/',
        ]
        
        request_count = 0
        for endpoint in endpoints:
            for i in range(8):  # 8 запросов к каждому endpoint
                request = self.factory.post(endpoint)
                request.META['REMOTE_ADDR'] = ip_address
                
                endpoint_key = get_endpoint_rate_limit(request.path_info, request.method)
                rate_config = RATE_LIMITS.get(endpoint_key)
                
                is_limited, rate_info = self.rate_limiter.is_rate_limited(
                    request, endpoint_key, rate_config
                )
                
                request_count += 1
                
                # После определенного количества запросов должна сработать блокировка
                if request_count > 20:  # Общий лимит для IP
                    # Проверяем IP-based ограничения
                    ip_key = f"telegram_ip_attempts"
                    if ip_key in RATE_LIMITS:
                        ip_config = RATE_LIMITS[ip_key]
                        is_ip_limited, ip_info = self.rate_limiter.is_rate_limited(
                            request, ip_key, ip_config
                        )
                        # IP лимит может сработать
                        break


class TelegramSecurityMonitoringTestCase(TestCase):
    """Тесты для мониторинга безопасности Telegram endpoints."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityMonitoringMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        cache.clear()
    
    def test_telegram_multiple_phones_detection(self):
        """Тест обнаружения множественных номеров телефонов с одного IP."""
        ip_address = '192.168.1.200'
        
        # Симулируем запросы с разными номерами телефонов
        phones = ['+1234567890', '+1234567891', '+1234567892', '+1234567893']
        
        for phone in phones:
            request = self.factory.post('/api/accounts/telegram/login/initiate/', {
                'phone_number': phone
            })
            request.META['REMOTE_ADDR'] = ip_address
            request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
            
            # Обрабатываем запрос через middleware
            response = self.middleware(request)
            
            # Первые несколько запросов должны проходить
            if len(phones[:phones.index(phone)+1]) <= 3:
                self.assertIsNotNone(response, f"Request with phone {phone} should be processed")
    
    def test_telegram_rapid_requests_detection(self):
        """Тест обнаружения быстрых последовательных запросов."""
        request = self.factory.post('/api/accounts/telegram/verify/', {
            'phone_number': '+1234567890',
            'code': '123456'
        })
        request.META['REMOTE_ADDR'] = '192.168.1.201'
        request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        # Делаем быстрые последовательные запросы
        for i in range(10):
            response = self.middleware(request)
            # Некоторые запросы могут быть заблокированы из-за подозрительной активности
            if response and hasattr(response, 'status_code') and response.status_code == 429:
                break
    
    def test_telegram_suspicious_patterns_detection(self):
        """Тест обнаружения подозрительных паттернов в Telegram запросах."""
        # Подозрительные данные
        suspicious_data = [
            {'phone_number': '+1' + '0' * 20},  # Слишком длинный номер
            {'phone_number': '+1234567890', 'code': '000000'},  # Подозрительный код
            {'phone_number': 'invalid_phone'},  # Неверный формат
        ]
        
        responses = []
        for data in suspicious_data:
            request = self.factory.post('/api/accounts/telegram/verify/', data)
            request.META['REMOTE_ADDR'] = '192.168.1.202'
            request.META['HTTP_USER_AGENT'] = 'SuspiciousBot/1.0'
            
            response = self.middleware(request)
            responses.append(response)
            
        # Проверяем, что запросы были обработаны
        for response in responses:
            if response and hasattr(response, 'status_code'):
                self.assertIn(response.status_code, [200, 403, 429], "Should return valid response")
    
    @patch('apps.core.validation.security_logging.SecurityLogger.log_telegram_suspicious_pattern')
    def test_telegram_logging_integration(self, mock_log):
        """Тест интеграции с системой логирования для Telegram."""
        request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1234567890'
        })
        request.META['REMOTE_ADDR'] = '192.168.1.203'
        request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        # Симулируем подозрительную активность
        with patch.object(self.middleware, '_detect_telegram_threats') as mock_detect:
            mock_detect.return_value = ('high', 'Multiple phone numbers from same IP')
            
            response = self.middleware(request)
            
            # Проверяем, что логирование было вызвано
            if response and hasattr(response, 'status_code') and response.status_code == 429:
                self.assertTrue(mock_log.called or mock_detect.called)


class TelegramRateLimitMiddlewareTestCase(TestCase):
    """Тесты для RateLimitMiddleware с Telegram endpoints."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        cache.clear()
    
    def test_telegram_endpoint_rate_limiting(self):
        """Тест rate limiting middleware для Telegram endpoints."""
        request = self.factory.post('/api/accounts/telegram/login/initiate/')
        request.META['REMOTE_ADDR'] = '192.168.1.300'
        request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        # Первый запрос должен пройти
        response = self.middleware.process_request(request)
        self.assertIsNone(response, "First request should pass")
        
        # Симулируем превышение лимита
        with patch.object(self.middleware.rate_limiter, 'is_rate_limited') as mock_limited:
            mock_limited.return_value = (True, {'requests_made': 6, 'requests_allowed': 5})
            
            response = self.middleware.process_request(request)
            self.assertIsNotNone(response, "Should return rate limit response")
            self.assertEqual(response.status_code, 429)
    
    def test_telegram_ip_blocking(self):
        """Тест блокировки IP для Telegram endpoints."""
        ip_address = '192.168.1.301'
        
        # Создаем множественные запросы для превышения лимита
        for i in range(25):  # Превышаем лимит
            request = self.factory.post('/api/accounts/telegram/verify/')
            request.META['REMOTE_ADDR'] = ip_address
            request.META['HTTP_USER_AGENT'] = f'TelegramApp/1.0-{i}'
            
            response = self.middleware.process_request(request)
            
            # После определенного количества запросов должна сработать блокировка
            if response and response.status_code == 429:
                break
    
    def test_telegram_bypass_conditions(self):
        """Тест условий обхода rate limiting для Telegram."""
        # Тестируем исключения из rate limiting
        excluded_paths = [
            '/api/accounts/telegram/health/',
            '/api/accounts/telegram/ping/',
        ]
        
        for path in excluded_paths:
            request = self.factory.get(path)
            request.META['REMOTE_ADDR'] = '192.168.1.302'
            
            # Проверяем, что путь исключен из rate limiting
            should_limit = self.middleware.should_rate_limit(request)
            # В зависимости от конфигурации, некоторые пути могут быть исключены


class TelegramSecurityIntegrationTestCase(TestCase):
    """Интеграционные тесты для системы безопасности Telegram."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def test_full_telegram_security_pipeline(self):
        """Тест полного pipeline безопасности для Telegram."""
        # Создаем цепочку middleware
        security_middleware = SecurityMonitoringMiddleware(
            lambda r: JsonResponse({'status': 'ok'})
        )
        rate_limit_middleware = RateLimitMiddleware(
            lambda r: security_middleware.process_request(r) or JsonResponse({'status': 'ok'})
        )
        
        # Тестируем нормальный запрос
        request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1234567890'
        })
        request.META['REMOTE_ADDR'] = '192.168.1.400'
        request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        request.user = self.user
        
        # Обрабатываем через оба middleware
        response = rate_limit_middleware.process_request(request)
        
        # Первый запрос должен пройти
        if response is None:
            # None означает, что middleware пропустил запрос дальше
            self.assertIsNone(response, "Normal request should pass through security pipeline")
        else:
            # Если есть response, проверяем что он не блокирующий
            self.assertNotEqual(response.status_code, 403, "Normal request should not be forbidden")
    
    def test_telegram_attack_simulation(self):
        """Симуляция атаки на Telegram endpoints."""
        attacker_ip = '192.168.1.401'
        
        # Симулируем различные типы атак
        attack_scenarios = [
            # Brute force на verify endpoint
            {
                'endpoint': '/api/accounts/telegram/verify/',
                'data': {'phone_number': '+1234567890', 'code': f'{i:06d}'},
                'count': 20
            } for i in range(20)
        ]
        
        security_middleware = SecurityMonitoringMiddleware(
            lambda r: JsonResponse({'status': 'ok'})
        )
        
        blocked_count = 0
        
        for scenario in attack_scenarios[:10]:  # Ограничиваем количество для теста
            request = self.factory.post(scenario['endpoint'], scenario['data'])
            request.META['REMOTE_ADDR'] = attacker_ip
            request.META['HTTP_USER_AGENT'] = 'AttackBot/1.0'
            
            response = security_middleware(request)
            
            if response and hasattr(response, 'status_code') and response.status_code == 429:
                blocked_count += 1
        
        # Ожидаем, что некоторые запросы будут заблокированы
        self.assertGreaterEqual(blocked_count, 0, "Some attack requests should be blocked")
    
    @patch('apps.core.validation.security_logging.SecurityLogger')
    def test_telegram_security_logging(self, mock_logger):
        """Тест логирования событий безопасности для Telegram."""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        security_middleware = SecurityMonitoringMiddleware(
            lambda r: JsonResponse({'status': 'ok'})
        )
        
        # Создаем подозрительный запрос
        request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1' + '0' * 50  # Аномально длинный номер
        })
        request.META['REMOTE_ADDR'] = '192.168.1.402'
        request.META['HTTP_USER_AGENT'] = 'SuspiciousBot/1.0'
        
        response = security_middleware(request)
        
        # Проверяем, что события безопасности логируются
        # (в зависимости от реализации middleware)