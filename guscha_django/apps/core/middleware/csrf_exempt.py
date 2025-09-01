from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class TelegramCSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware для исключения CSRF проверки для Telegram API endpoints.
    Должен быть размещен ПЕРЕД CsrfViewMiddleware в MIDDLEWARE настройках.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        # Telegram endpoints, которые должны быть исключены из CSRF проверки
        self.csrf_exempt_paths = [
            '/api/accounts/telegram/login/initiate/',
            '/api/accounts/telegram/login/status/',
            '/api/accounts/telegram/verify/',
            '/api/accounts/telegram/activate/',
            '/api/accounts/telegram/password-reset/',
            '/api/accounts/telegram/link/',
            '/api/accounts/telegram/unlink/',
        ]
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Исключает Telegram endpoints из CSRF проверки.
        """
        # Проверяем, является ли текущий путь Telegram endpoint
        if any(path in request.path for path in self.csrf_exempt_paths):
            # Применяем csrf_exempt к view функции
            return csrf_exempt(view_func)(request, *view_args, **view_kwargs)
        
        # Для всех остальных путей возвращаем None, чтобы продолжить обычную обработку
        return None