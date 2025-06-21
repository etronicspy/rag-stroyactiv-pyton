# 🚀 Руководство по миграции на новую систему логирования

## 📋 Содержание
1. [Введение](#введение)
2. [Совместимость переменных окружения](#совместимость-переменных-окружения)
3. [Миграция кода](#миграция-кода)
4. [Проверка после миграции](#проверка-после-миграции)
5. [Часто задаваемые вопросы](#часто-задаваемые-вопросы)

## 📝 Введение

Данное руководство описывает процесс миграции с существующей системы логирования на новую модульную систему. Новая система предлагает улучшенную производительность, более гибкую конфигурацию и расширенные возможности интеграции.

## 🔄 Совместимость переменных окружения

### Сравнение переменных окружения

| Существующая переменная | Новая переменная | Совместимость | Примечание |
|-------------------------|------------------|---------------|------------|
| `LOG_LEVEL` | `LOG_GENERAL_DEFAULT_LEVEL` | ✅ | Автоматическое преобразование |
| `ENABLE_STRUCTURED_LOGGING` | `LOG_FORMATTER_DEFAULT_TYPE=json` | ✅ | Автоматическое преобразование |
| `LOG_FILE` | `LOG_HANDLER_FILE_PATH` | ✅ | Автоматическое преобразование |
| `LOG_COLORS` | `LOG_FORMATTER_ENABLE_COLORS` | ✅ | Автоматическое преобразование |
| `LOG_THIRD_PARTY_LEVEL` | `LOG_GENERAL_THIRD_PARTY_LEVEL` | ✅ | Автоматическое преобразование |
| `ENABLE_REQUEST_LOGGING` | `LOG_HTTP_ENABLE_REQUEST_LOGGING` | ✅ | Автоматическое преобразование |
| `LOG_REQUEST_BODY` | `LOG_HTTP_LOG_REQUEST_BODY` | ✅ | Автоматическое преобразование |
| `LOG_RESPONSE_BODY` | `LOG_HTTP_LOG_RESPONSE_BODY` | ✅ | Автоматическое преобразование |
| `LOG_REQUEST_HEADERS` | `LOG_HTTP_LOG_REQUEST_HEADERS` | ✅ | Автоматическое преобразование |
| `LOG_MASK_SENSITIVE_HEADERS` | `LOG_HTTP_MASK_SENSITIVE_HEADERS` | ✅ | Автоматическое преобразование |
| `LOG_MAX_BODY_SIZE` | `LOG_HTTP_MAX_BODY_SIZE` | ✅ | Автоматическое преобразование |
| `LOG_CORRELATION_ID` | `LOG_CONTEXT_ENABLE_CORRELATION_ID` | ✅ | Автоматическое преобразование |
| `LOG_CORRELATION_ID_HEADER` | `LOG_CONTEXT_CORRELATION_ID_HEADER` | ✅ | Автоматическое преобразование |
| `LOG_DATABASE_OPERATIONS` | `LOG_DATABASE_ENABLE_DATABASE_LOGGING` | ✅ | Автоматическое преобразование |
| `LOG_SQL_QUERIES` | `LOG_DATABASE_LOG_SQL_QUERIES` | ✅ | Автоматическое преобразование |
| `LOG_SQL_PARAMETERS` | `LOG_DATABASE_LOG_SQL_PARAMETERS` | ✅ | Автоматическое преобразование |
| `LOG_VECTOR_OPERATIONS` | `LOG_DATABASE_LOG_VECTOR_OPERATIONS` | ✅ | Автоматическое преобразование |
| `LOG_CACHE_OPERATIONS` | `LOG_DATABASE_LOG_CACHE_OPERATIONS` | ✅ | Автоматическое преобразование |
| `LOG_PERFORMANCE_METRICS` | `LOG_METRICS_LOG_PERFORMANCE_METRICS` | ✅ | Автоматическое преобразование |
| `LOG_TIMING_DETAILS` | `LOG_METRICS_LOG_TIMING_DETAILS` | ✅ | Автоматическое преобразование |
| `LOG_SLOW_OPERATION_THRESHOLD_MS` | `LOG_METRICS_SLOW_OPERATION_THRESHOLD_MS` | ✅ | Автоматическое преобразование |
| `LOG_SECURITY_EVENTS` | Нет прямого аналога | ❌ | Требуется ручная настройка |
| `LOG_BLOCKED_REQUESTS` | Нет прямого аналога | ❌ | Требуется ручная настройка |
| `LOG_SECURITY_INCIDENTS` | Нет прямого аналога | ❌ | Требуется ручная настройка |
| `LOG_TIMESTAMP_FORMAT` | `LOG_FORMATTER_TIMESTAMP_FORMAT` | ⚠️ | Изменен формат значения |
| `LOG_SOURCE_INFO` | `LOG_FORMATTER_ENABLE_SOURCE_INFO` | ✅ | Автоматическое преобразование |
| `LOG_STACK_TRACE` | Нет прямого аналога | ❌ | Включено по умолчанию |
| `LOG_FILE_ROTATION` | Заменено на выбор типа обработчика | ❌ | Используйте `LOG_HANDLER_DEFAULT_TYPES` |
| `LOG_FILE_MAX_SIZE_MB` | `LOG_HANDLER_ROTATING_FILE_MAX_BYTES` | ⚠️ | Единица измерения изменена с МБ на байты |
| `LOG_FILE_BACKUP_COUNT` | `LOG_HANDLER_ROTATING_FILE_BACKUP_COUNT` | ✅ | Автоматическое преобразование |
| `LOG_ASYNC_LOGGING` | `LOG_GENERAL_ENABLE_ASYNC_LOGGING` | ✅ | Автоматическое преобразование |
| `LOG_BUFFER_SIZE` | `LOG_GENERAL_BATCH_SIZE` | ✅ | Автоматическое преобразование |
| `LOG_FLUSH_INTERVAL` | `LOG_GENERAL_FLUSH_INTERVAL` | ⚠️ | Единица измерения изменена с секунд на секунды с дробной частью |
| `LOG_MIDDLEWARE_LEVEL` | Нет прямого аналога | ❌ | Используйте настройку логгеров по модулям |
| `LOG_SERVICES_LEVEL` | Нет прямого аналога | ❌ | Используйте настройку логгеров по модулям |
| `LOG_API_LEVEL` | Нет прямого аналога | ❌ | Используйте настройку логгеров по модулям |
| `LOG_DATABASE_LEVEL` | Нет прямого аналога | ❌ | Используйте настройку логгеров по модулям |
| `LOG_EXCLUDE_PATHS` | Передается напрямую в `setup_fastapi_logging` | ❌ | Передается при настройке интеграции |
| `LOG_EXCLUDE_HEADERS` | Передается напрямую в `setup_fastapi_logging` | ❌ | Передается при настройке интеграции |

### Новые переменные окружения

Новая система вводит дополнительные переменные окружения для более гибкой настройки:

```bash
# Новые переменные для асинхронного логирования
LOG_GENERAL_WORKER_COUNT=2
LOG_GENERAL_QUEUE_SIZE=1000

# Новые переменные для контекста
LOG_CONTEXT_CORRELATION_ID_GENERATOR=uuid4
LOG_CONTEXT_ENABLE_CONTEXT_POOL=true
LOG_CONTEXT_CONTEXT_POOL_SIZE=100

# Новые переменные для оптимизации памяти
LOG_MEMORY_ENABLE_LOGGER_POOL=true
LOG_MEMORY_LOGGER_POOL_SIZE=100
LOG_MEMORY_ENABLE_MESSAGE_CACHE=true
LOG_MEMORY_MESSAGE_CACHE_SIZE=1000
LOG_MEMORY_MESSAGE_CACHE_TTL=300.0
LOG_MEMORY_ENABLE_STRUCTURED_LOG_CACHE=true
LOG_MEMORY_STRUCTURED_LOG_CACHE_SIZE=1000
LOG_MEMORY_STRUCTURED_LOG_CACHE_TTL=300.0
```

### Автоматическая миграция переменных окружения

Для облегчения перехода на новую систему, реализован механизм автоматического преобразования существующих переменных окружения в новые. Это позволяет использовать существующие .env файлы без изменений.

```python
# Пример кода для автоматического преобразования переменных
from core.logging.config.migration import migrate_legacy_env_vars

# Преобразование переменных окружения
migrate_legacy_env_vars()

# Далее использовать новую систему конфигурации
from core.logging.config import get_configuration
config = get_configuration()
```

## 🔄 Миграция кода

### Изменения импортов

| Существующий импорт | Новый импорт |
|---------------------|--------------|
| `from core.monitoring.logger import get_logger` | `from core.logging import get_logger` |
| `from core.monitoring.unified_manager import get_unified_logging_manager` | `from core.logging import get_unified_logging_manager` |
| `from core.monitoring.context import CorrelationContext` | `from core.logging.context import CorrelationContext` |
| `from core.middleware.logging import LoggingMiddleware` | `from core.logging.integration.fastapi import LoggingMiddleware` |

### Примеры миграции кода

#### 1. Базовое логирование

**Было:**
```python
from core.monitoring.logger import get_logger

logger = get_logger(__name__)
logger.info("Информационное сообщение")
logger.error("Ошибка", extra={"error_code": "E123"})
```

**Стало:**
```python
from core.logging import get_logger

logger = get_logger(__name__)
logger.info("Информационное сообщение")
logger.error("Ошибка", extra={"error_code": "E123"})
```

#### 2. Correlation ID

**Было:**
```python
from core.monitoring.context import CorrelationContext, get_correlation_id

with CorrelationContext.with_correlation_id():
    logger.info("Сообщение с correlation ID")
    current_id = get_correlation_id()
```

**Стало:**
```python
from core.logging.context import CorrelationContext, get_correlation_id

with CorrelationContext.with_correlation_id():
    logger.info("Сообщение с correlation ID")
    current_id = get_correlation_id()
```

#### 3. Логирование БД

**Было:**
```python
from core.monitoring.logger import DatabaseLogger

db_logger = DatabaseLogger("postgresql")
db_logger.log_operation(
    operation="select_users",
    duration_ms=25.5,
    success=True,
    record_count=10
)
```

**Стало:**
```python
from core.logging.specialized.database import DatabaseLogger

db_logger = DatabaseLogger("postgresql")
db_logger.log_operation(
    operation="select_users",
    duration_ms=25.5,
    success=True,
    record_count=10
)
```

#### 4. Middleware для FastAPI

**Было:**
```python
from fastapi import FastAPI
from core.middleware.logging import LoggingMiddleware

app = FastAPI()
app.add_middleware(LoggingMiddleware)
```

**Стало:**
```python
from fastapi import FastAPI
from core.logging.integration import setup_fastapi_logging

app = FastAPI()
setup_fastapi_logging(app, exclude_paths=["/health", "/metrics"])
```

## ✅ Проверка после миграции

После миграции рекомендуется выполнить следующие проверки:

1. **Валидация конфигурации**:
   ```python
   from core.logging.config import validate_configuration
   
   validator = validate_configuration()
   if not validator.validate():
       print("Ошибки конфигурации:")
       for error in validator.get_errors():
           print(f"- {error}")
   ```

2. **Проверка логирования**:
   ```python
   from core.logging import get_logger
   
   logger = get_logger("migration_test")
   logger.debug("Тестовое сообщение DEBUG")
   logger.info("Тестовое сообщение INFO")
   logger.warning("Тестовое сообщение WARNING")
   logger.error("Тестовое сообщение ERROR")
   ```

3. **Проверка correlation ID**:
   ```python
   from core.logging import get_logger
   from core.logging.context import CorrelationContext
   
   logger = get_logger("correlation_test")
   
   with CorrelationContext.with_correlation_id("test-migration-id"):
       logger.info("Сообщение с correlation ID")
   ```

## ❓ Часто задаваемые вопросы

### Нужно ли обновлять .env файлы?

Нет, существующие .env файлы будут работать без изменений благодаря механизму автоматического преобразования переменных окружения. Однако для использования новых возможностей рекомендуется постепенно переходить на новый формат переменных.

### Как настроить уровни логирования для разных модулей?

В новой системе уровни логирования для разных модулей настраиваются программно:

```python
from core.logging.config import get_configuration
import logging

config = get_configuration()
config.set_log_level("core.middleware", logging.DEBUG)
config.set_log_level("core.services", logging.INFO)
config.set_log_level("core.api", logging.WARNING)
```

### Как добавить новый обработчик логов?

```python
from core.logging import get_logger
import logging

logger = get_logger("my_module")
handler = logging.FileHandler("special_logs.log")
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
```

### Как использовать новые интеграции с базами данных?

```python
# Для SQLAlchemy
from sqlalchemy import create_engine
from core.logging.integration import setup_sqlalchemy_logging

engine = create_engine("postgresql://user:password@localhost/db")
setup_sqlalchemy_logging(engine)

# Для Qdrant
from qdrant_client import QdrantClient
from core.logging.integration import QdrantLoggerMixin

class LoggedQdrantClient(QdrantLoggerMixin, QdrantClient):
    pass

client = LoggedQdrantClient(url="http://localhost:6333")
```

### Как включить асинхронное логирование?

```bash
# В .env файле
LOG_GENERAL_ENABLE_ASYNC_LOGGING=true
LOG_GENERAL_WORKER_COUNT=2
LOG_GENERAL_FLUSH_INTERVAL=0.5
LOG_GENERAL_BATCH_SIZE=100
LOG_GENERAL_QUEUE_SIZE=1000
```

### Как мигрировать пользовательские логгеры?

Если у вас есть пользовательские логгеры, наследующиеся от классов старой системы, необходимо обновить наследование:

```python
# Было
from core.monitoring.logger import BaseLogger

class MyCustomLogger(BaseLogger):
    # ...

# Стало
from core.logging.base import BaseLogger

class MyCustomLogger(BaseLogger):
    # ...
``` 