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
import os

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
    log_level: Optional[str] = None,
    enable_structured: Optional[bool] = None,
    log_file: Optional[str] = None,
    enable_colors: Optional[bool] = None,
    third_party_level: Optional[str] = None
) -> None:
    """
    Setup application-wide logging configuration with optimized performance.
    
    All parameters are optional and will be read from environment variables if not provided.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - from LOG_LEVEL env var
        enable_structured: Enable JSON structured logging - from ENABLE_STRUCTURED_LOGGING env var
        log_file: Optional log file path - from LOG_FILE env var
        enable_colors: Enable colored terminal output - from LOG_COLORS env var
        third_party_level: Log level for third-party libraries - from LOG_THIRD_PARTY_LEVEL env var
    """
    # Import settings here to avoid circular imports
    from core.config import get_settings
    settings = get_settings()
    
    # Use environment variables if parameters not provided
    if log_level is None:
        log_level = settings.LOG_LEVEL
    if enable_structured is None:
        enable_structured = settings.ENABLE_STRUCTURED_LOGGING
    if log_file is None:
        log_file = settings.LOG_FILE
    if enable_colors is None:
        enable_colors = settings.LOG_COLORS
    if third_party_level is None:
        third_party_level = settings.LOG_THIRD_PARTY_LEVEL
    
    # Handle LogLevel enum or string
    if hasattr(log_level, 'value'):
        log_level = log_level.value
    if hasattr(third_party_level, 'value'):
        third_party_level = third_party_level.value
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers to avoid duplication
    root_logger.handlers.clear()
    
    # Console handler with optimized configuration
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if enable_structured:
        # Structured JSON logging for production
        console_handler.setFormatter(StructuredFormatter())
    else:
        # Beautiful colored format for development (like uvicorn)
        if enable_colors:
            try:
                import colorama
                colorama.init()
                
                class ColoredFormatter(logging.Formatter):
                    """Colored formatter for beautiful terminal output."""
                    
                    COLORS = {
                        'DEBUG': '\033[36m',     # Cyan
                        'INFO': '\033[32m',      # Green  
                        'WARNING': '\033[33m',   # Yellow
                        'ERROR': '\033[31m',     # Red
                        'CRITICAL': '\033[35m',  # Magenta
                        'RESET': '\033[0m'       # Reset
                    }
                    
                    def format(self, record):
                        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
                        reset = self.COLORS['RESET']
                        record.levelname = f"{color}{record.levelname:<8s}{reset}"
                        return super().format(record)
                
                console_handler.setFormatter(ColoredFormatter('%(levelname)s %(message)s'))
                
            except ImportError:
                # Fallback to simple format if colorama not available
                console_handler.setFormatter(
                    logging.Formatter('%(levelname)-8s %(message)s')
                )
        else:
            # Simple format without colors
            console_handler.setFormatter(
                logging.Formatter('%(levelname)-8s %(message)s')
            )
    
    root_logger.addHandler(console_handler)
    
    # File handler with consistent formatting
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Always use structured format for file logging
        if enable_structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
        root_logger.addHandler(file_handler)
    
    # Configure third-party loggers to reduce noise
    third_party_log_level = getattr(logging, third_party_level.upper())
    logging.getLogger("uvicorn").setLevel(third_party_log_level)
    logging.getLogger("httpx").setLevel(third_party_log_level)
    logging.getLogger("openai").setLevel(third_party_log_level)
    logging.getLogger("paramiko").setLevel(third_party_log_level)
    
    # 🔧 UNIFIED STRATEGY: Configure only the loggers we actually use
    # Configure middleware.http logger (used by LoggingMiddleware)
    middleware_logger = logging.getLogger("middleware.http")
    middleware_logger.setLevel(getattr(logging, log_level.upper()))
    middleware_logger.propagate = True
    
    # Configure core namespace logger for other core components
    core_logger = logging.getLogger("core")
    core_logger.setLevel(getattr(logging, log_level.upper()))
    core_logger.propagate = True


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