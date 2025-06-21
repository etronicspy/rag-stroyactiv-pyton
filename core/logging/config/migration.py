"""
Модуль для проверки наличия устаревших переменных окружения.

Вместо автоматической миграции старых переменных окружения, этот модуль
предоставляет функции для обнаружения устаревших переменных и вывода предупреждений.
"""

import os
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Маппинг старых переменных на новые
LEGACY_TO_NEW_ENV_VARS: Dict[str, str] = {
    "LOG_LEVEL": "LOG_GENERAL_DEFAULT_LEVEL",
    "ENABLE_STRUCTURED_LOGGING": "LOG_FORMATTER_DEFAULT_TYPE",  # true -> json, false -> text
    "LOG_FILE": "LOG_HANDLER_FILE_PATH",
    "LOG_COLORS": "LOG_FORMATTER_ENABLE_COLORS",
    "LOG_THIRD_PARTY_LEVEL": "LOG_GENERAL_THIRD_PARTY_LEVEL",
    "ENABLE_REQUEST_LOGGING": "LOG_HTTP_ENABLE_REQUEST_LOGGING",
    "LOG_REQUEST_BODY": "LOG_HTTP_LOG_REQUEST_BODY",
    "LOG_RESPONSE_BODY": "LOG_HTTP_LOG_RESPONSE_BODY",
    "LOG_REQUEST_HEADERS": "LOG_HTTP_LOG_REQUEST_HEADERS",
    "LOG_MASK_SENSITIVE_HEADERS": "LOG_HTTP_MASK_SENSITIVE_HEADERS",
    "LOG_MAX_BODY_SIZE": "LOG_HTTP_MAX_BODY_SIZE",
    "LOG_CORRELATION_ID": "LOG_CONTEXT_ENABLE_CORRELATION_ID",
    "LOG_CORRELATION_ID_HEADER": "LOG_CONTEXT_CORRELATION_ID_HEADER",
    "LOG_DATABASE_OPERATIONS": "LOG_DATABASE_ENABLE_DATABASE_LOGGING",
    "LOG_SQL_QUERIES": "LOG_DATABASE_LOG_SQL_QUERIES",
    "LOG_SQL_PARAMETERS": "LOG_DATABASE_LOG_SQL_PARAMETERS",
    "LOG_VECTOR_OPERATIONS": "LOG_DATABASE_LOG_VECTOR_OPERATIONS",
    "LOG_CACHE_OPERATIONS": "LOG_DATABASE_LOG_CACHE_OPERATIONS",
    "LOG_PERFORMANCE_METRICS": "LOG_METRICS_LOG_PERFORMANCE_METRICS",
    "LOG_TIMING_DETAILS": "LOG_METRICS_LOG_TIMING_DETAILS",
    "LOG_SLOW_OPERATION_THRESHOLD_MS": "LOG_METRICS_SLOW_OPERATION_THRESHOLD_MS",
    "LOG_TIMESTAMP_FORMAT": "LOG_FORMATTER_TIMESTAMP_FORMAT",
    "LOG_SOURCE_INFO": "LOG_FORMATTER_ENABLE_SOURCE_INFO",
    "LOG_FILE_MAX_SIZE_MB": "LOG_HANDLER_ROTATING_FILE_MAX_BYTES",  # Требует преобразования MB -> bytes
    "LOG_FILE_BACKUP_COUNT": "LOG_HANDLER_ROTATING_FILE_BACKUP_COUNT",
    "LOG_ASYNC_LOGGING": "LOG_GENERAL_ENABLE_ASYNC_LOGGING",
    "LOG_BUFFER_SIZE": "LOG_GENERAL_BATCH_SIZE",
    "LOG_FLUSH_INTERVAL": "LOG_GENERAL_FLUSH_INTERVAL",
    # Переменные без прямых аналогов
    "LOG_SECURITY_EVENTS": None,
    "LOG_BLOCKED_REQUESTS": None,
    "LOG_SECURITY_INCIDENTS": None,
    "LOG_STACK_TRACE": None,
    "LOG_FILE_ROTATION": None,
    "LOG_MIDDLEWARE_LEVEL": None,
    "LOG_SERVICES_LEVEL": None,
    "LOG_API_LEVEL": None,
    "LOG_DATABASE_LEVEL": None,
    "LOG_EXCLUDE_PATHS": None,
    "LOG_EXCLUDE_HEADERS": None,
}


def detect_legacy_env_vars() -> List[Tuple[str, str]]:
    """
    Обнаруживает устаревшие переменные окружения и возвращает список пар (старая_переменная, новая_переменная).
    
    Returns:
        List[Tuple[str, str]]: Список пар (старая_переменная, новая_переменная)
    """
    legacy_vars = []
    for legacy_var, new_var in LEGACY_TO_NEW_ENV_VARS.items():
        if legacy_var in os.environ:
            legacy_vars.append((legacy_var, new_var or "Нет прямого аналога"))
    
    return legacy_vars


def print_legacy_env_vars_warning() -> None:
    """
    Проверяет наличие устаревших переменных окружения и выводит предупреждение,
    если они обнаружены.
    """
    legacy_vars = detect_legacy_env_vars()
    
    if not legacy_vars:
        return
    
    warning_message = [
        "ВНИМАНИЕ: Обнаружены устаревшие переменные окружения для системы логирования!",
        "Автоматическая миграция не поддерживается. Пожалуйста, обновите ваши .env файлы:",
        ""
    ]
    
    for legacy_var, new_var in legacy_vars:
        if new_var != "Нет прямого аналога":
            warning_message.append(f"  - {legacy_var} -> {new_var}")
        else:
            warning_message.append(f"  - {legacy_var} -> {new_var} (требуется ручная настройка)")
    
    warning_message.extend([
        "",
        "Подробности см. в docs/LOGGING_SYSTEM_MIGRATION_GUIDE.md"
    ])
    
    logger.warning("\n".join(warning_message))


def check_env_configuration() -> None:
    """
    Проверяет конфигурацию переменных окружения и выводит предупреждения
    о наличии устаревших переменных.
    """
    print_legacy_env_vars_warning() 