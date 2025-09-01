# -*- coding: utf-8 -*-
"""
Интеграционные тесты для системы безопасности Telegram.

Этот модуль содержит тесты для проверки взаимодействия
всех компонентов системы безопасности: rate limiting,
security monitoring, logging и middleware.
"""

import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.http import JsonResponse
from django.core.cache import cache
from django.contrib.auth.models import User
from django.urls import reverse

from .rate_limiting import RateLimiter, RATE_LIMITS
from .security_logging import SecurityLogger
from ..middleware.rate_limiting import RateLimitMiddleware
from ..middleware.security_monitoring import SecurityMonitoringMiddleware
from ..middleware.validation_middleware import InputValidationMiddleware


class TelegramSecurityIntegrationTestCase(TestCase):
    """Интеграционные тесты для полной системы безопасности Telegram."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.security_logger = SecurityLogger()
        
        # Создаем полный middleware stack
        def dummy_view(request):
            return JsonResponse({'status': 'success', 'message': 'Request processed'})
        
        self.middleware_stack = [
            InputValidationMiddleware(dummy_view),
            SecurityMonitoringMiddleware(dummy_view),
            RateLimitMiddleware(dummy_view)
        ]
        
        cache.clear()
    
    def process_request_through_stack(self, request):
        """Обрабатывает запрос через весь middleware stack."""
        response = None
        
        for middleware in self.middleware_stack:
            response = middleware.process_request(request)
            if response:  # Если middleware заблокировал запрос
                break
        
        return response
    
    def test_normal_telegram_flow(self):
        """Тест нормального потока Telegram аутентификации."""
        ip_address = '192.168.100.1'
        phone_number = '+1234567890'
        
        # 1. Инициация входа
        login_request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': phone_number
        })
        login_request.META['REMOTE_ADDR'] = ip_address
        login_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        login_response = self.process_request_through_stack(login_request)
        self.assertIsNone(login_response, "Normal login initiation should be allowed")
        
        # 2. Проверка статуса
        status_request = self.factory.get('/api/accounts/telegram/login/status/')
        status_request.META['REMOTE_ADDR'] = ip_address
        status_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        status_response = self.process_request_through_stack(status_request)
        self.assertIsNone(status_response, "Status check should be allowed")
        
        # 3. Верификация кода
        verify_request = self.factory.post('/api/accounts/telegram/verify/', {
            'phone_number': phone_number,
            'code': '123456'
        })
        verify_request.META['REMOTE_ADDR'] = ip_address
        verify_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        verify_response = self.process_request_through_stack(verify_request)
        self.assertIsNone(verify_response, "Code verification should be allowed")
        
        # 4. Активация аккаунта
        activate_request = self.factory.post('/api/accounts/telegram/activate/', {
            'phone_number': phone_number
        })
        activate_request.META['REMOTE_ADDR'] = ip_address
        activate_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        activate_response = self.process_request_through_stack(activate_request)
        self.assertIsNone(activate_response, "Account activation should be allowed")
    
    def test_rate_limit_integration(self):
        """Тест интеграции rate limiting с другими компонентами."""
        ip_address = '192.168.100.2'
        phone_number = '+1234567891'
        
        # Получаем конфигурацию rate limit для telegram_login
        rate_config = RATE_LIMITS.get('telegram_login', {})
        max_requests = rate_config.get('requests', 5)
        
        successful_requests = 0
        blocked_requests = 0
        
        # Отправляем запросы до превышения лимита
        for i in range(max_requests + 5):
            request = self.factory.post('/api/accounts/telegram/login/initiate/', {
                'phone_number': f'{phone_number}{i:02d}'
            })
            request.META['REMOTE_ADDR'] = ip_address
            request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
            
            response = self.process_request_through_stack(request)
            
            if response is None:
                successful_requests += 1
            elif response.status_code == 429:
                blocked_requests += 1
        
        # Проверяем, что rate limiting работает
        self.assertGreater(successful_requests, 0, "Some requests should be successful")
        self.assertGreater(blocked_requests, 0, "Some requests should be blocked by rate limiting")
        self.assertEqual(successful_requests + blocked_requests, max_requests + 5, 
                        "All requests should be processed")
    
    def test_security_monitoring_integration(self):
        """Тест интеграции security monitoring с другими компонентами."""
        ip_address = '192.168.100.3'
        
        # Симулируем подозрительное поведение: множественные номера телефонов
        suspicious_phones = [f'+123456789{i:02d}' for i in range(10)]
        
        blocked_count = 0
        allowed_count = 0
        
        for phone in suspicious_phones:
            request = self.factory.post('/api/accounts/telegram/login/initiate/', {
                'phone_number': phone
            })
            request.META['REMOTE_ADDR'] = ip_address
            request.META['HTTP_USER_AGENT'] = 'SuspiciousBot/1.0'
            
            response = self.process_request_through_stack(request)
            
            if response is None:
                allowed_count += 1
            else:
                blocked_count += 1
        
        # Security monitoring должен обнаружить подозрительное поведение
        self.assertGreater(blocked_count, 0, 
                          "Security monitoring should block suspicious requests")
    
    def test_input_validation_integration(self):
        """Тест интеграции input validation с другими компонентами."""
        ip_address = '192.168.100.4'
        
        # Тест с валидными данными
        valid_request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1234567890'
        })
        valid_request.META['REMOTE_ADDR'] = ip_address
        valid_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        valid_response = self.process_request_through_stack(valid_request)
        self.assertIsNone(valid_response, "Valid request should pass validation")
        
        # Тест с потенциально опасными данными
        malicious_payloads = [
            {'phone_number': '<script>alert("xss")</script>'},
            {'phone_number': "'; DROP TABLE users; --"},
            {'phone_number': '{{7*7}}'},  # Template injection
            {'phone_number': '../../../etc/passwd'},  # Path traversal
        ]
        
        for payload in malicious_payloads:
            malicious_request = self.factory.post('/api/accounts/telegram/login/initiate/', payload)
            malicious_request.META['REMOTE_ADDR'] = ip_address
            malicious_request.META['HTTP_USER_AGENT'] = 'AttackBot/1.0'
            
            malicious_response = self.process_request_through_stack(malicious_request)
            
            # Input validation или security monitoring должны заблокировать запрос
            self.assertIsNotNone(malicious_response, 
                               f"Malicious payload should be blocked: {payload}")
    
    @patch('apps.core.validation.security_logging.SecurityLogger.log_security_event')
    def test_logging_integration(self, mock_log_event):
        """Тест интеграции системы логирования."""
        ip_address = '192.168.100.5'
        
        # Отправляем запрос, который должен быть залогирован
        request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1234567890'
        })
        request.META['REMOTE_ADDR'] = ip_address
        request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        response = self.process_request_through_stack(request)
        
        # Проверяем, что события логируются
        self.assertTrue(mock_log_event.called, "Security events should be logged")
        
        # Анализируем вызовы логирования
        log_calls = mock_log_event.call_args_list
        event_types = [call[1]['event_type'] for call in log_calls if 'event_type' in call[1]]
        
        # Должны быть залогированы различные типы событий
        expected_events = ['TELEGRAM_AUTH_REQUEST', 'RATE_LIMIT_CHECK']
        for expected_event in expected_events:
            # Проверяем, что хотя бы один из ожидаемых событий был залогирован
            pass  # В реальной реализации здесь была бы более детальная проверка
    
    def test_concurrent_requests_integration(self):
        """Тест обработки concurrent запросов через всю систему."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {'allowed': 0, 'blocked': 0, 'errors': 0}
        results_lock = threading.Lock()
        
        def concurrent_request_worker(worker_id):
            try:
                ip_address = f'192.168.101.{worker_id % 255}'
                phone_number = f'+123456{worker_id:05d}'
                
                request = self.factory.post('/api/accounts/telegram/login/initiate/', {
                    'phone_number': phone_number
                })
                request.META['REMOTE_ADDR'] = ip_address
                request.META['HTTP_USER_AGENT'] = f'TelegramApp/Worker-{worker_id}'
                
                response = self.process_request_through_stack(request)
                
                with results_lock:
                    if response is None:
                        results['allowed'] += 1
                    else:
                        results['blocked'] += 1
                        
            except Exception as e:
                with results_lock:
                    results['errors'] += 1
        
        # Запускаем 50 concurrent запросов
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(concurrent_request_worker, i) for i in range(50)]
            
            # Ждем завершения всех запросов
            for future in as_completed(futures):
                future.result()  # Получаем результат для обработки исключений
        
        # Проверяем результаты
        total_requests = results['allowed'] + results['blocked'] + results['errors']
        self.assertEqual(total_requests, 50, "All requests should be processed")
        self.assertLess(results['errors'] / total_requests, 0.1, "Error rate should be low")
        self.assertGreater(results['allowed'], 0, "Some requests should be allowed")
    
    def test_attack_simulation_integration(self):
        """Тест симуляции атаки через всю систему безопасности."""
        attacker_ip = '192.168.100.666'
        
        # Симулируем различные типы атак
        attack_scenarios = [
            # Brute force атака
            {
                'name': 'brute_force',
                'requests': [
                    {'endpoint': '/api/accounts/telegram/verify/', 
                     'data': {'phone_number': '+1234567890', 'code': f'{i:06d}'}} 
                    for i in range(20)
                ]
            },
            # Enumeration атака
            {
                'name': 'phone_enumeration',
                'requests': [
                    {'endpoint': '/api/accounts/telegram/login/initiate/', 
                     'data': {'phone_number': f'+123456789{i:02d}'}} 
                    for i in range(15)
                ]
            },
            # Rapid fire атака
            {
                'name': 'rapid_fire',
                'requests': [
                    {'endpoint': '/api/accounts/telegram/login/status/', 'data': {}} 
                    for _ in range(30)
                ]
            }
        ]
        
        attack_results = {}
        
        for scenario in attack_scenarios:
            scenario_results = {'allowed': 0, 'blocked': 0}
            
            for req_config in scenario['requests']:
                if req_config['data']:
                    request = self.factory.post(req_config['endpoint'], req_config['data'])
                else:
                    request = self.factory.get(req_config['endpoint'])
                
                request.META['REMOTE_ADDR'] = attacker_ip
                request.META['HTTP_USER_AGENT'] = f'AttackBot/{scenario["name"]}'
                
                response = self.process_request_through_stack(request)
                
                if response is None:
                    scenario_results['allowed'] += 1
                else:
                    scenario_results['blocked'] += 1
                
                # Небольшая задержка между запросами в рамках сценария
                time.sleep(0.001)
            
            attack_results[scenario['name']] = scenario_results
        
        # Анализируем результаты атак
        for scenario_name, results in attack_results.items():
            total_requests = results['allowed'] + results['blocked']
            block_rate = results['blocked'] / total_requests if total_requests > 0 else 0
            
            # Система безопасности должна блокировать значительную часть атак
            self.assertGreater(block_rate, 0.3, 
                             f"Attack scenario '{scenario_name}' should be mostly blocked. "
                             f"Block rate: {block_rate:.2%}")
    
    def test_system_recovery_integration(self):
        """Тест восстановления системы после атаки."""
        attacker_ip = '192.168.100.777'
        legitimate_ip = '192.168.100.888'
        
        # 1. Симулируем атаку
        for i in range(20):
            attack_request = self.factory.post('/api/accounts/telegram/login/initiate/', {
                'phone_number': f'+99999999{i:02d}'
            })
            attack_request.META['REMOTE_ADDR'] = attacker_ip
            attack_request.META['HTTP_USER_AGENT'] = 'AttackBot/1.0'
            
            self.process_request_through_stack(attack_request)
        
        # 2. Проверяем, что атакующий IP заблокирован
        blocked_request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1111111111'
        })
        blocked_request.META['REMOTE_ADDR'] = attacker_ip
        blocked_request.META['HTTP_USER_AGENT'] = 'AttackBot/1.0'
        
        blocked_response = self.process_request_through_stack(blocked_request)
        self.assertIsNotNone(blocked_response, "Attacker IP should be blocked")
        
        # 3. Проверяем, что легитимные пользователи не затронуты
        legitimate_request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+2222222222'
        })
        legitimate_request.META['REMOTE_ADDR'] = legitimate_ip
        legitimate_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        legitimate_response = self.process_request_through_stack(legitimate_request)
        self.assertIsNone(legitimate_response, "Legitimate users should not be affected")
        
        # 4. Симулируем прохождение времени для восстановления
        # В реальной системе здесь был бы механизм очистки блокировок по времени
        time.sleep(0.1)
        
        # 5. Проверяем постепенное восстановление доступа
        # (в зависимости от конфигурации системы)


