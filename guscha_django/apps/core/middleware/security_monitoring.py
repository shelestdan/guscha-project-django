"""Security Monitoring Middleware

This middleware integrates the security monitoring system into Django's
request/response cycle for real-time threat detection and response.
"""

import logging
import time
from typing import Callable, Optional
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from apps.core.utils.security_logger import security_logger
from apps.core.monitoring.security_monitor import security_monitor


class SecurityMonitoringMiddleware(MiddlewareMixin):
    """Middleware for real-time security monitoring and threat detection"""
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.logger = logging.getLogger('security')
        
        # Configuration
        self.enabled = getattr(settings, 'SECURITY_MONITORING_ENABLED', True)
        self.debug_bypass = getattr(settings, 'SECURITY_MONITORING_DEBUG_BYPASS', True)
        self.excluded_paths = getattr(settings, 'SECURITY_MONITORING_EXCLUDED_PATHS', [
            '/admin/jsi18n/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
            '/health/',
            '/metrics/'
        ])
        self.excluded_user_agents = getattr(settings, 'SECURITY_MONITORING_EXCLUDED_USER_AGENTS', [
            'HealthCheck',
            'ELB-HealthChecker',
            'GoogleHC'
        ])
        
        super().__init__(get_response)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request through security monitoring"""
        # Skip if disabled or in debug mode with bypass enabled
        if not self.enabled or (settings.DEBUG and self.debug_bypass):
            return self.get_response(request)
        
        # Skip excluded paths and user agents
        if self._should_skip_monitoring(request):
            return self.get_response(request)
        
        # Record request start time
        start_time = time.time()
        
        # Process request for security threats
        should_block, threats = security_monitor.process_request(request)
        
        # Специальная проверка для Telegram endpoints
        telegram_threat = self._detect_telegram_threats(request)
        if telegram_threat:
            threats = threats or []
            threats.append(telegram_threat)
            should_block = telegram_threat.get('severity') == 'HIGH'
        
        # Block request if threat detected
        if should_block:
            # Логируем каждую угрозу отдельно
            for threat in threats:
                self._log_threat(
                    request, 
                    threat.get('type', 'unknown_threat'),
                    threat.get('details', {}),
                    threat.get('severity', 'MEDIUM')
                )
            
            # Логируем блокировку через security logger
            security_logger.log_access_denied(
                request,
                'security_threat_detected',
                {'threats': threats, 'blocked': True}
            )
            
            self.logger.warning(
                f"Blocked request from {self._get_client_ip(request)} due to security threats"
            )
            return self._create_blocked_response(request, threats)
        
        # Continue with normal request processing
        response = self.get_response(request)
        
        # Log request completion time
        processing_time = time.time() - start_time
        if processing_time > 5.0:  # Log slow requests
            self.logger.info(
                f"Slow request detected: {request.path} took {processing_time:.2f}s"
            )
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """Handle exceptions that might indicate security issues"""
        if not self.enabled:
            return None
        
        # Log suspicious exceptions
        suspicious_exceptions = [
            'SuspiciousOperation',
            'PermissionDenied',
            'ValidationError',
            'DisallowedHost'
        ]
        
        exception_name = exception.__class__.__name__
        if exception_name in suspicious_exceptions:
            # Определяем серьезность исключения
            severity = 'MEDIUM'
            if exception_name in ['SuspiciousOperation', 'DisallowedHost']:
                severity = 'HIGH'
            
            # Используем новый security logger
            security_logger.log_threat_detected(
                request, 
                f"suspicious_exception_{exception_name.lower()}", 
                severity,
                {'exception': str(exception)}
            )
            
            # Также логируем как подозрительную активность
            risk_score = 70 if severity == 'HIGH' else 50
            security_logger.log_suspicious_activity(
                request,
                f"suspicious_exception_{exception_name.lower()}",
                {'exception': str(exception)},
                risk_score
            )
            
            # Report as security event
            security_monitor.report_suspicious_activity(
                request,
                f"suspicious_exception_{exception_name.lower()}",
                {'exception': str(exception)}
            )
            
            # Логируем через новый метод _log_threat
            self._log_threat(
                request,
                f"suspicious_exception_{exception_name.lower()}",
                {'exception': str(exception)},
                severity
            )
        
        return response
    
    def _detect_telegram_threats(self, request: HttpRequest) -> Optional[dict]:
        """
        Обнаруживает специфичные угрозы для Telegram endpoints.
        
        Args:
            request: HTTP запрос
            
        Returns:
            Словарь с информацией об угрозе или None
        """
        # Проверяем только Telegram endpoints
        if not self._is_telegram_endpoint(request.path):
            return None
        
        threats = []
        ip_address = self._get_client_ip(request)
        
        # 1. Проверка на множественные номера телефонов с одного IP
        phone_threat = self._check_multiple_phones_per_ip(request, ip_address)
        if phone_threat:
            threats.append(phone_threat)
        
        # 2. Проверка на слишком быстрые запросы
        rapid_requests_threat = self._check_rapid_telegram_requests(request, ip_address)
        if rapid_requests_threat:
            threats.append(rapid_requests_threat)
        
        # 3. Проверка на подозрительные паттерны в данных Telegram
        data_threat = self._check_telegram_data_patterns(request)
        if data_threat:
            threats.append(data_threat)
        
        # 4. Проверка на bot-подобное поведение
        bot_threat = self._check_bot_behavior(request, ip_address)
        if bot_threat:
            threats.append(bot_threat)
        
        if threats:
            # Определяем максимальную серьезность
            max_severity = max(threat.get('severity', 'LOW') for threat in threats)
            
            # Логируем через security_logger
            from apps.core.validation.security_logging import SecurityLogger
            logger = SecurityLogger()
            
            for threat in threats:
                logger.log_telegram_suspicious_pattern(
                    request=request,
                    pattern_type=threat.get('pattern_type', 'unknown'),
                    details=threat.get('details', {})
                )
            
            return {
                'type': 'telegram_threat',
                'severity': max_severity,
                'threats': threats,
                'count': len(threats)
            }
        
        return None
    
    def _is_telegram_endpoint(self, path: str) -> bool:
        """
        Проверяет, является ли путь Telegram endpoint.
        
        Args:
            path: Путь запроса
            
        Returns:
            True если это Telegram endpoint
        """
        telegram_patterns = [
            '/api/accounts/telegram/',
            '/api/auth/telegram/',
            '/telegram/',
            '/api/telegram/'
        ]
        
        return any(pattern in path for pattern in telegram_patterns)
    
    def _check_multiple_phones_per_ip(self, request: HttpRequest, ip_address: str) -> Optional[dict]:
        """
        Проверяет использование множественных номеров телефонов с одного IP.
        
        Args:
            request: HTTP запрос
            ip_address: IP адрес
            
        Returns:
            Информация об угрозе или None
        """
        if request.method != 'POST':
            return None
        
        try:
            # Получаем номер телефона из данных запроса
            phone_number = None
            
            # Сначала пробуем получить из POST данных
            if hasattr(request, 'POST') and request.POST:
                phone_number = request.POST.get('phone') or request.POST.get('phone_number')
            
            # Если не найден в POST, пробуем JSON body (только если еще не читали)
            if not phone_number and hasattr(request, '_body') and request._body:
                import json
                try:
                    data = json.loads(request._body)
                    phone_number = data.get('phone') or data.get('phone_number')
                except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                    pass
            
            if not phone_number:
                return None
            
            # Проверяем кэш для этого IP
            cache_key = f'telegram_phones:{ip_address}'
            phones_for_ip = cache.get(cache_key, set())
            
            if isinstance(phones_for_ip, list):
                phones_for_ip = set(phones_for_ip)
            
            phones_for_ip.add(phone_number)
            cache.set(cache_key, list(phones_for_ip), 3600)  # 1 час
            
            # Если с одного IP используется более 3 номеров за час
            if len(phones_for_ip) > 3:
                return {
                    'pattern_type': 'multiple_phones',
                    'severity': 'HIGH',
                    'details': {
                        'ip_address': ip_address,
                        'phone_count': len(phones_for_ip),
                        'current_phone': phone_number[:3] + '*' * (len(phone_number) - 6) + phone_number[-3:] if len(phone_number) > 6 else '*' * len(phone_number)
                    }
                }
        
        except Exception as e:
            self.logger.error(f"Error checking multiple phones: {e}")
        
        return None
    
    def _check_rapid_telegram_requests(self, request: HttpRequest, ip_address: str) -> Optional[dict]:
        """
        Проверяет слишком быстрые запросы к Telegram endpoints.
        
        Args:
            request: HTTP запрос
            ip_address: IP адрес
            
        Returns:
            Информация об угрозе или None
        """
        cache_key = f'telegram_requests:{ip_address}'
        request_times = cache.get(cache_key, [])
        
        current_time = time.time()
        
        # Удаляем запросы старше 1 минуты
        request_times = [t for t in request_times if current_time - t < 60]
        request_times.append(current_time)
        
        cache.set(cache_key, request_times, 300)  # 5 минут
        
        # Если более 10 запросов за минуту
        if len(request_times) > 10:
            return {
                'pattern_type': 'rapid_requests',
                'severity': 'MEDIUM',
                'details': {
                    'ip_address': ip_address,
                    'requests_per_minute': len(request_times),
                    'threshold': 10
                }
            }
        
        return None
    
    def _check_telegram_data_patterns(self, request: HttpRequest) -> Optional[dict]:
        """
        Проверяет подозрительные паттерны в данных Telegram.
        
        Args:
            request: HTTP запрос
            
        Returns:
            Информация об угрозе или None
        """
        if request.method != 'POST' or not hasattr(request, 'body'):
            return None
        
        try:
            import json
            data = json.loads(request.body)
            
            # Проверяем наличие обязательных полей Telegram
            telegram_fields = ['id', 'first_name', 'auth_date', 'hash']
            missing_fields = [field for field in telegram_fields if field not in data]
            
            if missing_fields:
                return {
                    'pattern_type': 'invalid_token',
                    'severity': 'HIGH',
                    'details': {
                        'missing_fields': missing_fields,
                        'provided_fields': list(data.keys())
                    }
                }
            
            # Проверяем временные метки
            auth_date = data.get('auth_date')
            if auth_date:
                try:
                    auth_timestamp = int(auth_date)
                    current_timestamp = int(time.time())
                    
                    # Если auth_date слишком старый (более 24 часов) или из будущего
                    if abs(current_timestamp - auth_timestamp) > 86400:
                        return {
                            'pattern_type': 'suspicious_timing',
                            'severity': 'MEDIUM',
                            'details': {
                                'auth_date': auth_timestamp,
                                'current_time': current_timestamp,
                                'time_diff': abs(current_timestamp - auth_timestamp)
                            }
                        }
                except (ValueError, TypeError):
                    return {
                        'pattern_type': 'invalid_token',
                        'severity': 'HIGH',
                        'details': {
                            'invalid_auth_date': str(auth_date)
                        }
                    }
        
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {
                'pattern_type': 'invalid_token',
                'severity': 'HIGH',
                'details': {
                    'error': 'Invalid JSON in request body'
                }
            }
        except Exception as e:
            self.logger.error(f"Error checking Telegram data patterns: {e}")
        
        return None
    
    def _check_bot_behavior(self, request: HttpRequest, ip_address: str) -> Optional[dict]:
        """
        Проверяет bot-подобное поведение.
        
        Args:
            request: HTTP запрос
            ip_address: IP адрес
            
        Returns:
            Информация об угрозе или None
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Подозрительные User-Agent'ы
        suspicious_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python', 'requests'
        ]
        
        if any(agent.lower() in user_agent.lower() for agent in suspicious_agents):
            return {
                'pattern_type': 'bot_like_behavior',
                'severity': 'HIGH',
                'details': {
                    'user_agent': user_agent,
                    'ip_address': ip_address
                }
            }
        
        # Проверяем отсутствие стандартных браузерных заголовков
        browser_headers = ['HTTP_ACCEPT', 'HTTP_ACCEPT_LANGUAGE', 'HTTP_ACCEPT_ENCODING']
        missing_headers = [header for header in browser_headers if not request.META.get(header)]
        
        if len(missing_headers) >= 2:
            return {
                'pattern_type': 'bot_like_behavior',
                'severity': 'MEDIUM',
                'details': {
                    'missing_headers': missing_headers,
                    'user_agent': user_agent
                }
            }
        
        return None
    
    def _should_skip_monitoring(self, request: HttpRequest) -> bool:
        """Determine if request should skip security monitoring"""
        # Skip excluded paths
        for path in self.excluded_paths:
            if request.path.startswith(path):
                return True
        
        # Skip excluded user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        for excluded_agent in self.excluded_user_agents:
            if excluded_agent.lower() in user_agent.lower():
                return True
        
        # Skip superusers if configured
        if (hasattr(request, 'user') and 
            request.user.is_authenticated and 
            request.user.is_superuser and 
            getattr(settings, 'SECURITY_MONITORING_SKIP_SUPERUSERS', True)):
            return True
        
        return False
    
    def _create_blocked_response(self, request: HttpRequest, threats: list) -> HttpResponse:
        """Create response for blocked requests"""
        client_ip = self._get_client_ip(request)
        
        # Determine if this is an API request
        is_api_request = (
            request.path.startswith('/api/') or
            request.META.get('HTTP_ACCEPT', '').startswith('application/json') or
            request.META.get('CONTENT_TYPE', '').startswith('application/json')
        )
        
        if is_api_request:
            return JsonResponse({
                'error': 'Access Denied',
                'message': 'Your request has been blocked due to security policy violations.',
                'code': 'SECURITY_BLOCK',
                'timestamp': time.time(),
                'request_id': getattr(request, 'id', 'unknown')
            }, status=403)
        else:
            # Return HTML response for web requests
            context = {
                'client_ip': client_ip,
                'timestamp': time.time(),
                'support_email': getattr(settings, 'SECURITY_SUPPORT_EMAIL', 'support@example.com')
            }
            return render(request, 'security/blocked.html', context, status=403)
    
    def _log_threat(self, request: HttpRequest, threat_type: str, 
                   details: dict, severity: str = 'MEDIUM') -> None:
        """Логировать обнаруженную угрозу."""
        try:
            # Определяем риск-скор на основе серьезности
            risk_score = self._calculate_risk_score(threat_type, severity, details)
            
            # Логируем через security logger
            security_logger.log_threat_detected(
                request, threat_type, severity, details
            )
            
            # Записываем в систему мониторинга
            ip_address = self._get_client_ip(request)
            security_monitor.record_threat(
                threat_type, ip_address, risk_score, details
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log threat: {e}")
    
    def _calculate_risk_score(self, threat_type: str, severity: str, details: dict) -> int:
        """Вычислить риск-скор на основе типа угрозы и серьезности."""
        base_scores = {
            'sql_injection': 90,
            'xss_attack': 80,
            'brute_force': 70,
            'suspicious_activity': 60,
            'rate_limit_exceeded': 50,
            'invalid_input': 40
        }
        
        severity_multipliers = {
            'HIGH': 1.2,
            'MEDIUM': 1.0,
            'LOW': 0.8
        }
        
        base_score = base_scores.get(threat_type, 50)
        multiplier = severity_multipliers.get(severity, 1.0)
        
        return min(100, int(base_score * multiplier))
    
    def _add_security_headers(self, response: HttpResponse) -> None:
        """Add security headers to response"""
        # Add security monitoring headers
        response['X-Security-Monitor'] = 'active'
        response['X-Request-ID'] = getattr(response, 'request_id', 'unknown')
        
        # Add additional security headers if not already present
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        for header, value in security_headers.items():
            if header not in response:
                response[header] = value
    
    def _log_request_audit(self, request: HttpRequest) -> None:
        """Логировать запрос через security logger для аудита."""
        try:
            # Определяем тип действия на основе пути и метода
            action = self._determine_audit_action(request)
            resource = self._determine_resource(request)
            
            # Собираем метаданные запроса
            metadata = {
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'content_type': request.content_type,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', ''),
            }
            
            # Логируем через security logger
            security_logger.log_audit_event(
                request, action, resource, 
                user=getattr(request, 'user', None),
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log request audit: {e}")
    
    def _log_response_audit(self, request: HttpRequest, response: HttpResponse) -> None:
        """Логировать ответ через security logger для аудита."""
        try:
            # Определяем тип действия на основе пути и метода
            action = f"{self._determine_audit_action(request)}_response"
            resource = self._determine_resource(request)
            
            # Собираем метаданные ответа
            metadata = {
                'status_code': response.status_code,
                'content_type': response.get('Content-Type', ''),
                'content_length': response.get('Content-Length', ''),
                'success': 200 <= response.status_code < 400,
            }
            
            # Логируем через security logger
            security_logger.log_audit_event(
                request, action, resource,
                user=getattr(request, 'user', None),
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log response audit: {e}")
    
    def _determine_audit_action(self, request: HttpRequest) -> str:
        """Определить тип действия для аудита."""
        method = request.method.lower()
        path = request.path.lower()
        
        if '/auth/' in path:
            if method == 'post':
                return 'authentication_attempt'
            elif method == 'delete':
                return 'logout'
        elif '/admin/' in path:
            return f'admin_{method}'
        elif '/api/users/' in path:
            return f'user_management_{method}'
        elif '/api/orders/' in path:
            return f'order_management_{method}'
        elif '/api/payments/' in path:
            return f'payment_operation_{method}'
        
        return f'sensitive_operation_{method}'
    
    def _determine_resource(self, request: HttpRequest) -> str:
        """Определить ресурс для аудита."""
        path = request.path
        
        if '/admin/' in path:
            return 'admin_panel'
        elif '/api/auth/' in path:
            return 'authentication_system'
        elif '/api/users/' in path:
            return 'user_data'
        elif '/api/orders/' in path:
            return 'order_data'
        elif '/api/payments/' in path:
            return 'payment_system'
        
        return path
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class SecurityMetricsMiddleware(MiddlewareMixin):
    """Middleware for collecting security metrics"""
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.enabled = getattr(settings, 'SECURITY_METRICS_ENABLED', True)
        self.logger = logging.getLogger('security.metrics')
        super().__init__(get_response)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Collect security metrics"""
        if not self.enabled:
            return self.get_response(request)
        
        start_time = time.time()
        
        # Record request metrics
        self._record_request_metrics(request)
        
        response = self.get_response(request)
        
        # Record response metrics
        processing_time = time.time() - start_time
        self._record_response_metrics(request, response)
        
        # Логируем метрики через security logger
        self._log_security_metrics(request, response, processing_time)
        
        return response
    
    def _record_request_metrics(self, request: HttpRequest) -> None:
        """Record request-level security metrics"""
        try:
            # Increment request counters
            cache.set('security_metrics:total_requests', 
                     cache.get('security_metrics:total_requests', 0) + 1, 
                     86400)  # 24 hours
            
            # Track unique IPs
            client_ip = self._get_client_ip(request)
            ip_key = f'security_metrics:ip:{client_ip}'
            if not cache.get(ip_key):
                cache.set(ip_key, True, 86400)
                cache.set('security_metrics:unique_ips',
                         cache.get('security_metrics:unique_ips', 0) + 1,
                         86400)
            
            # Track endpoints
            endpoint_key = f'security_metrics:endpoint:{request.path}'
            cache.set(endpoint_key,
                     cache.get(endpoint_key, 0) + 1,
                     86400)
            
        except Exception as e:
            logging.getLogger('security').error(
                f"Failed to record request metrics: {e}"
            )
    
    def _record_response_metrics(self, request: HttpRequest, response: HttpResponse) -> None:
        """Record response-level security metrics"""
        try:
            # Track error responses
            if response.status_code >= 400:
                error_key = f'security_metrics:errors:{response.status_code}'
                cache.set(error_key,
                         cache.get(error_key, 0) + 1,
                         86400)
            
            # Track authentication failures
            if response.status_code == 401:
                cache.set('security_metrics:auth_failures',
                         cache.get('security_metrics:auth_failures', 0) + 1,
                         86400)
            
            # Track permission denials
            if response.status_code == 403:
                cache.set('security_metrics:permission_denials',
                         cache.get('security_metrics:permission_denials', 0) + 1,
                         86400)
                
        except Exception as e:
            logging.getLogger('security').error(
                f"Failed to record response metrics: {e}"
            )
    
    def _log_security_metrics(self, request: HttpRequest, response: HttpResponse, processing_time: float) -> None:
        """Log security metrics through security logger"""
        try:
            metrics_data = {
                'processing_time': processing_time,
                'status_code': response.status_code,
                'method': request.method,
                'path': request.path,
                'client_ip': self._get_client_ip(request),
                'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            }
            
            # Логируем через security logger для централизованного мониторинга
            security_logger.log_security_event(
                request,
                'security_metrics_collected',
                metrics_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log security metrics: {e}")
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class SecurityAuditMiddleware(MiddlewareMixin):
    """Middleware for security audit logging"""
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.logger = logging.getLogger('security_audit')
        self.enabled = getattr(settings, 'SECURITY_AUDIT_ENABLED', True)
        
        # Sensitive endpoints to audit
        self.audit_endpoints = getattr(settings, 'SECURITY_AUDIT_ENDPOINTS', [
            '/api/accounts/login/',
            '/api/accounts/register/',
            '/api/accounts/password/',
            '/api/orders/',
            '/api/payments/',
            '/admin/'
        ])
        
        super().__init__(get_response)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Audit security-sensitive requests"""
        if not self.enabled:
            return self.get_response(request)
        
        # Check if this endpoint should be audited
        should_audit = any(request.path.startswith(endpoint) for endpoint in self.audit_endpoints)
        
        if should_audit:
            # Логируем запрос
            self._audit_request(request)
        
        response = self.get_response(request)
        
        if should_audit:
            # Логируем ответ
            self._audit_response(request, response)
        
        return response
    
    def _audit_request(self, request: HttpRequest) -> None:
        """Audit incoming request"""
        try:
            audit_data = {
                'timestamp': time.time(),
                'method': request.method,
                'path': request.path,
                'client_ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                'session_key': request.session.session_key if hasattr(request, 'session') else None,
                'content_type': request.META.get('CONTENT_TYPE', ''),
                'content_length': request.META.get('CONTENT_LENGTH', 0)
            }
            
            # Логируем через security logger для централизованного аудита
            security_logger.log_security_event(
                request,
                'audit_request',
                audit_data
            )
            
            self.logger.info(
                f"[AUDIT_REQUEST] {audit_data['method']} {audit_data['path']} | "
                f"IP: {audit_data['client_ip']} | User: {audit_data['user_id']}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to audit request: {e}")
    
    def _audit_response(self, request: HttpRequest, response: HttpResponse) -> None:
        """Audit response"""
        try:
            audit_data = {
                'timestamp': time.time(),
                'status_code': response.status_code,
                'content_type': response.get('Content-Type', ''),
                'content_length': len(response.content) if hasattr(response, 'content') else 0
            }
            
            # Логируем через security logger для централизованного аудита
            security_logger.log_security_event(
                request,
                'audit_response',
                audit_data
            )
            
            self.logger.info(
                f"[AUDIT_RESPONSE] {request.method} {request.path} | "
                f"Status: {audit_data['status_code']} | Size: {audit_data['content_length']}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to audit response: {e}")
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')