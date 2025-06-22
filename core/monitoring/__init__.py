# Backward-compatibility layer for legacy 'core.monitoring' imports.
# This module now simply re-exports objects from the new logging subsystem
# (`core.logging`).  All legacy code and tests can continue to import from
# `core.monitoring.*` while we finish migrating the codebase.

from importlib import import_module

# Eagerly import local thin-wrapper sub-modules so that nested imports such as
# ``core.monitoring.logger`` continue to work.
for _sub in (
    "logger",
    "metrics",
    "performance_optimizer",
    "unified_manager",
    "context",
    "metrics_integration",
):
    import_module(f"{__name__}.{_sub}")

# Clean public namespace by re-exporting the most commonly used symbols.
from .logger import get_logger, DatabaseLogger, RequestLogger, setup_structured_logging  # noqa: F401
from .metrics import MetricsCollector, DatabaseMetrics, PerformanceTracker, get_metrics_collector  # noqa: F401
from .performance_optimizer import PerformanceOptimizer, performance_optimized_log, get_performance_optimizer  # noqa: F401
from .unified_manager import UnifiedLoggingManager, get_unified_logging_manager, get_logger_with_metrics, log_database_operation, log_database_operation_optimized  # noqa: F401

__all__ = [
    # Logger
    "get_logger",
    "DatabaseLogger",
    "RequestLogger",
    "setup_structured_logging",
    # Metrics
    "MetricsCollector",
    "DatabaseMetrics",
    "PerformanceTracker",
    "get_metrics_collector",
    # Performance
    "PerformanceOptimizer",
    "performance_optimized_log",
    "get_performance_optimizer",
    # Unified manager
    "UnifiedLoggingManager",
    "get_unified_logging_manager",
    "get_logger_with_metrics",
    "log_database_operation",
    "log_database_operation_optimized",
] 