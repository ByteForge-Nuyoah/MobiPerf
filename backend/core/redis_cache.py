import json
import time
from typing import Any, Optional, Dict
from loguru import logger

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis as AsyncRedis
    from redis.asyncio import ConnectionPool as AsyncConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None
    AsyncRedis = None
    AsyncConnectionPool = None

from core.config_loader import config

class RedisCache:
    _instance = None
    _pool: Optional[AsyncConnectionPool] = None
    _client: Optional[AsyncRedis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def init(self):
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not installed, falling back to memory cache")
            return False
        
        if not config.redis.enabled:
            logger.info("Redis is disabled in config")
            return False
        
        try:
            self._pool = AsyncConnectionPool(
                host=config.redis.host,
                port=config.redis.port,
                password=config.redis.password if config.redis.password else None,
                db=config.redis.db,
                max_connections=config.redis.pool_size,
                decode_responses=True
            )
            self._client = AsyncRedis(connection_pool=self._pool)
            
            await self._client.ping()
            logger.info(f"Redis connected: {config.redis.host}:{config.redis.port}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._client = None
            self._pool = None
            return False
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        logger.info("Redis connection closed")
    
    def _get_key(self, key: str) -> str:
        return f"{config.redis.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        
        try:
            full_key = self._get_key(key)
            value = await self._client.get(full_key)
            
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 60):
        if not self._client:
            return False
        
        try:
            full_key = self._get_key(key)
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            await self._client.setex(full_key, ttl, value)
            logger.debug(f"Redis set: {full_key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str):
        if not self._client:
            return False
        
        try:
            full_key = self._get_key(key)
            await self._client.delete(full_key)
            logger.debug(f"Redis deleted: {full_key}")
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear(self):
        if not self._client:
            return False
        
        try:
            keys = await self._client.keys(f"{config.redis.prefix}*")
            if keys:
                await self._client.delete(*keys)
            logger.debug("Redis cache cleared")
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        if not self._client:
            return {"connected": False}
        
        try:
            info = await self._client.info("memory")
            keys = await self._client.keys(f"{config.redis.prefix}*")
            
            key_details = []
            for key in keys[:10]:
                ttl = await self._client.ttl(key)
                key_type = await self._client.type(key)
                key_details.append({
                    "key": key.replace(config.redis.prefix, ""),
                    "ttl": ttl,
                    "type": key_type
                })
            
            return {
                "connected": True,
                "total_keys": len(keys),
                "used_memory": info.get("used_memory_human", "unknown"),
                "max_memory": info.get("maxmemory_human", "unknown"),
                "keys": key_details
            }
        except Exception as e:
            logger.error(f"Redis get_stats error: {e}")
            return {"connected": False, "error": str(e)}
    
    async def incr(self, key: str) -> int:
        if not self._client:
            return 0
        
        try:
            full_key = self._get_key(key)
            return await self._client.incr(full_key)
        except Exception as e:
            logger.error(f"Redis incr error: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int):
        if not self._client:
            return False
        
        try:
            full_key = self._get_key(key)
            return await self._client.expire(full_key, ttl)
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        if not self._client:
            return -1
        
        try:
            full_key = self._get_key(key)
            return await self._client.ttl(full_key)
        except Exception as e:
            logger.error(f"Redis ttl error: {e}")
            return -1

redis_cache = RedisCache()
