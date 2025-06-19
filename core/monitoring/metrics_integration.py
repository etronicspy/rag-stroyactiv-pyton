"""
🚀 ЭТАП 5.1: Metrics Integration for Unified Logging System

Интеграция единой системы логгирования с существующей системой метрик.
Автоматическая отправка метрик при логгировании операций.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
from datetime import datetime

from .logger import get_logger
from .metrics import MetricsCollector, get_metrics_collector, PerformanceTracker
from .context import get_correlation_id, CorrelationContext
from .performance_optimizer import get_performance_optimizer, MetricEntry


class MetricsIntegratedLogger:
    """
    🎯 Logger с автоматической отправкой метрик.
    
    Интегрирует логгирование с системой метрик для полного мониторинга:
    - Database операции → Database metrics + Performance tracking
    - HTTP requests → Request metrics + Response time tracking  
    - Application events → Event counters + Gauge updates
    - Performance data → Histogram recording + Percentile tracking
    """
    
    def __init__(self, 
                 logger_name: str,
                 metrics_collector: Optional[MetricsCollector] = None,
                 enable_performance_optimization: bool = True):
        """
        Initialize metrics-integrated logger.
        
        Args:
            logger_name: Name for the logger instance
            metrics_collector: Optional metrics collector (uses global if None)
            enable_performance_optimization: Enable performance optimizations
        """
        self.logger_name = logger_name
        self.base_logger = get_logger(logger_name)
        self.metrics = metrics_collector or get_metrics_collector()
        self.performance_tracker = self.metrics.get_performance_tracker()
        
        # Performance optimization integration
        self.enable_performance_optimization = enable_performance_optimization
        if enable_performance_optimization:
            self.performance_optimizer = get_performance_optimizer()
        else:
            self.performance_optimizer = None
    
    def log_database_operation(self, 
                             db_type: str, 
                             operation: str, 
                             duration_ms: Optional[float] = None,
                             success: Optional[bool] = None,
                             record_count: Optional[int] = None,
                             error: Optional[str] = None,
                             **kwargs) -> None:
        """
        🎯 Log database operation with automatic metrics integration.
        
        Combines:
        - Structured logging with correlation ID
        - Performance metrics tracking
        - Database-specific metrics collection
        - Error rate monitoring
        
        Args:
            db_type: Database type (postgresql, qdrant, redis, etc.)
            operation: Operation name (search, insert, update, etc.)
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
            record_count: Number of records processed
            error: Error message if operation failed
            **kwargs: Additional context for logging
        """
        correlation_id = get_correlation_id()
        
        # Prepare log context
        log_context = {
            'db_type': db_type,
            'operation': operation,
            'correlation_id': correlation_id,
            **kwargs
        }
        
        if record_count is not None:
            log_context['record_count'] = record_count
        
        if duration_ms is not None:
            log_context['duration_ms'] = duration_ms
        
        if error:
            log_context['error'] = error
        
        # 📊 LOGGING: Structured log entry
        if success is True:
            self.base_logger.info(
                f"Database operation completed: {db_type}.{operation}",
                extra=log_context
            )
        elif success is False:
            self.base_logger.error(
                f"Database operation failed: {db_type}.{operation} - {error}",
                extra=log_context
            )
        else:
            self.base_logger.debug(
                f"Database operation logged: {db_type}.{operation}",
                extra=log_context
            )
        
        # 📈 METRICS: Performance tracking
        if duration_ms is not None and success is not None:
            self.performance_tracker.track_operation(
                db_type=db_type,
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                record_count=record_count
            )
        
        # 📊 METRICS: Counter increments
        operation_label = {"db_type": db_type, "operation": operation}
        self.metrics.increment_counter("database_operations_total", 1, operation_label)
        
        if success is True:
            self.metrics.increment_counter("database_operations_success_total", 1, operation_label)
        elif success is False:
            self.metrics.increment_counter("database_operations_error_total", 1, operation_label)
        
        # 📊 METRICS: Duration histogram
        if duration_ms is not None:
            self.metrics.record_histogram(
                "database_operation_duration_ms", 
                duration_ms, 
                operation_label
            )
        
        # 📊 METRICS: Record count gauge
        if record_count is not None and record_count > 0:
            self.metrics.set_gauge(
                f"database_last_operation_records_{db_type}_{operation}",
                float(record_count),
                {"db_type": db_type, "operation": operation}
            )
        
        # 🚀 PERFORMANCE OPTIMIZATION: Batch metrics if enabled
        if self.enable_performance_optimization and self.performance_optimizer:
            if duration_ms is not None:
                self.performance_optimizer.record_metric_with_batching(
                    metric_type="histogram",
                    metric_name="database_operation_duration_optimized",
                    value=duration_ms,
                    labels=operation_label
                )
    
    def log_http_request(self, 
                        method: str,
                        path: str, 
                        status_code: int,
                        duration_ms: float,
                        request_size_bytes: int = 0,
                        response_size_bytes: int = 0,
                        user_agent: Optional[str] = None,
                        ip_address: Optional[str] = None,
                        **kwargs) -> None:
        """
        🎯 Log HTTP request with automatic metrics integration.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            request_size_bytes: Request body size
            response_size_bytes: Response body size
            user_agent: User agent string
            ip_address: Client IP address
            **kwargs: Additional context
        """
        correlation_id = get_correlation_id()
        
        # Prepare log context
        log_context = {
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'correlation_id': correlation_id,
            'request_size_bytes': request_size_bytes,
            'response_size_bytes': response_size_bytes,
            **kwargs
        }
        
        if user_agent:
            log_context['user_agent'] = user_agent
        if ip_address:
            log_context['ip_address'] = ip_address
        
        # 📊 LOGGING: Structured log entry
        if 200 <= status_code < 400:
            self.base_logger.info(
                f"HTTP request completed: {method} {path} → {status_code}",
                extra=log_context
            )
        else:
            self.base_logger.warning(
                f"HTTP request error: {method} {path} → {status_code}",
                extra=log_context
            )
        
        # 📈 METRICS: HTTP request tracking
        request_labels = {
            "method": method,
            "status_code": str(status_code),
            "path_pattern": self._normalize_path(path)
        }
        
        # Counter metrics
        self.metrics.increment_counter("http_requests_total", 1, request_labels)
        
        # Duration histogram
        self.metrics.record_histogram(
            "http_request_duration_ms",
            duration_ms,
            request_labels
        )
        
        # Size metrics
        if request_size_bytes > 0:
            self.metrics.record_histogram(
                "http_request_size_bytes",
                float(request_size_bytes),
                {"method": method}
            )
        
        if response_size_bytes > 0:
            self.metrics.record_histogram(
                "http_response_size_bytes", 
                float(response_size_bytes),
                {"method": method, "status_code": str(status_code)}
            )
        
        # 🚀 PERFORMANCE OPTIMIZATION: Batch metrics if enabled
        if self.enable_performance_optimization and self.performance_optimizer:
            self.performance_optimizer.record_metric_with_batching(
                metric_type="histogram",
                metric_name="http_request_duration_optimized",
                value=duration_ms,
                labels=request_labels
            )
    
    def log_application_event(self,
                            event_type: str,
                            event_name: str,
                            success: bool = True,
                            duration_ms: Optional[float] = None,
                            metadata: Optional[Dict[str, Any]] = None,
                            **kwargs) -> None:
        """
        🎯 Log application event with automatic metrics integration.
        
        Args:
            event_type: Type of event (startup, shutdown, batch_process, etc.)
            event_name: Specific event name
            success: Whether event was successful
            duration_ms: Event duration if applicable
            metadata: Additional event metadata
            **kwargs: Additional context
        """
        correlation_id = get_correlation_id()
        
        # Prepare log context
        log_context = {
            'event_type': event_type,
            'event_name': event_name,
            'success': success,
            'correlation_id': correlation_id,
            **(metadata or {}),
            **kwargs
        }
        
        if duration_ms is not None:
            log_context['duration_ms'] = duration_ms
        
        # 📊 LOGGING: Structured log entry
        if success:
            self.base_logger.info(
                f"Application event: {event_type}.{event_name} completed successfully",
                extra=log_context
            )
        else:
            self.base_logger.error(
                f"Application event: {event_type}.{event_name} failed",
                extra=log_context
            )
        
        # 📈 METRICS: Event tracking
        event_labels = {"event_type": event_type, "event_name": event_name}
        
        # Counter metrics
        self.metrics.increment_counter("application_events_total", 1, event_labels)
        
        if success:
            self.metrics.increment_counter("application_events_success_total", 1, event_labels)
        else:
            self.metrics.increment_counter("application_events_error_total", 1, event_labels)
        
        # Duration histogram if provided
        if duration_ms is not None:
            self.metrics.record_histogram(
                "application_event_duration_ms",
                duration_ms,
                event_labels
            )
    
    @contextmanager
    def timed_operation(self, 
                       operation_type: str,
                       operation_name: str,
                       auto_log: bool = True,
                       **log_kwargs):
        """
        🎯 Context manager for timed operations with automatic logging and metrics.
        
        Args:
            operation_type: Type of operation (database, http, processing, etc.)
            operation_name: Specific operation name
            auto_log: Whether to automatically log the operation
            **log_kwargs: Additional arguments for logging
        
        Yields:
            Dictionary with operation context that can be updated
            
        Example:
            with logger.timed_operation("database", "user_search") as ctx:
                ctx["user_id"] = user_id
                results = await search_users(query)
                ctx["result_count"] = len(results)
        """
        start_time = time.time()
        operation_context = {"operation_type": operation_type, "operation_name": operation_name}
        correlation_id = get_correlation_id()
        
        if correlation_id:
            operation_context["correlation_id"] = correlation_id
        
        try:
            yield operation_context
            
            # Success path
            duration_ms = (time.time() - start_time) * 1000
            operation_context["duration_ms"] = duration_ms
            operation_context["success"] = True
            
            if auto_log:
                if operation_type == "database":
                    self.log_database_operation(
                        db_type=log_kwargs.get("db_type", "unknown"),
                        operation=operation_name,
                        duration_ms=duration_ms,
                        success=True,
                        record_count=operation_context.get("result_count"),
                        **log_kwargs
                    )
                else:
                    self.log_application_event(
                        event_type=operation_type,
                        event_name=operation_name,
                        success=True,
                        duration_ms=duration_ms,
                        metadata=operation_context,
                        **log_kwargs
                    )
            
        except Exception as e:
            # Error path
            duration_ms = (time.time() - start_time) * 1000
            operation_context["duration_ms"] = duration_ms
            operation_context["success"] = False
            operation_context["error"] = str(e)
            
            if auto_log:
                if operation_type == "database":
                    self.log_database_operation(
                        db_type=log_kwargs.get("db_type", "unknown"),
                        operation=operation_name,
                        duration_ms=duration_ms,
                        success=False,
                        error=str(e),
                        **log_kwargs
                    )
                else:
                    self.log_application_event(
                        event_type=operation_type,
                        event_name=operation_name,
                        success=False,
                        duration_ms=duration_ms,
                        metadata={**operation_context, "error": str(e)},
                        **log_kwargs
                    )
            
            raise
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            "logger_name": self.logger_name,
            "metrics_summary": self.metrics.get_metrics_summary(),
            "health_metrics": self.metrics.get_health_metrics(),
            "performance_optimization_enabled": self.enable_performance_optimization,
            "correlation_id": get_correlation_id(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for metrics to avoid high cardinality.
        
        Examples:
        - /api/v1/materials/123 → /api/v1/materials/{id}
        - /api/v1/search?q=test → /api/v1/search
        """
        # Remove query parameters
        if '?' in path:
            path = path.split('?')[0]
        
        # Replace common ID patterns
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        path = re.sub(r'/[a-f0-9-]{8,}', '/{uuid}', path)
        
        return path


