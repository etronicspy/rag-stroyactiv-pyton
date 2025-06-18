"""
Centralized logging system for RAG Construction Materials API.

Provides structured logging, database operation logging, and performance tracking.
FIXED: Refactored for better maintainability and eliminated code duplication.
"""

import logging
import json
import time
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from functools import wraps, lru_cache
from contextlib import contextmanager

from core.config import get_settings
from core.monitoring.context import CorrelationLoggingAdapter

# 🔧 CONSTANTS: Moved hardcoded values to module level
LOGGER_NAMES_TO_CONFIGURE = ["middleware", "services", "api", "database"]
THIRD_PARTY_LOGGERS = ["uvicorn", "httpx", "openai", "paramiko"]
MIDDLEWARE_LOGGER_NAME = "middleware.http"
CORE_LOGGER_NAME = "core"

# 🔧 PERFORMANCE: Cached logger instances
_logger_cache = {}

def get_logger(name: str, enable_correlation: bool = True) -> logging.Logger:
    """
    Get logger with optional correlation ID support.
    
    Args:
        name: Logger name
        enable_correlation: Whether to enable automatic correlation ID
        
    Returns:
        Logger instance with correlation support
    """
    if name in _logger_cache:
        return _logger_cache[name]
    
    logger = logging.getLogger(name)
    
    # 🎯 ЭТАП 3.2: Wrap with correlation adapter if enabled
    if enable_correlation:
        correlation_logger = CorrelationLoggingAdapter(logger, {})
        _logger_cache[name] = correlation_logger
        return correlation_logger
    
    _logger_cache[name] = logger
    return logger


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
        
        # 🔧 OPTIMIZED: Use list comprehension for performance
        extra_fields = [
            'correlation_id', 'database_type', 'operation', 'duration_ms',
            'record_count', 'error_details', 'user_id', 'request_id'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class BaseColorFormatter(logging.Formatter):
    """Base formatter with color support functionality."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def colorize_level(self, record: logging.LogRecord) -> str:
        """Colorize log level name."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        return f"{color}{record.levelname:<8s}{reset}"


class ColoredFormatter(BaseColorFormatter):
    """Colored formatter for beautiful terminal output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format record with colors."""
        record.levelname = self.colorize_level(record)
        return super().format(record)


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


class LoggingSetup:
    """
    🔧 REFACTORED: Centralized logging setup with modular methods.
    
    Breaks down the monolithic setup_structured_logging function into manageable parts.
    """
    
    def __init__(self, settings=None):
        """Initialize logging setup with settings."""
        self.settings = settings or get_settings()
    
    def _create_console_handler(self, log_level: str, enable_structured: bool, 
                               enable_colors: bool) -> logging.StreamHandler:
        """Create and configure console handler."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        if enable_structured:
            console_handler.setFormatter(StructuredFormatter())
        else:
            self._configure_console_formatter(console_handler, enable_colors)
        
        return console_handler
    
    def _configure_console_formatter(self, handler: logging.StreamHandler, enable_colors: bool):
        """Configure console formatter with optional colors."""
        if enable_colors:
            try:
                import colorama
                colorama.init()
                handler.setFormatter(ColoredFormatter('%(levelname)s %(message)s'))
            except ImportError:
                # Fallback to simple format if colorama not available
                handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
        else:
            handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    
    def _create_file_handler(self, log_file: str, log_level: str, 
                           enable_structured: bool) -> Optional[logging.FileHandler]:
        """Create and configure file handler."""
        if not log_file:
            return None
        
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
        
        return file_handler
    
    def _configure_third_party_loggers(self, third_party_level: str):
        """Configure third-party loggers to reduce noise."""
        third_party_log_level = getattr(logging, third_party_level.upper())
        
        for logger_name in THIRD_PARTY_LOGGERS:
            logging.getLogger(logger_name).setLevel(third_party_log_level)
    
    def _configure_application_loggers(self, log_level: str):
        """Configure application-specific loggers."""
        app_log_level = getattr(logging, log_level.upper())
        
        # Configure middleware.http logger (used by LoggingMiddleware)
        middleware_logger = logging.getLogger(MIDDLEWARE_LOGGER_NAME)
        middleware_logger.handlers = []
        middleware_logger.propagate = True
        middleware_logger.setLevel(app_log_level)
        
        # Configure core namespace logger
        core_logger = logging.getLogger(CORE_LOGGER_NAME)
        core_logger.handlers = []
        core_logger.propagate = True
        core_logger.setLevel(app_log_level)
        
        # Configure other named loggers
        for logger_name in LOGGER_NAMES_TO_CONFIGURE:
            named_logger = logging.getLogger(logger_name)
            named_logger.handlers = []
            named_logger.propagate = True
            named_logger.setLevel(app_log_level)
    
    def setup(self, log_level: Optional[str] = None, enable_structured: Optional[bool] = None,
              log_file: Optional[str] = None, enable_colors: Optional[bool] = None,
              third_party_level: Optional[str] = None) -> None:
        """
        Setup application-wide logging configuration.
        
        Args:
            log_level: Logging level - from LOG_LEVEL env var if None
            enable_structured: Enable JSON structured logging - from ENABLE_STRUCTURED_LOGGING if None
            log_file: Optional log file path - from LOG_FILE if None
            enable_colors: Enable colored terminal output - from LOG_COLORS if None
            third_party_level: Log level for third-party libraries - from LOG_THIRD_PARTY_LEVEL if None
        """
        # Use environment variables if parameters not provided
        log_level = log_level or self.settings.LOG_LEVEL
        enable_structured = enable_structured if enable_structured is not None else self.settings.ENABLE_STRUCTURED_LOGGING
        log_file = log_file or self.settings.LOG_FILE
        enable_colors = enable_colors if enable_colors is not None else self.settings.LOG_COLORS
        third_party_level = third_party_level or self.settings.LOG_THIRD_PARTY_LEVEL
        
        # Handle LogLevel enum or string
        if hasattr(log_level, 'value'):
            log_level = log_level.value
        if hasattr(third_party_level, 'value'):
            third_party_level = third_party_level.value
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        root_logger.handlers.clear()
        
        # Create and add console handler
        console_handler = self._create_console_handler(log_level, enable_structured, enable_colors)
        root_logger.addHandler(console_handler)
        
        # Create and add file handler if specified
        file_handler = self._create_file_handler(log_file, log_level, enable_structured)
        if file_handler:
            root_logger.addHandler(file_handler)
        
        # Configure third-party and application loggers
        self._configure_third_party_loggers(third_party_level)
        self._configure_application_loggers(log_level)


def setup_structured_logging(
    log_level: Optional[str] = None,
    enable_structured: Optional[bool] = None,
    log_file: Optional[str] = None,
    enable_colors: Optional[bool] = None,
    third_party_level: Optional[str] = None
) -> None:
    """
    Setup application-wide logging configuration with optimized performance.
    
    🔧 REFACTORED: Now uses LoggingSetup class for better organization.
    
    All parameters are optional and will be read from environment variables if not provided.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - from LOG_LEVEL env var
        enable_structured: Enable JSON structured logging - from ENABLE_STRUCTURED_LOGGING env var
        log_file: Optional log file path - from LOG_FILE env var
        enable_colors: Enable colored terminal output - from LOG_COLORS env var
        third_party_level: Log level for third-party libraries - from LOG_THIRD_PARTY_LEVEL env var
    """
    logging_setup = LoggingSetup()
    logging_setup.setup(log_level, enable_structured, log_file, enable_colors, third_party_level)


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
        
        # 🔧 OPTIMIZED: Use dictionary unpacking for optional fields
        optional_fields = {
            "user_id": user_id,
            "request_id": request_id,
            "request_size": request_size,
            "response_size": response_size,
            "user_agent": user_agent,
            "ip_address": ip_address
        }
        
        # Add only non-None fields
        extra.update({k: v for k, v in optional_fields.items() if v is not None})
            
        adapter = logging.LoggerAdapter(self.logger, extra)
        adapter.log(level, message, extra=extra) 