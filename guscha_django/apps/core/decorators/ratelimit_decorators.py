from functools import wraps
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from django.views.decorators.cache import cache_page


def api_ratelimit(group=None, key=None, rate=None, method=None, block=True):
    """
    Декоратор для ограничения частоты запросов к API.
    
    Args:
        group: Группа для ratelimit (по умолчанию 'api')
        key: Ключ для группировки (по умолчанию 'ip')
        rate: Частота запросов (по умолчанию из настроек)
        method: HTTP методы для ограничения (по умолчанию все)
        block: Блокировать ли превышение лимита
    """
    if group is None:
        group = 'api'
    if key is None:
        key = 'ip'
    if rate is None:
        rate = getattr(settings, 'API_RATELIMIT_RATE', '100/h')
    if method is None:
        method = ratelimit.ALL
    
    return ratelimit(
        group=group,
        key=key,
        rate=rate,
        method=method,
        block=block
    )


def auth_ratelimit(group=None, key=None, rate=None, method=None, block=True):
    """
    Декоратор для ограничения частоты попыток аутентификации.
    
    Args:
        group: Группа для ratelimit (по умолчанию 'auth')
        key: Ключ для группировки (по умолчанию 'ip')
        rate: Частота запросов (по умолчанию из настроек)
        method: HTTP методы для ограничения (по умолчанию POST)
        block: Блокировать ли превышение лимита
    """
    if group is None:
        group = 'auth'
    if key is None:
        key = 'ip'
    if rate is None:
        rate = getattr(settings, 'AUTH_RATELIMIT_RATE', '10/m')
    if method is None:
        method = ['POST']
    
    return ratelimit(
        group=group,
        key=key,
        rate=rate,
        method=method,
        block=block
    )


def registration_ratelimit(group=None, key=None, rate=None, method=None, block=True):
    """
    Декоратор для ограничения частоты регистраций.
    
    Args:
        group: Группа для ratelimit (по умолчанию 'registration')
        key: Ключ для группировки (по умолчанию 'ip')
        rate: Частота запросов (по умолчанию из настроек)
        method: HTTP методы для ограничения (по умолчанию POST)
        block: Блокировать ли превышение лимита
    """
    if group is None:
        group = 'registration'
    if key is None:
        key = 'ip'
    if rate is None:
        rate = getattr(settings, 'REGISTRATION_RATELIMIT_RATE', '5/h')
    if method is None:
        method = ['POST']
    
    return ratelimit(
        group=group,
        key=key,
        rate=rate,
        method=method,
        block=block
    )


def custom_ratelimit_response(request):
    """
    Кастомный ответ при превышении лимита запросов.
    """
    return JsonResponse({
        'error': 'Rate limit exceeded',
        'message': 'Слишком много запросов. Попробуйте позже.',
        'status_code': 429
    }, status=429)


def smart_ratelimit(view_func=None, *, group='default', key='ip', rate='60/h', method=None, block=True):
    """
    Умный декоратор ratelimit с автоматическим определением параметров.
    
    Использование:
    @smart_ratelimit(group='api', rate='100/h')
    def my_view(request):
        pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Применяем ratelimit
            ratelimited_func = ratelimit(
                group=group,
                key=key,
                rate=rate,
                method=method or ratelimit.ALL,
                block=block
            )(func)
            
            return ratelimited_func(request, *args, **kwargs)
        
        return wrapper
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)