# 🎯 Factory functions for easy usage

def get_metrics_integrated_logger(logger_name: str, 
                                 enable_performance_optimization: bool = True) -> MetricsIntegratedLogger:
    """
    Factory function to create metrics-integrated logger.
    
    Args:
        logger_name: Name for the logger
        enable_performance_optimization: Enable performance optimizations
        
    Returns:
        MetricsIntegratedLogger instance
    """
    return MetricsIntegratedLogger(
        logger_name=logger_name,
        enable_performance_optimization=enable_performance_optimization
    )


def log_database_operation_with_metrics(db_type: str, operation: str):
    """
    🎯 Decorator for automatic database operation logging with metrics.
    
    Args:
        db_type: Database type (postgresql, qdrant, redis, etc.)
        operation: Operation name (search, insert, update, etc.)
    
    Returns:
        Decorator function
        
    Example:
        @log_database_operation_with_metrics("qdrant", "search_materials")
        async def search_materials(query: str):
            # Function automatically logged with metrics
            return await vector_search(query)
    """
    def decorator(func):
        import functools
        import inspect
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_metrics_integrated_logger(f"db.{db_type}")
            
            with logger.timed_operation("database", operation, db_type=db_type) as ctx:
                if args and hasattr(args[0], '__class__'):
                    ctx["class_name"] = args[0].__class__.__name__
                
                result = await func(*args, **kwargs)
                
                # Try to extract result count
                if hasattr(result, '__len__'):
                    ctx["result_count"] = len(result)
                elif isinstance(result, dict) and 'count' in result:
                    ctx["result_count"] = result['count']
                
                return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_metrics_integrated_logger(f"db.{db_type}")
            
            with logger.timed_operation("database", operation, db_type=db_type) as ctx:
                if args and hasattr(args[0], '__class__'):
                    ctx["class_name"] = args[0].__class__.__name__
                
                result = func(*args, **kwargs)
                
                # Try to extract result count
                if hasattr(result, '__len__'):
                    ctx["result_count"] = len(result)
                elif isinstance(result, dict) and 'count' in result:
                    ctx["result_count"] = result['count']
                
                return result
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# 🎯 Global instance for easy access
_global_metrics_logger = None

def get_global_metrics_logger() -> MetricsIntegratedLogger:
    """Get global metrics-integrated logger instance."""
    global _global_metrics_logger
    if _global_metrics_logger is None:
        _global_metrics_logger = MetricsIntegratedLogger("global")
    return _global_metrics_logger 