import json
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from ..models.security_report import SecurityBlacklist
from ..services.security_analysis_service import SecurityAnalysisService

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """
    Middleware для проверки безопасности запросов
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_service = SecurityAnalysisService()
        
        # Настройки middleware
        self.enabled = getattr(settings, 'SECURITY_MIDDLEWARE_ENABLED', True)
        self.block_requests = getattr(settings, 'SECURITY_BLOCK_REQUESTS', True)
        self.cache_timeout = getattr(settings, 'SECURITY_CACHE_TIMEOUT', 300)
        
        # Пути, которые нужно проверять
        self.protected_paths = getattr(settings, 'SECURITY_PROTECTED_PATHS', [
            '/api/auth/',
            '/api/registration/',
            '/api/verification/',
            '/api/user/'
        ])
        
        # Пути, которые нужно исключить из проверки
        self.excluded_paths = getattr(settings, 'SECURITY_EXCLUDED_PATHS', [
            '/admin/',
            '/static/',
            '/media/',
            '/api/security/'
        ])
    
    def __call__(self, request):
        """
        Основной метод middleware
        """
        # Проверяем безопасность запроса
        blocked_response = self.process_request(request)
        if blocked_response:
            return blocked_response
        
        # Получаем ответ от следующего middleware/view
        response = self.get_response(request)
        
        # Обрабатываем ответ
        response = self.process_response(request, response)
        
        return response
    
    def process_request(self, request):
        """
        Обрабатывает входящий запрос
        """
        if not self.enabled:
            return None
        
        # Проверяем, нужно ли обрабатывать этот путь
        if not self._should_process_path(request.path):
            return None
        
        # Получаем IP адрес
        ip_address = self._get_client_ip(request)
        
        # Проверяем черный список
        if self._is_blacklisted(ip_address, request):
            logger.warning(f"Blocked request from blacklisted IP: {ip_address}")
            return self._create_blocked_response('IP address is blacklisted')
        
        # Проверяем rate limiting
        if self._check_rate_limit(ip_address, request):
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return self._create_blocked_response('Rate limit exceeded')
        
        return None
    
    def process_response(self, request, response):
        """
        Обрабатывает ответ
        """
        if not self.enabled:
            return response
        
        # Добавляем заголовки безопасности
        self._add_security_headers(response)
        
        return response
    
    def _should_process_path(self, path):
        """
        Определяет, нужно ли обрабатывать данный путь
        """
        # Исключаем определенные пути
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return False
        
        # Проверяем защищенные пути
        for protected_path in self.protected_paths:
            if path.startswith(protected_path):
                return True
        
        return False
    
    def _get_client_ip(self, request):
        """
        Получает IP адрес клиента
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_blacklisted(self, ip_address, request):
        """
        Проверяет, находится ли IP в черном списке
        """
        # Проверяем IP
        if SecurityBlacklist.is_blocked('ip', ip_address):
            return True
        
        # Проверяем User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if user_agent and SecurityBlacklist.is_blocked('user_agent', user_agent):
            return True
        
        return False
    
    def _check_rate_limit(self, ip_address, request):
        """
        Проверяет превышение лимитов запросов
        """
        # Настройки rate limiting
        max_requests_per_minute = getattr(settings, 'SECURITY_MAX_REQUESTS_PER_MINUTE', 60)
        max_requests_per_hour = getattr(settings, 'SECURITY_MAX_REQUESTS_PER_HOUR', 1000)
        
        # Ключи для кеша
        minute_key = f'rate_limit_minute_{ip_address}'
        hour_key = f'rate_limit_hour_{ip_address}'
        
        # Проверяем лимит за минуту
        minute_count = cache.get(minute_key, 0)
        if minute_count >= max_requests_per_minute:
            return True
        
        # Проверяем лимит за час
        hour_count = cache.get(hour_key, 0)
        if hour_count >= max_requests_per_hour:
            return True
        
        # Увеличиваем счетчики
        cache.set(minute_key, minute_count + 1, 60)  # 1 минута
        cache.set(hour_key, hour_count + 1, 3600)    # 1 час
        
        return False
    
    def _create_blocked_response(self, reason):
        """
        Создает ответ для заблокированного запроса
        """
        if not self.block_requests:
            return None
        
        return JsonResponse({
            'error': 'Request blocked',
            'reason': reason,
            'code': 'SECURITY_BLOCK'
        }, status=403)
    
    def _add_security_headers(self, response):
        """
        Добавляет заголовки безопасности к ответу
        """
        if response is None:
            return
            
        # Защита от XSS
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # CSP заголовок
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = "default-src 'self'"
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'


