"""
Metrics collection and integration system.

Provides metrics collectors, performance optimization, and logging integration.
"""

from .collectors import (
    DatabaseMetrics,
    MetricsCollector,
    PerformanceTracker,
    get_metrics_collector,
)
from .integration import (
    MetricsIntegratedLogger,
    get_global_metrics_logger,
    get_metrics_integrated_logger,
    log_database_operation_with_metrics,
)
from .performance import (
    BatchProcessor,
    LogEntry,
    LoggerInstanceCache,
    MetricEntry,
    OptimizedJSONEncoder,
    PerformanceOptimizer,
    PerformanceStats,
    get_cached_correlation_id,
    get_performance_optimizer,
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