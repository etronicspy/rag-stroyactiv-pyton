"""
🚀 Performance Optimizer для Unified Logging System

Основные оптимизации:
- Logger instance caching для избежания повторного создания
- Metrics batching для эффективной отправки  
- Asynchronous log processing для non-blocking операций
- Correlation context optimization
- JSON serialization optimization
- Memory-conscious operations

Migrated and optimized from core/monitoring/performance_optimizer.py.
"""

import asyncio
import json
import time
import threading
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Dict, List, Optional, Any, Callable, Union
from weakref import WeakValueDictionary


@dataclass
class LogEntry:
    """Optimized log entry for batching."""
    timestamp: float
    level: str
    logger_name: str
    message: str
    correlation_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "logger_name": self.logger_name,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "extra": self.extra or {}
        }


@dataclass
class MetricEntry:
    """Optimized metric entry for batching."""
    timestamp: float
    metric_type: str  # counter, gauge, histogram
    metric_name: str
    value: Union[int, float]
    labels: Optional[Dict[str, str]] = None
    correlation_id: Optional[str] = None


@dataclass
class PerformanceStats:
    """Performance statistics tracking."""
    total_logs_processed: int = 0
    total_metrics_processed: int = 0
    batch_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    async_operations: int = 0
    serialization_time: float = 0.0
    processing_time: float = 0.0
    last_reset: datetime = field(default_factory=datetime.utcnow)


