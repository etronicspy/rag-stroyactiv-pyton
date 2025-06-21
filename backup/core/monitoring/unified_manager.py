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
from datetime import datetime
import asyncio

from core.config import get_settings
from core.monitoring.logger import (
    get_logger, DatabaseLogger, RequestLogger, 
    setup_structured_logging
)
from core.monitoring.metrics import (
    MetricsCollector, PerformanceTracker, get_metrics_collector
)
from core.monitoring.performance_optimizer import (
    get_performance_optimizer, 
    PerformanceOptimizer,
    performance_optimized_log,
    LogEntry,
    MetricEntry
)
from core.monitoring.metrics_integration import (
    MetricsIntegratedLogger,
    get_metrics_integrated_logger,
    log_database_operation_with_metrics
)
from core.monitoring.context import get_correlation_id


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
        self.settings = settings or get_settings()
        
        # 🚀 ЭТАП 4.2: Performance Optimization Integration
        self.performance_optimizer = get_performance_optimizer()
        
        # Initialize all components
        self.metrics_collector = get_metrics_collector()
        self.performance_tracker = self.metrics_collector.get_performance_tracker()
        self.request_logger = RequestLogger()
        self.database_logger = DatabaseLogger("unified")
        
        # Health checker initialization (optional)
        self.health_checker = None
        
        # Performance settings
        self.enable_batching = getattr(settings, 'ENABLE_LOG_BATCHING', True)
        self.enable_async_processing = getattr(settings, 'ENABLE_ASYNC_LOG_PROCESSING', True)
        self.enable_performance_optimization = getattr(settings, 'ENABLE_PERFORMANCE_OPTIMIZATION', True)
        
        # 🎯 ЭТАП 5.2: Metrics Integration Settings
        self.enable_metrics_integration = getattr(settings, 'ENABLE_METRICS_INTEGRATION', True)
        
        # Initialize logger for this manager
        self.logger = get_logger("unified_manager")
        
        # Initialize metrics integrated logger if enabled
        if self.enable_metrics_integration:
            try:
                self.metrics_integrated_logger = get_metrics_integrated_logger("unified_manager")
            except Exception as e:
                self.logger.warning(f"Metrics integration not available: {e}, falling back to standard logging")
                self.metrics_integrated_logger = None
                self.enable_metrics_integration = False
        else:
            self.metrics_integrated_logger = None
        
        self.logger.info(
            f"✅ UnifiedLoggingManager initialized with performance optimization: "
            f"batching={self.enable_batching}, async={self.enable_async_processing}, "
            f"optimization={self.enable_performance_optimization}, "
            f"metrics_integration={self.enable_metrics_integration}"
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
        """🎯 Enhanced database operation logging with metrics integration and performance optimization."""
        
        # 🎯 ЭТАП 5.2: Use MetricsIntegratedLogger for comprehensive logging + metrics
        if self.enable_metrics_integration:
            self.metrics_integrated_logger.log_database_operation(
                db_type=db_type,
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                record_count=record_count,
                error=error,
                **kwargs
            )
        else:
            # Fallback to original implementation
            correlation_id = get_correlation_id()
            
            # Prepare log message
            status = "SUCCESS" if success else "FAILED"
            message = f"[{db_type.upper()}] {operation} - {status} ({duration_ms:.2f}ms)"
            
            if record_count is not None:
                message += f" | Records: {record_count}"
            
            if error:
                message += f" | Error: {error}"
            
            # Enhanced extra data
            extra_data = {
                "db_type": db_type,
                "operation": operation,
                "duration_ms": duration_ms,
                "success": success,
                "correlation_id": correlation_id,
                **kwargs
            }
            
            if record_count is not None:
                extra_data["record_count"] = record_count
            
            if error:
                extra_data["error"] = error
            
            # 🚀 ЭТАП 4.2: Use performance-optimized logging
            if self.enable_batching and self.enable_performance_optimization:
                # Use batch processing for high-performance logging
                self.performance_optimizer.log_with_batching(
                    logger_name=f"db.{db_type}",
                    level="ERROR" if not success else "INFO",
                    message=message,
                    extra=extra_data
                )
            else:
                # Traditional logging
                logger = self.get_optimized_logger(f"db.{db_type}")
                if success:
                    logger.info(message, extra=extra_data)
                else:
                    logger.error(message, extra=extra_data)
        
        # Record performance metrics with batching
        if self.enable_performance_optimization:
            self.performance_optimizer.record_metric_with_batching(
                metric_type="histogram",
                metric_name=f"db_operation_duration_ms",
                value=duration_ms,
                labels={
                    "db_type": db_type,
                    "operation": operation,
                    "success": str(success).lower()
                }
            )
        
        # Traditional metrics tracking
        self.performance_tracker.track_operation(
            db_type, operation, duration_ms, success, record_count
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
        """🎯 Enhanced HTTP request logging with metrics integration and performance optimization."""
        
        # 🎯 ЭТАП 5.2: Use MetricsIntegratedLogger for comprehensive HTTP logging + metrics
        if self.enable_metrics_integration:
            self.metrics_integrated_logger.log_http_request(
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                ip_address=ip_address,
                user_agent=user_agent,
                request_size_bytes=request_size_bytes,
                response_size_bytes=response_size_bytes,
                **kwargs
            )
        else:
            # Fallback to original implementation
            correlation_id = request_id or get_correlation_id()
            
            # Prepare log message
            message = f"[HTTP] {method} {path} - {status_code} ({duration_ms:.2f}ms)"
            
            # Enhanced extra data
            extra_data = {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "correlation_id": correlation_id,
                **kwargs
            }
            
            if ip_address:
                extra_data["ip_address"] = ip_address
            
            if user_agent:
                extra_data["user_agent"] = user_agent
            
            # 🚀 ЭТАП 4.2: Use performance-optimized logging
            if self.enable_batching and self.enable_performance_optimization:
                # Use batch processing for high-performance logging
                level = "ERROR" if status_code >= 500 else "WARNING" if status_code >= 400 else "INFO"
                self.performance_optimizer.log_with_batching(
                    logger_name="http.requests",
                    level=level,
                    message=message,
                    extra=extra_data
                )
            else:
                # Traditional logging
                logger = self.get_optimized_logger("http.requests")
                self.request_logger.log_request(
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    correlation_id=correlation_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            # Record performance metrics with batching
            if self.enable_performance_optimization:
                self.performance_optimizer.record_metric_with_batching(
                    metric_type="histogram",
                    metric_name="http_request_duration_ms",
                    value=duration_ms,
                    labels={
                        "method": method,
                        "status_code": str(status_code),
                        "path_pattern": self._get_path_pattern(path)
                    }
                )
    
    def _get_path_pattern(self, path: str) -> str:
        """Extract path pattern for metrics."""
        # Convert dynamic paths to patterns
        # /api/v1/materials/123 -> /api/v1/materials/{id}
        import re
        
        patterns = [
            (r'/\d+', '/{id}'),
            (r'/[a-f0-9-]{36}', '/{uuid}'),
            (r'/[a-zA-Z0-9_-]{10,}', '/{token}')
        ]
        
        path_pattern = path
        for pattern, replacement in patterns:
            path_pattern = re.sub(pattern, replacement, path_pattern)
        
        return path_pattern
    
    # === CONTEXT MANAGERS ===
    
    @contextmanager
    def database_operation_context(self, 
                                  db_type: str, 
                                  operation: str,
                                  enable_performance_optimization: bool = True):
        """🎯 Enhanced context manager with performance optimization."""
        start_time = time.time()
        correlation_id = get_correlation_id()
        
        # 🚀 ЭТАП 4.2: Performance-optimized context
        if enable_performance_optimization and self.enable_performance_optimization:
            # Use optimized logging
            logger = self.performance_optimizer.get_optimized_logger(f"db.{db_type}")
        else:
            logger = get_logger(f"db.{db_type}")
        
        logger.debug(f"Starting {operation} operation", extra={
            "db_type": db_type,
            "operation": operation,
            "correlation_id": correlation_id
        })
        
        try:
            yield
            
            duration_ms = (time.time() - start_time) * 1000
            self.log_database_operation(
                db_type=db_type,
                operation=operation,
                duration_ms=duration_ms,
                success=True
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_database_operation(
                db_type=db_type,
                operation=operation,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
            raise
    
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
        """🎯 Enhanced health status with performance optimization metrics."""
        base_health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "unified_logging": {
                "enabled": True,
                "components": {
                    "request_logger": "active",
                    "database_logger": "active", 
                    "performance_tracker": "active",
                    "metrics_collector": "active"
                },
                "settings": {
                    "enable_batching": self.enable_batching,
                    "enable_async_processing": self.enable_async_processing,
                    "enable_performance_optimization": self.enable_performance_optimization
                }
            }
        }
        
        # 🚀 ЭТАП 4.2: Add performance optimization metrics
        if self.enable_performance_optimization:
            perf_stats = self.performance_optimizer.get_comprehensive_stats()
            base_health["performance_optimization"] = perf_stats
        
        return base_health
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "performance_tracker": self.performance_tracker.get_database_summary(),
            "optimization_features": {
                "logger_caching": self.enable_performance_optimization,
                "batch_processing": self.enable_batching,
                "async_processing": self.enable_async_processing
            }
        }
        
        # 🚀 ЭТАП 4.2: Add detailed performance optimization stats
        if self.enable_performance_optimization:
            perf_stats = self.performance_optimizer.get_comprehensive_stats()
            summary["detailed_optimization_stats"] = perf_stats
        
        return summary


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


# 🚀 ЭТАП 4.2: Enhanced decorator with performance optimization
def log_database_operation_optimized(db_type: str, operation: str = None):
    """Enhanced decorator with performance optimization."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            unified_manager = get_unified_logging_manager()
            op_name = operation or func.__name__
            
            # 🚀 Use performance-optimized context
            with unified_manager.database_operation_context(
                db_type, op_name, enable_performance_optimization=True
            ):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            unified_manager = get_unified_logging_manager()
            op_name = operation or func.__name__
            
            # 🚀 Use performance-optimized context
            with unified_manager.database_operation_context(
                db_type, op_name, enable_performance_optimization=True
            ):
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
