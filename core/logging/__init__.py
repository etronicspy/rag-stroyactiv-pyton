"""
🏗️ Modular Logging System for RAG Construction Materials API

This module provides a clean, modular architecture for logging, metrics, and correlation tracking.
REFACTORED: From monolithic core/monitoring to modular core/logging structure.

Architecture:
- base/      - Fundamental components (interfaces, base classes, formatters)
- context/   - Correlation ID and request context management  
- handlers/  - Specialized loggers (database, request, structured)
- metrics/   - Metrics collection and integration
- managers/  - Unified management and factories

Configuration:
    All logging settings are managed through core.config.logging.LoggingConfig
    and can be configured via environment variables or .env files.
    
    Environment Variables:
        LOG_LEVEL                    - Main logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        ENABLE_STRUCTURED_LOGGING    - Enable JSON structured logging for production
        LOG_CORRELATION_ID           - Enable correlation ID tracking
        LOG_DATABASE_OPERATIONS      - Enable database operation logging
        LOG_PERFORMANCE_METRICS      - Enable performance metrics collection
        
        See core.config.logging.LoggingConfig for complete list of settings.

Quick Start:
    >>> from core.logging import get_logger, get_unified_logging_manager
    >>> 
    >>> # Basic logging
    >>> logger = get_logger("my_app")
    >>> logger.info("Application started")
    >>> 
    >>> # Advanced logging with metrics
    >>> manager = get_unified_logging_manager()
    >>> manager.log_database_operation(
    ...     db_type="postgresql",
    ...     operation="select_users", 
    ...     duration_ms=25.5,
    ...     success=True,
    ...     record_count=10
    ... )

Advanced Usage:
    >>> from core.logging import get_performance_optimizer, get_metrics_collector
    >>> from core.logging import CorrelationContext, DatabaseLogger
    >>> 
    >>> # Performance optimization
    >>> optimizer = get_performance_optimizer()
    >>> await optimizer.initialize()  # Enable async batching
    >>> 
    >>> # Metrics collection
    >>> metrics = get_metrics_collector()
    >>> metrics.increment_counter("user_requests", labels={"endpoint": "/api/users"})
    >>> 
    >>> # Database logging with correlation
    >>> with CorrelationContext.with_correlation_id():
    ...     db_logger = DatabaseLogger("postgresql")
    ...     db_logger.log_operation("select", duration_ms=50.0, success=True)

Integration Examples:
    >>> # Decorator for automatic operation tracking
    >>> from core.logging.metrics.performance import performance_optimized_log
    >>> 
    >>> @performance_optimized_log
    >>> async def fetch_user_data(user_id: int):
    ...     # Function will be automatically logged with performance metrics
    ...     return await get_user(user_id)
    >>> 
    >>> # Context manager for database operations
    >>> from core.logging import get_unified_logging_manager
    >>> 
    >>> manager = get_unified_logging_manager()
    >>> with manager.database_operation_context("postgresql", "complex_query"):
    ...     result = await execute_complex_query()
    ...     # Operation will be automatically logged with duration and success metrics
"""

# Import from base components
from .base.interfaces import LoggerInterface
from .base.loggers import get_logger, safe_log, get_safe_logger
from .base.formatters import StructuredFormatter, ColoredFormatter

# Import from context management
from .context.correlation import (
    CorrelationContext, 
    get_correlation_id, 
    set_correlation_id, 
    generate_correlation_id,
    get_or_generate_correlation_id,
    force_clear_correlation_id,
    with_correlation_context
)
from .context.adapters import CorrelationLoggingAdapter, log_with_correlation

# Import from specialized handlers
from .handlers.database import DatabaseLogger
from .handlers.request import RequestLogger

# Import from metrics system
from .metrics.collectors import MetricsCollector, get_metrics_collector
from .metrics.integration import (
    MetricsIntegratedLogger,
    get_metrics_integrated_logger,
    log_database_operation_with_metrics
)
from .metrics.performance import (
    PerformanceOptimizer,
    get_performance_optimizer,
    PerformanceStats
)

# Import from management layer
from .managers.unified import (
    UnifiedLoggingManager,
    get_unified_logging_manager,
    log_database_operation
)

# Core logging setup function
from .base.loggers import setup_structured_logging

# Configuration integration
from core.config.log_config import LoggingConfig, LogLevel, LogTimestampFormat

# Import migration check
from .config.migration import check_env_configuration

# Check for legacy environment variables
check_env_configuration()

# Backward compatibility aliases for core.monitoring imports
# These ensure existing code continues to work without changes
get_logger_with_metrics = get_unified_logging_manager().get_logger
log_database_operation_optimized = log_database_operation

# Create a decorator function for database operations
def log_database_operation_decorator(db_type: str, operation: str = None):
    """Decorator for automatic database operation logging.
    
    Args:
        db_type: Database type (e.g., "postgresql", "qdrant", "redis")
        operation: Operation name (defaults to function name if not provided)
        
    Returns:
        Decorator function that wraps the original function with database operation logging
    """
    manager = get_unified_logging_manager()
    return manager.log_database_operation_decorator(db_type, operation)

