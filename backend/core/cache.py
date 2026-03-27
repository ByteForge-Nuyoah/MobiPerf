import time
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from functools import wraps
from loguru import logger

from core.config_loader import config
from core.redis_cache import redis_cache

T = TypeVar('T')

class CacheItem(Generic[T]):
    def __init__(self, value: T, ttl: int):
        self.value = value
        self.expires_at = time.time() + ttl
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

class MemoryCache:
    _cache: Dict[str, CacheItem] = {}
    
    def get(self, key: str) -> Optional[Any]:
        item = self._cache.get(key)
        if item is None:
            return None
        if item.is_expired():
            del self._cache[key]
            return None
        return item.value
    
    def set(self, key: str, value: Any, ttl: int = 60):
        self._cache[key] = CacheItem(value, ttl)
        logger.debug(f"Memory cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Memory cache deleted: {key}")
    
    def clear(self):
        self._cache.clear()
        logger.debug("Memory cache cleared")
    
    def get_stats(self) -> Dict[str, int]:
        return {
            "total_items": len(self._cache),
            "expired_items": sum(1 for item in self._cache.values() if item.is_expired())
        }

class Cache:
    _instance = None
    _memory_cache: MemoryCache = MemoryCache()
    _use_redis: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def init(self):
        if config.cache.backend == "redis" and config.redis.enabled:
            self._use_redis = await redis_cache.init()
            if self._use_redis:
                logger.info("Using Redis cache backend")
            else:
                logger.info("Falling back to memory cache")
        else:
            self._use_redis = False
            logger.info("Using memory cache backend")
    
    async def close(self):
        if self._use_redis:
            await redis_cache.close()
    
    async def get(self, key: str) -> Optional[Any]:
        if self._use_redis:
            return await redis_cache.get(key)
        return self._memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 60):
        if self._use_redis:
            await redis_cache.set(key, value, ttl)
        else:
            self._memory_cache.set(key, value, ttl)
    
    async def delete(self, key: str):
        if self._use_redis:
            await redis_cache.delete(key)
        else:
            self._memory_cache.delete(key)
    
    async def clear(self):
        if self._use_redis:
            await redis_cache.clear()
        else:
            self._memory_cache.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        if self._use_redis:
            return await redis_cache.get_stats()
        return {
            "backend": "memory",
            **self._memory_cache.get_stats()
        }

cache = Cache()

def cached(key_prefix: str, ttl: int = 60):
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{':'.join(str(arg) for arg in args)}"
            
            result = await cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result
            
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{':'.join(str(arg) for arg in args)}"
            
            result = cache._memory_cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result
            
            result = func(*args, **kwargs)
            cache._memory_cache.set(cache_key, result, ttl)
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
