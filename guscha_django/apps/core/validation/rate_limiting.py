import time
import hashlib
from typing import Dict, Tuple, Optional
from django.core.cache import cache
from django.http import HttpRequest
from django.conf import settings
from .security_logging import SecurityLogger


class RateLimiter:
    """
    Advanced rate limiter with sliding window and burst protection
    """
    
    def __init__(self):
        self.security_logger = SecurityLogger()
        self.cache_prefix = 'rate_limit:'
        self.cache_timeout = 3600  # 1 hour
    
    def get_client_identifier(self, request: HttpRequest) -> str:
        """
        Get unique client identifier for rate limiting
        """
        # Try to get real IP from headers (for proxy/load balancer setups)
        real_ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or
            request.META.get('HTTP_X_REAL_IP', '') or
            request.META.get('REMOTE_ADDR', '')
        )
        
        # Include user ID if authenticated for more precise limiting
        user_id = str(request.user.id) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
        
        # Create composite identifier
        identifier = f"{real_ip}:{user_id}:{request.META.get('HTTP_USER_AGENT', '')[:50]}"
        
        # Hash to avoid cache key issues
        return hashlib.md5(identifier.encode()).hexdigest()
    
    def parse_rate_limit(self, rate_string: str) -> Tuple[int, int]:
        """
        Parse rate limit string like '5/min' or '100/hour'
        Returns (requests, seconds)
        """
        try:
            requests, period = rate_string.split('/')
            requests = int(requests)
            
            period_map = {
                'sec': 1, 'second': 1,
                'min': 60, 'minute': 60,
                'hour': 3600, 'hr': 3600,
                'day': 86400
            }
            
            seconds = period_map.get(period.lower(), 60)
            return requests, seconds
        except (ValueError, KeyError):
            # Default to 60 requests per minute if parsing fails
            return 60, 60
    
    def is_rate_limited(self, request: HttpRequest, endpoint: str, 
                       rate_config: Dict[str, any]) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request should be rate limited
        Returns (is_limited, rate_info)
        """
        client_id = self.get_client_identifier(request)
        rate_string = rate_config.get('rate', '60/min')
        burst_limit = rate_config.get('burst', 100)
        
        requests_allowed, window_seconds = self.parse_rate_limit(rate_string)
        
        # Create cache keys
        rate_key = f"{self.cache_prefix}{endpoint}:{client_id}:rate"
        burst_key = f"{self.cache_prefix}{endpoint}:{client_id}:burst"
        
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        # Get current request timestamps from cache
        request_times = cache.get(rate_key, [])
        burst_count = cache.get(burst_key, 0)
        
        # Clean old requests outside the window
        request_times = [t for t in request_times if t > window_start]
        
        # Check rate limit
        rate_limited = len(request_times) >= requests_allowed
        
        # Check burst limit
        burst_limited = burst_count >= burst_limit
        
        rate_info = {
            'endpoint': endpoint,
            'client_id': client_id[:8],  # Truncated for logging
            'requests_in_window': len(request_times),
            'requests_allowed': requests_allowed,
            'window_seconds': window_seconds,
            'burst_count': burst_count,
            'burst_limit': burst_limit,
            'reset_time': window_start + window_seconds,
            'retry_after': max(1, min(request_times) + window_seconds - current_time) if request_times else 0
        }
        
        if rate_limited or burst_limited:
            # Log rate limit violation
            self.security_logger.log_rate_limit_exceeded(
                request, endpoint, rate_info['requests_in_window'], rate_info['requests_allowed']
            )
            return True, rate_info
        
        # Update counters
        request_times.append(current_time)
        cache.set(rate_key, request_times, self.cache_timeout)
        cache.set(burst_key, burst_count + 1, 60)  # Burst counter resets every minute
        
        return False, rate_info
    
    def get_rate_limit_headers(self, rate_info: Dict[str, any]) -> Dict[str, str]:
        """
        Generate rate limit headers for response
        """
        return {
            'X-RateLimit-Limit': str(rate_info['requests_allowed']),
            'X-RateLimit-Remaining': str(max(0, rate_info['requests_allowed'] - rate_info['requests_in_window'])),
            'X-RateLimit-Reset': str(rate_info['reset_time']),
            'X-RateLimit-Window': str(rate_info['window_seconds']),
            'Retry-After': str(rate_info['retry_after']) if rate_info['retry_after'] > 0 else '1'
        }


# Rate limiting configuration based on actual API endpoints
RATE_LIMITS = {
    # Authentication endpoints - /api/accounts/
    'auth_login': {'rate': '5/min', 'burst': 10},  # POST /api/accounts/login/
    'auth_register': {'rate': '3/min', 'burst': 5},  # POST /api/accounts/register/
    'password_reset': {'rate': '3/min', 'burst': 5},  # POST /api/accounts/password/reset/
    'password_change': {'rate': '5/min', 'burst': 8},  # POST /api/accounts/password/change/
    'jwt_token': {'rate': '10/min', 'burst': 15},  # POST /api/accounts/token/
    'jwt_refresh': {'rate': '20/min', 'burst': 30},  # POST /api/accounts/token/refresh/
    
    # Order and Payment endpoints - /api/orders/
    'order_create': {'rate': '10/min', 'burst': 15},  # POST /api/orders/
    'order_cancel': {'rate': '5/min', 'burst': 8},   # POST /api/orders/{id}/cancel/
    'payment_initiate': {'rate': '5/min', 'burst': 8},  # POST /api/orders/{id}/pay/
    'payment_status': {'rate': '30/min', 'burst': 50},  # GET /api/orders/{id}/payment-status/
    
    # Cart operations - /api/cart/
    'cart_add': {'rate': '30/min', 'burst': 50},     # POST /api/cart/add/
    'cart_update': {'rate': '30/min', 'burst': 50},  # PUT /api/cart/update/{id}/
    'cart_clear': {'rate': '10/min', 'burst': 15},   # POST /api/cart/clear/
    'cart_reservations': {'rate': '10/min', 'burst': 15},  # POST /api/cart/create-reservations/
    
    # Address management - /api/addresses/
    'address_create': {'rate': '10/min', 'burst': 15},  # POST /api/addresses/
    'address_update': {'rate': '15/min', 'burst': 20},  # PUT /api/addresses/{id}/
    
    # User profile and statistics
    'user_profile': {'rate': '30/min', 'burst': 50},    # GET/PUT /api/accounts/me/
    'user_statistics': {'rate': '20/min', 'burst': 30}, # GET /api/accounts/user_statistics/
    
    # Telegram endpoints - критически важные для безопасности
    'telegram_login': {'rate': '10/min', 'burst': 15},      # POST /api/accounts/telegram/login/initiate/
    'telegram_status': {'rate': '20/min', 'burst': 30},     # GET /api/accounts/telegram/login/status/
    'telegram_activate': {'rate': '5/min', 'burst': 8},     # POST /api/accounts/telegram/activate/
    'telegram_verify': {'rate': '10/min', 'burst': 15},     # POST /api/accounts/telegram/verify/
    'telegram_link': {'rate': '5/min', 'burst': 8},         # POST /api/accounts/telegram/link/
    'telegram_unlink': {'rate': '5/min', 'burst': 8},       # POST /api/accounts/telegram/unlink/
    'telegram_password_reset': {'rate': '3/min', 'burst': 5}, # POST /api/accounts/telegram/password-reset/
    
    # IP-based ограничения для Telegram (предотвращение обхода через разные номера)
    'telegram_ip_phone_limit': {'rate': '5/hour', 'burst': 8},  # Максимум 5 разных номеров с одного IP за час
    'telegram_ip_attempts': {'rate': '20/hour', 'burst': 30},   # Общий лимит попыток с одного IP
    
    # General API endpoints
    'api_general': {'rate': '100/min', 'burst': 150},
    'api_upload': {'rate': '20/min', 'burst': 30},
    
    # Admin endpoints
    'admin_api': {'rate': '200/min', 'burst': 300},
    'admin_orders': {'rate': '50/min', 'burst': 75},  # Admin order management
}


def get_client_ip(request: HttpRequest) -> str:
    """
    Получает IP адрес клиента с учетом прокси и load balancer
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')
    return ip


