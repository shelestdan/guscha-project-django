import secrets
import base64
from django.conf import settings

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def generate_nonce(self):
        """Генерирует криптографически стойкий nonce для CSP"""
        return base64.b64encode(secrets.token_bytes(16)).decode('utf-8')

    def __call__(self, request):
        response = self.get_response(request)
        
        # Разные CSP политики для разработки и продакшена
        if settings.DEBUG:
            # Более разрешительная политика для разработки
            csp_policy = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: "
                "http://localhost:8000 http://127.0.0.1:8000 http://localhost http://127.0.0.1 "
                "ws://localhost:8000 ws://127.0.0.1:8000 "
                "https://accounts.google.com https://apis.google.com https://fonts.googleapis.com https://fonts.gstatic.com; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "http://localhost:8000 http://127.0.0.1:8000 http://localhost http://127.0.0.1 "
                "https://accounts.google.com https://apis.google.com https://www.googletagmanager.com; "
                "connect-src 'self' "
                "http://localhost:8000 http://127.0.0.1:8000 http://localhost http://127.0.0.1 "
                "ws://localhost:8000 ws://127.0.0.1:8000 "
                "https://accounts.google.com https://apis.google.com; "
                "img-src 'self' data: blob: https: http:; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "frame-src 'self' https://accounts.google.com;"
            )
        else:
            # Строгая политика для продакшена БЕЗ unsafe-inline и unsafe-eval
            nonce = self.generate_nonce()
            request.csp_nonce = nonce  # Сохраняем nonce для использования в шаблонах
            
            csp_policy = (
                "default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}' https://accounts.google.com https://apis.google.com https://www.googletagmanager.com; "
                f"style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://accounts.google.com https://apis.google.com; "
                "frame-src 'self' https://accounts.google.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests;"
            )
        
        response['Content-Security-Policy'] = csp_policy
        
        # Дополнительные заголовки безопасности
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response