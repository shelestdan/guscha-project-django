from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Утилита для ограничения частоты запросов"""
    
    def __init__(self, key_prefix='rate_limit', default_limit=100, default_window=3600):
        self.key_prefix = key_prefix
        self.default_limit = default_limit
        self.default_window = default_window
    
    def is_allowed(self, identifier, limit=None, window=None):
        """Проверяет, разрешен ли запрос для данного идентификатора"""
        limit = limit or self.default_limit
        window = window or self.default_window
        
        cache_key = f"{self.key_prefix}:{identifier}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{limit}")
            return False
        
        # Увеличиваем счетчик
        cache.set(cache_key, current_count + 1, window)
        return True
    
    def get_remaining(self, identifier, limit=None):
        """Возвращает количество оставшихся запросов"""
        limit = limit or self.default_limit
        cache_key = f"{self.key_prefix}:{identifier}"
        current_count = cache.get(cache_key, 0)
        return max(0, limit - current_count)
    
    def reset(self, identifier):
        """Сбрасывает счетчик для идентификатора"""
        cache_key = f"{self.key_prefix}:{identifier}"
        cache.delete(cache_key)
        logger.info(f"Rate limit reset for {identifier}")