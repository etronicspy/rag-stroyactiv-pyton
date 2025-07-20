"""
Specialized components module for the logging system.

This module provides specialized components for the logging system.
"""

from core.logging.specialized.context import (
    AsyncContextualLogger,
    AsyncCorrelationMiddleware,
    ContextProvider,
    ContextualLogger,
    CorrelationMiddleware,
    CorrelationProvider,
    get_correlation_middleware,
)
from core.logging.specialized.database import (
    AsyncDatabaseLogger,
    AsyncRedisLogger,
    AsyncSqlLogger,
    AsyncVectorDbLogger,
    DatabaseLogger,
    RedisLogger,
    SqlLogger,
    VectorDbLogger,
)
from core.logging.specialized.http import (
    AsyncRequestLogger,
    AsyncRequestLoggingMiddleware,
    RequestLogger,
    RequestLoggingMiddleware,
    get_request_logging_middleware,
)
from core.logging.specialized.metrics import (
    AsyncMetricsCollector,
    AsyncMetricsExporter,
    AsyncPerformanceTracker,
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    MetricsExporter,
    PerformanceTracker,
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