class SecurityReportMiddleware(MiddlewareMixin):
    """
    Middleware для создания отчетов о безопасности
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Обрабатывает входящий запрос для создания отчета
        """
        # Создание отчета о запросе
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Сохраняем информацию в request для последующего использования
        request.security_report_data = {
            'ip_address': ip_address,
            'user_agent': user_agent,
            'path': request.path,
            'method': request.method,
            'timestamp': timezone.now()
        }
        
        return None
    
    def process_response(self, request, response):
        """
        Обрабатывает ответ и создает отчет о безопасности
        """
        if hasattr(request, 'security_report_data'):
            try:
                from ..services.security_report_service import SecurityReportService
                service = SecurityReportService()
                
                # Создаем отчет о безопасности
                service.create_security_report(
                    ip_address=request.security_report_data['ip_address'],
                    user_agent=request.security_report_data['user_agent'],
                    device_fingerprint=request.META.get('HTTP_X_DEVICE_ID', ''),
                    risk_score=self._calculate_risk_score(request, response)
                )
            except Exception as e:
                logger.error(f"Ошибка создания отчета безопасности: {e}")
        
        return response
    
    def _calculate_risk_score(self, request, response):
        """
        Вычисляет оценку риска для запроса
        """
        risk_score = 0
        
        # Увеличиваем риск для неуспешных ответов
        if response.status_code >= 400:
            risk_score += 30
        
        # Увеличиваем риск для подозрительных User Agents
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
        if any(agent in user_agent for agent in suspicious_agents):
            risk_score += 50
        
        # Увеличиваем риск для подозрительных путей
        suspicious_paths = ['/admin/', '/.env', '/wp-admin/']
        if any(path in request.path for path in suspicious_paths):
            risk_score += 40
        
        return min(risk_score, 100)  # Максимальный риск 100
    
    def _get_client_ip(self, request):
        """
        Получает IP адрес клиента
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования событий безопасности
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_logger = logging.getLogger('security')
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Логирует входящие запросы
        """
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Логируем подозрительные запросы
        if self._is_suspicious_request(request):
            self.security_logger.warning(
                f"Подозрительный запрос от {ip_address}: {request.method} {request.path} - {user_agent}"
            )
        
        # Логируем все запросы к защищенным путям
        protected_paths = ['/api/auth/', '/api/registration/', '/api/user/']
        if any(path in request.path for path in protected_paths):
            self.security_logger.info(
                f"Запрос к защищенному пути от {ip_address}: {request.method} {request.path}"
            )
        
        return None
    
    def process_response(self, request, response):
        """
        Логирует ответы на запросы
        """
        ip_address = self._get_client_ip(request)
        
        # Логируем неуспешные ответы
        if response.status_code >= 400:
            self.security_logger.warning(
                f"Неуспешный ответ {response.status_code} для {ip_address}: {request.method} {request.path}"
            )
        
        # Логируем множественные неудачные попытки
        if response.status_code == 401 or response.status_code == 403:
            cache_key = f"failed_attempts_{ip_address}"
            attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attempts, 3600)  # Сохраняем на час
            
            if attempts >= 5:
                self.security_logger.error(
                    f"Множественные неудачные попытки от {ip_address}: {attempts} попыток"
                )
        
        return response
    
    def _is_suspicious_request(self, request):
        """
        Определяет, является ли запрос подозрительным
        """
        # Подозрительные User Agents
        suspicious_user_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'selenium', 'phantomjs'
        ]
        
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        for suspicious_ua in suspicious_user_agents:
            if suspicious_ua in user_agent:
                return True
        
        # Подозрительные пути
        suspicious_paths = [
            '/admin/', '/.env', '/wp-admin/', '/phpmyadmin/',
            '/config/', '/backup/', '/database/'
        ]
        
        for suspicious_path in suspicious_paths:
            if suspicious_path in request.path:
                return True
        
        return False
    
    def _get_client_ip(self, request):
        """
        Получает IP адрес клиента
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_blacklisted(self, ip_address, request):
        """
        Проверяет, находится ли IP в черном списке
        """
        # Проверяем IP
        if SecurityBlacklist.is_blocked('ip', ip_address):
            return True
        
        # Проверяем User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if user_agent and SecurityBlacklist.is_blocked('user_agent', user_agent):
            return True
        
        return False
    
    def _check_rate_limit(self, ip_address, request):
        """
        Проверяет превышение лимитов запросов
        """
        # Настройки rate limiting
        max_requests_per_minute = getattr(settings, 'SECURITY_MAX_REQUESTS_PER_MINUTE', 60)
        max_requests_per_hour = getattr(settings, 'SECURITY_MAX_REQUESTS_PER_HOUR', 1000)
        
        # Ключи для кеша
        minute_key = f'rate_limit_minute_{ip_address}'
        hour_key = f'rate_limit_hour_{ip_address}'
        
        # Проверяем лимит за минуту
        minute_count = cache.get(minute_key, 0)
        if minute_count >= max_requests_per_minute:
            return True
        
        # Проверяем лимит за час
        hour_count = cache.get(hour_key, 0)
        if hour_count >= max_requests_per_hour:
            return True
        
        # Увеличиваем счетчики
        cache.set(minute_key, minute_count + 1, 60)  # 1 минута
        cache.set(hour_key, hour_count + 1, 3600)    # 1 час
        
        return False
    
    def _create_blocked_response(self, reason):
        """
        Создает ответ для заблокированного запроса
        """
        if not self.block_requests:
            return None
        
        return JsonResponse({
            'error': 'Request blocked',
            'reason': reason,
            'code': 'SECURITY_BLOCK'
        }, status=403)
    
    def _add_security_headers(self, response):
        """
        Добавляет заголовки безопасности к ответу
        """
        # Защита от XSS
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # CSP заголовок
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = "default-src 'self'"
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'


class SecurityReportMiddleware(MiddlewareMixin):
    """
    Middleware для автоматической обработки отчетов безопасности
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_service = SecurityAnalysisService()
        
        # Настройки
        self.enabled = getattr(settings, 'SECURITY_REPORT_MIDDLEWARE_ENABLED', True)
        self.auto_block = getattr(settings, 'SECURITY_AUTO_BLOCK_ENABLED', False)
        
        super().__init__(get_response)
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Обрабатывает представление
        """
        if not self.enabled:
            return None
        
        # Проверяем, есть ли данные безопасности в запросе
        security_data = self._extract_security_data(request)
        if not security_data:
            return None
        
        try:
            # Анализируем данные безопасности
            analysis_result = self.security_service.analyze_security_data(security_data)
            
            # Сохраняем результат в атрибутах запроса
            request.security_analysis = analysis_result
            
            # Автоматическая блокировка при высоком риске
            if (self.auto_block and 
                analysis_result.get('recommended_action') == 'block'):
                
                logger.warning(
                    f"Auto-blocking request due to high risk: {analysis_result.get('overall_risk', {}).get('score', 0)}"
                )
                
                return JsonResponse({
                    'error': 'Request blocked due to security analysis',
                    'code': 'SECURITY_AUTO_BLOCK'
                }, status=403)
        
        except Exception as e:
            logger.error(f"Error in security analysis: {str(e)}")
            # При ошибке анализа не блокируем запрос
        
        return None
    
    def _extract_security_data(self, request):
        """
        Извлекает данные безопасности из запроса
        """
        # Проверяем заголовки
        security_header = request.META.get('HTTP_X_SECURITY_DATA')
        if security_header:
            try:
                return json.loads(security_header)
            except json.JSONDecodeError:
                pass
        
        # Проверяем POST данные
        if request.method == 'POST' and hasattr(request, 'body'):
            try:
                body_data = json.loads(request.body)
                if 'securityData' in body_data:
                    return body_data['securityData']
            except (json.JSONDecodeError, AttributeError):
                pass
        
        return None


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования событий безопасности
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'SECURITY_LOGGING_ENABLED', True)
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Логирует входящие запросы
        """
        if not self.enabled:
            return None
        
        # Логируем подозрительные запросы
        if self._is_suspicious_request(request):
            logger.warning(
                f"Suspicious request detected: {request.method} {request.path} "
                f"from {self._get_client_ip(request)} "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
            )
        
        return None
    
    def process_response(self, request, response):
        """
        Логирует ответы
        """
        if not self.enabled:
            return response
        
        # Логируем заблокированные запросы
        if response.status_code == 403:
            logger.warning(
                f"Request blocked: {request.method} {request.path} "
                f"from {self._get_client_ip(request)} "
                f"Status: {response.status_code}"
            )
        
        return response
    
    def _is_suspicious_request(self, request):
        """
        Определяет, является ли запрос подозрительным
        """
        # Подозрительные User Agents
        suspicious_user_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'selenium', 'phantomjs'
        ]
        
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        for suspicious_ua in suspicious_user_agents:
            if suspicious_ua in user_agent:
                return True
        
        # Подозрительные пути
        suspicious_paths = [
            '/admin/', '/.env', '/wp-admin/', '/phpmyadmin/',
            '/config/', '/backup/', '/database/'
        ]
        
        for suspicious_path in suspicious_paths:
            if suspicious_path in request.path:
                return True
        
        # Подозрительные параметры
        suspicious_params = ['<script', 'javascript:', 'eval(', 'union select']
        query_string = request.META.get('QUERY_STRING', '').lower()
        
        for suspicious_param in suspicious_params:
            if suspicious_param in query_string:
                return True
        
        return False
    
    def _get_client_ip(self, request):
        """
        Получает IP адрес клиента
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip