class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Разрешаем все необходимые источники для разработки
        csp_policy = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: "
            "http://localhost:8000 http://127.0.0.1:8000 "
            "ws://localhost:8000 ws://127.0.0.1:8000 "
            "https://accounts.google.com https://apis.google.com https://fonts.googleapis.com https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "http://localhost:8000 http://127.0.0.1:8000 "
            "https://accounts.google.com https://apis.google.com https://www.googletagmanager.com; "
            "connect-src 'self' "
            "http://localhost:8000 http://127.0.0.1:8000 "
            "ws://localhost:8000 ws://127.0.0.1:8000 "
            "https://accounts.google.com https://apis.google.com; "
            "img-src 'self' data: blob: https: http:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "frame-src 'self' https://accounts.google.com;"
        )
        
        response['Content-Security-Policy'] = csp_policy
        
        return response