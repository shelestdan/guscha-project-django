from django.http import JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from ..validation.rate_limiting import RateLimiter, RATE_LIMITS, get_endpoint_rate_limit
from ..validation.security_logging import SecurityLogger
from ..security.monitoring import security_monitor
import json


class RateLimitMiddleware(MiddlewareMixin):
    """
    Django middleware for API rate limiting
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.rate_limiter = RateLimiter()
        self.security_logger = SecurityLogger()
        self.enabled = getattr(settings, 'RATE_LIMITING_ENABLED', True)
        
        # Paths to exclude from rate limiting
        self.excluded_paths = getattr(settings, 'RATE_LIMIT_EXCLUDED_PATHS', [
            '/admin/jsi18n/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/health/',
            '/ping/',
        ])
        
        # User agents to exclude (bots, monitoring tools)
        self.excluded_user_agents = getattr(settings, 'RATE_LIMIT_EXCLUDED_USER_AGENTS', [
            'GoogleBot',
            'BingBot',
            'YandexBot',
            'facebookexternalhit',
            'Twitterbot',
            'LinkedInBot',
            'WhatsApp',
            'Telegram',
        ])
    
    def should_rate_limit(self, request):
        """
        Determine if request should be rate limited
        """
        if not self.enabled:
            return False
        
        # Skip if disabled in settings
        if getattr(settings, 'DEBUG', False) and not getattr(settings, 'RATE_LIMIT_IN_DEBUG', False):
            return False
        
        # Skip excluded paths
        path = request.path_info
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return False
        
        # Skip excluded user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        for excluded_ua in self.excluded_user_agents:
            if excluded_ua.lower() in user_agent.lower():
                return False
        
        # Skip superusers in production (optional)
        if (hasattr(request, 'user') and 
            request.user.is_authenticated and 
            request.user.is_superuser and 
            getattr(settings, 'RATE_LIMIT_SKIP_SUPERUSER', False)):
            return False
        
        return True
    
    def create_rate_limit_response(self, request, rate_info, is_api=True):
        """
        Create appropriate rate limit response
        """
        headers = self.rate_limiter.get_rate_limit_headers(rate_info)
        
        if is_api or request.content_type == 'application/json':
            # JSON response for API endpoints
            response_data = {
                'error': 'Rate limit exceeded',
                'message': f"Too many requests. Try again in {rate_info['retry_after']} seconds.",
                'details': {
                    'limit': rate_info['requests_allowed'],
                    'window_seconds': rate_info['window_seconds'],
                    'retry_after': rate_info['retry_after']
                }
            }
            response = JsonResponse(response_data, status=429)
        else:
            # HTML response for web endpoints
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rate Limit Exceeded</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .container {{ max-width: 500px; margin: 0 auto; }}
                    .error {{ color: #d32f2f; }}
                    .retry {{ color: #1976d2; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="error">Rate Limit Exceeded</h1>
                    <p>You have made too many requests. Please wait before trying again.</p>
                    <div class="retry">
                        <strong>Retry after: {rate_info['retry_after']} seconds</strong>
                    </div>
                    <p><small>Limit: {rate_info['requests_allowed']} requests per {rate_info['window_seconds']} seconds</small></p>
                </div>
            </body>
            </html>
            """
            response = HttpResponse(html_content, status=429, content_type='text/html')
        
        # Add rate limit headers
        for header_name, header_value in headers.items():
            response[header_name] = header_value
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def process_request(self, request):
        """
        Process incoming request for rate limiting
        """
        if not self.should_rate_limit(request):
            return None
        
        # Get endpoint configuration
        endpoint_key = get_endpoint_rate_limit(request.path_info, request.method)
        
        if not endpoint_key:
            # No specific rate limit configured for this endpoint
            return None
        
        rate_config = RATE_LIMITS.get(endpoint_key)
        if not rate_config:
            return None
        
        # Check rate limit
        is_limited, rate_info = self.rate_limiter.is_rate_limited(
            request, endpoint_key, rate_config
        )
        
        if is_limited:
            # Log security event
            self.security_logger.log_rate_limit_exceeded(
                request,
                endpoint_key,
                rate_info.get('current_count', 0),
                rate_info.get('limit', 0)
            )
            
            # Record in security monitoring system
            ip_address = self._get_client_ip(request)
            risk_score = min(100, 30 + (rate_info.get('requests_made', 0) - rate_info.get('requests_allowed', 0)) * 5)
            
            security_monitor.record_threat(
                'rate_limit_exceeded',
                ip_address,
                risk_score,
                {
                    'endpoint': endpoint_key,
                    'requests_made': rate_info.get('requests_made', 0),
                    'requests_allowed': rate_info.get('requests_allowed', 0),
                    'window_seconds': rate_info.get('window_seconds', 0),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
                }
            )
            
            # Return rate limit response
            is_api = (
                request.path_info.startswith('/api/') or
                request.content_type == 'application/json' or
                'application/json' in request.META.get('HTTP_ACCEPT', '')
            )
            
            return self.create_rate_limit_response(request, rate_info, is_api)
        
        # Store rate info in request for potential use in views
        request.rate_limit_info = rate_info
        
        return None
    
    def process_response(self, request, response):
        """
        Add rate limit headers to successful responses
        """
        if (hasattr(request, 'rate_limit_info') and 
            self.should_rate_limit(request) and
            response.status_code < 400):
            
            headers = self.rate_limiter.get_rate_limit_headers(request.rate_limit_info)
            for header_name, header_value in headers.items():
                if header_name != 'Retry-After':  # Only add Retry-After on rate limit
                    response[header_name] = header_value
        
        return response


