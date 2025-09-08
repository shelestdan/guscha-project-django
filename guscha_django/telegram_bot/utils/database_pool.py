"""Database utilities for async operations without connection pooling."""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional
from django.conf import settings
from django.db import transaction
from asgiref.sync import sync_to_async
# Use sync_to_async from asgiref instead of database_sync_to_async

logger = logging.getLogger(__name__)


def optimized_sync_to_async(func: Callable, using: str = 'default', timeout: Optional[int] = None) -> Callable:
    """Optimized sync_to_async wrapper with thread-safe database access.
    
    Args:
        func: Synchronous function to wrap
        using: Database alias to use
        timeout: Operation timeout in seconds
    
    Returns:
        Async function with thread-safe database access
    """
    timeout = timeout or getattr(settings, 'ASYNC_DATABASE_TIMEOUT', 30)
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Use sync_to_async with thread_sensitive=False for proper Django async support
            result = await asyncio.wait_for(
                sync_to_async(func, thread_sensitive=False)(*args, **kwargs),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Database operation timeout after {timeout}s: {func.__name__}")
            raise
        except Exception as e:
            logger.error(f"Database operation error in {func.__name__}: {e}")
            raise
    
    return wrapper


def batch_sync_to_async(func: Callable, batch_size: int = 100, using: str = 'default') -> Callable:
    """Batch processing wrapper for sync_to_async operations.
    
    Args:
        func: Function that processes a single item
        batch_size: Number of items to process in each batch
        using: Database alias to use
    
    Returns:
        Async function that processes items in batches
    """
    
    @wraps(func)
    async def wrapper(items, *args, **kwargs):
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}, size: {len(batch)}")
            
            # Use sync_to_async with thread_sensitive=False for proper Django async support
            batch_results = await sync_to_async(
                lambda: [func(item, *args, **kwargs) for item in batch],
                thread_sensitive=False
            )()
            results.extend(batch_results)
        
        return results
    
    return wrapper


def transaction_sync_to_async(func: Callable, using: str = 'default', savepoint: bool = True) -> Callable:
    """Transaction-aware sync_to_async wrapper.
    
    Args:
        func: Function to wrap in transaction
        using: Database alias to use
        savepoint: Whether to use savepoints
    
    Returns:
        Async function with transaction support
    """
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Use sync_to_async with thread_sensitive=False and transaction.atomic
            @sync_to_async(thread_sensitive=False)
            def sync_func():
                with transaction.atomic(using=using, savepoint=savepoint):
                    return func(*args, **kwargs)
            
            result = await sync_func()
            return result
        except Exception as e:
            logger.error(f"Transaction error in {func.__name__}: {e}")
            raise
    
    return wrapper


class DatabaseMetrics:
    """Collect database performance metrics."""
    
    def __init__(self):
        self.query_count = 0
        self.total_time = 0.0
        self.slow_queries = []
        self.errors = []
    
    def record_query(self, duration: float, query: str = ""):
        """Record query execution metrics."""
        self.query_count += 1
        self.total_time += duration
        
        # Log slow queries (>1 second)
        if duration > 1.0:
            self.slow_queries.append({
                'duration': duration,
                'query': query[:200] + '...' if len(query) > 200 else query
            })
            logger.warning(f"Slow query detected: {duration:.2f}s")
    
    def record_error(self, error: str):
        """Record database error."""
        self.errors.append(error)
        logger.error(f"Database error: {error}")
    
    def get_stats(self) -> dict:
        """Get performance statistics."""
        avg_time = self.total_time / self.query_count if self.query_count > 0 else 0
        return {
            'query_count': self.query_count,
            'total_time': self.total_time,
            'average_time': avg_time,
            'slow_queries_count': len(self.slow_queries),
            'errors_count': len(self.errors),
            'connection_pool_usage': db_pool._connection_count / db_pool.pool_size
        }


# Global metrics instance
db_metrics = DatabaseMetrics()


def monitored_sync_to_async(func: Callable, using: str = 'default') -> Callable:
    """Sync_to_async wrapper with performance monitoring.
    
    Args:
        func: Function to monitor
        using: Database alias to use
    
    Returns:
        Async function with performance monitoring
    """
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await optimized_sync_to_async(func, using=using)(*args, **kwargs)
            duration = asyncio.get_event_loop().time() - start_time
            db_metrics.record_query(duration, func.__name__)
            return result
        except Exception as e:
            db_metrics.record_error(str(e))
            raise
    
    return wrapper


# Convenience decorators
def async_db_operation(using: str = 'default', timeout: Optional[int] = None):
    """Decorator for optimized database operations."""
    def decorator(func):
        return optimized_sync_to_async(func, using=using, timeout=timeout)
    return decorator


def monitored_sync_to_async(func: Callable, using: str = 'default') -> Callable:
    """Monitored sync_to_async wrapper for performance tracking.
    
    Args:
        func: Function to wrap
        using: Database alias to use
    
    Returns:
        Async function with monitoring
    """
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        import time
        import asyncio
        start_time = time.time()
        try:
            # Check if function is already async
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await sync_to_async(func, thread_sensitive=False)(*args, **kwargs)
            duration = time.time() - start_time
            if duration > 1.0:  # Log slow operations
                logger.warning(f"Slow database operation {func.__name__}: {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Database operation error in {func.__name__} after {duration:.2f}s: {e}")
            raise
    
    return wrapper


# Simple operation wrapper
def async_db_operation(using: str = 'default'):
    """Decorator for simple database operations."""
    def decorator(func):
        return optimized_sync_to_async(func, using=using)
    return decorator


def async_db_transaction(using: str = 'default', savepoint: bool = True):
    """Decorator for transactional database operations."""
    def decorator(func):
        return transaction_sync_to_async(func, using=using, savepoint=savepoint)
    return decorator


def async_db_batch(batch_size: int = 100, using: str = 'default'):
    """Decorator for batch database operations."""
    def decorator(func):
        return batch_sync_to_async(func, batch_size=batch_size, using=using)
    return decorator


def async_db_monitored(using: str = 'default'):
    """Decorator for monitored database operations."""
    def decorator(func):
        return monitored_sync_to_async(func, using=using)
    return decorator