"""
Centralized logging system for RAG Construction Materials API.

Provides structured logging, database operation logging, and performance tracking.
"""

import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from functools import wraps
from contextlib import contextmanager

from core.config import get_settings


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter for production environments."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON structure."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        if hasattr(record, 'database_type'):
            log_data['database_type'] = record.database_type
            
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation
            
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
            
        if hasattr(record, 'record_count'):
            log_data['record_count'] = record.record_count
            
        if hasattr(record, 'error_details'):
            log_data['error_details'] = record.error_details
            
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
            
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
            
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class DatabaseLogger:
    """Specialized logger for database operations."""
    
    def __init__(self, db_type: str, logger: Optional[logging.Logger] = None):
        """
        Initialize database logger.
        
        Args:
            db_type: Database type (postgresql, qdrant, redis, etc.)
            logger: Optional parent logger
        """
        self.db_type = db_type
        self.logger = logger or get_logger(f"db.{db_type}")
        
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
        level = logging.INFO if success else logging.ERROR
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
            
        if correlation_id:
            extra["correlation_id"] = correlation_id
            
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
            record_count: Number of records being processed
            correlation_id: Request correlation ID
            extra_data: Additional data to log
            
        Yields:
            Context with operation tracking
        """
        start_time = time.time()
        error = None
        
        try:
            yield
        except Exception as e:
            error = e
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.log_operation(
                operation=operation,
                duration_ms=duration_ms,
                record_count=record_count,
                success=error is None,
                error=error,
                extra_data=extra_data,
                correlation_id=correlation_id
            )


def setup_structured_logging(
    log_level: str = "INFO",
    enable_structured: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Setup application-wide logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_structured: Enable JSON structured logging
        log_file: Optional log file path
    """
    settings = get_settings()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    if enable_structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter() if enable_structured else 
                                 logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with consistent configuration.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_database_operation(db_type: str):
    """
    Decorator to automatically log database operations.
    
    Args:
        db_type: Database type identifier
        
    Returns:
        Decorated function with operation logging
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            db_logger = DatabaseLogger(db_type)
            correlation_id = kwargs.get('correlation_id') or str(uuid.uuid4())
            
            with db_logger.operation_timer(
                operation=func.__name__,
                correlation_id=correlation_id
            ):
                return await func(*args, **kwargs)
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            db_logger = DatabaseLogger(db_type)
            correlation_id = kwargs.get('correlation_id') or str(uuid.uuid4())
            
            with db_logger.operation_timer(
                operation=func.__name__,
                correlation_id=correlation_id
            ):
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


class RequestLogger:
    """Logger for HTTP requests with correlation tracking."""
    
    def __init__(self):
        self.logger = get_logger("api.requests")
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """
        Log HTTP request with structured data.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            user_id: User identifier
            request_id: Request correlation ID
            request_size: Request size in bytes
            response_size: Response size in bytes
            user_agent: User agent string
            ip_address: Client IP address
        """
        level = logging.INFO if status_code < 400 else logging.ERROR
        message = f"{method} {path} - {status_code} ({duration_ms:.2f}ms)"
        
        extra = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2)
        }
        
        if user_id:
            extra["user_id"] = user_id
        if request_id:
            extra["request_id"] = request_id
        if request_size:
            extra["request_size"] = request_size
        if response_size:
            extra["response_size"] = response_size
        if user_agent:
            extra["user_agent"] = user_agent
        if ip_address:
            extra["ip_address"] = ip_address
            
        adapter = logging.LoggerAdapter(self.logger, extra)
        adapter.log(level, message, extra=extra) 