class RateLimitBypassMiddleware(MiddlewareMixin):
    """
    Middleware to bypass rate limiting for specific conditions
    Useful for testing, monitoring, or trusted sources
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        
        # Trusted IP addresses that bypass rate limiting
        self.trusted_ips = getattr(settings, 'RATE_LIMIT_TRUSTED_IPS', [])
        
        # API keys that bypass rate limiting
        self.bypass_api_keys = getattr(settings, 'RATE_LIMIT_BYPASS_API_KEYS', [])
    
    def get_client_ip(self, request):
        """
        Get client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def process_request(self, request):
        """
        Check if request should bypass rate limiting
        """
        # Check trusted IPs
        client_ip = self.get_client_ip(request)
        if client_ip in self.trusted_ips:
            request._rate_limit_bypass = True
            return None
        
        # Check API key bypass
        api_key = (
            request.META.get('HTTP_X_API_KEY') or
            request.GET.get('api_key') or
            request.POST.get('api_key')
        )
        
        if api_key in self.bypass_api_keys:
            request._rate_limit_bypass = True
            return None
        
        return None


# Decorator for view-level rate limiting
def rate_limit(endpoint_key=None, rate=None, burst=None):
    """
    Decorator for applying rate limiting to specific views
    
    Usage:
    @rate_limit('custom_endpoint', rate='10/min', burst=20)
    def my_view(request):
        ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if hasattr(request, '_rate_limit_bypass') and request._rate_limit_bypass:
                return view_func(request, *args, **kwargs)
            
            rate_limiter = RateLimiter()
            
            # Use provided config or default
            if endpoint_key and (rate or burst):
                rate_config = {
                    'rate': rate or '60/min',
                    'burst': burst or 100
                }
                
                is_limited, rate_info = rate_limiter.is_rate_limited(
                    request, endpoint_key, rate_config
                )
                
                if is_limited:
                    is_api = (
                        request.path_info.startswith('/api/') or
                        request.content_type == 'application/json'
                    )
                    
                    middleware = RateLimitMiddleware()
                    return middleware.create_rate_limit_response(request, rate_info, is_api)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator