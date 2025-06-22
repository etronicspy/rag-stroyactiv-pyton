"""High-level re-exports for metrics utilities.

This module previously contained dynamic fallbacks to the legacy implementation in
``backup.core.monitoring.metrics``.  The project has fully migrated to the new
implementation under ``core.logging.metrics``.  All legacy fallbacks have been
removed to simplify the dependency graph and eliminate obsolete code paths.

See also: ``PLAN_DOCS/LEGACY_CODE_REMOVAL_PLAN.md``.
"""

# NOTE: No runtime fallbacks – rely exclusively on the canonical metrics module.
from core.logging.metrics import (
    MetricsCollector,
    PerformanceTracker,
    DatabaseMetrics,
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