# 🚀 Руководство по миграции на новую систему логирования

## 📋 Содержание
1. [Введение](#введение)
2. [Переход на новые переменные окружения](#переход-на-новые-переменные-окружения)
3. [Миграция кода](#миграция-кода)
4. [Проверка после миграции](#проверка-после-миграции)
5. [Часто задаваемые вопросы](#часто-задаваемые-вопросы)

## 📝 Введение

Данное руководство описывает процесс миграции с существующей системы логирования на новую модульную систему. Новая система предлагает улучшенную производительность, более гибкую конфигурацию и расширенные возможности интеграции.

## 🔄 Переход на новые переменные окружения

### Важно: Полный переход на новые переменные

В рамках миграции на новую систему логирования необходимо **полностью перейти на новые переменные окружения**. Старые переменные больше не будут использоваться, поэтому их следует удалить из всех конфигурационных файлов.

### Сравнение старых и новых переменных окружения

Используйте следующую таблицу для замены старых переменных на новые:

| Старая переменная | Новая переменная | Примечание |
|-------------------------|------------------|------------|
| `LOG_LEVEL` | `LOG_GENERAL_DEFAULT_LEVEL` | Уровень логирования |
| `ENABLE_STRUCTURED_LOGGING` | `LOG_FORMATTER_DEFAULT_TYPE=json` | `true` → `json`, `false` → `text` или `colored` |
| `LOG_FILE` | `LOG_HANDLER_FILE_PATH` | Путь к файлу логов |
| `LOG_COLORS` | `LOG_FORMATTER_ENABLE_COLORS` | Цветное логирование |
| `LOG_THIRD_PARTY_LEVEL` | `LOG_GENERAL_THIRD_PARTY_LEVEL` | Уровень для сторонних библиотек |
| `ENABLE_REQUEST_LOGGING` | `LOG_HTTP_ENABLE_REQUEST_LOGGING` | Логирование HTTP запросов |
| `LOG_REQUEST_BODY` | `LOG_HTTP_LOG_REQUEST_BODY` | Логирование тел запросов |
| `LOG_RESPONSE_BODY` | `LOG_HTTP_LOG_RESPONSE_BODY` | Логирование тел ответов |
| `LOG_REQUEST_HEADERS` | `LOG_HTTP_LOG_REQUEST_HEADERS` | Логирование заголовков |
| `LOG_MASK_SENSITIVE_HEADERS` | `LOG_HTTP_MASK_SENSITIVE_HEADERS` | Маскирование заголовков |
| `LOG_MAX_BODY_SIZE` | `LOG_HTTP_MAX_BODY_SIZE` | Максимальный размер тела |
| `LOG_CORRELATION_ID` | `LOG_CONTEXT_ENABLE_CORRELATION_ID` | Включение correlation ID |
| `LOG_CORRELATION_ID_HEADER` | `LOG_CONTEXT_CORRELATION_ID_HEADER` | Имя заголовка |
| `LOG_DATABASE_OPERATIONS` | `LOG_DATABASE_ENABLE_DATABASE_LOGGING` | Логирование БД операций |
| `LOG_SQL_QUERIES` | `LOG_DATABASE_LOG_SQL_QUERIES` | Логирование SQL запросов |
| `LOG_SQL_PARAMETERS` | `LOG_DATABASE_LOG_SQL_PARAMETERS` | Логирование параметров SQL |
| `LOG_VECTOR_OPERATIONS` | `LOG_DATABASE_LOG_VECTOR_OPERATIONS` | Логирование векторных операций |
| `LOG_CACHE_OPERATIONS` | `LOG_DATABASE_LOG_CACHE_OPERATIONS` | Логирование операций с кешем |
| `LOG_PERFORMANCE_METRICS` | `LOG_METRICS_LOG_PERFORMANCE_METRICS` | Метрики производительности |
| `LOG_TIMING_DETAILS` | `LOG_METRICS_LOG_TIMING_DETAILS` | Детальные метрики времени |
| `LOG_SLOW_OPERATION_THRESHOLD_MS` | `LOG_METRICS_SLOW_OPERATION_THRESHOLD_MS` | Порог медленных операций |
| `LOG_TIMESTAMP_FORMAT` | `LOG_FORMATTER_TIMESTAMP_FORMAT` | Формат временных меток |
| `LOG_SOURCE_INFO` | `LOG_FORMATTER_ENABLE_SOURCE_INFO` | Информация о файле и строке |
| `LOG_FILE_MAX_SIZE_MB` | `LOG_HANDLER_ROTATING_FILE_MAX_BYTES` | В байтах (умножить на 1024*1024) |
| `LOG_FILE_BACKUP_COUNT` | `LOG_HANDLER_ROTATING_FILE_BACKUP_COUNT` | Количество резервных копий |
| `LOG_ASYNC_LOGGING` | `LOG_GENERAL_ENABLE_ASYNC_LOGGING` | Асинхронное логирование |
| `LOG_BUFFER_SIZE` | `LOG_GENERAL_BATCH_SIZE` | Размер батча |
| `LOG_FLUSH_INTERVAL` | `LOG_GENERAL_FLUSH_INTERVAL` | В секундах (с дробной частью) |
| `LOG_EXCLUDE_PATHS` | Передается напрямую в `setup_fastapi_logging` | Программная настройка |
| `LOG_EXCLUDE_HEADERS` | Передается напрямую в `setup_fastapi_logging` | Программная настройка |

### Новые переменные окружения

Новая система вводит дополнительные переменные окружения для более гибкой настройки:

```bash
# Новые переменные для асинхронного логирования
LOG_GENERAL_WORKER_COUNT=2
LOG_GENERAL_QUEUE_SIZE=1000
LOG_GENERAL_PROPAGATE=false

# Новые переменные для форматирования
LOG_FORMATTER_JSON_ENSURE_ASCII=false
LOG_FORMATTER_JSON_SORT_KEYS=true

# Новые переменные для обработчиков
LOG_HANDLER_DEFAULT_TYPES=console  # console, file, rotating_file, timed_rotating_file
LOG_HANDLER_CONSOLE_STREAM=stdout
LOG_HANDLER_FILE_MODE=a
LOG_HANDLER_FILE_ENCODING=utf-8
LOG_HANDLER_TIMED_ROTATING_FILE_WHEN=midnight
LOG_HANDLER_TIMED_ROTATING_FILE_INTERVAL=1
LOG_HANDLER_TIMED_ROTATING_FILE_BACKUP_COUNT=7

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

# Новые переменные для HTTP логирования
LOG_HTTP_LOG_RESPONSE_HEADERS=true
LOG_HTTP_SENSITIVE_HEADERS=Authorization,Cookie,Set-Cookie
```

### Пример обновления .env файла

```bash
# Старые переменные (удалить)
# LOG_LEVEL=INFO
# ENABLE_STRUCTURED_LOGGING=false
# LOG_FILE=logs/app.log
# LOG_COLORS=true
# ...

# Новые переменные (добавить)
LOG_GENERAL_DEFAULT_LEVEL=INFO
LOG_FORMATTER_DEFAULT_TYPE=colored
LOG_HANDLER_FILE_PATH=logs/app.log
LOG_FORMATTER_ENABLE_COLORS=true
LOG_GENERAL_THIRD_PARTY_LEVEL=WARNING
LOG_HTTP_ENABLE_REQUEST_LOGGING=true
# ...
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

### Нужно ли сохранять старые переменные окружения?

Нет, старые переменные окружения должны быть полностью удалены из всех конфигурационных файлов и заменены на новые. Это обеспечит чистоту кода и конфигурации.

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