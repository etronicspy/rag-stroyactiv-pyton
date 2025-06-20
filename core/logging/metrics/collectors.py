"""
Performance metrics collection system.

Provides metrics collection, performance tracking, and database operation monitoring.
Migrated and optimized from core/monitoring/metrics.py.
"""

import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager

from ..base.interfaces import MetricsCollectorInterface


class MetricType(str, Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Individual metric value with timestamp."""
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class DatabaseMetrics:
    """Database-specific metrics collection."""
    operation_count: int = 0
    total_duration_ms: float = 0.0
    error_count: int = 0
    success_count: int = 0
    avg_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    records_processed: int = 0
    last_operation_time: Optional[datetime] = None
    operation_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def update(self, duration_ms: float, success: bool, record_count: Optional[int] = None):
        """Update metrics with new operation data."""
        self.operation_count += 1
        self.total_duration_ms += duration_ms
        self.records_processed += record_count or 0
        self.last_operation_time = datetime.utcnow()
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            
        # Update duration statistics
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.avg_duration_ms = self.total_duration_ms / self.operation_count if self.operation_count > 0 else 0.0
        
        # Add to history
        self.operation_history.append({
            'timestamp': self.last_operation_time,
            'duration_ms': duration_ms,
            'success': success,
            'record_count': record_count
        })
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.operation_count == 0:
            return 0.0
        return (self.success_count / self.operation_count) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        if self.operation_count == 0:
            return 0.0
        return (self.error_count / self.operation_count) * 100
    
    def get_recent_operations(self, minutes: int = 5) -> List[Dict]:
        """Get operations from the last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            op for op in self.operation_history 
            if op['timestamp'] >= cutoff_time
        ]
    
    def get_stats_dict(self) -> Dict[str, Any]:
        """Get metrics as dictionary for JSON serialization."""
        return {
            'operation_count': self.operation_count,
            'total_duration_ms': round(self.total_duration_ms, 2),
            'avg_duration_ms': round(self.avg_duration_ms, 2),
            'max_duration_ms': round(self.max_duration_ms, 2),
            'min_duration_ms': round(self.min_duration_ms, 2) if self.min_duration_ms != float('inf') else 0.0,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': round(self.success_rate, 2),
            'error_rate': round(self.error_rate, 2),
            'records_processed': self.records_processed,
            'last_operation_time': self.last_operation_time.isoformat() if self.last_operation_time else None
        }


