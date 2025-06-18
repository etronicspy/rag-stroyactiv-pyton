"""
🎯 Unified Logging Manager - Central hub for all logging and monitoring
Integrates logging, metrics, performance tracking, and correlation ID management.

ЭТАП 2.1: Создание единого менеджера для всех систем мониторинга
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from contextlib import contextmanager
from functools import wraps

from core.config import get_settings
from core.monitoring.logger import (
    get_logger, DatabaseLogger, RequestLogger, 
    setup_structured_logging
)
from core.monitoring.metrics import (
    MetricsCollector, PerformanceTracker, get_metrics_collector
)


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
        """Initialize unified logging manager."""
        self.settings = settings or get_settings()
        
        # Initialize core components
        self.metrics_collector = get_metrics_collector()
        self.performance_tracker = self.metrics_collector.get_performance_tracker()
        
        # Initialize specialized loggers
        self.request_logger = RequestLogger()
        self.database_logger = DatabaseLogger("unified")
        self.app_logger = get_logger("unified_manager")
        
        # Context storage for correlation IDs
        self._operation_contexts: Dict[str, OperationContext] = {}
        
        self.app_logger.info("✅ UnifiedLoggingManager initialized with full metrics integration")
    
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
    
    def log_database_operation(
        self,
        db_type: str,
        operation: str,
        duration_ms: float,
        success: bool,
        record_count: int = 0,
        correlation_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log database operation with integrated metrics.
        
        Args:
            db_type: Database type (postgresql, qdrant, etc.)
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            record_count: Number of records processed
            correlation_id: Correlation ID for tracing
            error: Error message if failed
            metadata: Additional metadata
        """
        # Log using specialized database logger
        self.database_logger.log_operation(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            record_count=record_count,
            metadata=metadata,
            correlation_id=correlation_id
        )
        
        # Track performance metrics
        self.performance_tracker.track_operation(
            db_type=db_type,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            record_count=record_count
        )
        
        # Collect additional metrics
        self.metrics_collector.increment_counter(
            f"database_{db_type}_operations_total",
            labels={"operation": operation, "success": str(success)}
        )
        
        self.metrics_collector.record_histogram(
            f"database_{db_type}_duration_ms",
            duration_ms,
            labels={"operation": operation}
        )
        
        if not success and error:
            self.metrics_collector.increment_counter(
                f"database_{db_type}_errors_total",
                labels={"operation": operation, "error_type": "database_error"}
            )
    
    def log_http_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str,
        ip_address: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log HTTP request with integrated metrics.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration
            request_id: Request/correlation ID
            ip_address: Client IP
            metadata: Additional metadata
        """
        # Log using specialized request logger
        self.request_logger.log_request(
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            request_id=request_id,
            ip_address=ip_address,
            metadata=metadata
        )
        
        # Collect HTTP metrics
        self.metrics_collector.increment_counter(
            "http_requests_total",
            labels={
                "method": method,
                "status_code": str(status_code),
                "status_class": f"{status_code // 100}xx"
            }
        )
        
        self.metrics_collector.record_histogram(
            "http_request_duration_ms",
            duration_ms,
            labels={"method": method, "path": path}
        )
        
        # Track errors
        if status_code >= 400:
            self.metrics_collector.increment_counter(
                "http_errors_total",
                labels={"status_code": str(status_code), "method": method}
            )
    
    # === CONTEXT MANAGERS ===
    
    @contextmanager
    def database_operation_context(
        self,
        db_type: str,
        operation: str,
        correlation_id: Optional[str] = None,
        record_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager specifically for database operations.
        
        Args:
            db_type: Database type
            operation: Operation name
            correlation_id: Correlation ID
            record_count: Expected record count
            metadata: Additional metadata
        """
        start_time = time.time()
        correlation_id = correlation_id or str(uuid.uuid4())
        success = True
        error_msg = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log database operation with metrics
            self.log_database_operation(
                db_type=db_type,
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                record_count=record_count,
                correlation_id=correlation_id,
                error=error_msg,
                metadata=metadata
            )
    
    # === DECORATORS ===
    
    def log_database_operation_decorator(self, db_type: str, operation: str = None):
        """
        Decorator for automatic database operation logging.
        
        Args:
            db_type: Database type
            operation: Operation name (defaults to function name)
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                op_name = operation or func.__name__
                correlation_id = kwargs.get('correlation_id') or str(uuid.uuid4())
                
                with self.database_operation_context(
                    db_type=db_type,
                    operation=op_name,
                    correlation_id=correlation_id
                ):
                    return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                op_name = operation or func.__name__
                correlation_id = kwargs.get('correlation_id') or str(uuid.uuid4())
                
                with self.database_operation_context(
                    db_type=db_type,
                    operation=op_name,
                    correlation_id=correlation_id
                ):
                    return func(*args, **kwargs)
            
            import asyncio
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    # === METRICS AND HEALTH ===
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status with metrics."""
        health_metrics = self.metrics_collector.get_health_metrics()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "unified_logging": {
                "active_contexts": len(self._operation_contexts),
                "settings": {
                    "structured_logging": self.settings.ENABLE_STRUCTURED_LOGGING,
                    "request_logging": self.settings.ENABLE_REQUEST_LOGGING,
                    "database_logging": self.settings.LOG_DATABASE_OPERATIONS,
                    "performance_metrics": self.settings.LOG_PERFORMANCE_METRICS
                }
            },
            "metrics": health_metrics,
            "performance": self.performance_tracker.get_database_summary()
        }


# Global unified logging manager instance
_unified_manager = None


def get_unified_logging_manager() -> UnifiedLoggingManager:
    """Get the global unified logging manager instance."""
    global _unified_manager
    if _unified_manager is None:
        _unified_manager = UnifiedLoggingManager()
    return _unified_manager


# Convenience functions for backward compatibility
def get_logger_with_metrics(name: str):
    """Get logger through unified manager."""
    return get_unified_logging_manager().get_logger(name)


def log_database_operation(db_type: str, operation: str = None):
    """Decorator for database operations."""
    return get_unified_logging_manager().log_database_operation_decorator(db_type, operation)
