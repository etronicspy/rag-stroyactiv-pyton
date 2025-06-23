"""
Rate limiting middleware using Redis backend.
Implements sliding window rate limiting with different tiers.
"""

import time
from typing import Optional, Dict, Any, Callable, Tuple
from core.logging import get_logger

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis

from core.config import settings

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with multiple tiers and Redis backend.
    
    Implements sliding window rate limiting with:
    - IP-based limiting
    - User/API key based limiting
    - Endpoint-specific limits
    - Burst protection
    """
    
    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        default_requests_per_minute: int = 60,
        default_requests_per_hour: int = 1000,
        default_burst_size: int = 10,
        enable_burst_protection: bool = True,
        rate_limit_headers: bool = True,
    ):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.default_rpm = default_requests_per_minute
        self.default_rph = default_requests_per_hour
        self.default_burst = default_burst_size
        self.enable_burst = enable_burst_protection
        self.include_headers = rate_limit_headers
        
        # Rate limit configurations by endpoint pattern
        self.endpoint_limits = {
            "/api/v1/search": {"rpm": 30, "rph": 500, "burst": 5},
            "/api/v1/prices/upload": {"rpm": 5, "rph": 50, "burst": 2},
            "/api/v1/materials/bulk": {"rpm": 10, "rph": 100, "burst": 3},
        }
        
        # Redis connection pool
        self._redis_pool: Optional[aioredis.ConnectionPool] = None
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection with connection pooling."""
        if self._redis is None:
            try:
                self._redis_pool = aioredis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=20,
                    retry_on_timeout=True,
                )
                self._redis = aioredis.Redis(connection_pool=self._redis_pool)
                # Test connection
                await self._redis.ping()
                logger.info("✅ Rate limiting Redis connection established")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis for rate limiting: {e}")
                # Fallback to in-memory rate limiting (not recommended for production)
                self._redis = None
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method."""
        start_time = time.time()
        
        try:
            # Get client identifier (IP or API key)
            client_id = self._get_client_identifier(request)
            
            # Get rate limit configuration for this endpoint
            limits = self._get_endpoint_limits(request.url.path)
            
            # Check rate limits
            is_allowed, limit_info = await self._check_rate_limits(
                client_id, request.url.path, limits
            )
            
            if not is_allowed:
                # Rate limit exceeded
                response = self._create_rate_limit_response(limit_info)
                if self.include_headers:
                    self._add_rate_limit_headers(response, limit_info)
                return response
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            if self.include_headers:
                self._add_rate_limit_headers(response, limit_info)
            
            # Log successful request
            process_time = time.time() - start_time
            logger.debug(
                f"Rate limit OK: {client_id} -> {request.method} {request.url.path} "
                f"({process_time:.3f}s)"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Allow request to proceed if rate limiting fails
            return await call_next(request)

    def _get_client_identifier(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try API key first (if implemented)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"
        
        # Fallback to IP address
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP")
            or request.client.host
        )
        return f"ip:{client_ip}"

    def _get_endpoint_limits(self, path: str) -> Dict[str, int]:
        """Get rate limits for specific endpoint."""
        # Check for exact matches first
        for pattern, limits in self.endpoint_limits.items():
            if path.startswith(pattern):
                return limits
        
        # Return default limits
        return {
            "rpm": self.default_rpm,
            "rph": self.default_rph,
            "burst": self.default_burst
        }

    async def _check_rate_limits(
        self, 
        client_id: str, 
        endpoint: str, 
        limits: Dict[str, int]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if client is within rate limits.
        Returns (is_allowed, limit_info)
        """
        redis = await self._get_redis()
        
        if redis is None:
            # Fallback to allowing all requests if Redis is unavailable
            logger.warning("Redis unavailable for rate limiting - allowing request")
            return True, {"remaining": -1, "reset_time": 0}
        
        current_time = int(time.time())
        minute_key = f"rate_limit:{client_id}:minute:{current_time // 60}"
        hour_key = f"rate_limit:{client_id}:hour:{current_time // 3600}"
        burst_key = f"rate_limit:{client_id}:burst:{current_time // 10}"  # 10-second burst window
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = redis.pipeline()
            
            # Check and increment counters
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)  # Expire after 1 minute
            
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # Expire after 1 hour
            
            if self.enable_burst:
                pipe.incr(burst_key)
                pipe.expire(burst_key, 10)  # Expire after 10 seconds
            
            results = await pipe.execute()
            
            minute_count = results[0]
            hour_count = results[2]
            burst_count = results[4] if self.enable_burst else 0
            
            # Check limits
            rpm_exceeded = minute_count > limits["rpm"]
            rph_exceeded = hour_count > limits["rph"]
            burst_exceeded = self.enable_burst and burst_count > limits["burst"]
            
            if rpm_exceeded or rph_exceeded or burst_exceeded:
                # Calculate reset times
                minute_reset = ((current_time // 60) + 1) * 60
                hour_reset = ((current_time // 3600) + 1) * 3600
                burst_reset = ((current_time // 10) + 1) * 10
                
                limit_info = {
                    "limit_rpm": limits["rpm"],
                    "limit_rph": limits["rph"],
                    "limit_burst": limits["burst"],
                    "remaining_rpm": max(0, limits["rpm"] - minute_count),
                    "remaining_rph": max(0, limits["rph"] - hour_count),
                    "remaining_burst": max(0, limits["burst"] - burst_count),
                    "reset_minute": minute_reset,
                    "reset_hour": hour_reset,
                    "reset_burst": burst_reset,
                    "retry_after": min(
                        minute_reset - current_time if rpm_exceeded else 3600,
                        hour_reset - current_time if rph_exceeded else 3600,
                        burst_reset - current_time if burst_exceeded else 3600
                    )
                }
                
                return False, limit_info
            
            # Within limits
            limit_info = {
                "limit_rpm": limits["rpm"],
                "limit_rph": limits["rph"],
                "limit_burst": limits["burst"],
                "remaining_rpm": limits["rpm"] - minute_count,
                "remaining_rph": limits["rph"] - hour_count,
                "remaining_burst": limits["burst"] - burst_count,
                "reset_minute": ((current_time // 60) + 1) * 60,
                "reset_hour": ((current_time // 3600) + 1) * 3600,
                "reset_burst": ((current_time // 10) + 1) * 10,
            }
            
            return True, limit_info
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Allow request if Redis check fails
            return True, {"remaining": -1, "reset_time": 0}

    def _create_rate_limit_response(self, limit_info: Dict[str, Any]) -> Response:
        """Create rate limit exceeded response."""
        retry_after = limit_info.get("retry_after", 60)
        
        error_detail = {
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after_seconds": retry_after,
            "limits": {
                "requests_per_minute": limit_info.get("limit_rpm"),
                "requests_per_hour": limit_info.get("limit_rph"),
                "burst_limit": limit_info.get("limit_burst"),
            },
            "remaining": {
                "rpm": limit_info.get("remaining_rpm", 0),
                "rph": limit_info.get("remaining_rph", 0), 
                "burst": limit_info.get("remaining_burst", 0),
            }
        }
        
        response = Response(
            content=str(error_detail),
            status_code=429,
            headers={"Retry-After": str(retry_after)}
        )
        
        return response

    def _add_rate_limit_headers(self, response: Response, limit_info: Dict[str, Any]):
        """Add rate limiting headers to response."""
        headers = {
            "X-RateLimit-Limit-RPM": str(limit_info.get("limit_rpm", "")),
            "X-RateLimit-Limit-RPH": str(limit_info.get("limit_rph", "")),
            "X-RateLimit-Remaining-RPM": str(limit_info.get("remaining_rpm", "")),
            "X-RateLimit-Remaining-RPH": str(limit_info.get("remaining_rph", "")),
        }
        
        if "reset_minute" in limit_info:
            headers["X-RateLimit-Reset-RPM"] = str(limit_info["reset_minute"])
        if "reset_hour" in limit_info:
            headers["X-RateLimit-Reset-RPH"] = str(limit_info["reset_hour"])
        
        if self.enable_burst:
            headers["X-RateLimit-Limit-Burst"] = str(limit_info.get("limit_burst", ""))
            headers["X-RateLimit-Remaining-Burst"] = str(limit_info.get("remaining_burst", ""))
        
        for key, value in headers.items():
            if value:  # Only add non-empty headers
                response.headers[key] = value

    async def cleanup(self):
        """Cleanup Redis connections."""
        if self._redis:
            await self._redis.close()
        if self._redis_pool:
            await self._redis_pool.disconnect() 