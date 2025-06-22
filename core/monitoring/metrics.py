import importlib
from types import ModuleType
from typing import Any

try:
    # Prefer new metrics from core.logging
    from core.logging import MetricsCollector, PerformanceTracker
    # DatabaseMetrics may not exist in new module, fallback to backup
    try:
        from core.logging import DatabaseMetrics  # type: ignore
    except ImportError:  # pragma: no cover
        _backup_metrics: ModuleType = importlib.import_module("backup.core.monitoring.metrics")
        DatabaseMetrics = getattr(_backup_metrics, "DatabaseMetrics")  # type: ignore
except ImportError:  # pragma: no cover
    # Fallback entirely to backup implementation
    _backup_metrics: ModuleType = importlib.import_module("backup.core.monitoring.metrics")
    MetricsCollector = getattr(_backup_metrics, "MetricsCollector")  # type: ignore
    PerformanceTracker = getattr(_backup_metrics, "PerformanceTracker")  # type: ignore
    DatabaseMetrics = getattr(_backup_metrics, "DatabaseMetrics")  # type: ignore

# Re-export helper

def get_metrics_collector() -> "MetricsCollector":
    """Return a global metrics collector instance (singleton-like)."""
    return MetricsCollector()

__all__ = [
    "MetricsCollector",
    "DatabaseMetrics",
    "PerformanceTracker",
    "get_metrics_collector",
] 