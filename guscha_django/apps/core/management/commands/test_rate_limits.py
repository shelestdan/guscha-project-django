from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.core.validation.rate_limiting import RateLimiter, RATE_LIMITS, get_endpoint_rate_limit
import time
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test and monitor rate limiting functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoint',
            type=str,
            help='Test specific endpoint (e.g., auth_login, order_create)'
        )
        parser.add_argument(
            '--requests',
            type=int,
            default=10,
            help='Number of test requests to send'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between requests in seconds'
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear rate limit cache before testing'
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Monitor current rate limit status'
        )
        parser.add_argument(
            '--list-endpoints',
            action='store_true',
            help='List all configured rate limit endpoints'
        )
    
    def handle(self, *args, **options):
        if options['list_endpoints']:
            self.list_endpoints()
            return
        
        if options['monitor']:
            self.monitor_rate_limits()
            return
        
        if options['clear_cache']:
            self.clear_rate_limit_cache()
        
        if options['endpoint']:
            self.test_endpoint(options['endpoint'], options['requests'], options['delay'])
        else:
            self.test_all_endpoints(options['requests'], options['delay'])
    
    def list_endpoints(self):
        """List all configured rate limit endpoints"""
        self.stdout.write(self.style.SUCCESS('\nConfigured Rate Limit Endpoints:'))
        self.stdout.write('=' * 50)
        
        for endpoint, config in RATE_LIMITS.items():
            rate = config.get('rate', 'N/A')
            burst = config.get('burst', 'N/A')
            self.stdout.write(f"{endpoint:20} | Rate: {rate:10} | Burst: {burst}")
        
        self.stdout.write('\nEndpoint Path Mappings:')
        self.stdout.write('=' * 50)
        
        test_paths = [
            ('/api/accounts/login/', 'POST'),
            ('/api/accounts/register/', 'POST'),
            ('/api/orders/', 'POST'),
            ('/api/orders/123/cancel/', 'POST'),
            ('/api/orders/123/pay/', 'POST'),
            ('/api/cart/add/', 'POST'),
            ('/api/addresses/', 'POST'),
        ]
        
        for path, method in test_paths:
            endpoint_key = get_endpoint_rate_limit(path, method)
            self.stdout.write(f"{method:4} {path:30} -> {endpoint_key or 'No limit'}")
    
    def clear_rate_limit_cache(self):
        """Clear all rate limit cache entries"""
        self.stdout.write('Clearing rate limit cache...')
        
        # Get all cache keys with rate limit prefix
        cache_keys = cache.keys('rate_limit:*')
        if cache_keys:
            cache.delete_many(cache_keys)
            self.stdout.write(
                self.style.SUCCESS(f'Cleared {len(cache_keys)} rate limit cache entries')
            )
        else:
            self.stdout.write('No rate limit cache entries found')
    
    def monitor_rate_limits(self):
        """Monitor current rate limit status"""
        self.stdout.write(self.style.SUCCESS('\nRate Limit Monitoring:'))
        self.stdout.write('=' * 60)
        
        factory = RequestFactory()
        rate_limiter = RateLimiter()
        
        # Create a test request
        request = factory.get('/api/test/')
        request.user = User.objects.filter(is_superuser=False).first() or User()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'RateLimitMonitor/1.0'
        
        client_id = rate_limiter.get_client_identifier(request)
        
        self.stdout.write(f"Client ID: {client_id[:16]}...")
        self.stdout.write(f"Timestamp: {int(time.time())}")
        self.stdout.write('')
        
        # Check status for each endpoint
        for endpoint, config in RATE_LIMITS.items():
            cache_key = f"rate_limit:{endpoint}:{client_id}:rate"
            burst_key = f"rate_limit:{endpoint}:{client_id}:burst"
            
            request_times = cache.get(cache_key, [])
            burst_count = cache.get(burst_key, 0)
            
            rate_string = config.get('rate', '60/min')
            burst_limit = config.get('burst', 100)
            
            requests_allowed, window_seconds = rate_limiter.parse_rate_limit(rate_string)
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Clean old requests
            active_requests = [t for t in request_times if t > window_start]
            
            status = 'OK'
            if len(active_requests) >= requests_allowed:
                status = 'RATE LIMITED'
            elif burst_count >= burst_limit:
                status = 'BURST LIMITED'
            
            self.stdout.write(
                f"{endpoint:20} | {status:12} | "
                f"Requests: {len(active_requests):2}/{requests_allowed:2} | "
                f"Burst: {burst_count:2}/{burst_limit:2}"
            )
    
    def test_endpoint(self, endpoint_key, num_requests, delay):
        """Test specific endpoint rate limiting"""
        if endpoint_key not in RATE_LIMITS:
            self.stdout.write(
                self.style.ERROR(f'Endpoint "{endpoint_key}" not found in configuration')
            )
            return
        
        config = RATE_LIMITS[endpoint_key]
        self.stdout.write(
            self.style.SUCCESS(f'\nTesting endpoint: {endpoint_key}')
        )
        self.stdout.write(f'Configuration: {json.dumps(config, indent=2)}')
        self.stdout.write(f'Sending {num_requests} requests with {delay}s delay\n')
        
        factory = RequestFactory()
        rate_limiter = RateLimiter()
        
        # Create test request
        request = factory.post('/api/test/')
        request.user = User.objects.filter(is_superuser=False).first() or User()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'RateLimitTester/1.0'
        
        results = []
        
        for i in range(num_requests):
            start_time = time.time()
            
            is_limited, rate_info = rate_limiter.is_rate_limited(
                request, endpoint_key, config
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms
            
            status = 'BLOCKED' if is_limited else 'ALLOWED'
            
            result = {
                'request': i + 1,
                'status': status,
                'response_time_ms': round(response_time, 2),
                'requests_in_window': rate_info['requests_in_window'],
                'burst_count': rate_info['burst_count'],
                'retry_after': rate_info['retry_after']
            }
            
            results.append(result)
            
            # Print result
            color = self.style.ERROR if is_limited else self.style.SUCCESS
            self.stdout.write(
                color(
                    f"Request {i+1:2}: {status:7} | "
                    f"Window: {rate_info['requests_in_window']:2}/{rate_info['requests_allowed']:2} | "
                    f"Burst: {rate_info['burst_count']:2}/{rate_info['burst_limit']:2} | "
                    f"Time: {response_time:5.1f}ms"
                )
            )
            
            if delay > 0 and i < num_requests - 1:
                time.sleep(delay)
        
        # Summary
        allowed = sum(1 for r in results if r['status'] == 'ALLOWED')
        blocked = sum(1 for r in results if r['status'] == 'BLOCKED')
        avg_response_time = sum(r['response_time_ms'] for r in results) / len(results)
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Test Summary:'))
        self.stdout.write(f'Total requests: {num_requests}')
        self.stdout.write(f'Allowed: {allowed}')
        self.stdout.write(f'Blocked: {blocked}')
        self.stdout.write(f'Average response time: {avg_response_time:.2f}ms')
        
        if blocked > 0:
            first_block = next(r for r in results if r['status'] == 'BLOCKED')
            self.stdout.write(f'First block at request: {first_block["request"]}')
    
    def test_all_endpoints(self, num_requests, delay):
        """Test all configured endpoints"""
        self.stdout.write(
            self.style.SUCCESS(f'Testing all endpoints with {num_requests} requests each\n')
        )
        
        for endpoint_key in RATE_LIMITS.keys():
            self.test_endpoint(endpoint_key, min(num_requests, 5), delay)
            self.stdout.write('')  # Empty line between tests
            
            if delay > 0:
                time.sleep(delay * 2)  # Extra delay between endpoint tests