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
    OperationContext, LogLevel
)
from .context import (
    CorrelationContext, CorrelationLoggingAdapter,
    get_correlation_id, set_correlation_id, generate_correlation_id,
    get_or_generate_correlation_id, with_correlation_context,
    log_with_correlation
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
    "log_with_correlation"
] 