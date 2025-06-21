"""
Core middleware package for FastAPI application.

This package contains middleware components for:
- Rate limiting through Redis
- Request/response logging
- Security headers and protections
- Error handling and monitoring
"""

from core.logging.specialized.http.request_logging_middleware import RequestLoggingMiddleware as LoggingMiddleware
from .rate_limiting import RateLimitMiddleware
from .security import SecurityMiddleware
from .conditional import ConditionalMiddleware, MiddlewareOptimizer
from .compression import CompressionMiddleware

__all__ = [
    "LoggingMiddleware",
    "RateLimitMiddleware", 
    "SecurityMiddleware",
    "ConditionalMiddleware",
    "CompressionMiddleware",
    "MiddlewareOptimizer",
] 