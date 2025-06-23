"""
Metrics integration for unified logging system.

Integrates metrics collection with logging operations for comprehensive monitoring.
Migrated and optimized from core/monitoring/metrics_integration.py.
"""

import time
import threading
from typing import Dict, Any, Optional
from contextlib import contextmanager

from .collectors import get_metrics_collector
from .performance import get_performance_optimizer
from ..base.loggers import get_logger
from ..context.correlation import get_correlation_id


class MetricsIntegratedLogger:
    """Logger with comprehensive metrics integration."""
    
    def __init__(self, name: str):
        """Initialize metrics integrated logger."""
        self.logger = get_logger(name)
        self.name = name
        self.metrics_collector = get_metrics_collector()
        self.performance_optimizer = get_performance_optimizer()
    
    def info(self, message: str, **kwargs):
        """Log info with metrics integration."""
        self._log_with_metrics("INFO", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error with metrics integration."""
        self._log_with_metrics("ERROR", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning with metrics integration."""
        self._log_with_metrics("WARNING", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug with metrics integration."""
        self._log_with_metrics("DEBUG", message, **kwargs)
    
    def _log_with_metrics(self, level: str, message: str, **kwargs):
        """Internal method to log with metrics."""
        # Extract metrics data
        duration_ms = kwargs.get('duration_ms')
        operation = kwargs.get('operation', 'unknown')
        success = kwargs.get('success', True)
        
        # Log using performance optimizer if available
        if hasattr(self.performance_optimizer, 'log_with_batching'):
            self.performance_optimizer.log_with_batching(
                logger_name=self.name,
                level=level,
                message=message,
                extra=kwargs
            )
        else:
            # Fallback to standard logging
            getattr(self.logger, level.lower())(message, extra=kwargs)
        
        # Record metrics if duration is provided
        if duration_ms is not None:
            self.metrics_collector.record_operation(
                operation=f"{self.name}.{operation}",
                duration_ms=duration_ms,
                success=success,
                metadata=kwargs
            )
    
    def log_database_operation(self,
                              db_type: str,
                              operation: str,
                              duration_ms: float,
                              success: bool,
                              record_count: Optional[int] = None,
                              error: Optional[str] = None,
                              **kwargs):
        """Log database operation with comprehensive metrics."""
        correlation_id = get_correlation_id()
        
        # Enhanced logging data
        log_data = {
            'db_type': db_type,
            'operation': operation,
            'duration_ms': duration_ms,
            'success': success,
            'record_count': record_count,
            'correlation_id': correlation_id,
            **kwargs
        }
        
        if error:
            log_data['error'] = error
        
        # Prepare message
        status = "SUCCESS" if success else "FAILED"
        message = f"[{db_type.upper()}] {operation} - {status} ({duration_ms:.2f}ms)"
        
        if record_count is not None:
            message += f" | Records: {record_count}"
        
        if error and not success:
            message += f" | Error: {error}"
        
        # Log with appropriate level
        if success:
            self.info(message, **log_data)
        else:
            self.error(message, **log_data)
        
        # Track performance metrics
        performance_tracker = self.metrics_collector.get_performance_tracker()
        performance_tracker.track_operation(
            db_type=db_type,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            record_count=record_count or 0
        )


class MetricsIntegration:
    """Comprehensive metrics integration for logging operations."""
    
    def __init__(self):
        """Initialize metrics integration."""
        self.metrics_collector = get_metrics_collector()
        self.performance_optimizer = get_performance_optimizer()
        self.logger = get_logger("metrics_integration")
        self.enabled = True
        
        self.logger.info("✅ MetricsIntegration initialized")
    
    def integrate_metrics(self, operation: str, data: Dict[str, Any]) -> bool:
        """Integrate metrics with logging operation."""
        try:
            correlation_id = get_correlation_id()
            
            # Extract metrics from operation data
            duration_ms = data.get('duration_ms', 0.0)
            success = data.get('success', True)
            operation_type = data.get('operation_type', 'unknown')
            
            # Record operation metrics
            self.metrics_collector.record_operation(
                operation=f"{operation_type}.{operation}",
                duration_ms=duration_ms,
                success=success,
                metadata={
                    'correlation_id': correlation_id,
                    **data
                }
            )
            
            # Record timing histogram
            self.metrics_collector.record_histogram(
                f"{operation_type}_duration_ms",
                duration_ms,
                labels={
                    'operation': operation,
                    'success': str(success).lower()
                }
            )
            
            # Increment counters
            self.metrics_collector.increment_counter(
                f"{operation_type}_total",
                labels={
                    'operation': operation,
                    'status': 'success' if success else 'error'
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to integrate metrics for operation {operation}: {e}")
            return False
    
    def log_with_metrics(self, 
                        operation: str, 
                        operation_type: str = "application",
                        duration_ms: Optional[float] = None,
                        success: bool = True,
                        extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log operation with automatic metrics integration."""
        
        data = {
            'operation_type': operation_type,
            'duration_ms': duration_ms or 0.0,
            'success': success,
            **(extra_data or {})
        }
        
        # Integrate metrics
        self.integrate_metrics(operation, data)
        
        # Log using performance optimizer if available
        level = "INFO" if success else "ERROR"
        message = f"[{operation_type.upper()}] {operation} - {'SUCCESS' if success else 'FAILED'}"
        
        if duration_ms:
            message += f" ({duration_ms:.2f}ms)"
        
        if hasattr(self.performance_optimizer, 'log_with_batching'):
            self.performance_optimizer.log_with_batching(
                logger_name=f"{operation_type}.operations",
                level=level,
                message=message,
                extra=data
            )
        else:
            # Fallback to standard logging
            logger = get_logger(f"{operation_type}.operations")
            getattr(logger, level.lower())(message, extra=data)
    
    @contextmanager
    def operation_context(self, operation: str, operation_type: str = "application"):
        """Context manager for automatic operation metrics and logging."""
        start_time = time.perf_counter()
        success = True
        error = None
        
        try:
            yield
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            extra_data = {}
            if error:
                extra_data['error'] = error
            
            self.log_with_metrics(
                operation=operation,
                operation_type=operation_type,
                duration_ms=duration_ms,
                success=success,
                extra_data=extra_data
            )
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get metrics integration statistics."""
        return {
            "enabled": self.enabled,
            "metrics_collector_stats": self.metrics_collector.get_health_metrics(),
            "performance_optimizer_stats": (
                self.performance_optimizer.get_comprehensive_stats()
                if hasattr(self.performance_optimizer, 'get_comprehensive_stats')
                else {}
            )
        }


# Global instances
_global_metrics_integration: Optional[MetricsIntegration] = None
_global_loggers: Dict[str, MetricsIntegratedLogger] = {}
_loggers_lock = threading.Lock()


def get_metrics_integration() -> MetricsIntegration:
    """Get global metrics integration instance."""
    global _global_metrics_integration
    
    if _global_metrics_integration is None:
        _global_metrics_integration = MetricsIntegration()
    
    return _global_metrics_integration


def get_metrics_integrated_logger(name: str) -> MetricsIntegratedLogger:
    """Get metrics integrated logger with caching."""
    global _global_loggers
    
    if name not in _global_loggers:
        with _loggers_lock:
            if name not in _global_loggers:
                _global_loggers[name] = MetricsIntegratedLogger(name)
    
    return _global_loggers[name]


def log_database_operation_with_metrics(
    db_type: str,
    operation: str,
    duration_ms: float,
    success: bool,
    record_count: Optional[int] = None,
    error: Optional[str] = None,
    **kwargs
) -> None:
    """Log database operation with comprehensive metrics integration."""
    logger = get_metrics_integrated_logger('database')
    logger.log_database_operation(
        db_type=db_type,
        operation=operation,
        duration_ms=duration_ms,
        success=success,
        record_count=record_count,
        error=error,
        **kwargs
    )


def get_global_metrics_logger() -> MetricsIntegratedLogger:
    """Get global metrics logger."""
    return get_metrics_integrated_logger('global')


def log_with_metrics(operation: str, 
                    operation_type: str = "application",
                    duration_ms: Optional[float] = None,
                    success: bool = True,
                    extra_data: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for logging with metrics integration."""
    integration = get_metrics_integration()
    integration.log_with_metrics(
        operation=operation,
        operation_type=operation_type,
        duration_ms=duration_ms,
        success=success,
        extra_data=extra_data
    ) 