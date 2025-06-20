"""
Metrics collection and integration system.

Provides metrics collectors, performance optimization, and logging integration.
"""

from .collectors import MetricsCollector, get_metrics_collector, DatabaseMetrics, PerformanceTracker
from .integration import (
    MetricsIntegratedLogger,
    get_metrics_integrated_logger, 
    log_database_operation_with_metrics,
    get_global_metrics_logger
)
from .performance import (
    PerformanceOptimizer,
    get_performance_optimizer,
    PerformanceStats,
    LogEntry,
    MetricEntry,
    OptimizedJSONEncoder,
    LoggerInstanceCache,
    BatchProcessor,
    get_cached_correlation_id
)

__all__ = [
    # Core metrics
    "MetricsCollector",
    "get_metrics_collector", 
    "DatabaseMetrics",
    "PerformanceTracker",
    
    # Integration
    "MetricsIntegratedLogger",
    "get_metrics_integrated_logger",
    "log_database_operation_with_metrics", 
    "get_global_metrics_logger",
    
    # Performance optimization
    "PerformanceOptimizer",
    "get_performance_optimizer",
    "PerformanceStats",
    "LogEntry",
    "MetricEntry", 
    "OptimizedJSONEncoder",
    "LoggerInstanceCache",
    "BatchProcessor",
    "get_cached_correlation_id"
] 