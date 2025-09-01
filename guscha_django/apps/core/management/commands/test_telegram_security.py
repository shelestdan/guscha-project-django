# -*- coding: utf-8 -*-
"""
Django management команда для тестирования системы безопасности Telegram.

Эта команда позволяет запускать различные тесты безопасности
и проверки конфигурации для Telegram endpoints.
"""

import time
import json
from django.core.management.base import BaseCommand, CommandError
from django.test import RequestFactory
from django.core.cache import cache
from django.conf import settings

from apps.core.validation.rate_limiting import RateLimiter, RATE_LIMITS
from apps.core.validation.security_logging import SecurityLogger
from apps.core.middleware.rate_limiting import RateLimitMiddleware
from apps.core.middleware.security_monitoring import SecurityMonitoringMiddleware


class Command(BaseCommand):
    help = 'Тестирование системы безопасности Telegram endpoints'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['rate-limits', 'security-monitoring', 'integration', 'performance', 'all'],
            default='all',
            help='Тип тестов для запуска'
        )
        
        parser.add_argument(
            '--endpoint',
            type=str,
            choices=['telegram_login', 'telegram_verify', 'telegram_status', 'telegram_activate'],
            help='Конкретный endpoint для тестирования'
        )
        
        parser.add_argument(
            '--requests',
            type=int,
            default=10,
            help='Количество тестовых запросов'
        )
        
        parser.add_argument(
            '--ip',
            type=str,
            default='127.0.0.1',
            help='IP адрес для тестирования'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Подробный вывод результатов'
        )
        
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Очистить кеш перед тестированием'
        )
    
    def handle(self, *args, **options):
        if options['clear_cache']:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('Кеш очищен'))
        
        test_type = options['test_type']
        
        self.stdout.write(f"Запуск тестов безопасности Telegram: {test_type}")
        self.stdout.write("=" * 60)
        
        try:
            if test_type == 'rate-limits' or test_type == 'all':
                self.test_rate_limits(options)
            
            if test_type == 'security-monitoring' or test_type == 'all':
                self.test_security_monitoring(options)
            
            if test_type == 'integration' or test_type == 'all':
                self.test_integration(options)
            
            if test_type == 'performance' or test_type == 'all':
                self.test_performance(options)
            
            self.stdout.write(self.style.SUCCESS('\nВсе тесты завершены успешно!'))
            
        except Exception as e:
            raise CommandError(f'Ошибка при выполнении тестов: {str(e)}')
    
    def test_rate_limits(self, options):
        """Тестирование rate limiting."""
        self.stdout.write(self.style.WARNING('\n--- Тестирование Rate Limits ---'))
        
        factory = RequestFactory()
        rate_limiter = RateLimiter()
        
        endpoints_to_test = [
            ('telegram_login', '/api/accounts/telegram/login/initiate/'),
            ('telegram_verify', '/api/accounts/telegram/verify/'),
            ('telegram_status', '/api/accounts/telegram/login/status/'),
            ('telegram_activate', '/api/accounts/telegram/activate/')
        ]
        
        if options['endpoint']:
            endpoints_to_test = [(ep, url) for ep, url in endpoints_to_test 
                               if ep == options['endpoint']]
        
        for endpoint_key, url in endpoints_to_test:
            self.stdout.write(f"\nТестирование endpoint: {endpoint_key} ({url})")
            
            rate_config = RATE_LIMITS.get(endpoint_key)
            if not rate_config:
                self.stdout.write(self.style.ERROR(f"Конфигурация не найдена для {endpoint_key}"))
                continue
            
            max_requests = rate_config.get('requests', 5)
            window_seconds = rate_config.get('window', 60)
            
            self.stdout.write(f"Лимит: {max_requests} запросов за {window_seconds} секунд")
            
            # Тестируем rate limiting
            allowed_count = 0
            blocked_count = 0
            
            for i in range(options['requests']):
                if 'login' in url or 'verify' in url or 'activate' in url:
                    request = factory.post(url, {
                        'phone_number': f'+123456789{i:02d}'
                    })
                else:
                    request = factory.get(url)
                
                request.META['REMOTE_ADDR'] = options['ip']
                request.META['HTTP_USER_AGENT'] = 'TestBot/1.0'
                
                is_limited, rate_info = rate_limiter.is_rate_limited(
                    request, endpoint_key, rate_config
                )
                
                if is_limited:
                    blocked_count += 1
                    if options['verbose']:
                        self.stdout.write(f"  Запрос {i+1}: ЗАБЛОКИРОВАН")
                else:
                    allowed_count += 1
                    if options['verbose']:
                        self.stdout.write(f"  Запрос {i+1}: разрешен")
            
            self.stdout.write(f"Результат: {allowed_count} разрешено, {blocked_count} заблокировано")
            
            # Проверяем корректность работы
            if allowed_count <= max_requests:
                self.stdout.write(self.style.SUCCESS("✓ Rate limiting работает корректно"))
            else:
                self.stdout.write(self.style.ERROR("✗ Rate limiting работает некорректно"))
    
    def test_security_monitoring(self, options):
        """Тестирование security monitoring."""
        self.stdout.write(self.style.WARNING('\n--- Тестирование Security Monitoring ---'))
        
        factory = RequestFactory()
        
        def dummy_view(request):
            from django.http import JsonResponse
            return JsonResponse({'status': 'ok'})
        
        security_middleware = SecurityMonitoringMiddleware(dummy_view)
        
        # Тест 1: Нормальное поведение
        self.stdout.write("\nТест 1: Нормальные запросы")
        normal_request = factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1234567890'
        })
        normal_request.META['REMOTE_ADDR'] = options['ip']
        normal_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        response = security_middleware.process_request(normal_request)
        if response is None:
            self.stdout.write(self.style.SUCCESS("✓ Нормальный запрос разрешен"))
        else:
            self.stdout.write(self.style.ERROR("✗ Нормальный запрос заблокирован"))
        
        # Тест 2: Подозрительные паттерны
        self.stdout.write("\nТест 2: Подозрительные паттерны")
        suspicious_patterns = [
            # Множественные номера телефонов
            [f'+123456789{i:02d}' for i in range(5)],
            # Быстрые запросы
            ['+1111111111'] * 10,
        ]
        
        for pattern_idx, phones in enumerate(suspicious_patterns):
            blocked_count = 0
            
            for phone in phones:
                suspicious_request = factory.post('/api/accounts/telegram/login/initiate/', {
                    'phone_number': phone
                })
                suspicious_request.META['REMOTE_ADDR'] = f'192.168.1.{100 + pattern_idx}'
                suspicious_request.META['HTTP_USER_AGENT'] = 'SuspiciousBot/1.0'
                
                response = security_middleware.process_request(suspicious_request)
                if response is not None:
                    blocked_count += 1
                
                time.sleep(0.01)  # Небольшая задержка
            
            self.stdout.write(f"Паттерн {pattern_idx + 1}: {blocked_count}/{len(phones)} заблокировано")
            
            if blocked_count > 0:
                self.stdout.write(self.style.SUCCESS("✓ Подозрительное поведение обнаружено"))
            else:
                self.stdout.write(self.style.WARNING("⚠ Подозрительное поведение не обнаружено"))
    
    def test_integration(self, options):
        """Тестирование интеграции компонентов."""
        self.stdout.write(self.style.WARNING('\n--- Тестирование Интеграции ---'))
        
        factory = RequestFactory()
        
        def dummy_view(request):
            from django.http import JsonResponse
            return JsonResponse({'status': 'ok'})
        
        # Создаем полный middleware stack
        middleware_stack = [
            SecurityMonitoringMiddleware(dummy_view),
            RateLimitMiddleware(dummy_view)
        ]
        
        def process_through_stack(request):
            for middleware in middleware_stack:
                response = middleware.process_request(request)
                if response:
                    return response
            return None
        
        # Тест полного потока аутентификации
        self.stdout.write("\nТест полного потока аутентификации")
        
        test_ip = '192.168.100.1'
        test_phone = '+1234567890'
        
        # 1. Инициация входа
        login_request = factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': test_phone
        })
        login_request.META['REMOTE_ADDR'] = test_ip
        login_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        login_response = process_through_stack(login_request)
        if login_response is None:
            self.stdout.write(self.style.SUCCESS("✓ Инициация входа разрешена"))
        else:
            self.stdout.write(self.style.ERROR("✗ Инициация входа заблокирована"))
        
        # 2. Проверка статуса
        status_request = factory.get('/api/accounts/telegram/login/status/')
        status_request.META['REMOTE_ADDR'] = test_ip
        status_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        status_response = process_through_stack(status_request)
        if status_response is None:
            self.stdout.write(self.style.SUCCESS("✓ Проверка статуса разрешена"))
        else:
            self.stdout.write(self.style.ERROR("✗ Проверка статуса заблокирована"))
        
        # 3. Верификация
        verify_request = factory.post('/api/accounts/telegram/verify/', {
            'phone_number': test_phone,
            'code': '123456'
        })
        verify_request.META['REMOTE_ADDR'] = test_ip
        verify_request.META['HTTP_USER_AGENT'] = 'TelegramApp/1.0'
        
        verify_response = process_through_stack(verify_request)
        if verify_response is None:
            self.stdout.write(self.style.SUCCESS("✓ Верификация разрешена"))
        else:
            self.stdout.write(self.style.ERROR("✗ Верификация заблокирована"))
    
    def test_performance(self, options):
        """Тестирование производительности."""
        self.stdout.write(self.style.WARNING('\n--- Тестирование Производительности ---'))
        
        factory = RequestFactory()
        rate_limiter = RateLimiter()
        
        # Тест производительности rate limiter
        self.stdout.write("\nТест производительности Rate Limiter")
        
        request = factory.post('/api/accounts/telegram/login/initiate/', {
            'phone_number': '+1234567890'
        })
        request.META['REMOTE_ADDR'] = options['ip']
        request.META['HTTP_USER_AGENT'] = 'TestBot/1.0'
        
        endpoint_key = 'telegram_login'
        rate_config = RATE_LIMITS.get(endpoint_key)
        
        # Измеряем время выполнения
        start_time = time.time()
        
        for i in range(100):
            is_limited, rate_info = rate_limiter.is_rate_limited(
                request, endpoint_key, rate_config
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        self.stdout.write(f"100 проверок выполнено за {total_time:.3f} секунд")
        self.stdout.write(f"Среднее время на проверку: {avg_time:.6f} секунд")
        
        if avg_time < 0.01:
            self.stdout.write(self.style.SUCCESS("✓ Производительность отличная"))
        elif avg_time < 0.05:
            self.stdout.write(self.style.SUCCESS("✓ Производительность хорошая"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Производительность требует оптимизации"))
        
        # Тест производительности с множественными IP
        self.stdout.write("\nТест производительности с множественными IP")
        
        start_time = time.time()
        
        for i in range(50):
            test_request = factory.post('/api/accounts/telegram/login/initiate/', {
                'phone_number': f'+123456789{i:02d}'
            })
            test_request.META['REMOTE_ADDR'] = f'192.168.1.{i}'
            test_request.META['HTTP_USER_AGENT'] = 'TestBot/1.0'
            
            is_limited, rate_info = rate_limiter.is_rate_limited(
                test_request, endpoint_key, rate_config
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 50
        
        self.stdout.write(f"50 проверок с разными IP выполнено за {total_time:.3f} секунд")
        self.stdout.write(f"Среднее время на проверку: {avg_time:.6f} секунд")
        
        if avg_time < 0.01:
            self.stdout.write(self.style.SUCCESS("✓ Масштабируемость отличная"))
        elif avg_time < 0.05:
            self.stdout.write(self.style.SUCCESS("✓ Масштабируемость хорошая"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Масштабируемость требует оптимизации"))
    
    def print_configuration_info(self):
        """Выводит информацию о текущей конфигурации."""
        self.stdout.write(self.style.WARNING('\n--- Конфигурация Системы ---'))
        
        # Информация о rate limits
        self.stdout.write("\nRate Limits конфигурация:")
        for endpoint, config in RATE_LIMITS.items():
            if 'telegram' in endpoint:
                self.stdout.write(f"  {endpoint}: {config['requests']} запросов за {config['window']} сек")
        
        # Информация о настройках Django
        debug_mode = getattr(settings, 'DEBUG', False)
        rate_limit_debug = getattr(settings, 'RATE_LIMIT_IN_DEBUG', False)
        
        self.stdout.write(f"\nDjango DEBUG: {debug_mode}")
        self.stdout.write(f"Rate Limiting в DEBUG: {rate_limit_debug}")
        
        # Информация о кеше
        cache_info = cache._cache if hasattr(cache, '_cache') else 'Неизвестно'
        self.stdout.write(f"Кеш backend: {type(cache).__name__}")