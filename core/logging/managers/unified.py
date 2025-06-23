"""
🎯 Unified Logging Manager - Central hub for all logging and monitoring

Integrates logging, metrics, performance tracking, and correlation ID management.
Migrated and optimized from core/monitoring/unified_manager.py.
"""

import time
import uuid
import threading
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from contextlib import contextmanager
from functools import wraps
from datetime import datetime
import asyncio

from ..base.loggers import get_logger
from ..handlers.database import DatabaseLogger
from ..handlers.request import RequestLogger
from ..metrics.collectors import MetricsCollector, PerformanceTracker, get_metrics_collector
from ..metrics.performance import get_performance_optimizer
from ..context.correlation import get_correlation_id


class LogLevel(str, Enum):
    """Log levels for unified system."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class OperationContext:
    """Context for logging operations with metrics integration."""
    operation_id: str
    operation_type: str  # "database", "http", "api", "service"
    operation_name: str
    start_time: float
    metadata: Dict[str, Any]
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "operation_name": self.operation_name,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "started_at": self.start_time
        }


class UnifiedLoggingManager:
    """
    🎯 Central manager for all logging and monitoring operations.
    
    Provides:
    - Unified logging interface for all components
    - Automatic metrics collection integration
    - Correlation ID management
    - Performance tracking
    - Structured logging with context
    """
    
    def __init__(self, settings: Optional[Any] = None):
        """Initialize unified logging manager with performance optimization."""
        self.settings = settings
        
        # Performance optimization integration
        self.performance_optimizer = get_performance_optimizer()
        
        # Initialize all components
        self.metrics_collector = get_metrics_collector()
        self.performance_tracker = self.metrics_collector.get_performance_tracker()
        self.request_logger = RequestLogger()
        self.database_logger = DatabaseLogger("unified")
        
        # Track active operations
        self._active_operations: Dict[str, OperationContext] = {}
        self._operations_lock = threading.Lock()
        
        # Performance settings
        self.enable_batching = getattr(settings, 'ENABLE_LOG_BATCHING', True) if settings else True
        self.enable_async_processing = getattr(settings, 'ENABLE_ASYNC_LOG_PROCESSING', True) if settings else True
        self.enable_performance_optimization = getattr(settings, 'ENABLE_PERFORMANCE_OPTIMIZATION', True) if settings else True
        
        # Initialize logger for this manager
        self.logger = get_logger("unified_manager")
        
        self.logger.info(
            f"✅ UnifiedLoggingManager initialized with performance optimization: "
            f"batching={self.enable_batching}, async={self.enable_async_processing}, "
            f"optimization={self.enable_performance_optimization}"
        )
    
    async def initialize_async_components(self):
        """Initialize async components including performance optimizer."""
        if self.enable_performance_optimization:
            await self.performance_optimizer.initialize()
            self.logger.info("🚀 Performance optimization system initialized")
    
    async def shutdown_async_components(self):
        """Shutdown async components."""
        if self.enable_performance_optimization:
            await self.performance_optimizer.shutdown()
            self.logger.info("✅ Performance optimization system shutdown completed")
    
    def get_optimized_logger(self, name: str):
        """Get performance-optimized logger instance."""
        if self.enable_performance_optimization:
            return self.performance_optimizer.get_optimized_logger(name)
        else:
            return get_logger(name, enable_correlation=True)
    
    def get_logger(self, name: str):
        """Get a logger with unified configuration."""
        return get_logger(name)
    
    def get_database_logger(self, db_type: str) -> DatabaseLogger:
        """Get specialized database logger."""
        return DatabaseLogger(db_type)
    
    def get_request_logger(self) -> RequestLogger:
        """Get specialized request logger."""
        return self.request_logger
    
    def get_metrics_collector(self) -> MetricsCollector:
        """Get metrics collector."""
        return self.metrics_collector
    
    def get_performance_tracker(self) -> PerformanceTracker:
        """Get performance tracker."""
        return self.performance_tracker
    
    # === UNIFIED LOGGING METHODS ===
    
    def log_database_operation(self, 
                              db_type: str, 
                              operation: str, 
                              duration_ms: float,
                              success: bool,
                              record_count: Optional[int] = None,
                              error: Optional[str] = None,
                              **kwargs):
        """Enhanced database operation logging with metrics integration and performance optimization."""
        
        correlation_id = get_correlation_id()
        
        # Prepare log message
        status = "SUCCESS" if success else "FAILED"
        message = f"[{db_type.upper()}] {operation} - {status} ({duration_ms:.2f}ms)"
        
        if record_count is not None:
            message += f" | Records: {record_count}"
        
        if error and not success:
            message += f" | Error: {error}"
        
        # Enhanced logging with correlation ID
        extra_data = {
            "db_type": db_type,
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "record_count": record_count,
            "correlation_id": correlation_id,
            **kwargs
        }
        
        if error:
            extra_data["error"] = error
        
        # Use performance-optimized logging if enabled
        if self.enable_performance_optimization:
            self.performance_optimizer.log_with_batching(
                logger_name=f"db.{db_type}",
                level="INFO" if success else "ERROR",
                message=message,
                extra=extra_data
            )
        else:
            # Standard logging fallback
            db_logger = self.get_database_logger(db_type)
            if success:
                db_logger.info(message, extra=extra_data)
            else:
                db_logger.error(message, extra=extra_data)
        
        # Track performance metrics
        self.performance_tracker.track_operation(
            db_type=db_type,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            record_count=record_count or 0
        )
    
    def log_http_request(self, 
                        method: str, 
                        path: str, 
                        status_code: int, 
                        duration_ms: float,
                        request_id: Optional[str] = None,
                        ip_address: Optional[str] = None,
                        user_agent: Optional[str] = None,
                        request_size_bytes: int = 0,
                        response_size_bytes: int = 0,
                        **kwargs):
        """Enhanced HTTP request logging with performance optimization."""
        
        correlation_id = get_correlation_id()
        request_id = request_id or correlation_id
        
        # Pattern-based path for better grouping
        path_pattern = self._get_path_pattern(path)
        
        message = f"[HTTP] {method} {path_pattern} - {status_code} ({duration_ms:.2f}ms)"
        
        if response_size_bytes > 0:
            message += f" | Response: {response_size_bytes} bytes"
        
        extra_data = {
            "method": method,
            "path": path,
            "path_pattern": path_pattern,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_size_bytes": request_size_bytes,
            "response_size_bytes": response_size_bytes,
            **kwargs
        }
        
        # Use performance-optimized logging if enabled
        if self.enable_performance_optimization:
            level = "INFO" if 200 <= status_code < 400 else "WARNING" if 400 <= status_code < 500 else "ERROR"
            self.performance_optimizer.log_with_batching(
                logger_name="http.requests",
                level=level,
                message=message,
                extra=extra_data
            )
        else:
            # Standard logging fallback
            if 200 <= status_code < 400:
                self.request_logger.info(message, extra=extra_data)
            elif 400 <= status_code < 500:
                self.request_logger.warning(message, extra=extra_data)
            else:
                self.request_logger.error(message, extra=extra_data)
        
        # Record HTTP metrics
        self.metrics_collector.record_histogram(
            "http_request_duration_ms", 
            duration_ms,
            labels={
                "method": method,
                "path_pattern": path_pattern,
                "status_code": str(status_code)
            }
        )
        
        self.metrics_collector.increment_counter(
            "http_requests_total",
            labels={
                "method": method,
                "path_pattern": path_pattern,
                "status_code": str(status_code)
            }
        )
    
    def _get_path_pattern(self, path: str) -> str:
        """Convert path to pattern for better grouping."""
        # Simple pattern extraction - replace IDs with placeholders
        import re
        
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace other common patterns
        path = re.sub(r'/[a-f0-9]{24}', '/{objectid}', path)  # MongoDB ObjectIds
        
        return path
    
    @contextmanager
    def database_operation_context(self, 
                                  db_type: str, 
                                  operation: str,
                                  enable_performance_optimization: bool = True):
        """Context manager for database operations with automatic logging and metrics."""
        operation_id = str(uuid.uuid4())
        correlation_id = get_correlation_id()
        start_time = time.perf_counter()
        
        context = OperationContext(
            operation_id=operation_id,
            operation_type="database",
            operation_name=operation,
            start_time=start_time,
            metadata={"db_type": db_type},
            correlation_id=correlation_id
        )
        
        # Register the operation
        self._register_operation(context)
        
        success = True
        error = None
        record_count = None
        
        try:
            yield context
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            # Unregister the operation
            self._unregister_operation(operation_id)
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Get record count from context if set
            record_count = context.metadata.get('record_count')
            
            # Log the operation
            self.log_database_operation(
                db_type=db_type,
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                record_count=record_count,
                error=error,
                operation_id=operation_id
            )
    
    def log_database_operation_decorator(self, db_type: str, operation: str = None):
        """Decorator for automatic database operation logging."""
        
        def decorator(func):
            operation_name = operation or func.__name__
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.database_operation_context(db_type, operation_name):
                    return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.database_operation_context(db_type, operation_name):
                    return func(*args, **kwargs)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of logging system."""
        metrics_health = self.metrics_collector.get_health_metrics()
        
        return {
            "unified_logging": {
                "status": "healthy",
                "performance_optimization": self.enable_performance_optimization,
                "batching": self.enable_batching,
                "async_processing": self.enable_async_processing,
                "settings": {
                    "structured_logging": True,
                    "correlation_tracking": True,
                    "performance_monitoring": self.enable_performance_optimization,
                    "async_processing": self.enable_async_processing,
                    "batching": self.enable_batching
                }
            },
            "metrics": metrics_health,
            "performance": self.performance_optimizer.get_comprehensive_stats() if self.enable_performance_optimization else {},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all tracked operations."""
        db_summary = self.performance_tracker.get_database_summary()
        metrics_summary = self.metrics_collector.get_stats()
        
        return {
            "database_operations": db_summary,
            "metrics_summary": metrics_summary,
            "performance_optimization": (
                self.performance_optimizer.get_comprehensive_stats() 
                if self.enable_performance_optimization else {}
            ),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive logging statistics."""
        return self.get_performance_summary()
    
    def get_operation_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active operation contexts."""
        with self._operations_lock:
            return {
                op_id: context.to_dict() 
                for op_id, context in self._active_operations.items()
            }
    
    def _register_operation(self, context: OperationContext):
        """Register an active operation."""
        with self._operations_lock:
            self._active_operations[context.operation_id] = context
    
    def _unregister_operation(self, operation_id: str):
        """Unregister an active operation."""
        with self._operations_lock:
            self._active_operations.pop(operation_id, None)

    # Legacy method for backward compatibility
    def log_operation(self, operation: str, **kwargs):
        """Log operation (backward compatibility)."""
        self.logger.info(f"Operation: {operation}", extra=kwargs)


# Global unified logging manager instance
_global_unified_manager: Optional[UnifiedLoggingManager] = None
_manager_lock = threading.Lock()


def get_unified_logging_manager() -> UnifiedLoggingManager:
    """Get global unified logging manager instance."""
    global _global_unified_manager
    
    if _global_unified_manager is None:
        with _manager_lock:
            if _global_unified_manager is None:
                _global_unified_manager = UnifiedLoggingManager()
    
    return _global_unified_manager


def get_logger_with_metrics(name: str):
    """Get logger with automatic metrics integration."""
    manager = get_unified_logging_manager()
    return manager.get_optimized_logger(name)


def log_database_operation(
    db_type: str,
    operation: str,
    duration_ms: float,
    success: bool,
    record_count: Optional[int] = None,
    error: Optional[str] = None,
    **kwargs
) -> None:
    """Log database operation with full metrics integration."""
    manager = get_unified_logging_manager()
    manager.log_database_operation(
        db_type=db_type,
        operation=operation,
        duration_ms=duration_ms,
        success=success,
        record_count=record_count,
        error=error,
        **kwargs
    )


def log_database_operation_optimized(
    db_type: str,
    operation: str,
    duration_ms: float,
    success: bool,
    record_count: Optional[int] = None,
    error: Optional[str] = None,
    **kwargs
) -> None:
    """Optimized database operation logging with performance features."""
    # Same as log_database_operation - optimization is built-in
    log_database_operation(
        db_type=db_type,
        operation=operation,
        duration_ms=duration_ms,
        success=success,
        record_count=record_count,
        error=error,
        **kwargs
    ) 