"""
Base logging functionality.

Provides core logger creation and setup functions.
Extracted and refactored from core/monitoring/logger.py.
"""

import logging
import os
from typing import Optional
from functools import lru_cache

from core.config import get_settings

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
    
    # Import here to avoid circular imports
    if enable_correlation:
        from ..context.adapters import CorrelationLoggingAdapter
        correlation_logger = CorrelationLoggingAdapter(logger, {})
        _logger_cache[name] = correlation_logger
        return correlation_logger
    
    _logger_cache[name] = logger
    return logger


class LoggingSetup:
    """Centralized logging configuration and setup."""
    
    def __init__(self, settings=None):
        """Initialize logging setup with configuration."""
        self.settings = settings or get_settings()
    
    def _create_console_handler(self, log_level: str, enable_structured: bool, 
                               enable_colors: bool) -> logging.StreamHandler:
        """
        Create console handler with appropriate formatter.
        
        Args:
            log_level: Logging level
            enable_structured: Whether to use structured JSON formatting
            enable_colors: Whether to enable colored output
            
        Returns:
            Configured console handler
        """
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, log_level.upper()))
        
        if enable_structured:
            from .formatters import StructuredFormatter
            handler.setFormatter(StructuredFormatter())
        else:
            self._configure_console_formatter(handler, enable_colors)
        
        return handler
    
    def _configure_console_formatter(self, handler: logging.StreamHandler, enable_colors: bool):
        """Configure console formatter with optional colors."""
        if enable_colors:
            from .formatters import ColoredFormatter
            formatter = ColoredFormatter(
                '%(levelname)s | %(name)s | %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
            )
        handler.setFormatter(formatter)
    
    def _create_file_handler(self, log_file: str, log_level: str, 
                           enable_structured: bool) -> Optional[logging.FileHandler]:
        """
        Create file handler for logging to file.
        
        Args:
            log_file: Path to log file
            log_level: Logging level
            enable_structured: Whether to use structured JSON formatting
            
        Returns:
            Configured file handler or None if creation failed
        """
        try:
            # Ensure log directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            handler = logging.FileHandler(log_file)
            handler.setLevel(getattr(logging, log_level.upper()))
            
            if enable_structured:
                from .formatters import StructuredFormatter
                handler.setFormatter(StructuredFormatter())
            else:
                formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
                )
                handler.setFormatter(formatter)
            
            return handler
            
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create log file {log_file}: {e}")
            return None
    
    def _configure_third_party_loggers(self, third_party_level: str):
        """Configure third-party library loggers."""
        for logger_name in THIRD_PARTY_LOGGERS:
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, third_party_level.upper()))
    
    def _configure_application_loggers(self, log_level: str):
        """Configure application-specific loggers."""
        for logger_name in LOGGER_NAMES_TO_CONFIGURE:
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, log_level.upper()))
    
    def setup(self, log_level: Optional[str] = None, enable_structured: Optional[bool] = None,
              log_file: Optional[str] = None, enable_colors: Optional[bool] = None,
              third_party_level: Optional[str] = None) -> None:
        """
        Setup logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_structured: Whether to use structured JSON logging
            log_file: Path to log file (optional)
            enable_colors: Whether to enable colored console output
            third_party_level: Log level for third-party libraries
        """
        # Use settings defaults if not provided
        log_level = log_level or getattr(self.settings, 'LOG_LEVEL', 'INFO')
        enable_structured = enable_structured if enable_structured is not None else getattr(self.settings, 'ENABLE_STRUCTURED_LOGGING', False)
        enable_colors = enable_colors if enable_colors is not None else getattr(self.settings, 'ENABLE_COLORED_LOGGING', True)
        third_party_level = third_party_level or getattr(self.settings, 'THIRD_PARTY_LOG_LEVEL', 'WARNING')
        log_file = log_file or getattr(self.settings, 'LOG_FILE', None)
        
        # Clear existing handlers from root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set root logger level
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Add console handler
        console_handler = self._create_console_handler(log_level, enable_structured, enable_colors)
        root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            file_handler = self._create_file_handler(log_file, log_level, enable_structured)
            if file_handler:
                root_logger.addHandler(file_handler)
        
        # Configure third-party loggers
        self._configure_third_party_loggers(third_party_level)
        
        # Configure application loggers
        self._configure_application_loggers(log_level)


def setup_structured_logging(
    log_level: Optional[str] = None,
    enable_structured: Optional[bool] = None,
    log_file: Optional[str] = None,
    enable_colors: Optional[bool] = None,
    third_party_level: Optional[str] = None
) -> None:
    """
    Convenience function to setup structured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_structured: Whether to use structured JSON logging
        log_file: Path to log file (optional)
        enable_colors: Whether to enable colored console output  
        third_party_level: Log level for third-party libraries
    """
    setup = LoggingSetup()
    setup.setup(
        log_level=log_level,
        enable_structured=enable_structured,
        log_file=log_file,
        enable_colors=enable_colors,
        third_party_level=third_party_level
    ) 