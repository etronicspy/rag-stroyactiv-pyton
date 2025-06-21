"""
Модуль для автоматической миграции переменных окружения
со старой системы логирования на новую.

Позволяет использовать существующие .env файлы без изменений,
автоматически преобразуя старые переменные в новый формат.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# Карта соответствия старых и новых переменных окружения
ENV_VAR_MAPPING = {
    # Основные настройки
    "LOG_LEVEL": "LOG_GENERAL_DEFAULT_LEVEL",
    "LOG_THIRD_PARTY_LEVEL": "LOG_GENERAL_THIRD_PARTY_LEVEL",
    "LOG_ASYNC_LOGGING": "LOG_GENERAL_ENABLE_ASYNC_LOGGING",
    "LOG_BUFFER_SIZE": "LOG_GENERAL_BATCH_SIZE",
    "LOG_FLUSH_INTERVAL": "LOG_GENERAL_FLUSH_INTERVAL",
    
    # Форматирование
    "LOG_COLORS": "LOG_FORMATTER_ENABLE_COLORS",
    "LOG_SOURCE_INFO": "LOG_FORMATTER_ENABLE_SOURCE_INFO",
    "LOG_TIMESTAMP_FORMAT": "LOG_FORMATTER_TIMESTAMP_FORMAT",
    "ENABLE_STRUCTURED_LOGGING": None,  # Требует специальной обработки
    
    # Обработчики
    "LOG_FILE": "LOG_HANDLER_FILE_PATH",
    "LOG_FILE_ROTATION": None,  # Требует специальной обработки
    "LOG_FILE_MAX_SIZE_MB": None,  # Требует специальной обработки
    "LOG_FILE_BACKUP_COUNT": "LOG_HANDLER_ROTATING_FILE_BACKUP_COUNT",
    
    # HTTP логирование
    "ENABLE_REQUEST_LOGGING": "LOG_HTTP_ENABLE_REQUEST_LOGGING",
    "LOG_REQUEST_BODY": "LOG_HTTP_LOG_REQUEST_BODY",
    "LOG_RESPONSE_BODY": "LOG_HTTP_LOG_RESPONSE_BODY",
    "LOG_REQUEST_HEADERS": "LOG_HTTP_LOG_REQUEST_HEADERS",
    "LOG_MASK_SENSITIVE_HEADERS": "LOG_HTTP_MASK_SENSITIVE_HEADERS",
    "LOG_MAX_BODY_SIZE": "LOG_HTTP_MAX_BODY_SIZE",
    
    # Контекст
    "LOG_CORRELATION_ID": "LOG_CONTEXT_ENABLE_CORRELATION_ID",
    "LOG_CORRELATION_ID_HEADER": "LOG_CONTEXT_CORRELATION_ID_HEADER",
    
    # База данных
    "LOG_DATABASE_OPERATIONS": "LOG_DATABASE_ENABLE_DATABASE_LOGGING",
    "LOG_SQL_QUERIES": "LOG_DATABASE_LOG_SQL_QUERIES",
    "LOG_SQL_PARAMETERS": "LOG_DATABASE_LOG_SQL_PARAMETERS",
    "LOG_VECTOR_OPERATIONS": "LOG_DATABASE_LOG_VECTOR_OPERATIONS",
    "LOG_CACHE_OPERATIONS": "LOG_DATABASE_LOG_CACHE_OPERATIONS",
    
    # Метрики
    "LOG_PERFORMANCE_METRICS": "LOG_METRICS_LOG_PERFORMANCE_METRICS",
    "LOG_TIMING_DETAILS": "LOG_METRICS_LOG_TIMING_DETAILS",
    "LOG_SLOW_OPERATION_THRESHOLD_MS": "LOG_METRICS_SLOW_OPERATION_THRESHOLD_MS",
}


def migrate_legacy_env_vars() -> Dict[str, Any]:
    """
    Автоматически преобразует переменные окружения из старого формата в новый.
    
    Возвращает словарь с преобразованными переменными окружения.
    """
    migrated_vars = {}
    
    # Обработка стандартных преобразований
    for old_var, new_var in ENV_VAR_MAPPING.items():
        if old_var in os.environ and new_var is not None:
            value = os.environ[old_var]
            os.environ[new_var] = value
            migrated_vars[new_var] = value
            logger.debug(f"Migrated {old_var} -> {new_var}: {value}")
    
    # Обработка специальных случаев
    _handle_structured_logging(migrated_vars)
    _handle_file_rotation(migrated_vars)
    _handle_file_max_size(migrated_vars)
    
    return migrated_vars


def _handle_structured_logging(migrated_vars: Dict[str, Any]) -> None:
    """
    Специальная обработка для ENABLE_STRUCTURED_LOGGING.
    Преобразует в LOG_FORMATTER_DEFAULT_TYPE=json или text.
    """
    if "ENABLE_STRUCTURED_LOGGING" in os.environ:
        value = os.environ["ENABLE_STRUCTURED_LOGGING"].lower()
        if value in ("true", "1", "yes", "y"):
            os.environ["LOG_FORMATTER_DEFAULT_TYPE"] = "json"
        else:
            os.environ["LOG_FORMATTER_DEFAULT_TYPE"] = "text"
        
        migrated_vars["LOG_FORMATTER_DEFAULT_TYPE"] = os.environ["LOG_FORMATTER_DEFAULT_TYPE"]
        logger.debug(f"Migrated ENABLE_STRUCTURED_LOGGING -> LOG_FORMATTER_DEFAULT_TYPE: {os.environ['LOG_FORMATTER_DEFAULT_TYPE']}")


def _handle_file_rotation(migrated_vars: Dict[str, Any]) -> None:
    """
    Специальная обработка для LOG_FILE_ROTATION.
    Преобразует в LOG_HANDLER_DEFAULT_TYPES.
    """
    if "LOG_FILE_ROTATION" in os.environ and "LOG_FILE" in os.environ:
        value = os.environ["LOG_FILE_ROTATION"].lower()
        if value in ("true", "1", "yes", "y"):
            os.environ["LOG_HANDLER_DEFAULT_TYPES"] = "console,rotating_file"
        else:
            os.environ["LOG_HANDLER_DEFAULT_TYPES"] = "console,file"
        
        migrated_vars["LOG_HANDLER_DEFAULT_TYPES"] = os.environ["LOG_HANDLER_DEFAULT_TYPES"]
        logger.debug(f"Migrated LOG_FILE_ROTATION -> LOG_HANDLER_DEFAULT_TYPES: {os.environ['LOG_HANDLER_DEFAULT_TYPES']}")


def _handle_file_max_size(migrated_vars: Dict[str, Any]) -> None:
    """
    Специальная обработка для LOG_FILE_MAX_SIZE_MB.
    Преобразует из МБ в байты для LOG_HANDLER_ROTATING_FILE_MAX_BYTES.
    """
    if "LOG_FILE_MAX_SIZE_MB" in os.environ:
        try:
            mb_value = int(os.environ["LOG_FILE_MAX_SIZE_MB"])
            bytes_value = mb_value * 1024 * 1024  # Преобразование МБ в байты
            os.environ["LOG_HANDLER_ROTATING_FILE_MAX_BYTES"] = str(bytes_value)
            
            migrated_vars["LOG_HANDLER_ROTATING_FILE_MAX_BYTES"] = str(bytes_value)
            logger.debug(f"Migrated LOG_FILE_MAX_SIZE_MB -> LOG_HANDLER_ROTATING_FILE_MAX_BYTES: {bytes_value}")
        except ValueError:
            logger.warning(f"Could not convert LOG_FILE_MAX_SIZE_MB value '{os.environ['LOG_FILE_MAX_SIZE_MB']}' to integer")


def get_legacy_env_var(name: str, default: Optional[Any] = None) -> Any:
    """
    Получает значение переменной окружения с учетом миграции.
    
    Сначала проверяет новую переменную, затем старую.
    
    Args:
        name: Имя переменной в новом формате
        default: Значение по умолчанию, если переменная не найдена
        
    Returns:
        Значение переменной или значение по умолчанию
    """
    # Поиск старой переменной для нового имени
    old_var = None
    for old_name, new_name in ENV_VAR_MAPPING.items():
        if new_name == name:
            old_var = old_name
            break
    
    # Сначала проверяем новую переменную
    if name in os.environ:
        return os.environ[name]
    
    # Затем проверяем старую переменную, если найдена
    if old_var and old_var in os.environ:
        return os.environ[old_var]
    
    # Возвращаем значение по умолчанию
    return default 