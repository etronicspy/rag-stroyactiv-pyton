"""
Database operation logging handler.

Provides specialized logging for database operations with metrics tracking.
Extracted and refactored from core/monitoring/logger.py.
"""

import logging
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager

from ..base.interfaces import DatabaseLoggerInterface
from ..context.correlation import get_correlation_id


class DatabaseLogger(DatabaseLoggerInterface):
    """Specialized logger for database operations."""
    
    def __init__(self, db_type: str, logger: Optional[logging.Logger] = None):
        """
        Initialize database logger.
        
        Args:
            db_type: Database type (postgresql, qdrant, redis, etc.)
            logger: Optional parent logger
        """
        self.db_type = db_type
        if logger is None:
            from ..base.loggers import get_logger
            self.logger = get_logger(f"db.{db_type}")
        else:
            self.logger = logger
        
    def log_operation(
        self,
        operation: str,
        duration_ms: Optional[float] = None,
        record_count: Optional[int] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Log database operation with structured data.
        
        Args:
            operation: Operation name (search, insert, update, etc.)
            duration_ms: Operation duration in milliseconds
            record_count: Number of records affected
            success: Whether operation was successful
            error: Exception if operation failed
            extra_data: Additional data to log
            correlation_id: Request correlation ID
        """
        logging.INFO if success else logging.ERROR
        message = f"Database operation: {operation}"
        
        if not success and error:
            message += f" - Error: {str(error)}"
            
        # Create log record with extra fields
        extra = {
            "database_type": self.db_type,
            "operation": operation,
            "success": success
        }
        
        if duration_ms is not None:
            extra["duration_ms"] = round(duration_ms, 2)
            
        if record_count is not None:
            extra["record_count"] = record_count
            
        # Use correlation ID from parameter or context
        if correlation_id:
            extra["correlation_id"] = correlation_id
        else:
            context_correlation_id = get_correlation_id()
            if context_correlation_id:
                extra["correlation_id"] = context_correlation_id
            
        if error:
            extra["error_details"] = {
                "type": type(error).__name__,
                "message": str(error)
            }
            
        if extra_data:
            extra.update(extra_data)
            
        # Use LoggerAdapter to add extra fields
        adapter = logging.LoggerAdapter(self.logger, extra)
        
        if success:
            adapter.info(message, extra=extra)
        else:
            adapter.error(message, exc_info=error, extra=extra)
    
    @contextmanager
    def operation_timer(
        self,
        operation: str,
        record_count: Optional[int] = None,
        correlation_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager to time database operations.
        
        Args:
            operation: Operation name
            record_count: Number of records affected
            correlation_id: Request correlation ID
            extra_data: Additional data to log
            
        Yields:
            Context manager for timed operation
            
        Example:
            with db_logger.operation_timer('search', record_count=100):
                # Database operation here
                pass
        """
        start_time = time.perf_counter()
        error = None
        
        try:
            yield
        except Exception as e:
            error = e
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.log_operation(
                operation=operation,
                duration_ms=duration_ms,
                record_count=record_count,
                success=error is None,
                error=error,
                extra_data=extra_data,
                correlation_id=correlation_id
            ) 