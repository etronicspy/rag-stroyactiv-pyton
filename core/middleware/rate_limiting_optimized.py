"""
Optimized rate limiting middleware using Redis Lua scripts for atomic operations.
Provides distributed rate limiting with minimal race conditions.
"""

import asyncio
import time
from core.logging import get_logger
from typing import Optional, Dict, Any, Callable, Tuple
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis

from core.config import settings

logger = get_logger(__name__)


class OptimizedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Optimized rate limiting middleware using Redis Lua scripts.
    
    Key improvements:
    - Atomic operations with Lua scripts (eliminates race conditions)
    - Sliding window rate limiting
    - Distributed synchronization across multiple instances
    - Efficient batch operations
    - Advanced burst protection
    - Performance monitoring
    """
    
    # Lua script for atomic sliding window rate limiting
    SLIDING_WINDOW_SCRIPT = """
        local key = KEYS[1]
        local window = tonumber(ARGV[1])
        local limit = tonumber(ARGV[2])
        local current_time = tonumber(ARGV[3])
        local increment = tonumber(ARGV[4]) or 1
        
        -- Remove expired entries
        redis.call('ZREMRANGEBYSCORE', key, 0, current_time - window)
        
        -- Count current requests
        local current_requests = redis.call('ZCARD', key)
        
        if current_requests < limit then
            -- Add current request
            redis.call('ZADD', key, current_time, current_time .. ':' .. math.random())
            redis.call('EXPIRE', key, window)
            
            -- Return success with remaining requests
            return {1, limit - current_requests - increment}
        else
            -- Get oldest request time for reset calculation
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local reset_time = 0
            if #oldest > 0 then
                reset_time = oldest[2] + window
            end
            
            -- Return failure with reset time
            return {0, 0, reset_time}
        end
    """
    
    # Lua script for multi-tier rate limiting (minute + hour + burst)
    MULTI_TIER_SCRIPT = """
        local minute_key = KEYS[1]
        local hour_key = KEYS[2]
        local burst_key = KEYS[3]
        
        local minute_window = tonumber(ARGV[1])
        local hour_window = tonumber(ARGV[2])
        local burst_window = tonumber(ARGV[3])
        
        local minute_limit = tonumber(ARGV[4])
        local hour_limit = tonumber(ARGV[5])
        local burst_limit = tonumber(ARGV[6])
        
        local current_time = tonumber(ARGV[7])
        
        -- Clean expired entries
        redis.call('ZREMRANGEBYSCORE', minute_key, 0, current_time - minute_window)
        redis.call('ZREMRANGEBYSCORE', hour_key, 0, current_time - hour_window)
        redis.call('ZREMRANGEBYSCORE', burst_key, 0, current_time - burst_window)
        
        -- Count current requests
        local minute_count = redis.call('ZCARD', minute_key)
        local hour_count = redis.call('ZCARD', hour_key)
        local burst_count = redis.call('ZCARD', burst_key)
        
        -- Check all limits
        if minute_count >= minute_limit then
            return {0, 'minute', minute_count, minute_limit}
        end
        
        if hour_count >= hour_limit then
            return {0, 'hour', hour_count, hour_limit}
        end
        
        if burst_count >= burst_limit then
            return {0, 'burst', burst_count, burst_limit}
        end
        
        -- All checks passed, add request to all windows
        local request_id = current_time .. ':' .. math.random()
        redis.call('ZADD', minute_key, current_time, request_id)
        redis.call('ZADD', hour_key, current_time, request_id)
        redis.call('ZADD', burst_key, current_time, request_id)
        
        -- Set expiration
        redis.call('EXPIRE', minute_key, minute_window)
        redis.call('EXPIRE', hour_key, hour_window)
        redis.call('EXPIRE', burst_key, burst_window)
        
        -- Return success with remaining requests
        return {
            1, 
            minute_limit - minute_count - 1,
            hour_limit - hour_count - 1,
            burst_limit - burst_count - 1
        }
    """

    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        default_requests_per_minute: int = 60,
        default_requests_per_hour: int = 1000,
        default_burst_size: int = 10,
        burst_window_seconds: int = 10,
        enable_burst_protection: bool = True,
        rate_limit_headers: bool = True,
        enable_distributed_sync: bool = True,
        enable_performance_logging: bool = False,
    ):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.default_rpm = default_requests_per_minute
        self.default_rph = default_requests_per_hour
        self.default_burst = default_burst_size
        self.burst_window = burst_window_seconds
        self.enable_burst = enable_burst_protection
        self.include_headers = rate_limit_headers
        self.enable_distributed_sync = enable_distributed_sync
        self.enable_performance_logging = enable_performance_logging
        
        # Enhanced endpoint configurations
        self.endpoint_limits = {
            "/api/v1/search/*": {"rpm": 30, "rph": 500, "burst": 5},
            "/api/v1/prices/upload": {"rpm": 5, "rph": 50, "burst": 2},
            "/api/v1/materials/bulk": {"rpm": 10, "rph": 100, "burst": 3},
            "/api/v1/materials/*": {"rpm": 100, "rph": 2000, "burst": 20},
            "/api/v1/health/*": {"rpm": 300, "rph": 10000, "burst": 50},
        }
        
        # Performance tracking
        self.total_requests = 0
        self.allowed_requests = 0
        self.rate_limited_requests = 0
        self.total_lua_execution_time = 0
        
        # Redis connection and Lua scripts
        self._redis_pool: Optional[aioredis.ConnectionPool] = None
        self._redis: Optional[aioredis.Redis] = None
        self._sliding_window_script = None
        self._multi_tier_script = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection with enhanced connection pooling."""
        if self._redis is None:
            try:
                # Check if we should use mock Redis
                if getattr(settings, 'DISABLE_REDIS_CONNECTION', False) or getattr(settings, 'QDRANT_ONLY_MODE', False):
                    # Use mock Redis adapter
                    from core.database.factories import DatabaseFactory
                    cache_db = DatabaseFactory.create_cache_database()
                    if hasattr(cache_db, 'mock_redis'):
                        logger.info("🔧 Using mock Redis for rate limiting (Qdrant-only mode)")
                        self._redis = cache_db.mock_redis
                        return self._redis
                
                # Use real Redis
                self._redis_pool = aioredis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=50,  # Increased pool size
                    retry_on_timeout=True,
                    retry_on_error=[aioredis.ConnectionError, aioredis.TimeoutError],
                    health_check_interval=30,
                )
                self._redis = aioredis.Redis(
                    connection_pool=self._redis_pool,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                )
                
                # Test connection and load Lua scripts
                await self._redis.ping()
                if not hasattr(self._redis, 'mock_redis'):  # Skip Lua scripts for mock Redis
                    await self._load_lua_scripts()
                
                logger.info("✅ Optimized rate limiting Redis connection established")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis for rate limiting: {e}")
                
                # Try fallback to mock if enabled
                try:
                    if getattr(settings, 'ENABLE_FALLBACK_DATABASES', True):
                        from core.database.factories import DatabaseFactory
                        cache_db = DatabaseFactory.create_cache_database()
                        if hasattr(cache_db, 'mock_redis'):
                            logger.warning("🔧 Using mock Redis as fallback for rate limiting")
                            self._redis = cache_db.mock_redis
                            return self._redis
                except Exception as fallback_error:
                    logger.error(f"Fallback to mock Redis failed: {fallback_error}")
                
                self._redis = None
        return self._redis

    async def _load_lua_scripts(self):
        """Load and register Lua scripts in Redis."""
        if self._redis:
            self._sliding_window_script = await self._redis.script_load(self.SLIDING_WINDOW_SCRIPT)
            self._multi_tier_script = await self._redis.script_load(self.MULTI_TIER_SCRIPT)
            logger.info("✅ Rate limiting Lua scripts loaded")

    def _get_client_identifier(self, request: Request) -> str:
        """Enhanced client identifier extraction."""
        # Priority: API key > JWT token > IP address
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key[:16]}"  # Use first 16 chars for security
        
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_hash = hash(auth_header) % 1000000  # Simple hash for identification
            return f"token:{token_hash}"
        
        # Enhanced IP extraction with proxy support
        client_ip = (
            request.headers.get("CF-Connecting-IP") or  # Cloudflare
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP") or
            request.headers.get("X-Client-IP") or
            request.client.host if request.client else "unknown"
        )
        return f"ip:{client_ip}"

    def _get_endpoint_limits(self, path: str) -> Dict[str, int]:
        """Enhanced endpoint limit matching with pattern support."""
        # Try exact match first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Try pattern matching
        for pattern, limits in self.endpoint_limits.items():
            if pattern.endswith("*"):
                if path.startswith(pattern[:-1]):
                    return limits
            elif pattern.startswith("*"):
                if path.endswith(pattern[1:]):
                    return limits
        
        # Return default limits
        return {
            "rpm": self.default_rpm,
            "rph": self.default_rph,
            "burst": self.default_burst
        }

    async def _check_rate_limits_optimized(
        self, 
        client_id: str, 
        endpoint: str, 
        limits: Dict[str, int]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Optimized rate limit checking using Lua scripts.
        """
        redis = await self._get_redis()
        
        if redis is None or self._multi_tier_script is None:
            logger.warning("Redis/Lua scripts unavailable - allowing request")
            return True, {"remaining": -1, "reset_time": 0}
        
        current_time = int(time.time() * 1000)  # Use milliseconds for precision
        
        # Create keys for different time windows
        minute_key = f"rl:{client_id}:m:{current_time // 60000}"
        hour_key = f"rl:{client_id}:h:{current_time // 3600000}"
        burst_key = f"rl:{client_id}:b:{current_time // (self.burst_window * 1000)}"
        
        try:
            start_time = time.time() if self.enable_performance_logging else 0
            
            # Execute Lua script atomically
            result = await redis.evalsha(
                self._multi_tier_script,
                3,  # Number of keys
                minute_key, hour_key, burst_key,
                60000,  # minute window (ms)
                3600000,  # hour window (ms)
                self.burst_window * 1000,  # burst window (ms)
                limits["rpm"],
                limits["rph"],
                limits["burst"],
                current_time
            )
            
            if self.enable_performance_logging:
                execution_time = time.time() - start_time
                self.total_lua_execution_time += execution_time
            
            is_allowed = result[0] == 1
            
            if is_allowed:
                self.allowed_requests += 1
                limit_info = {
                    "remaining_minute": result[1],
                    "remaining_hour": result[2],
                    "remaining_burst": result[3],
                    "reset_time": current_time + 60000,  # Next minute
                }
            else:
                self.rate_limited_requests += 1
                limit_type = result[1]
                current_count = result[2]
                limit_value = result[3]
                
                limit_info = {
                    "limit_type": limit_type,
                    "current_count": current_count,
                    "limit_value": limit_value,
                    "reset_time": current_time + 60000,  # Approximate reset time
                }
            
            self.total_requests += 1
            return is_allowed, limit_info
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return True, {"remaining": -1, "reset_time": 0, "error": str(e)}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enhanced dispatch with optimized rate limiting."""
        start_time = time.time() if self.enable_performance_logging else 0
        
        try:
            # Get client identifier and endpoint limits
            client_id = self._get_client_identifier(request)
            limits = self._get_endpoint_limits(request.url.path)
            
            # Check rate limits using optimized Lua scripts
            is_allowed, limit_info = await self._check_rate_limits_optimized(
                client_id, request.url.path, limits
            )
            
            if not is_allowed:
                # Create enhanced rate limit response
                response = self._create_enhanced_rate_limit_response(limit_info)
                if self.include_headers:
                    self._add_enhanced_rate_limit_headers(response, limit_info)
                return response
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            if self.include_headers:
                self._add_enhanced_rate_limit_headers(response, limit_info)
            
            # Log successful request
            if self.enable_performance_logging:
                process_time = time.time() - start_time
                logger.debug(
                    f"Rate limit OK: {client_id} -> {request.method} {request.url.path} "
                    f"({process_time*1000:.2f}ms total, "
                    f"remaining: {limit_info.get('remaining_minute', 'N/A')})"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Optimized rate limiting middleware error: {e}")
            # Allow request to proceed if rate limiting fails
            return await call_next(request)

    def _create_enhanced_rate_limit_response(self, limit_info: Dict[str, Any]) -> Response:
        """Create enhanced rate limit exceeded response."""
        limit_type = limit_info.get("limit_type", "unknown")
        current_count = limit_info.get("current_count", 0)
        limit_value = limit_info.get("limit_value", 0)
        reset_time = limit_info.get("reset_time", 0)
        
        error_detail = f"Rate limit exceeded: {current_count}/{limit_value} {limit_type} requests"
        
        return Response(
            content=f'{{"error": "Rate limit exceeded", "detail": "{error_detail}", "reset_time": {reset_time}}}',
            status_code=429,
            headers={
                "Content-Type": "application/json",
                "Retry-After": str(max(1, (reset_time - int(time.time() * 1000)) // 1000)),
            }
        )

    def _add_enhanced_rate_limit_headers(self, response: Response, limit_info: Dict[str, Any]):
        """Add enhanced rate limiting headers."""
        response.headers["X-RateLimit-Remaining-Minute"] = str(limit_info.get("remaining_minute", 0))
        response.headers["X-RateLimit-Remaining-Hour"] = str(limit_info.get("remaining_hour", 0))
        response.headers["X-RateLimit-Remaining-Burst"] = str(limit_info.get("remaining_burst", 0))
        response.headers["X-RateLimit-Reset"] = str(limit_info.get("reset_time", 0))

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get enhanced performance statistics."""
        if self.total_requests == 0:
            return {
                "total_requests": 0,
                "allowed_requests": 0,
                "rate_limited_requests": 0,
                "allow_rate": 0.0,
                "average_lua_execution_time": 0.0,
            }
        
        return {
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "rate_limited_requests": self.rate_limited_requests,
            "allow_rate": self.allowed_requests / self.total_requests,
            "rate_limit_rate": self.rate_limited_requests / self.total_requests,
            "average_lua_execution_time": (
                self.total_lua_execution_time / self.total_requests
                if self.total_requests > 0 else 0.0
            ),
            "redis_connected": self._redis is not None,
            "lua_scripts_loaded": self._multi_tier_script is not None,
        }

    async def cleanup(self):
        """Enhanced cleanup with connection pool management."""
        if self._redis_pool:
            try:
                await self._redis_pool.disconnect()
                logger.info("✅ Optimized rate limiting Redis pool disconnected")
            except Exception as e:
                logger.error(f"❌ Error disconnecting rate limiting Redis pool: {e}") 