class PerformanceTracker:
    """Performance tracking for database operations."""
    
    def __init__(self):
        self._metrics: Dict[str, DatabaseMetrics] = defaultdict(DatabaseMetrics)
        self._lock = threading.Lock()
        
    def track_operation(
        self,
        db_type: str,
        operation: str,
        duration_ms: float,
        success: bool,
        record_count: int = 0
    ):
        """Track database operation performance."""
        with self._lock:
            key = f"{db_type}.{operation}"
            self._metrics[key].update(duration_ms, success, record_count)
    
    def get_metrics(self, db_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics."""
        with self._lock:
            if db_type:
                filtered_metrics = {
                    key: metrics.get_stats_dict() 
                    for key, metrics in self._metrics.items() 
                    if key.startswith(f"{db_type}.")
                }
                return filtered_metrics
            else:
                return {
                    key: metrics.get_stats_dict() 
                    for key, metrics in self._metrics.items()
                }
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all databases."""
        with self._lock:
            if not self._metrics:
                return {}
                
            summary = defaultdict(lambda: {
                'total_operations': 0,
                'total_errors': 0,
                'avg_duration_ms': 0.0,
                'operations': {}
            })
            
            for key, metrics in self._metrics.items():
                db_type, operation = key.split('.', 1)
                summary[db_type]['total_operations'] += metrics.operation_count
                summary[db_type]['total_errors'] += metrics.error_count
                summary[db_type]['operations'][operation] = metrics.get_stats_dict()
            
            # Calculate averages
            for db_type, data in summary.items():
                if data['total_operations'] > 0:
                    total_duration = sum(
                        op['total_duration_ms'] 
                        for op in data['operations'].values()
                    )
                    data['avg_duration_ms'] = round(
                        total_duration / data['total_operations'], 2
                    )
                    data['success_rate'] = round(
                        ((data['total_operations'] - data['total_errors']) / data['total_operations']) * 100, 2
                    )
            
            return dict(summary)
    
    @contextmanager
    def time_operation(self, db_type: str, operation: str, record_count: int = 0):
        """Context manager to time database operations."""
        start_time = time.perf_counter()
        success = True
        
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.track_operation(db_type, operation, duration_ms, success, record_count)


class MetricsCollector(MetricsCollectorInterface):
    """High-performance metrics collector."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self._metrics: Dict[str, List[MetricValue]] = defaultdict(list)
        self._lock = threading.Lock()
        self._performance_tracker = PerformanceTracker()
        
    def record_operation(
        self, 
        operation: str, 
        duration_ms: float, 
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an operation metric."""
        metric_value = MetricValue(
            value=duration_ms,
            timestamp=datetime.utcnow(),
            labels=metadata or {}
        )
        
        with self._lock:
            self._metrics[operation].append(metric_value)
            # Keep only last 1000 metrics per operation
            if len(self._metrics[operation]) > 1000:
                self._metrics[operation] = self._metrics[operation][-1000:]
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        self._add_metric(name, value, MetricType.COUNTER, labels)
        
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        self._add_metric(name, value, MetricType.GAUGE, labels)
        
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        self._add_metric(name, value, MetricType.HISTOGRAM, labels)
    
    @contextmanager
    def time_operation(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager to time operations."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.record_histogram(f"{name}.duration_ms", duration_ms, labels)
    
    def get_performance_tracker(self) -> PerformanceTracker:
        """Get the performance tracker instance."""
        return self._performance_tracker
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a unique key for metric with labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _add_metric(self, name: str, value: float, metric_type: MetricType, labels: Optional[Dict[str, str]]):
        """Add a metric value."""
        key = self._make_key(name, labels)
        metric_value = MetricValue(
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {}
        )
        
        with self._lock:
            self._metrics[key].append(metric_value)
            # Keep only last 1000 metrics per key
            if len(self._metrics[key]) > 1000:
                self._metrics[key] = self._metrics[key][-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive metrics statistics."""
        with self._lock:
            stats = {}
            for key, values in self._metrics.items():
                if not values:
                    continue
                    
                numeric_values = [v.value for v in values]
                stats[key] = {
                    'count': len(numeric_values),
                    'sum': sum(numeric_values),
                    'avg': sum(numeric_values) / len(numeric_values),
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'p50': self._percentile(numeric_values, 50),
                    'p95': self._percentile(numeric_values, 95),
                    'p99': self._percentile(numeric_values, 99),
                    'last_updated': max(v.timestamp for v in values).isoformat()
                }
            
            return stats
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for monitoring."""
        stats = self.get_stats()
        total_operations = sum(len(hist) for hist in stats.get('histograms', {}).values())
        
        return {
            'status': 'healthy',
            'total_counters': len(stats.get('counters', {})),
            'total_gauges': len(stats.get('gauges', {})),
            'total_histograms': len(stats.get('histograms', {})),
            'total_operations': total_operations,
            'performance_tracker': {
                'database_summary': self._performance_tracker.get_database_summary()
            }
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary for health checks."""
        stats = self.get_stats()
        return {
            'counters': stats.get('counters', {}),
            'gauges': stats.get('gauges', {}),
            'histograms': stats.get('histograms', {}),
            'performance': self._performance_tracker.get_database_summary(),
            'health': self.get_health_metrics()
        }


# Global metrics collector instance
_global_metrics_collector: Optional[MetricsCollector] = None
_metrics_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _global_metrics_collector
    
    if _global_metrics_collector is None:
        with _metrics_lock:
            if _global_metrics_collector is None:
                _global_metrics_collector = MetricsCollector()
    
    return _global_metrics_collector 