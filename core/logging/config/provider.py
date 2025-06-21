"""
Configuration provider implementation.

This module provides a provider for logging configuration.
"""

import logging
import os
import sys
from typing import Dict, List, Optional, Any, Union, Type, TypeVar, cast

from core.logging.config.settings import LoggingSettings, get_logging_settings
from core.logging.config.validator import validate_configuration


T = TypeVar('T')


class ConfigurationProvider:
    """
    Provider for logging configuration.
    
    This provider provides access to logging configuration.
    """
    
    def __init__(self, settings: Optional[LoggingSettings] = None):
        """
        Initialize a new configuration provider.
        
        Args:
            settings: The logging settings to use
        """
        self._settings = settings or get_logging_settings()
        
        # Validate settings
        validator = validate_configuration(self._settings)
        if not validator.validate():
            errors = validator.get_errors()
            raise ValueError(f"Invalid logging configuration: {', '.join(errors)}")
    
    def get_settings(self) -> LoggingSettings:
        """
        Get the logging settings.
        
        Returns:
            LoggingSettings: The logging settings
        """
        return self._settings
    
    def get_log_level(self, name: str = "") -> int:
        """
        Get the log level for a logger.
        
        Args:
            name: The logger name
            
        Returns:
            int: The log level
        """
        # Check if the logger is a third-party logger
        if name and not name.startswith(("core.", "api.", "services.")):
            level_name = self._settings.GENERAL.THIRD_PARTY_LEVEL.value
        else:
            level_name = self._settings.GENERAL.DEFAULT_LEVEL.value
        
        # Convert level name to level
        return getattr(logging, level_name)
    
    def get_formatter_settings(self) -> Dict[str, Any]:
        """
        Get formatter settings.
        
        Returns:
            Dict[str, Any]: The formatter settings
        """
        return {
            "type": self._settings.FORMATTER.DEFAULT_TYPE.value,
            "timestamp_format": self._settings.FORMATTER.TIMESTAMP_FORMAT,
            "enable_source_info": self._settings.FORMATTER.ENABLE_SOURCE_INFO,
            "enable_colors": self._settings.FORMATTER.ENABLE_COLORS,
            "json_ensure_ascii": self._settings.FORMATTER.JSON_ENSURE_ASCII,
            "json_indent": self._settings.FORMATTER.JSON_INDENT,
            "json_sort_keys": self._settings.FORMATTER.JSON_SORT_KEYS,
        }
    
    def get_handler_settings(self) -> Dict[str, Any]:
        """
        Get handler settings.
        
        Returns:
            Dict[str, Any]: The handler settings
        """
        return {
            "types": [handler_type.value for handler_type in self._settings.HANDLER.DEFAULT_TYPES],
            "console_stream": self._settings.HANDLER.CONSOLE_STREAM,
            "file_path": self._settings.HANDLER.FILE_PATH,
            "file_mode": self._settings.HANDLER.FILE_MODE,
            "file_encoding": self._settings.HANDLER.FILE_ENCODING,
            "rotating_file_max_bytes": self._settings.HANDLER.ROTATING_FILE_MAX_BYTES,
            "rotating_file_backup_count": self._settings.HANDLER.ROTATING_FILE_BACKUP_COUNT,
            "timed_rotating_file_when": self._settings.HANDLER.TIMED_ROTATING_FILE_WHEN,
            "timed_rotating_file_interval": self._settings.HANDLER.TIMED_ROTATING_FILE_INTERVAL,
            "timed_rotating_file_backup_count": self._settings.HANDLER.TIMED_ROTATING_FILE_BACKUP_COUNT,
        }
    
    def get_context_settings(self) -> Dict[str, Any]:
        """
        Get context settings.
        
        Returns:
            Dict[str, Any]: The context settings
        """
        return {
            "enable_correlation_id": self._settings.CONTEXT.ENABLE_CORRELATION_ID,
            "correlation_id_header": self._settings.CONTEXT.CORRELATION_ID_HEADER,
            "correlation_id_generator": self._settings.CONTEXT.CORRELATION_ID_GENERATOR,
            "enable_context_pool": self._settings.CONTEXT.ENABLE_CONTEXT_POOL,
            "context_pool_size": self._settings.CONTEXT.CONTEXT_POOL_SIZE,
        }
    
    def get_memory_settings(self) -> Dict[str, Any]:
        """
        Get memory optimization settings.
        
        Returns:
            Dict[str, Any]: The memory optimization settings
        """
        return {
            "enable_logger_pool": self._settings.MEMORY.ENABLE_LOGGER_POOL,
            "logger_pool_size": self._settings.MEMORY.LOGGER_POOL_SIZE,
            "enable_message_cache": self._settings.MEMORY.ENABLE_MESSAGE_CACHE,
            "message_cache_size": self._settings.MEMORY.MESSAGE_CACHE_SIZE,
            "message_cache_ttl": self._settings.MEMORY.MESSAGE_CACHE_TTL,
            "enable_structured_log_cache": self._settings.MEMORY.ENABLE_STRUCTURED_LOG_CACHE,
            "structured_log_cache_size": self._settings.MEMORY.STRUCTURED_LOG_CACHE_SIZE,
            "structured_log_cache_ttl": self._settings.MEMORY.STRUCTURED_LOG_CACHE_TTL,
        }
    
    def get_http_settings(self) -> Dict[str, Any]:
        """
        Get HTTP logging settings.
        
        Returns:
            Dict[str, Any]: The HTTP logging settings
        """
        return {
            "enable_request_logging": self._settings.HTTP.ENABLE_REQUEST_LOGGING,
            "log_request_body": self._settings.HTTP.LOG_REQUEST_BODY,
            "log_response_body": self._settings.HTTP.LOG_RESPONSE_BODY,
            "log_request_headers": self._settings.HTTP.LOG_REQUEST_HEADERS,
            "log_response_headers": self._settings.HTTP.LOG_RESPONSE_HEADERS,
            "mask_sensitive_headers": self._settings.HTTP.MASK_SENSITIVE_HEADERS,
            "sensitive_headers": self._settings.HTTP.SENSITIVE_HEADERS,
            "max_body_size": self._settings.HTTP.MAX_BODY_SIZE,
        }
    
    def get_database_settings(self) -> Dict[str, Any]:
        """
        Get database logging settings.
        
        Returns:
            Dict[str, Any]: The database logging settings
        """
        return {
            "enable_database_logging": self._settings.DATABASE.ENABLE_DATABASE_LOGGING,
            "log_sql_queries": self._settings.DATABASE.LOG_SQL_QUERIES,
            "log_sql_parameters": self._settings.DATABASE.LOG_SQL_PARAMETERS,
            "log_vector_operations": self._settings.DATABASE.LOG_VECTOR_OPERATIONS,
            "log_cache_operations": self._settings.DATABASE.LOG_CACHE_OPERATIONS,
            "slow_query_threshold_ms": self._settings.DATABASE.SLOW_QUERY_THRESHOLD_MS,
        }
    
    def get_metrics_settings(self) -> Dict[str, Any]:
        """
        Get metrics settings.
        
        Returns:
            Dict[str, Any]: The metrics settings
        """
        return {
            "enable_metrics": self._settings.METRICS.ENABLE_METRICS,
            "log_performance_metrics": self._settings.METRICS.LOG_PERFORMANCE_METRICS,
            "log_timing_details": self._settings.METRICS.LOG_TIMING_DETAILS,
            "slow_operation_threshold_ms": self._settings.METRICS.SLOW_OPERATION_THRESHOLD_MS,
        }
    
    def get_async_logging_settings(self) -> Dict[str, Any]:
        """
        Get asynchronous logging settings.
        
        Returns:
            Dict[str, Any]: The asynchronous logging settings
        """
        return {
            "enable_async_logging": self._settings.GENERAL.ENABLE_ASYNC_LOGGING,
            "worker_count": self._settings.GENERAL.WORKER_COUNT,
            "flush_interval": self._settings.GENERAL.FLUSH_INTERVAL,
            "batch_size": self._settings.GENERAL.BATCH_SIZE,
            "queue_size": self._settings.GENERAL.QUEUE_SIZE,
        }
    
    def get_value(self, path: str, default: Optional[T] = None) -> T:
        """
        Get a configuration value by path.
        
        Args:
            path: The configuration path (e.g., "GENERAL.DEFAULT_LEVEL")
            default: The default value
            
        Returns:
            The configuration value
        """
        # Split path into parts
        parts = path.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid configuration path: {path}")
        
        # Get section and option
        section, option = parts
        
        # Get section
        try:
            section_obj = getattr(self._settings, section)
        except AttributeError:
            return default
        
        # Get option
        try:
            return cast(T, getattr(section_obj, option))
        except AttributeError:
            return default


# Singleton instance
_provider: Optional[ConfigurationProvider] = None


def get_configuration() -> ConfigurationProvider:
    """
    Get the configuration provider.
    
    Returns:
        ConfigurationProvider: The configuration provider
    """
    global _provider
    
    if _provider is None:
        _provider = ConfigurationProvider()
    
    return _provider 