# Import interfaces
from core.logging.interfaces.core import ILogger, IFormatter, IHandler
from core.logging.interfaces.factories import ILoggerFactory, IFormatterFactory, IHandlerFactory
from core.logging.interfaces.context import ICorrelationProvider, IContextProvider
from core.logging.interfaces.database import IDatabaseLogger
from core.logging.interfaces.http import IRequestLogger
from core.logging.interfaces.metrics import IMetricsCollector, IPerformanceTracker

# Import core implementations
from core.logging.core.logger import Logger
from core.logging.core.formatter import JsonFormatter, TextFormatter
from core.logging.core.handler import ConsoleHandler, FileHandler

# Import specialized implementations
from core.logging.specialized.context.contextual_logger import ContextualLogger, AsyncContextualLogger
from core.logging.specialized.context.correlation_middleware import CorrelationMiddleware, AsyncCorrelationMiddleware, get_correlation_middleware
from core.logging.specialized.context.correlation_provider import CorrelationProvider
from core.logging.specialized.context.context_provider import ContextProvider

# Import database loggers
from core.logging.specialized.database.database_logger import DatabaseLogger, AsyncDatabaseLogger
from core.logging.specialized.database.sql_logger import SqlLogger, AsyncSqlLogger
from core.logging.specialized.database.vector_db_logger import VectorDbLogger, AsyncVectorDbLogger
from core.logging.specialized.database.redis_logger import RedisLogger, AsyncRedisLogger

# Import HTTP loggers
from core.logging.specialized.http.request_logger import RequestLogger, AsyncRequestLogger
from core.logging.specialized.http.request_logging_middleware import RequestLoggingMiddleware, AsyncRequestLoggingMiddleware, get_request_logging_middleware

# Import metrics
from core.logging.specialized.metrics.metrics_collector import MetricsCollector, AsyncMetricsCollector, Counter, Gauge, Histogram
from core.logging.specialized.metrics.performance_tracker import PerformanceTracker, AsyncPerformanceTracker
from core.logging.specialized.metrics.metrics_exporter import MetricsExporter, AsyncMetricsExporter

__all__ = [
    # Core functions
    "get_logger",
    "safe_log",
    "get_safe_logger", 
    "setup_structured_logging",
    
    # Configuration
    "LoggingConfig",
    "LogLevel", 
    "LogTimestampFormat",
    
    # Context management
    "CorrelationContext",
    "get_correlation_id", 
    "set_correlation_id",
    "generate_correlation_id",
    "get_or_generate_correlation_id",
    "force_clear_correlation_id",
    "with_correlation_context",
    "CorrelationLoggingAdapter",
    "log_with_correlation",
    
    # Specialized handlers
    "DatabaseLogger",
    "RequestLogger",
    
    # Formatters
    "StructuredFormatter",
    "ColoredFormatter",
    
    # Metrics system
    "MetricsCollector",
    "get_metrics_collector",
    "MetricsIntegratedLogger", 
    "get_metrics_integrated_logger",
    "log_database_operation_with_metrics",
    
    # Performance optimization
    "PerformanceOptimizer",
    "get_performance_optimizer", 
    "PerformanceStats",
    
    # Management layer
    "UnifiedLoggingManager",
    "get_unified_logging_manager",
    "log_database_operation",
    "log_database_operation_decorator",
    
    # Backward compatibility
    "get_logger_with_metrics",
    "log_database_operation_optimized",
    
    # Interfaces
    "LoggerInterface",
    "ILogger", "IFormatter", "IHandler", "ILoggerFactory", "IFormatterFactory", "IHandlerFactory",
    "ICorrelationProvider", "IContextProvider",
    "IDatabaseLogger", "IRequestLogger", "IMetricsCollector", "IPerformanceTracker",
    
    # Core
    "Logger", "JsonFormatter", "TextFormatter", "ConsoleHandler", "FileHandler",
    
    # Context
    "ContextualLogger", "AsyncContextualLogger",
    "CorrelationMiddleware", "AsyncCorrelationMiddleware", "get_correlation_middleware",
    "CorrelationProvider", "ContextProvider",
    
    # Database
    "DatabaseLogger", "AsyncDatabaseLogger",
    "SqlLogger", "AsyncSqlLogger",
    "VectorDbLogger", "AsyncVectorDbLogger",
    "RedisLogger", "AsyncRedisLogger",
    
    # HTTP
    "RequestLogger", "AsyncRequestLogger",
    "RequestLoggingMiddleware", "AsyncRequestLoggingMiddleware", "get_request_logging_middleware",
    
    # Metrics
    "MetricsCollector", "AsyncMetricsCollector",
    "Counter", "Gauge", "Histogram",
    "PerformanceTracker", "AsyncPerformanceTracker",
    "MetricsExporter", "AsyncMetricsExporter"
] 