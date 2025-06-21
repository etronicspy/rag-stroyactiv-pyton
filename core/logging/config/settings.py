"""
Logging settings implementation.

This module provides settings for the logging system.
"""

import os
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, field_validator


class LogLevel(str, Enum):
    """Log level enumeration."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class FormatterType(str, Enum):
    """Formatter type enumeration."""
    
    TEXT = "text"
    JSON = "json"
    COLORED = "colored"


class HandlerType(str, Enum):
    """Handler type enumeration."""
    
    CONSOLE = "console"
    FILE = "file"
    ROTATING_FILE = "rotating_file"
    TIMED_ROTATING_FILE = "timed_rotating_file"
    NULL = "null"


class GeneralSettings(BaseModel):
    """General logging settings."""
    
    DEFAULT_LEVEL: LogLevel = Field(
        default=LogLevel.INFO,
        description="Default log level"
    )
    
    THIRD_PARTY_LEVEL: LogLevel = Field(
        default=LogLevel.WARNING,
        description="Log level for third-party libraries"
    )
    
    PROPAGATE: bool = Field(
        default=False,
        description="Whether to propagate logs to parent loggers"
    )
    
    ENABLE_ASYNC_LOGGING: bool = Field(
        default=True,
        description="Whether to enable asynchronous logging"
    )
    
    WORKER_COUNT: int = Field(
        default=1,
        description="Number of worker tasks for asynchronous logging"
    )
    
    FLUSH_INTERVAL: float = Field(
        default=0.5,
        description="Flush interval in seconds for asynchronous logging"
    )
    
    BATCH_SIZE: int = Field(
        default=100,
        description="Batch size for asynchronous logging"
    )
    
    QUEUE_SIZE: int = Field(
        default=1000,
        description="Queue size for asynchronous logging"
    )
    
    @field_validator("WORKER_COUNT")
    def validate_worker_count(cls, v: int) -> int:
        """Validate worker count."""
        if v < 1:
            return 1
        return v
    
    @field_validator("FLUSH_INTERVAL")
    def validate_flush_interval(cls, v: float) -> float:
        """Validate flush interval."""
        if v < 0.1:
            return 0.1
        return v
    
    @field_validator("BATCH_SIZE")
    def validate_batch_size(cls, v: int) -> int:
        """Validate batch size."""
        if v < 1:
            return 1
        return v
    
    @field_validator("QUEUE_SIZE")
    def validate_queue_size(cls, v: int) -> int:
        """Validate queue size."""
        if v < 10:
            return 10
        return v


class FormatterSettings(BaseModel):
    """Formatter settings."""
    
    DEFAULT_TYPE: FormatterType = Field(
        default=FormatterType.TEXT,
        description="Default formatter type"
    )
    
    TIMESTAMP_FORMAT: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="Timestamp format"
    )
    
    ENABLE_SOURCE_INFO: bool = Field(
        default=True,
        description="Whether to include source information (file, line, function)"
    )
    
    ENABLE_COLORS: bool = Field(
        default=True,
        description="Whether to enable colors in console output"
    )
    
    JSON_ENSURE_ASCII: bool = Field(
        default=False,
        description="Whether to ensure ASCII in JSON output"
    )
    
    JSON_INDENT: Optional[int] = Field(
        default=None,
        description="Indentation in JSON output"
    )
    
    JSON_SORT_KEYS: bool = Field(
        default=True,
        description="Whether to sort keys in JSON output"
    )
    
    @field_validator("JSON_INDENT")
    def validate_json_indent(cls, v: Optional[int]) -> Optional[int]:
        """Validate JSON indent."""
        if v is not None and v < 0:
            return None
        return v


class HandlerSettings(BaseModel):
    """Handler settings."""
    
    DEFAULT_TYPES: List[HandlerType] = Field(
        default=[HandlerType.CONSOLE],
        description="Default handler types"
    )
    
    CONSOLE_STREAM: str = Field(
        default="stdout",
        description="Console stream (stdout or stderr)"
    )
    
    FILE_PATH: Optional[str] = Field(
        default=None,
        description="Log file path"
    )
    
    FILE_MODE: str = Field(
        default="a",
        description="Log file mode"
    )
    
    FILE_ENCODING: str = Field(
        default="utf-8",
        description="Log file encoding"
    )
    
    ROTATING_FILE_MAX_BYTES: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        description="Maximum file size for rotating file handler"
    )
    
    ROTATING_FILE_BACKUP_COUNT: int = Field(
        default=5,
        description="Number of backup files for rotating file handler"
    )
    
    TIMED_ROTATING_FILE_WHEN: str = Field(
        default="midnight",
        description="When to rotate for timed rotating file handler"
    )
    
    TIMED_ROTATING_FILE_INTERVAL: int = Field(
        default=1,
        description="Interval for timed rotating file handler"
    )
    
    TIMED_ROTATING_FILE_BACKUP_COUNT: int = Field(
        default=7,
        description="Number of backup files for timed rotating file handler"
    )
    
    @field_validator("CONSOLE_STREAM")
    def validate_console_stream(cls, v: str) -> str:
        """Validate console stream."""
        if v not in ["stdout", "stderr"]:
            return "stdout"
        return v
    
    @field_validator("FILE_MODE")
    def validate_file_mode(cls, v: str) -> str:
        """Validate file mode."""
        if v not in ["a", "w"]:
            return "a"
        return v
    
    @field_validator("ROTATING_FILE_MAX_BYTES")
    def validate_rotating_file_max_bytes(cls, v: int) -> int:
        """Validate rotating file max bytes."""
        if v < 1024:
            return 1024
        return v
    
    @field_validator("ROTATING_FILE_BACKUP_COUNT")
    def validate_rotating_file_backup_count(cls, v: int) -> int:
        """Validate rotating file backup count."""
        if v < 0:
            return 0
        return v
    
    @field_validator("TIMED_ROTATING_FILE_WHEN")
    def validate_timed_rotating_file_when(cls, v: str) -> str:
        """Validate timed rotating file when."""
        valid_values = ["S", "M", "H", "D", "W0", "W1", "W2", "W3", "W4", "W5", "W6", "midnight"]
        if v not in valid_values:
            return "midnight"
        return v
    
    @field_validator("TIMED_ROTATING_FILE_INTERVAL")
    def validate_timed_rotating_file_interval(cls, v: int) -> int:
        """Validate timed rotating file interval."""
        if v < 1:
            return 1
        return v
    
    @field_validator("TIMED_ROTATING_FILE_BACKUP_COUNT")
    def validate_timed_rotating_file_backup_count(cls, v: int) -> int:
        """Validate timed rotating file backup count."""
        if v < 0:
            return 0
        return v


class ContextSettings(BaseModel):
    """Context settings."""
    
    ENABLE_CORRELATION_ID: bool = Field(
        default=True,
        description="Whether to enable correlation ID"
    )
    
    CORRELATION_ID_HEADER: str = Field(
        default="X-Correlation-ID",
        description="Correlation ID header name"
    )
    
    CORRELATION_ID_GENERATOR: str = Field(
        default="uuid4",
        description="Correlation ID generator (uuid4 or timestamp)"
    )
    
    ENABLE_CONTEXT_POOL: bool = Field(
        default=True,
        description="Whether to enable context pool"
    )
    
    CONTEXT_POOL_SIZE: int = Field(
        default=100,
        description="Context pool size"
    )
    
    @field_validator("CORRELATION_ID_GENERATOR")
    def validate_correlation_id_generator(cls, v: str) -> str:
        """Validate correlation ID generator."""
        if v not in ["uuid4", "timestamp"]:
            return "uuid4"
        return v
    
    @field_validator("CONTEXT_POOL_SIZE")
    def validate_context_pool_size(cls, v: int) -> int:
        """Validate context pool size."""
        if v < 10:
            return 10
        return v


class MemorySettings(BaseModel):
    """Memory optimization settings."""
    
    ENABLE_LOGGER_POOL: bool = Field(
        default=True,
        description="Whether to enable logger pool"
    )
    
    LOGGER_POOL_SIZE: int = Field(
        default=100,
        description="Logger pool size"
    )
    
    ENABLE_MESSAGE_CACHE: bool = Field(
        default=True,
        description="Whether to enable message cache"
    )
    
    MESSAGE_CACHE_SIZE: int = Field(
        default=1000,
        description="Message cache size"
    )
    
    MESSAGE_CACHE_TTL: float = Field(
        default=300.0,  # 5 minutes
        description="Message cache TTL in seconds"
    )
    
    ENABLE_STRUCTURED_LOG_CACHE: bool = Field(
        default=True,
        description="Whether to enable structured log cache"
    )
    
    STRUCTURED_LOG_CACHE_SIZE: int = Field(
        default=1000,
        description="Structured log cache size"
    )
    
    STRUCTURED_LOG_CACHE_TTL: float = Field(
        default=300.0,  # 5 minutes
        description="Structured log cache TTL in seconds"
    )
    
    @field_validator("LOGGER_POOL_SIZE")
    def validate_logger_pool_size(cls, v: int) -> int:
        """Validate logger pool size."""
        if v < 10:
            return 10
        return v
    
    @field_validator("MESSAGE_CACHE_SIZE")
    def validate_message_cache_size(cls, v: int) -> int:
        """Validate message cache size."""
        if v < 100:
            return 100
        return v
    
    @field_validator("MESSAGE_CACHE_TTL")
    def validate_message_cache_ttl(cls, v: float) -> float:
        """Validate message cache TTL."""
        if v < 10.0:
            return 10.0
        return v
    
    @field_validator("STRUCTURED_LOG_CACHE_SIZE")
    def validate_structured_log_cache_size(cls, v: int) -> int:
        """Validate structured log cache size."""
        if v < 100:
            return 100
        return v
    
    @field_validator("STRUCTURED_LOG_CACHE_TTL")
    def validate_structured_log_cache_ttl(cls, v: float) -> float:
        """Validate structured log cache TTL."""
        if v < 10.0:
            return 10.0
        return v


class HttpSettings(BaseModel):
    """HTTP logging settings."""
    
    ENABLE_REQUEST_LOGGING: bool = Field(
        default=True,
        description="Whether to enable request logging"
    )
    
    LOG_REQUEST_BODY: bool = Field(
        default=True,
        description="Whether to log request body"
    )
    
    LOG_RESPONSE_BODY: bool = Field(
        default=True,
        description="Whether to log response body"
    )
    
    LOG_REQUEST_HEADERS: bool = Field(
        default=True,
        description="Whether to log request headers"
    )
    
    LOG_RESPONSE_HEADERS: bool = Field(
        default=True,
        description="Whether to log response headers"
    )
    
    MASK_SENSITIVE_HEADERS: bool = Field(
        default=True,
        description="Whether to mask sensitive headers"
    )
    
    SENSITIVE_HEADERS: List[str] = Field(
        default=["Authorization", "Cookie", "Set-Cookie"],
        description="Sensitive headers to mask"
    )
    
    MAX_BODY_SIZE: int = Field(
        default=10 * 1024,  # 10 KB
        description="Maximum body size to log"
    )
    
    @field_validator("MAX_BODY_SIZE")
    def validate_max_body_size(cls, v: int) -> int:
        """Validate max body size."""
        if v < 0:
            return 0
        return v


class DatabaseSettings(BaseModel):
    """Database logging settings."""
    
    ENABLE_DATABASE_LOGGING: bool = Field(
        default=True,
        description="Whether to enable database logging"
    )
    
    LOG_SQL_QUERIES: bool = Field(
        default=True,
        description="Whether to log SQL queries"
    )
    
    LOG_SQL_PARAMETERS: bool = Field(
        default=True,
        description="Whether to log SQL parameters"
    )
    
    LOG_VECTOR_OPERATIONS: bool = Field(
        default=True,
        description="Whether to log vector operations"
    )
    
    LOG_CACHE_OPERATIONS: bool = Field(
        default=True,
        description="Whether to log cache operations"
    )
    
    SLOW_QUERY_THRESHOLD_MS: int = Field(
        default=1000,  # 1 second
        description="Slow query threshold in milliseconds"
    )
    
    @field_validator("SLOW_QUERY_THRESHOLD_MS")
    def validate_slow_query_threshold_ms(cls, v: int) -> int:
        """Validate slow query threshold."""
        if v < 0:
            return 0
        return v


class MetricsSettings(BaseModel):
    """Metrics settings."""
    
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Whether to enable metrics"
    )
    
    LOG_PERFORMANCE_METRICS: bool = Field(
        default=True,
        description="Whether to log performance metrics"
    )
    
    LOG_TIMING_DETAILS: bool = Field(
        default=True,
        description="Whether to log timing details"
    )
    
    SLOW_OPERATION_THRESHOLD_MS: int = Field(
        default=1000,  # 1 second
        description="Slow operation threshold in milliseconds"
    )
    
    @field_validator("SLOW_OPERATION_THRESHOLD_MS")
    def validate_slow_operation_threshold_ms(cls, v: int) -> int:
        """Validate slow operation threshold."""
        if v < 0:
            return 0
        return v


class LoggingSettings(BaseModel):
    """Logging settings."""
    
    GENERAL: GeneralSettings = Field(default_factory=GeneralSettings)
    FORMATTER: FormatterSettings = Field(default_factory=FormatterSettings)
    HANDLER: HandlerSettings = Field(default_factory=HandlerSettings)
    CONTEXT: ContextSettings = Field(default_factory=ContextSettings)
    MEMORY: MemorySettings = Field(default_factory=MemorySettings)
    HTTP: HttpSettings = Field(default_factory=HttpSettings)
    DATABASE: DatabaseSettings = Field(default_factory=DatabaseSettings)
    METRICS: MetricsSettings = Field(default_factory=MetricsSettings)
    
    @classmethod
    def from_env(cls) -> "LoggingSettings":
        """
        Create settings from environment variables.
        
        Returns:
            LoggingSettings: The settings
        """
        settings_dict = {}
        
        # Process environment variables
        for key, value in os.environ.items():
            if key.startswith("LOG_"):
                # Convert to nested dictionary structure
                parts = key[4:].split("_", 1)
                if len(parts) == 2:
                    section, option = parts
                    
                    # Initialize section if needed
                    if section not in settings_dict:
                        settings_dict[section] = {}
                    
                    # Convert value to appropriate type
                    if value.lower() in ["true", "yes", "1"]:
                        settings_dict[section][option] = True
                    elif value.lower() in ["false", "no", "0"]:
                        settings_dict[section][option] = False
                    elif value.isdigit():
                        settings_dict[section][option] = int(value)
                    elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                        settings_dict[section][option] = float(value)
                    else:
                        settings_dict[section][option] = value
        
        # Create settings from dictionary
        return cls(**settings_dict)


# Singleton instance
_settings: Optional[LoggingSettings] = None


def get_logging_settings() -> LoggingSettings:
    """
    Get logging settings.
    
    Returns:
        LoggingSettings: The logging settings
    """
    global _settings
    
    if _settings is None:
        _settings = LoggingSettings.from_env()
    
    return _settings 