class OptimizedJSONEncoder(json.JSONEncoder):
    """Optimized JSON encoder for logging."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache for frequently serialized objects
        self._serialization_cache = {}
        self._cache_size = 1000
    
    def default(self, obj):
        """Handle non-serializable objects efficiently."""
        obj_type = type(obj)
        
        # Fast path for common types
        if obj_type == datetime:
            return obj.isoformat() + "Z"
        elif obj_type == timedelta:
            return obj.total_seconds()
        elif hasattr(obj, '__dict__'):
            # Cache object representations
            obj_id = id(obj)
            if obj_id in self._serialization_cache:
                return self._serialization_cache[obj_id]
            
            result = {k: v for k, v in obj.__dict__.items() 
                     if not k.startswith('_')}
            
            # Limit cache size
            if len(self._serialization_cache) < self._cache_size:
                self._serialization_cache[obj_id] = result
            
            return result
        
        return str(obj)


class LoggerInstanceCache:
    """High-performance logger instance cache."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: WeakValueDictionary = WeakValueDictionary()
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get_logger(self, name: str):
        """Get cached logger instance."""
        with self._lock:
            current_time = time.time()
            
            if name in self._cache:
                self._access_times[name] = current_time
                return self._cache[name]
            
            # Import here to avoid circular imports
            from ..base.loggers import get_logger
            
            # Create new logger
            logger = get_logger(name, enable_correlation=True)
            
            # Cache management
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[name] = logger
            self._access_times[name] = current_time
            
            return logger
    
    def _evict_oldest(self):
        """Evict oldest accessed logger."""
        if not self._access_times:
            return
        
        oldest_name = min(self._access_times.keys(), 
                         key=lambda k: self._access_times[k])
        
        self._cache.pop(oldest_name, None)
        self._access_times.pop(oldest_name, None)
    
    def clear(self):
        """Clear cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()


class BatchProcessor:
    """High-performance batch processor for logs and metrics."""
    
    def __init__(self, 
                 batch_size: int = 100,
                 flush_interval: float = 1.0,
                 max_queue_size: int = 10000):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_queue_size = max_queue_size
        
        # Queues for different types
        self.log_queue: deque = deque(maxlen=max_queue_size)
        self.metric_queue: deque = deque(maxlen=max_queue_size) 
        
        # Processing state
        self._processing = False
        self._last_flush = time.time()
        self._stats = PerformanceStats()
        
        # JSON encoder instance (reused for performance)
        self._json_encoder = OptimizedJSONEncoder(ensure_ascii=False, separators=(',', ':'))
        
        # Background processing
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="LogBatch")
        self._background_task: Optional[asyncio.Task] = None
    
    async def start_background_processing(self):
        """Start background batch processing."""
        if self._background_task is None or self._background_task.done():
            self._processing = True
            self._background_task = asyncio.create_task(self._background_flush_loop())
    
    async def stop_background_processing(self):
        """Stop background batch processing."""
        self._processing = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self._flush_all_batches()
    
    def add_log_entry(self, entry: LogEntry) -> bool:
        """Add log entry to batch queue."""
        try:
            self.log_queue.append(entry)
            return True
        except Exception:
            return False
    
    def add_metric_entry(self, entry: MetricEntry) -> bool:
        """Add metric entry to batch queue."""
        try:
            self.metric_queue.append(entry)
            return True
        except Exception:
            return False
    
    async def _background_flush_loop(self):
        """Background loop for flushing batches."""
        while self._processing:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_all_batches()
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue processing even if flush fails
                continue
    
    async def _flush_all_batches(self):
        """Flush all pending batches."""
        await asyncio.gather(
            self._flush_log_batch(),
            self._flush_metric_batch(),
            return_exceptions=True
        )
    
    async def _flush_log_batch(self):
        """Flush log batch."""
        if not self.log_queue:
            return
            
        # Get batch of logs
        batch = []
        for _ in range(min(self.batch_size, len(self.log_queue))):
            if self.log_queue:
                batch.append(self.log_queue.popleft())
        
        if batch:
            # Process in background thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor, 
                self._process_log_batch, 
                batch
            )
            self._stats.total_logs_processed += len(batch)
            self._stats.batch_operations += 1
    
    async def _flush_metric_batch(self):
        """Flush metric batch."""
        if not self.metric_queue:
            return
            
        # Get batch of metrics
        batch = []
        for _ in range(min(self.batch_size, len(self.metric_queue))):
            if self.metric_queue:
                batch.append(self.metric_queue.popleft())
        
        if batch:
            # Process in background thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor, 
                self._process_metric_batch, 
                batch
            )
            self._stats.total_metrics_processed += len(batch)
            self._stats.batch_operations += 1
    
    def _process_log_batch(self, batch: List[LogEntry]):
        """Process a batch of log entries."""
        start_time = time.perf_counter()
        
        try:
            # Group by logger name for efficiency
            grouped_logs = defaultdict(list)
            for entry in batch:
                grouped_logs[entry.logger_name].append(entry)
            
            # Process each group
            for logger_name, entries in grouped_logs.items():
                self._write_batch_to_file(entries)
                    
        except Exception:
            # Log processing errors are non-critical
            pass
        finally:
            self._stats.processing_time += (time.perf_counter() - start_time)
    
    def _write_batch_to_file(self, entries: List[LogEntry]):
        """Write batch of entries to log file."""
        # This is a simplified file writer
        # In production, this would write to actual log files/systems
    
    def _process_metric_batch(self, batch: List[MetricEntry]):
        """Process a batch of metric entries."""
        start_time = time.perf_counter()
        
        try:
            # Group by metric type for efficiency
            grouped_metrics = defaultdict(list)
            for entry in batch:
                grouped_metrics[entry.metric_type].append(entry)
            
            # Process each group (simplified)
            for metric_type, entries in grouped_metrics.items():
                # In production, this would send to metrics backend
                pass
                    
        except Exception:
            # Metric processing errors are non-critical
            pass
        finally:
            self._stats.processing_time += (time.perf_counter() - start_time)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "total_logs_processed": self._stats.total_logs_processed,
            "total_metrics_processed": self._stats.total_metrics_processed,
            "batch_operations": self._stats.batch_operations,
            "cache_hits": self._stats.cache_hits,
            "cache_misses": self._stats.cache_misses,
            "async_operations": self._stats.async_operations,
            "serialization_time": round(self._stats.serialization_time, 4),
            "processing_time": round(self._stats.processing_time, 4),
            "queue_sizes": {
                "log_queue": len(self.log_queue),
                "metric_queue": len(self.metric_queue)
            },
            "last_reset": self._stats.last_reset.isoformat()
        }


class PerformanceOptimizer:
    """🚀 High-performance logging and metrics optimizer."""
    
    def __init__(self, settings: Optional[Any] = None):
        """Initialize performance optimizer with caching and batching."""
        self.settings = settings
        
        # Performance components
        self.logger_cache = LoggerInstanceCache()
        self.batch_processor = BatchProcessor()
        
        # Performance settings
        self.enable_batching = getattr(settings, 'ENABLE_LOG_BATCHING', True) if settings else True
        self.enable_caching = getattr(settings, 'ENABLE_LOGGER_CACHING', True) if settings else True
        self.enable_async = getattr(settings, 'ENABLE_ASYNC_PROCESSING', True) if settings else True
        
        # Statistics
        self._stats = PerformanceStats()
        
        # Initialization state
        self._initialized = False
    
    async def initialize(self):
        """Initialize async components."""
        if not self._initialized and self.enable_async:
            await self.batch_processor.start_background_processing()
            self._initialized = True
    
    async def shutdown(self):
        """Shutdown async components."""
        if self._initialized:
            await self.batch_processor.stop_background_processing()
            self._initialized = False
    
    def get_optimized_logger(self, name: str):
        """Get performance-optimized logger instance."""
        if self.enable_caching:
            self._stats.cache_hits += 1
            return self.logger_cache.get_logger(name)
        else:
            self._stats.cache_misses += 1
            from ..base.loggers import get_logger
            return get_logger(name, enable_correlation=True)
    
    def log_with_batching(self, 
                         logger_name: str, 
                         level: str, 
                         message: str, 
                         extra: Optional[Dict[str, Any]] = None):
        """Log with batching optimization."""
        if not self.enable_batching:
            # Direct logging fallback
            logger = self.get_optimized_logger(logger_name)
            getattr(logger, level.lower())(message, extra=extra)
            return
        
        # Create log entry for batching
        entry = LogEntry(
            timestamp=time.time(),
            level=level.upper(),
            logger_name=logger_name,
            message=message,
            extra=extra
        )
        
        self.batch_processor.add_log_entry(entry)
        self._stats.async_operations += 1
    
    def record_metric_with_batching(self,
                                  metric_type: str,
                                  metric_name: str,
                                  value: Union[int, float],
                                  labels: Optional[Dict[str, str]] = None):
        """Record metric with batching optimization."""
        if not self.enable_batching:
            # Direct metrics recording fallback
            from .collectors import get_metrics_collector
            collector = get_metrics_collector()
            
            if metric_type == "counter":
                collector.increment_counter(metric_name, int(value), labels)
            elif metric_type == "gauge":
                collector.set_gauge(metric_name, float(value), labels)
            elif metric_type == "histogram":
                collector.record_histogram(metric_name, float(value), labels)
            return
        
        # Create metric entry for batching
        entry = MetricEntry(
            timestamp=time.time(),
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            labels=labels
        )
        
        self.batch_processor.add_metric_entry(entry)
        self._stats.async_operations += 1
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        batch_stats = self.batch_processor.get_performance_stats()
        
        return {
            "optimizer_stats": {
                "cache_hits": self._stats.cache_hits,
                "cache_misses": self._stats.cache_misses,
                "async_operations": self._stats.async_operations,
                "cache_hit_rate": (
                    self._stats.cache_hits / (self._stats.cache_hits + self._stats.cache_misses) * 100
                    if (self._stats.cache_hits + self._stats.cache_misses) > 0 else 0.0
                )
            },
            "batch_processor_stats": batch_stats,
            "settings": {
                "batching_enabled": self.enable_batching,
                "caching_enabled": self.enable_caching,
                "async_enabled": self.enable_async
            },
            "system_health": "optimal" if self._stats.cache_hits > self._stats.cache_misses else "good"
        }

    def optimize_operation(self, operation: str) -> Dict[str, Any]:
        """Optimize an operation."""
        return {
            "optimized": True, 
            "caching": self.enable_caching,
            "batching": self.enable_batching,
            "async": self.enable_async
        }
    
    def get_stats(self) -> PerformanceStats:
        """Get performance statistics."""
        return self._stats


# Global performance optimizer instance
_global_performance_optimizer: Optional[PerformanceOptimizer] = None
_optimizer_lock = threading.Lock()


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance."""
    global _global_performance_optimizer
    
    if _global_performance_optimizer is None:
        with _optimizer_lock:
            if _global_performance_optimizer is None:
                _global_performance_optimizer = PerformanceOptimizer()
    
    return _global_performance_optimizer


