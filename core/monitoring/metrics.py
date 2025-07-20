"""High-level re-exports for metrics utilities."""

# NOTE: No runtime fallbacks – rely exclusively on the canonical metrics module.
from core.logging.metrics import (
    DatabaseMetrics,
    MetricsCollector,
    PerformanceTracker,
)
from core.logging.metrics import (
    get_metrics_collector as _get_collector,
)

# Re-export helper

def get_metrics_collector() -> "MetricsCollector":
    """Return the shared metrics collector instance exposed by the new module."""
    return _get_collector()

__all__ = [
    "MetricsCollector",
    "DatabaseMetrics",
    "PerformanceTracker",
    "get_metrics_collector",
] 