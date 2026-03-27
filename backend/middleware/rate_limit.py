import time
from typing import Dict, Optional, Callable
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from loguru import logger
from core.config_loader import config, RateLimitEndpointConfig
from core.redis_cache import redis_cache

class MemoryRateLimiter:
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
    
    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _clean_old_requests(self, key: str, window: int):
        current_time = time.time()
        cutoff_time = current_time - window
        self._requests[key] = [
            req_time for req_time in self._requests[key]
            if req_time > cutoff_time
        ]
    
    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        self._clean_old_requests(key, window)
        
        current_count = len(self._requests[key])
        
        if current_count >= limit:
            oldest_request = min(self._requests[key]) if self._requests[key] else time.time()
            retry_after = int(oldest_request + window - time.time())
            return False, current_count, max(1, retry_after)
        
        self._requests[key].append(time.time())
        return True, current_count + 1, window
    
    def get_remaining(self, key: str, limit: int, window: int) -> int:
        self._clean_old_requests(key, window)
        return max(0, limit - len(self._requests[key]))

class RedisRateLimiter:
    def __init__(self):
        self._prefix = "rate_limit:"
    
    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        try:
            current = await redis_cache.incr(key)
            
            if current == 1:
                await redis_cache.expire(key, window)
                return True, 1, window
            
            ttl = await redis_cache.ttl(key)
            
            if current > limit:
                return False, current, max(1, ttl)
            
            return True, current, window
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            return True, limit, window
    
    async def get_remaining(self, key: str, limit: int, window: int) -> int:
        try:
            value = await redis_cache.get(key)
            current = int(value) if value else 0
            return max(0, limit - current)
        except Exception as e:
            logger.error(f"Redis get_remaining error: {e}")
            return limit

RATE_LIMIT_RULES: Dict[str, RateLimitEndpointConfig] = {
    "/api/auth/login": config.get_rate_limit("auth", "login"),
    "/api/auth/register": config.get_rate_limit("auth", "register"),
    "/api/devices": config.get_rate_limit("devices", "list"),
    "/api/apps": config.get_rate_limit("apps", "list"),
}

def get_rate_limit_for_path(path: str) -> RateLimitEndpointConfig:
    for pattern, limit_config in RATE_LIMIT_RULES.items():
        if path.startswith(pattern):
            return limit_config
    return config.rate_limit.default

memory_limiter = MemoryRateLimiter()
redis_limiter = RedisRateLimiter()

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exempt_paths: Optional[list] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self._use_redis = False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not config.rate_limit.enabled:
            return await call_next(request)
        
        path = request.url.path
        
        if path in self.exempt_paths:
            return await call_next(request)
        
        if path.startswith("/ws/"):
            return await call_next(request)
        
        if path.startswith("/static/"):
            return await call_next(request)
        
        rate_limit_config = get_rate_limit_for_path(path)
        
        if config.rate_limit.backend == "redis" and config.redis.enabled:
            return await self._redis_rate_limit(request, call_next, rate_limit_config)
        else:
            return await self._memory_rate_limit(request, call_next, rate_limit_config)
    
    async def _redis_rate_limit(
        self, 
        request: Request, 
        call_next: Callable, 
        rate_limit_config: RateLimitEndpointConfig
    ) -> Response:
        client_id = redis_limiter._get_client_id(request)
        key = f"rate_limit:{client_id}:{request.url.path}"
        
        allowed, current, retry_after = await redis_limiter.is_allowed(
            key,
            rate_limit_config.requests,
            rate_limit_config.window
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path} "
                f"({current}/{rate_limit_config.requests} in {rate_limit_config.window}s)"
            )
            
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "请求过于频繁",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "message": f"请在 {retry_after} 秒后重试",
                        "retry_after": retry_after,
                        "limit": rate_limit_config.requests,
                        "window": rate_limit_config.window
                    }
                }
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(rate_limit_config.requests)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + retry_after)
            return response
        
        remaining = await redis_limiter.get_remaining(
            key,
            rate_limit_config.requests,
            rate_limit_config.window
        )
        
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(rate_limit_config.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + rate_limit_config.window)
        
        return response
    
    async def _memory_rate_limit(
        self, 
        request: Request, 
        call_next: Callable, 
        rate_limit_config: RateLimitEndpointConfig
    ) -> Response:
        client_id = memory_limiter._get_client_id(request)
        key = f"{client_id}:{request.url.path}"
        
        allowed, current, retry_after = memory_limiter.is_allowed(
            key,
            rate_limit_config.requests,
            rate_limit_config.window
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path} "
                f"({current}/{rate_limit_config.requests} in {rate_limit_config.window}s)"
            )
            
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "请求过于频繁",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "message": f"请在 {retry_after} 秒后重试",
                        "retry_after": retry_after,
                        "limit": rate_limit_config.requests,
                        "window": rate_limit_config.window
                    }
                }
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(rate_limit_config.requests)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + retry_after)
            return response
        
        remaining = memory_limiter.get_remaining(
            key,
            rate_limit_config.requests,
            rate_limit_config.window
        )
        
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(rate_limit_config.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + rate_limit_config.window)
        
        return response