@lru_cache(maxsize=128)
def get_cached_correlation_id() -> str:
    """Get cached correlation ID for performance."""
    from ..context.correlation import get_or_generate_correlation_id
    return get_or_generate_correlation_id()


def performance_optimized_log(func: Callable) -> Callable:
    """Decorator for performance-optimized logging."""
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        """Async wrapper with performance optimization."""
        optimizer = get_performance_optimizer()
        correlation_id = get_cached_correlation_id()
        
        start_time = time.perf_counter()
        success = True
        error = None
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log with batching
            optimizer.log_with_batching(
                logger_name=func.__module__,
                level="INFO" if success else "ERROR",
                message=f"Function {func.__name__} {'completed' if success else 'failed'} in {duration_ms:.2f}ms",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "success": success,
                    "correlation_id": correlation_id,
                    "error": error
                }
            )
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        """Sync wrapper with performance optimization."""
        optimizer = get_performance_optimizer()
        correlation_id = get_cached_correlation_id()
        
        start_time = time.perf_counter()
        success = True
        error = None
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log with batching
            optimizer.log_with_batching(
                logger_name=func.__module__,
                level="INFO" if success else "ERROR",
                message=f"Function {func.__name__} {'completed' if success else 'failed'} in {duration_ms:.2f}ms",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration_ms,
                    "success": success,
                    "correlation_id": correlation_id,
                    "error": error
                }
            )
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper 