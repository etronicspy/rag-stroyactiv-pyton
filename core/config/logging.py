"""
Unified logging configuration for RAG Construction Materials API.
All logging-related settings in one place for better maintainability.
"""

from enum import Enum
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import json


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogTimestampFormat(str, Enum):
    """Log timestamp format options."""
    ISO8601 = "ISO8601"
    RFC3339 = "RFC3339"
    TIMESTAMP = "timestamp"


class LoggingConfig(BaseSettings):
    """
    🔧 UNIFIED LOGGING CONFIGURATION
    
    All logging settings from env.example in typed, validated form.
    """
    
    # === ОСНОВНЫЕ НАСТРОЙКИ ЛОГГИРОВАНИЯ ===
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Основной уровень логгирования")
    ENABLE_STRUCTURED_LOGGING: bool = Field(default=False, description="JSON логгирование для продакшн")
    LOG_FILE: Optional[str] = Field(default=None, description="Путь к файлу логов")
    LOG_COLORS: bool = Field(default=True, description="Цветное логгирование в консоли")
    LOG_THIRD_PARTY_LEVEL: LogLevel = Field(default=LogLevel.WARNING, description="Уровень для сторонних библиотек")
    
    # === HTTP ЛОГГИРОВАНИЕ (MIDDLEWARE) ===  
    ENABLE_REQUEST_LOGGING: bool = Field(default=True, description="Логгирование HTTP запросов")
    LOG_REQUEST_BODY: bool = Field(default=False, description="Логгировать тела запросов")
    LOG_RESPONSE_BODY: bool = Field(default=False, description="Логгировать тела ответов")
    LOG_REQUEST_HEADERS: bool = Field(default=True, description="Включить заголовки в логи")
    LOG_MASK_SENSITIVE_HEADERS: bool = Field(default=True, description="Маскировать чувствительные заголовки")
    LOG_MAX_BODY_SIZE: int = Field(default=65536, description="Максимальный размер тела для логгирования (байт)")
    
    # === CORRELATION ID И ТРАССИРОВКА ===
    LOG_CORRELATION_ID: bool = Field(default=True, description="Включить correlation ID")
    LOG_CORRELATION_ID_HEADER: bool = Field(default=True, description="Передавать correlation ID в заголовках")
    
    # === БАЗА ДАННЫХ ЛОГГИРОВАНИЕ ===
    LOG_DATABASE_OPERATIONS: bool = Field(default=True, description="Логгирование операций с БД")
    LOG_SQL_QUERIES: bool = Field(default=False, description="Логгировать SQL запросы")
    LOG_SQL_PARAMETERS: bool = Field(default=False, description="Логгировать параметры SQL")
    LOG_VECTOR_OPERATIONS: bool = Field(default=True, description="Логгировать операции с векторными БД")
    LOG_CACHE_OPERATIONS: bool = Field(default=False, description="Логгировать операции с кешем")
    
    # === PERFORMANCE МЕТРИКИ ===
    LOG_PERFORMANCE_METRICS: bool = Field(default=True, description="Логгирование производительности")
    LOG_TIMING_DETAILS: bool = Field(default=True, description="Детальные метрики времени")
    LOG_SLOW_OPERATION_THRESHOLD_MS: int = Field(default=1000, description="Порог медленных операций (мс)")
    
    # === БЕЗОПАСНОСТЬ ЛОГГИРОВАНИЯ ===
    LOG_SECURITY_EVENTS: bool = Field(default=True, description="Логгирование событий безопасности")
    LOG_BLOCKED_REQUESTS: bool = Field(default=True, description="Логгировать заблокированные запросы")
    LOG_SECURITY_INCIDENTS: bool = Field(default=True, description="Логгировать попытки атак")
    
    # === ФОРМАТИРОВАНИЕ ЛОГОВ ===
    LOG_TIMESTAMP_FORMAT: LogTimestampFormat = Field(default=LogTimestampFormat.ISO8601, description="Формат временных меток")
    LOG_SOURCE_INFO: bool = Field(default=True, description="Информация о файле и строке")
    LOG_STACK_TRACE: bool = Field(default=True, description="Stack trace для ошибок")
    
    # === ПРОДВИНУТЫЕ НАСТРОЙКИ ===
    LOG_FILE_ROTATION: bool = Field(default=True, description="Ротация файлов логов")
    LOG_FILE_MAX_SIZE_MB: int = Field(default=100, description="Максимальный размер файла лога (МБ)")
    LOG_FILE_BACKUP_COUNT: int = Field(default=5, description="Количество backup файлов")
    LOG_ASYNC_LOGGING: bool = Field(default=False, description="Асинхронное логгирование")
    LOG_BUFFER_SIZE: int = Field(default=100, description="Размер буфера для логов")
    LOG_FLUSH_INTERVAL: int = Field(default=5, description="Интервал flush буфера (сек)")
    
    # === СПЕЦИАЛИЗИРОВАННЫЕ ЛОГГЕРЫ ===
    LOG_MIDDLEWARE_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Уровень для middleware")
    LOG_SERVICES_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Уровень для сервисов")
    LOG_API_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Уровень для API endpoints")
    LOG_DATABASE_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Уровень для database operations")
    
    # === EXCLUDE PATTERNS ===
    LOG_EXCLUDE_PATHS: List[str] = Field(
        default=["/docs", "/openapi.json", "/favicon.ico", "/static", "/health"], 
        description="Пути для исключения из логгирования"
    )
    LOG_EXCLUDE_HEADERS: List[str] = Field(
        default=["user-agent", "accept-encoding", "accept-language"],
        description="Заголовки для исключения из логгирования"
    )
    
    @field_validator('LOG_EXCLUDE_PATHS', mode='before')
    @classmethod
    def parse_exclude_paths(cls, v):
        """Parse JSON string or return list as-is."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v.split(',')
        return v if isinstance(v, list) else []
    
    @field_validator('LOG_EXCLUDE_HEADERS', mode='before')
    @classmethod
    def parse_exclude_headers(cls, v):
        """Parse JSON string or return list as-is."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v.split(',')
        return v if isinstance(v, list) else []
    
    class Config:
        env_file = ".env"
        case_sensitive = True 