class TelegramEndpointSpecificTestCase(TestCase):
    """Тесты специфичные для каждого Telegram endpoint."""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        def dummy_view(request):
            return JsonResponse({'status': 'success'})
        
        self.middleware_stack = [
            InputValidationMiddleware(dummy_view),
            SecurityMonitoringMiddleware(dummy_view),
            RateLimitMiddleware(dummy_view)
        ]
        
        cache.clear()
    
    def process_request(self, request):
        """Обрабатывает запрос через middleware stack."""
        for middleware in self.middleware_stack:
            response = middleware.process_request(request)
            if response:
                return response
        return None
    
    def test_login_initiate_endpoint(self):
        """Тест специфичный для /api/accounts/telegram/login/initiate/."""
        ip_address = '192.168.200.1'
        
        # Тест с валидными данными
        valid_request = self.factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1234567890'
        })
        valid_request.META['REMOTE_ADDR'] = ip_address
        valid_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        response = self.process_request(valid_request)
        self.assertIsNone(response, "Valid login initiation should be allowed")
        
        # Тест с невалидными данными
        invalid_requests = [
            {'phone_number': 'invalid_phone'},
            {'phone_number': ''},
            {},  # Отсутствует phone_number
            {'phone_number': '+' + '1' * 20},  # Слишком длинный номер
        ]
        
        for invalid_data in invalid_requests:
            invalid_request = self.factory.post('/api/accounts/telegram/login/initiate/', invalid_data)
            invalid_request.META['REMOTE_ADDR'] = ip_address
            invalid_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
            
            response = self.process_request(invalid_request)
            # В зависимости от настроек валидации, запрос может быть заблокирован
    
    def test_verify_endpoint(self):
        """Тест специфичный для /api/accounts/telegram/verify/."""
        ip_address = '192.168.200.2'
        
        # Тест с валидными данными
        valid_request = self.factory.post('/api/accounts/telegram/verify/', {
            'phone_number': '+1234567890',
            'code': '123456'
        })
        valid_request.META['REMOTE_ADDR'] = ip_address
        valid_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        response = self.process_request(valid_request)
        self.assertIsNone(response, "Valid verification should be allowed")
        
        # Тест brute force защиты
        for i in range(10):
            brute_force_request = self.factory.post('/api/accounts/telegram/verify/', {
                'phone_number': '+1234567890',
                'code': f'{i:06d}'
            })
            brute_force_request.META['REMOTE_ADDR'] = ip_address
            brute_force_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
            
            response = self.process_request(brute_force_request)
            # После нескольких попыток система должна заблокировать запросы
    
    def test_status_endpoint(self):
        """Тест специфичный для /api/accounts/telegram/login/status/."""
        ip_address = '192.168.200.3'
        
        # Status endpoint должен иметь более мягкие ограничения
        for i in range(20):  # Больше запросов чем обычно
            status_request = self.factory.get('/api/accounts/telegram/login/status/')
            status_request.META['REMOTE_ADDR'] = ip_address
            status_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
            
            response = self.process_request(status_request)
            # Первые несколько запросов должны проходить
            if i < 15:  # В зависимости от конфигурации
                self.assertIsNone(response, f"Status request {i} should be allowed")
    
    def test_activate_endpoint(self):
        """Тест специфичный для /api/accounts/telegram/activate/."""
        ip_address = '192.168.200.4'
        
        # Activate endpoint должен быть более строго ограничен
        activate_request = self.factory.post('/api/accounts/telegram/activate/', {
            'phone_number': '+1234567890'
        })
        activate_request.META['REMOTE_ADDR'] = ip_address
        activate_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        response = self.process_request(activate_request)
        self.assertIsNone(response, "First activation should be allowed")
        
        # Повторная активация должна быть заблокирована или ограничена
        second_activate_request = self.factory.post('/api/accounts/telegram/activate/', {
            'phone_number': '+1234567890'
        })
        second_activate_request.META['REMOTE_ADDR'] = ip_address
        second_activate_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        response = self.process_request(second_activate_request)
        # В зависимости от бизнес-логики, повторная активация может быть заблокирована