def check_telegram_ip_restrictions(request, phone_number=None):
    """
    Проверяет IP-based ограничения для Telegram endpoints
    
    Args:
        request: Django request объект
        phone_number: Номер телефона (для отслеживания уникальных номеров с IP)
    
    Returns:
        tuple: (is_restricted, restriction_info)
    """
    client_ip = get_client_ip(request)
    
    # Проверяем общий лимит попыток с IP
    attempts_key = f"telegram_ip_attempts:{client_ip}"
    current_attempts = cache.get(attempts_key, 0)
    
    if current_attempts >= 20:  # Лимит из конфигурации telegram_ip_attempts
        return True, {
            'type': 'ip_attempts_exceeded',
            'message': 'Превышен лимит попыток с данного IP адреса',
            'reset_in': 3600  # 1 час
        }
    
    # Если передан номер телефона, проверяем лимит уникальных номеров
    if phone_number:
        phones_key = f"telegram_ip_phones:{client_ip}"
        used_phones = cache.get(phones_key, set())
        
        if isinstance(used_phones, list):
            used_phones = set(used_phones)
        
        if len(used_phones) >= 5 and phone_number not in used_phones:
            return True, {
                'type': 'unique_phones_exceeded',
                'message': 'Превышен лимит уникальных номеров телефонов с данного IP',
                'reset_in': 3600  # 1 час
            }
        
        # Добавляем номер в список использованных
        used_phones.add(phone_number)
        cache.set(phones_key, used_phones, 3600)  # 1 час
    
    # Увеличиваем счетчик попыток
    cache.set(attempts_key, current_attempts + 1, 3600)  # 1 час
    
    return False, {'status': 'allowed'}


