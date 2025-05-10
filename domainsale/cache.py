"""
Cache module for DNS and RDAP lookups.

This module handles caching of DNS and RDAP lookups to limit repeated queries.
It addresses the high severity issue of DoS / Enumeration.
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple, List, TypeVar, Generic, Callable

logger = logging.getLogger(__name__)

# Type variable for cache value
T = TypeVar('T')


class Cache(Generic[T]):
    """
    Generic cache for DNS and RDAP lookups.
    """

    def __init__(self, ttl: int = 300):
        """
        Initialize the cache.

        Args:
            ttl: Time-to-live for cache entries in seconds. Default is 300 seconds (5 minutes).
        """
        self.ttl = ttl
        self._cache: Dict[str, Tuple[T, float]] = {}

    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value, or None if the key is not in the cache or the entry has expired.
        """
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                logger.debug(f"Cache hit for {key}")
                return value
            else:
                logger.debug(f"Cache entry for {key} has expired")
                del self._cache[key]
        
        logger.debug(f"Cache miss for {key}")
        return None

    def set(self, key: str, value: T) -> None:
        """
        Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        expiry = time.time() + self.ttl
        self._cache[key] = (value, expiry)
        logger.debug(f"Cached {key} with TTL {self.ttl}s")

    def invalidate(self, key: str) -> None:
        """
        Invalidate a cache entry.

        Args:
            key: The cache key to invalidate.
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Invalidated cache entry for {key}")

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        logger.debug("Cleared cache")

    def __len__(self) -> int:
        """
        Get the number of entries in the cache.

        Returns:
            The number of entries in the cache.
        """
        # Remove expired entries
        current_time = time.time()
        self._cache = {
            key: (value, expiry)
            for key, (value, expiry) in self._cache.items()
            if current_time < expiry
        }
        
        return len(self._cache)


def cached(cache_instance: Cache[T], key_func: Callable[..., str]) -> Callable:
    """
    Decorator for caching function results.

    Args:
        cache_instance: The cache instance to use.
        key_func: A function that takes the same arguments as the decorated function
                  and returns a cache key.

    Returns:
        A decorator that caches the results of the decorated function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            key = key_func(*args, **kwargs)
            
            # Check cache
            cached_value = cache_instance.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_instance.set(key, result)
            
            return result
        
        return wrapper
    
    return decorator
