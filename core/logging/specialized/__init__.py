"""
Specialized components module for the logging system.

This module provides specialized components for the logging system.
"""

from core.logging.specialized.context import (
    ContextualLogger, AsyncContextualLogger,
    CorrelationMiddleware, AsyncCorrelationMiddleware, get_correlation_middleware,
    CorrelationProvider, ContextProvider
)
from core.logging.specialized.database import (
    DatabaseLogger, AsyncDatabaseLogger,
    SqlLogger, AsyncSqlLogger,
    VectorDbLogger, AsyncVectorDbLogger,
    RedisLogger, AsyncRedisLogger
)
from core.logging.specialized.http import (
    RequestLogger, AsyncRequestLogger,
    RequestLoggingMiddleware, AsyncRequestLoggingMiddleware, get_request_logging_middleware
)
from core.logging.specialized.metrics import (
    MetricsCollector, AsyncMetricsCollector,
    Counter, Gauge, Histogram,
    PerformanceTracker, AsyncPerformanceTracker,
    MetricsExporter, AsyncMetricsExporter
)


__all__ = [
    # Context
    "ContextualLogger",
    "AsyncContextualLogger",
    "CorrelationMiddleware",
    "AsyncCorrelationMiddleware",
    "get_correlation_middleware",
    "CorrelationProvider",
    "ContextProvider",
    
    # Database
    "DatabaseLogger",
    "AsyncDatabaseLogger",
    "SqlLogger",
    "AsyncSqlLogger",
    "VectorDbLogger",
    "AsyncVectorDbLogger",
    "RedisLogger",
    "AsyncRedisLogger",
    
    # HTTP
    "RequestLogger",
    "AsyncRequestLogger",
    "RequestLoggingMiddleware",
    "AsyncRequestLoggingMiddleware",
    "get_request_logging_middleware",
    
    # Metrics
    "MetricsCollector",
    "AsyncMetricsCollector",
    "Counter",
    "Gauge",
    "Histogram",
    "PerformanceTracker",
    "AsyncPerformanceTracker",
    "MetricsExporter",
    "AsyncMetricsExporter",
] 