def is_rate_limited(request, rate_limit_key=None):
    """
    Проверяет, превышен ли rate limit для данного запроса
    
    Args:
        request: Django request объект
        rate_limit_key: Ключ для rate limit (если None, определяется автоматически)
    
    Returns:
        tuple: (is_limited, limit_info)
            is_limited (bool): True если лимит превышен
            limit_info (dict): Информация о лимите
    """
    # В режиме DEBUG rate limiting может быть отключен
    if settings.DEBUG and not getattr(settings, 'RATE_LIMIT_IN_DEBUG', False):
        return False, {'status': 'disabled_in_debug'}
    
    # Определяем ключ rate limit если не передан
    if rate_limit_key is None:
        rate_limit_key = get_endpoint_rate_limit(request.path, request.method)
    
    # Если ключ не найден, rate limiting не применяется
    if rate_limit_key is None or rate_limit_key not in RATE_LIMITS:
        return False, {'status': 'no_limit_configured'}
    
    # Специальная проверка для Telegram endpoints
    if rate_limit_key.startswith('telegram_'):
        # Извлекаем номер телефона из POST данных если доступен
        phone_number = None
        if request.method == 'POST' and hasattr(request, 'data'):
            phone_number = request.data.get('phone_number') or request.data.get('phone')
        elif request.method == 'POST' and request.POST:
            phone_number = request.POST.get('phone_number') or request.POST.get('phone')
        
        # Проверяем IP ограничения
        is_ip_restricted, ip_info = check_telegram_ip_restrictions(request, phone_number)
        if is_ip_restricted:
            return True, ip_info
    
    # Получаем IP адрес клиента
    client_ip = get_client_ip(request)
    
    # Получаем конфигурацию лимита
    limit_config = RATE_LIMITS[rate_limit_key]
    rate = limit_config['rate']
    burst = limit_config.get('burst', None)
    
    # Создаем уникальный ключ для кеша
    cache_key = f"rate_limit:{rate_limit_key}:{client_ip}"
    
    # Проверяем текущее состояние лимита
    current_count = cache.get(cache_key, 0)
    
    # Парсим rate (например, "10/min" -> 10 запросов в минуту)
    rate_parts = rate.split('/')
    if len(rate_parts) != 2:
        return False, {'status': 'invalid_rate_format'}
    
    limit_count = int(rate_parts[0])
    time_unit = rate_parts[1]
    
    # Определяем время в секундах
    time_seconds = {
        'sec': 1,
        'min': 60,
        'hour': 3600,
        'day': 86400
    }.get(time_unit, 60)  # По умолчанию минута
    
    # Проверяем лимит
    if current_count >= limit_count:
        return True, {
            'status': 'rate_limited',
            'limit': limit_count,
            'current': current_count,
            'time_unit': time_unit,
            'reset_in': time_seconds
        }
    
    # Увеличиваем счетчик
    cache.set(cache_key, current_count + 1, time_seconds)
    
    return False, {
        'status': 'allowed',
        'limit': limit_count,
        'current': current_count + 1,
        'time_unit': time_unit
    }


