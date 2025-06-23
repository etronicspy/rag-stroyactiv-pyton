"""
Configuration validator implementation.

This module provides a validator for logging configuration.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional

from core.logging.config.settings import LoggingSettings


class ConfigurationValidator:
    """
    Validator for logging configuration.
    
    This validator checks the logging configuration for errors and warnings.
    """
    
    def __init__(self, settings: LoggingSettings):
        """
        Initialize a new configuration validator.
        
        Args:
            settings: The logging settings to validate
        """
        self._settings = settings
        self._errors: List[str] = []
        self._warnings: List[str] = []
    
    def validate(self) -> bool:
        """
        Validate the logging configuration.
        
        Returns:
            bool: True if the configuration is valid, False otherwise
        """
        # Reset errors and warnings
        self._errors = []
        self._warnings = []
        
        # Validate all sections
        self._validate_general()
        self._validate_formatter()
        self._validate_handler()
        self._validate_context()
        self._validate_memory()
        self._validate_http()
        self._validate_database()
        self._validate_metrics()
        
        # Check for errors
        return len(self._errors) == 0
    
    def get_errors(self) -> List[str]:
        """
        Get validation errors.
        
        Returns:
            List[str]: The validation errors
        """
        return self._errors
    
    def get_warnings(self) -> List[str]:
        """
        Get validation warnings.
        
        Returns:
            List[str]: The validation warnings
        """
        return self._warnings
    
    def _validate_general(self) -> None:
        """Validate general settings."""
        # Check log level
        try:
            level_name = self._settings.GENERAL.DEFAULT_LEVEL.value
            level = getattr(logging, level_name)
            if not isinstance(level, int):
                self._errors.append(f"Invalid log level: {level_name}")
        except (AttributeError, ValueError):
            self._errors.append(f"Invalid log level: {self._settings.GENERAL.DEFAULT_LEVEL}")
        
        # Check third-party log level
        try:
            level_name = self._settings.GENERAL.THIRD_PARTY_LEVEL.value
            level = getattr(logging, level_name)
            if not isinstance(level, int):
                self._errors.append(f"Invalid third-party log level: {level_name}")
        except (AttributeError, ValueError):
            self._errors.append(f"Invalid third-party log level: {self._settings.GENERAL.THIRD_PARTY_LEVEL}")
        
        # Check worker count
        if self._settings.GENERAL.ENABLE_ASYNC_LOGGING and self._settings.GENERAL.WORKER_COUNT < 1:
            self._errors.append("Worker count must be at least 1")
        
        # Check flush interval
        if self._settings.GENERAL.ENABLE_ASYNC_LOGGING and self._settings.GENERAL.FLUSH_INTERVAL < 0.1:
            self._errors.append("Flush interval must be at least 0.1 seconds")
        
        # Check batch size
        if self._settings.GENERAL.ENABLE_ASYNC_LOGGING and self._settings.GENERAL.BATCH_SIZE < 1:
            self._errors.append("Batch size must be at least 1")
        
        # Check queue size
        if self._settings.GENERAL.ENABLE_ASYNC_LOGGING and self._settings.GENERAL.QUEUE_SIZE < 10:
            self._errors.append("Queue size must be at least 10")
    
    def _validate_formatter(self) -> None:
        """Validate formatter settings."""
        # Check timestamp format
        try:
            import datetime
            datetime.datetime.now().strftime(self._settings.FORMATTER.TIMESTAMP_FORMAT)
        except ValueError:
            self._errors.append(f"Invalid timestamp format: {self._settings.FORMATTER.TIMESTAMP_FORMAT}")
    
    def _validate_handler(self) -> None:
        """Validate handler settings."""
        # Check console stream
        if self._settings.HANDLER.CONSOLE_STREAM not in ["stdout", "stderr"]:
            self._errors.append(f"Invalid console stream: {self._settings.HANDLER.CONSOLE_STREAM}")
        
        # Check file path
        if self._settings.HANDLER.FILE_PATH is not None:
            file_path = Path(self._settings.HANDLER.FILE_PATH)
            
            # Check if the directory exists
            if not file_path.parent.exists():
                self._warnings.append(f"Log file directory does not exist: {file_path.parent}")
            
            # Check if the file is writable
            if file_path.exists() and not os.access(file_path, os.W_OK):
                self._errors.append(f"Log file is not writable: {file_path}")
        
        # Check file mode
        if self._settings.HANDLER.FILE_MODE not in ["a", "w"]:
            self._errors.append(f"Invalid file mode: {self._settings.HANDLER.FILE_MODE}")
        
        # Check rotating file settings
        if self._settings.HANDLER.ROTATING_FILE_MAX_BYTES < 1024:
            self._errors.append("Rotating file max bytes must be at least 1024")
        
        if self._settings.HANDLER.ROTATING_FILE_BACKUP_COUNT < 0:
            self._errors.append("Rotating file backup count must be at least 0")
        
        # Check timed rotating file settings
        valid_when_values = ["S", "M", "H", "D", "W0", "W1", "W2", "W3", "W4", "W5", "W6", "midnight"]
        if self._settings.HANDLER.TIMED_ROTATING_FILE_WHEN not in valid_when_values:
            self._errors.append(f"Invalid timed rotating file when: {self._settings.HANDLER.TIMED_ROTATING_FILE_WHEN}")
        
        if self._settings.HANDLER.TIMED_ROTATING_FILE_INTERVAL < 1:
            self._errors.append("Timed rotating file interval must be at least 1")
        
        if self._settings.HANDLER.TIMED_ROTATING_FILE_BACKUP_COUNT < 0:
            self._errors.append("Timed rotating file backup count must be at least 0")
    
    def _validate_context(self) -> None:
        """Validate context settings."""
        # Check correlation ID generator
        if self._settings.CONTEXT.CORRELATION_ID_GENERATOR not in ["uuid4", "timestamp"]:
            self._errors.append(f"Invalid correlation ID generator: {self._settings.CONTEXT.CORRELATION_ID_GENERATOR}")
        
        # Check context pool size
        if self._settings.CONTEXT.ENABLE_CONTEXT_POOL and self._settings.CONTEXT.CONTEXT_POOL_SIZE < 10:
            self._errors.append("Context pool size must be at least 10")
    
    def _validate_memory(self) -> None:
        """Validate memory settings."""
        # Check logger pool size
        if self._settings.MEMORY.ENABLE_LOGGER_POOL and self._settings.MEMORY.LOGGER_POOL_SIZE < 10:
            self._errors.append("Logger pool size must be at least 10")
        
        # Check message cache size
        if self._settings.MEMORY.ENABLE_MESSAGE_CACHE and self._settings.MEMORY.MESSAGE_CACHE_SIZE < 100:
            self._errors.append("Message cache size must be at least 100")
        
        # Check message cache TTL
        if self._settings.MEMORY.ENABLE_MESSAGE_CACHE and self._settings.MEMORY.MESSAGE_CACHE_TTL < 10.0:
            self._errors.append("Message cache TTL must be at least 10.0 seconds")
        
        # Check structured log cache size
        if self._settings.MEMORY.ENABLE_STRUCTURED_LOG_CACHE and self._settings.MEMORY.STRUCTURED_LOG_CACHE_SIZE < 100:
            self._errors.append("Structured log cache size must be at least 100")
        
        # Check structured log cache TTL
        if self._settings.MEMORY.ENABLE_STRUCTURED_LOG_CACHE and self._settings.MEMORY.STRUCTURED_LOG_CACHE_TTL < 10.0:
            self._errors.append("Structured log cache TTL must be at least 10.0 seconds")
    
    def _validate_http(self) -> None:
        """Validate HTTP settings."""
        # Check max body size
        if self._settings.HTTP.MAX_BODY_SIZE < 0:
            self._errors.append("Max body size must be at least 0")
    
    def _validate_database(self) -> None:
        """Validate database settings."""
        # Check slow query threshold
        if self._settings.DATABASE.SLOW_QUERY_THRESHOLD_MS < 0:
            self._errors.append("Slow query threshold must be at least 0")
    
    def _validate_metrics(self) -> None:
        """Validate metrics settings."""
        # Check slow operation threshold
        if self._settings.METRICS.SLOW_OPERATION_THRESHOLD_MS < 0:
            self._errors.append("Slow operation threshold must be at least 0")


def validate_configuration(settings: Optional[LoggingSettings] = None) -> ConfigurationValidator:
    """
    Validate logging configuration.
    
    Args:
        settings: The logging settings to validate
        
    Returns:
        ConfigurationValidator: The configuration validator
    """
    # Get settings if not provided
    if settings is None:
        from core.logging.config.settings import get_logging_settings
        settings = get_logging_settings()
    
    # Create validator
    validator = ConfigurationValidator(settings)
    
    # Validate settings
    validator.validate()
    
    return validator 