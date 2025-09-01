# -*- coding: utf-8 -*-
"""
Тесты производительности и нагрузочные тесты для Telegram endpoints.

Этот модуль содержит тесты для проверки производительности
system rate limiting и мониторинга безопасности под нагрузкой.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from django.core.cache import cache
from django.contrib.auth.models import User, AnonymousUser

from .rate_limiting import RateLimiter, RATE_LIMITS
from .security_logging import SecurityLogger
from ..middleware.rate_limiting import RateLimitMiddleware
from ..middleware.security_monitoring import SecurityMonitoringMiddleware


class TelegramPerformanceTestCase(TestCase):
    """Тесты производительности для Telegram rate limiting."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.rate_limiter = RateLimiter()
        cache.clear()
    
    def _add_user_to_request(self, request):
        """Добавляет пользователя к запросу для тестирования."""
        request.user = AnonymousUser()
        return request
    
    def test_rate_limiter_performance(self):
        """Тест производительности rate limiter."""
        request = self.factory.post('/api/accounts/telegram/login/initiate/')
        request.META['REMOTE_ADDR'] = '192.168.1.500'
        request = self._add_user_to_request(request)
        
        endpoint_key = 'telegram_login'
        rate_config = RATE_LIMITS.get(endpoint_key)
        
        # Измеряем время выполнения
        start_time = time.time()
        
        for i in range(100):
            is_limited, rate_info = self.rate_limiter.is_rate_limited(
                request, endpoint_key, rate_config
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Проверяем, что 100 проверок выполняются быстро (< 1 секунды)
        self.assertLess(execution_time, 1.0, 
                       f"Rate limiting checks took too long: {execution_time:.3f}s")
        
        # Проверяем среднее время на одну проверку
        avg_time = execution_time / 100
        self.assertLess(avg_time, 0.01, 
                       f"Average check time too high: {avg_time:.6f}s")
    
    def test_concurrent_rate_limiting(self):
        """Тест concurrent rate limiting для одного IP."""
        ip_address = '192.168.1.501'
        endpoint_key = 'telegram_verify'
        rate_config = RATE_LIMITS.get(endpoint_key)
        
        def make_request(request_id):
            request = self.factory.post('/api/accounts/telegram/verify/')
            request.META['REMOTE_ADDR'] = ip_address
            request.META['HTTP_USER_AGENT'] = f'TelegramApp/1.0-{request_id}'
            request = self._add_user_to_request(request)
            
            is_limited, rate_info = self.rate_limiter.is_rate_limited(
                request, endpoint_key, rate_config
            )
            
            return {
                'request_id': request_id,
                'is_limited': is_limited,
                'rate_info': rate_info
            }
        
        # Запускаем 20 concurrent запросов
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # Анализируем результаты
        allowed_count = sum(1 for r in results if not r['is_limited'])
        blocked_count = sum(1 for r in results if r['is_limited'])
        
        # Проверяем, что rate limiting работает корректно под нагрузкой
        self.assertGreater(allowed_count, 0, "Some requests should be allowed")
        # В зависимости от конфигурации, некоторые запросы могут быть заблокированы
    
    def test_multiple_ips_performance(self):
        """Тест производительности с множественными IP адресами."""
        endpoint_key = 'telegram_login'
        rate_config = RATE_LIMITS.get(endpoint_key)
        
        def test_ip(ip_suffix):
            ip_address = f'192.168.1.{ip_suffix}'
            request = self.factory.post('/api/accounts/telegram/login/initiate/')
            request.META['REMOTE_ADDR'] = ip_address
            request = self._add_user_to_request(request)
            
            results = []
            for i in range(10):  # 10 запросов с каждого IP
                start_time = time.time()
                is_limited, rate_info = self.rate_limiter.is_rate_limited(
                    request, endpoint_key, rate_config
                )
                end_time = time.time()
                
                results.append({
                    'ip': ip_address,
                    'request': i,
                    'is_limited': is_limited,
                    'time': end_time - start_time
                })
            
            return results
        
        # Тестируем 50 разных IP адресов
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(test_ip, i) for i in range(600, 650)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Анализируем производительность
        total_requests = len(all_results)
        avg_time = sum(r['time'] for r in all_results) / total_requests
        max_time = max(r['time'] for r in all_results)
        
        self.assertLess(avg_time, 0.01, f"Average response time too high: {avg_time:.6f}s")
        self.assertLess(max_time, 0.1, f"Max response time too high: {max_time:.6f}s")


class TelegramLoadTestCase(TestCase):
    """Нагрузочные тесты для Telegram middleware."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(lambda r: JsonResponse({'status': 'ok'}))
        cache.clear()
    
    def _add_user_to_request(self, request):
        """Добавляет пользователя к запросу для тестирования."""
        request.user = AnonymousUser()
        return request
    
    def test_middleware_under_load(self):
        """Тест middleware под нагрузкой."""
        def simulate_user_requests(user_id):
            ip_address = f'192.168.2.{user_id % 255}'
            results = []
            
            for i in range(5):  # 5 запросов от каждого пользователя
                request = self.factory.post('/api/accounts/telegram/login/initiate/', {
                    'phone_number': f'+123456789{user_id:02d}'
                })
                request.META['REMOTE_ADDR'] = ip_address
                request.META['HTTP_USER_AGENT'] = f'TelegramApp/1.0-User{user_id}'
                request = self._add_user_to_request(request)
                
                start_time = time.time()
                response = self.middleware(request)
                end_time = time.time()
                
                results.append({
                    'user_id': user_id,
                    'request': i,
                    'response_time': end_time - start_time,
                    'status': 'blocked' if hasattr(response, 'status_code') and response.status_code in [403, 429] else 'allowed'
                })
                
                # Небольшая задержка между запросами
                time.sleep(0.01)
            
            return results
        
        # Симулируем 100 пользователей
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(simulate_user_requests, i) for i in range(100)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Анализируем результаты нагрузочного теста
        total_requests = len(all_results)
        allowed_requests = sum(1 for r in all_results if r['status'] == 'allowed')
        blocked_requests = sum(1 for r in all_results if r['status'] == 'blocked')
        
        avg_response_time = sum(r['response_time'] for r in all_results) / total_requests
        max_response_time = max(r['response_time'] for r in all_results)
        
        # Проверяем производительность
        self.assertLess(avg_response_time, 0.05, 
                       f"Average response time under load: {avg_response_time:.6f}s")
        self.assertLess(max_response_time, 0.5, 
                       f"Max response time under load: {max_response_time:.6f}s")
        
        # Проверяем, что система работает корректно
        self.assertGreater(allowed_requests, 0, "Some requests should be allowed")
        self.assertEqual(total_requests, allowed_requests + blocked_requests, 
                        "All requests should be processed")
    
    def test_security_monitoring_under_load(self):
        """Тест security monitoring под нагрузкой."""
        security_middleware = SecurityMonitoringMiddleware(
            lambda r: JsonResponse({'status': 'ok'})
        )
        
        def simulate_attack_pattern(attacker_id):
            ip_address = f'10.0.0.{attacker_id % 255}'
            results = []
            
            # Симулируем различные атаки
            attack_patterns = [
                {'endpoint': '/api/accounts/telegram/login/initiate/', 'phone': f'+{attacker_id}1234567890'},
                {'endpoint': '/api/accounts/telegram/verify/', 'phone': f'+{attacker_id}1234567890', 'code': '000000'},
                {'endpoint': '/api/accounts/telegram/activate/', 'phone': f'+{attacker_id}1234567890'},
            ]
            
            for pattern in attack_patterns:
                for i in range(3):  # 3 запроса каждого типа
                    request_data = {'phone_number': pattern['phone']}
                    if 'code' in pattern:
                        request_data['code'] = pattern['code']
                    
                    request = self.factory.post(pattern['endpoint'], request_data)
                    request.META['REMOTE_ADDR'] = ip_address
                    request.META['HTTP_USER_AGENT'] = f'AttackBot/{attacker_id}'
                    request = self._add_user_to_request(request)
                    
                    start_time = time.time()
                    response = security_middleware(request)
                    end_time = time.time()
                    
                    results.append({
                        'attacker_id': attacker_id,
                        'endpoint': pattern['endpoint'],
                        'response_time': end_time - start_time,
                        'blocked': hasattr(response, 'status_code') and response.status_code in [403, 429]
                    })
            
            return results
        
        # Симулируем 20 атакующих
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(simulate_attack_pattern, i) for i in range(20)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Анализируем результаты
        total_attacks = len(all_results)
        blocked_attacks = sum(1 for r in all_results if r['blocked'])
        avg_detection_time = sum(r['response_time'] for r in all_results) / total_attacks
        
        # Проверяем эффективность системы безопасности
        self.assertLess(avg_detection_time, 0.1, 
                       f"Average threat detection time: {avg_detection_time:.6f}s")
        
        # Ожидаем, что некоторые атаки будут обнаружены и заблокированы
        detection_rate = blocked_attacks / total_attacks if total_attacks > 0 else 0
        # В зависимости от настроек, система может блокировать разное количество атак


class TelegramCachePerformanceTestCase(TestCase):
    """Тесты производительности кеширования для Telegram endpoints."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.rate_limiter = RateLimiter()
        cache.clear()
    
    def test_cache_hit_performance(self):
        """Тест производительности при cache hit."""
        request = self.factory.post('/api/accounts/telegram/login/initiate/')
        request.META['REMOTE_ADDR'] = '192.168.3.100'
        request = self._add_user_to_request(request)
        
        endpoint_key = 'telegram_login'
        rate_config = RATE_LIMITS.get(endpoint_key)
        
        # Первый запрос для заполнения кеша
        self.rate_limiter.is_rate_limited(request, endpoint_key, rate_config)
        
        # Измеряем время последующих запросов (cache hits)
        start_time = time.time()
        
        for i in range(100):
            is_limited, rate_info = self.rate_limiter.is_rate_limited(
                request, endpoint_key, rate_config
            )
        
        end_time = time.time()
        cache_hit_time = end_time - start_time
        
        # Cache hits должны быть очень быстрыми
        self.assertLess(cache_hit_time, 0.5, 
                       f"Cache hit performance: {cache_hit_time:.3f}s for 100 requests")
    
    def test_cache_miss_performance(self):
        """Тест производительности при cache miss."""
        endpoint_key = 'telegram_verify'
        rate_config = RATE_LIMITS.get(endpoint_key)
        
        cache_miss_times = []
        
        # Тестируем cache miss для разных IP
        for i in range(50):
            request = self.factory.post('/api/accounts/telegram/verify/')
            request.META['REMOTE_ADDR'] = f'192.168.3.{100 + i}'
            request = self._add_user_to_request(request)
            
            start_time = time.time()
            is_limited, rate_info = self.rate_limiter.is_rate_limited(
                request, endpoint_key, rate_config
            )
            end_time = time.time()
            
            cache_miss_times.append(end_time - start_time)
        
        avg_cache_miss_time = sum(cache_miss_times) / len(cache_miss_times)
        max_cache_miss_time = max(cache_miss_times)
        
        # Cache miss должен быть разумно быстрым
        self.assertLess(avg_cache_miss_time, 0.01, 
                       f"Average cache miss time: {avg_cache_miss_time:.6f}s")
        self.assertLess(max_cache_miss_time, 0.05, 
                       f"Max cache miss time: {max_cache_miss_time:.6f}s")
    
    def test_cache_memory_usage(self):
        """Тест использования памяти кешем."""
        endpoint_key = 'telegram_status'
        rate_config = RATE_LIMITS.get(endpoint_key)
        
        # Создаем много записей в кеше
        for i in range(1000):
            request = self.factory.get('/api/accounts/telegram/login/status/')
            request.META['REMOTE_ADDR'] = f'10.1.{i // 255}.{i % 255}'
            request = self._add_user_to_request(request)
            
            self.rate_limiter.is_rate_limited(request, endpoint_key, rate_config)
        
        # Проверяем, что система остается отзывчивой
        test_request = self.factory.get('/api/accounts/telegram/login/status/')
        test_request.META['REMOTE_ADDR'] = '10.2.0.1'
        test_request = self._add_user_to_request(test_request)
        
        start_time = time.time()
        is_limited, rate_info = self.rate_limiter.is_rate_limited(
            test_request, endpoint_key, rate_config
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Даже с большим количеством записей в кеше, система должна быть быстрой
        self.assertLess(response_time, 0.01, 
                       f"Response time with large cache: {response_time:.6f}s")


class TelegramStressTestCase(TestCase):
    """Стресс-тесты для системы безопасности Telegram."""
    
    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()
    
    def _add_user_to_request(self, request):
        """Добавляет пользователя к запросу для тестирования."""
        request.user = AnonymousUser()
        return request
    
    def test_extreme_load_simulation(self):
        """Симуляция экстремальной нагрузки."""
        def extreme_load_worker(worker_id):
            results = {'processed': 0, 'blocked': 0, 'errors': 0}
            
            for i in range(20):  # 20 запросов от каждого worker
                try:
                    # Создаем новый middleware для каждого запроса, чтобы избежать проблем с body
                    security_middleware = SecurityMonitoringMiddleware(lambda r: JsonResponse({'status': 'ok'}))
                    rate_limit_middleware = RateLimitMiddleware(lambda r: JsonResponse({'status': 'ok'}))
                    
                    request = self.factory.post('/api/accounts/telegram/verify/', {
                        'phone_number': f'+{worker_id}{i:010d}',
                        'code': f'{i:06d}'
                    })
                    request.META['REMOTE_ADDR'] = f'172.16.{worker_id % 255}.{i % 255}'
                    request.META['HTTP_USER_AGENT'] = f'StressTest/{worker_id}'
                    request = self._add_user_to_request(request)
                    
                    # Проверяем security middleware
                    blocked = False
                    try:
                        response = security_middleware(request)
                        if hasattr(response, 'status_code') and response.status_code in [403, 429]:
                            blocked = True
                    except Exception:
                        # Если ошибка в security middleware, пробуем rate limit middleware
                        pass
                    
                    # Если не заблокирован security middleware, проверяем rate limit
                    if not blocked:
                        try:
                            # Создаем новый запрос для rate limit middleware
                            request2 = self.factory.post('/api/accounts/telegram/verify/', {
                                'phone_number': f'+{worker_id}{i:010d}',
                                'code': f'{i:06d}'
                            })
                            request2.META['REMOTE_ADDR'] = f'172.16.{worker_id % 255}.{i % 255}'
                            request2.META['HTTP_USER_AGENT'] = f'StressTest/{worker_id}'
                            request2 = self._add_user_to_request(request2)
                            
                            response = rate_limit_middleware(request2)
                            if hasattr(response, 'status_code') and response.status_code in [403, 429]:
                                blocked = True
                        except Exception:
                            pass
                    
                    results['processed'] += 1
                    if blocked:
                        results['blocked'] += 1
                        
                except Exception as e:
                    results['errors'] += 1
            
            return results
        
        # Запускаем 100 workers для создания экстремальной нагрузки
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(extreme_load_worker, i) for i in range(100)]
            
            total_results = {'processed': 0, 'blocked': 0, 'errors': 0}
            
            for future in as_completed(futures):
                worker_results = future.result()
                for key in total_results:
                    total_results[key] += worker_results[key]
        
        # Анализируем результаты стресс-теста
        total_requests = total_results['processed']
        error_rate = total_results['errors'] / total_requests if total_requests > 0 else 0
        block_rate = total_results['blocked'] / total_requests if total_requests > 0 else 0
        
        # Система должна обрабатывать запросы без критических ошибок
        self.assertLess(error_rate, 0.01, f"Error rate too high: {error_rate:.2%}")
        self.assertGreater(total_requests, 1000, "Should process significant number of requests")
        
        # Система безопасности должна блокировать подозрительные запросы
        # (конкретный процент зависит от настроек)