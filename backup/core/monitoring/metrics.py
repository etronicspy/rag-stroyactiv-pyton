"""
Performance metrics collection system for RAG Construction Materials API.

Provides metrics collection, performance tracking, and database operation monitoring.
"""

import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from contextlib import contextmanager


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
        """
        Track database operation performance.
        
        Args:
            db_type: Database type (postgresql, qdrant, etc.)
            operation: Operation name (search, insert, update, etc.)
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
            record_count: Number of records processed
        """
        with self._lock:
            key = f"{db_type}.{operation}"
            self._metrics[key].update(duration_ms, success, record_count)
    
    def get_metrics(self, db_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Args:
            db_type: Filter by database type, or None for all
            
        Returns:
            Dictionary of metrics
        """
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
            # Если нет метрик, возвращаем пустой словарь
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
        """
        Context manager to time database operations.
        
        Args:
            db_type: Database type
            operation: Operation name
            record_count: Number of records being processed
        """
        start_time = time.time()
        error_occurred = False
        
        try:
            yield
        except Exception:
            error_occurred = True
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.track_operation(
                db_type=db_type,
                operation=operation,
                duration_ms=duration_ms,
                success=not error_occurred,
                record_count=record_count
            )


class MetricsCollector:
    """Central metrics collection system."""
    
    def __init__(self):
        self._metrics: Dict[str, List[MetricValue]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._performance_tracker = PerformanceTracker()
        
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            self._add_metric(name, value, MetricType.COUNTER, labels)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            self._add_metric(name, value, MetricType.GAUGE, labels)
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            # Keep only last 1000 values
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            self._add_metric(name, value, MetricType.HISTOGRAM, labels)
    
    def time_operation(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager to time operations."""
        @contextmanager
        def timer():
            start_time = time.time()
            try:
                yield
            finally:
                duration = time.time() - start_time
                self.record_histogram(f"{name}_duration_seconds", duration, labels)
        
        return timer()
    
    def get_performance_tracker(self) -> PerformanceTracker:
        """Get the performance tracker instance."""
        return self._performance_tracker
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a key from metric name and labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _add_metric(self, name: str, value: float, metric_type: MetricType, labels: Optional[Dict[str, str]]):
        """Add metric to the time series."""
        metric_value = MetricValue(
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {}
        )
        
        key = f"{name}:{metric_type.value}"
        self._metrics[key].append(metric_value)
        
        # Keep only last 1000 values per metric
        if len(self._metrics[key]) > 1000:
            self._metrics[key] = self._metrics[key][-1000:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {
                    name: {
                        'count': len(values),
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0,
                        'avg': sum(values) / len(values) if values else 0,
                        'p50': self._percentile(values, 50) if values else 0,
                        'p95': self._percentile(values, 95) if values else 0,
                        'p99': self._percentile(values, 99) if values else 0
                    }
                    for name, values in self._histograms.items()
                },
                'database_performance': self._performance_tracker.get_database_summary(),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get health-related metrics for monitoring."""
        performance_summary = self._performance_tracker.get_database_summary()
        
        health_metrics = {
            'uptime_seconds': time.time() - getattr(self, '_start_time', time.time()),
            'total_requests': self._counters.get('http_requests_total', 0),
            'error_rate': 0.0,
            'avg_response_time_ms': 0.0,
            'database_health': {}
        }
        
        # Calculate overall error rate
        total_ops = sum(db['total_operations'] for db in performance_summary.values())
        total_errors = sum(db['total_errors'] for db in performance_summary.values())
        
        if total_ops > 0:
            health_metrics['error_rate'] = round((total_errors / total_ops) * 100, 2)
        
        # Database health status
        for db_type, stats in performance_summary.items():
            health_metrics['database_health'][db_type] = {
                'total_operations': stats['total_operations'],
                'error_rate': round((stats['total_errors'] / stats['total_operations']) * 100, 2) if stats['total_operations'] > 0 else 0.0,
                'avg_response_time_ms': stats['avg_duration_ms'],
                'status': 'healthy' if stats['total_errors'] == 0 or (stats['total_errors'] / stats['total_operations']) < 0.05 else 'degraded'
            }
        
        return health_metrics


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector 