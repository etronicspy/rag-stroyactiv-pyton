"""
Monitoring and logging utilities for RAG Construction Materials API.

This module provides centralized monitoring, logging, and metrics collection
for database operations and application performance.
"""

from .logger import get_logger, DatabaseLogger, setup_structured_logging
from .metrics import MetricsCollector, DatabaseMetrics, PerformanceTracker, get_metrics_collector
from .unified_manager import (
    UnifiedLoggingManager, get_unified_logging_manager, 
    get_logger_with_metrics, log_database_operation,
    OperationContext, LogLevel,
    log_database_operation_optimized
)
from .context import (
    CorrelationContext, CorrelationLoggingAdapter,
    get_correlation_id, set_correlation_id, generate_correlation_id,
    get_or_generate_correlation_id, with_correlation_context,
    log_with_correlation
)

# 🚀 ЭТАП 4.3: Performance Optimization Exports
from .performance_optimizer import (
    PerformanceOptimizer,
    get_performance_optimizer,
    performance_optimized_log,
    LogEntry,
    MetricEntry,
    PerformanceStats,
    OptimizedJSONEncoder,
    LoggerInstanceCache,
    BatchProcessor,
    get_cached_correlation_id
)

# 🎯 ЭТАП 5.3: Metrics Integration Exports
from .metrics_integration import (
    MetricsIntegratedLogger,
    get_metrics_integrated_logger,
    log_database_operation_with_metrics,
    get_global_metrics_logger
)

__all__ = [
    "get_logger",
    "DatabaseLogger", 
    "setup_structured_logging",
    "MetricsCollector",
    "DatabaseMetrics",
    "PerformanceTracker",
    "get_metrics_collector",
    # Unified manager exports
    "UnifiedLoggingManager",
    "get_unified_logging_manager",
    "get_logger_with_metrics",
    "log_database_operation",
    "log_database_operation_optimized",
    "OperationContext",
    "LogLevel",
    # Correlation context system exports
    "CorrelationContext",
    "CorrelationLoggingAdapter",
    "get_correlation_id",
    "set_correlation_id",
    "generate_correlation_id",
    "get_or_generate_correlation_id",
    "with_correlation_context",
    "log_with_correlation",
    # 🚀 ЭТАП 4.3: Performance Optimization
    "PerformanceOptimizer",
    "get_performance_optimizer",
    "performance_optimized_log",
    "LogEntry",
    "MetricEntry", 
    "PerformanceStats",
    "OptimizedJSONEncoder",
    "LoggerInstanceCache",
    "BatchProcessor",
    "get_cached_correlation_id",
    # 🎯 ЭТАП 5.3: Metrics Integration
    "MetricsIntegratedLogger",
    "get_metrics_integrated_logger",
    "log_database_operation_with_metrics",
    "get_global_metrics_logger"
] 