def get_endpoint_rate_limit(request_path: str, request_method: str) -> Optional[str]:
    """
    Map request path and method to rate limit configuration key
    """
    path = request_path.lower()
    method = request_method.upper()
    
    # Telegram endpoints - высокий приоритет безопасности
    if '/api/accounts/telegram/' in path:
        if 'login/initiate' in path:
            return 'telegram_login'
        elif 'login/status' in path or 'status' in path:
            return 'telegram_status'
        elif 'activate' in path:
            return 'telegram_activate'
        elif 'verify' in path:
            return 'telegram_verify'
        elif 'link' in path and 'unlink' not in path:
            return 'telegram_link'
        elif 'unlink' in path:
            return 'telegram_unlink'
        elif 'password-reset' in path:
            return 'telegram_password_reset'
        # Fallback для других Telegram endpoints
        return 'telegram_status'
    
    # Authentication endpoints
    elif '/api/accounts/login/' in path and method == 'POST':
        return 'auth_login'
    elif '/api/accounts/register/' in path and method == 'POST':
        return 'auth_register'
    elif '/api/accounts/password/reset/' in path and method == 'POST':
        return 'password_reset'
    elif '/api/accounts/password/change/' in path and method == 'POST':
        return 'password_change'
    elif '/api/accounts/token/' in path and method == 'POST':
        if 'refresh' in path:
            return 'jwt_refresh'
        return 'jwt_token'
    elif '/api/accounts/me/' in path:
        return 'user_profile'
    elif '/api/accounts/user_statistics/' in path:
        return 'user_statistics'
    
    # Order endpoints
    elif '/api/orders/' in path:
        if method == 'POST' and path.endswith('/api/orders/'):
            return 'order_create'
        elif '/cancel/' in path and method == 'POST':
            return 'order_cancel'
        elif '/pay/' in path and method == 'POST':
            return 'payment_initiate'
        elif '/payment-status/' in path and method == 'GET':
            return 'payment_status'
    
    # Cart endpoints
    elif '/api/cart/' in path:
        if '/add/' in path and method == 'POST':
            return 'cart_add'
        elif '/update/' in path and method in ['PUT', 'PATCH']:
            return 'cart_update'
        elif '/clear/' in path and method == 'POST':
            return 'cart_clear'
        elif '/create-reservations/' in path and method == 'POST':
            return 'cart_reservations'
    
    # Address endpoints
    elif '/api/addresses/' in path:
        if method == 'POST':
            return 'address_create'
        elif method in ['PUT', 'PATCH']:
            return 'address_update'
    
    # Admin endpoints
    elif '/admin/' in path:
        if '/api/orders/' in path:
            return 'admin_orders'
        return 'admin_api'
    
    # File upload endpoints
    elif 'upload' in path or 'image' in path:
        return 'api_upload'
    
    # Default for other API endpoints
    elif '/api/' in path:
        return 'api_general'
    
    return None