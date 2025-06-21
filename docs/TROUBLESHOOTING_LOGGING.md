# 🔧 Troubleshooting Guide: Система логирования

## 🚨 Частые проблемы и их решения

### 1. Логи не отображаются / Неправильный уровень логирования

#### Проблема
Логи не отображаются в консоли или файле, либо отображаются не все уровни.

#### Диагностика
```python
from core.logging import LoggingConfig, get_logger

# Проверка текущей конфигурации
config = LoggingConfig()
print(f"Текущий уровень логирования: {config.LOG_LEVEL}")
print(f"Structured logging: {config.ENABLE_STRUCTURED_LOGGING}")
print(f"Log file: {config.LOG_FILE}")

# Проверка логгера
logger = get_logger(__name__)
print(f"Logger level: {logger.level}")
print(f"Logger handlers: {[h.__class__.__name__ for h in logger.handlers]}")
```

#### Решения
```bash
# 1. Установить правильный уровень в .env
LOG_LEVEL=DEBUG

# 2. Проверить переменные окружения
export LOG_LEVEL=DEBUG
export ENABLE_STRUCTURED_LOGGING=false
```

```python
# 3. Программная установка уровня
import logging
import os

os.environ["LOG_LEVEL"] = "DEBUG"
logging.getLogger().setLevel(logging.DEBUG)

# 4. Принудительная настройка логгера
from core.logging import get_logger
logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
```

---

### 2. Отсутствует Correlation ID

#### Проблема
В логах отсутствует correlation ID, что затрудняет трассировку запросов.

#### Диагностика
```python
from core.logging import get_correlation_id, LoggingConfig

# Проверка конфигурации
config = LoggingConfig()
print(f"Correlation ID включен: {config.LOG_CORRELATION_ID}")

# Проверка текущего correlation ID
current_id = get_correlation_id()
print(f"Текущий correlation ID: {current_id}")
```

#### Решения
```bash
# 1. Включить correlation ID в .env
LOG_CORRELATION_ID=true
LOG_CORRELATION_ID_HEADER=true
```

```python
# 2. Использование контекстного менеджера
from core.logging import CorrelationContext, get_logger

logger = get_logger(__name__)

# Правильно - с контекстом
with CorrelationContext.with_correlation_id():
    logger.info("Этот лог будет содержать correlation ID")

# 3. Ручная установка correlation ID
from core.logging import set_correlation_id
set_correlation_id("custom-request-123")
logger.info("Лог с пользовательским correlation ID")
```

---

### 3. Проблемы с производительностью логирования

#### Проблема
Логирование работает медленно, особенно при высокой нагрузке.

#### Диагностика
```python
from core.logging import get_performance_optimizer, get_metrics_collector

# Проверка производительности
optimizer = get_performance_optimizer()
stats = optimizer.get_performance_summary()

print(f"Logs per second: {stats.logs_per_second}")
print(f"Average log time: {stats.average_log_time_ms}ms")
print(f"Cache hit rate: {stats.cache_hit_rate}%")

# Проверка метрик
metrics = get_metrics_collector()
metrics_summary = metrics.get_metrics_summary()
print(f"Metrics buffer size: {len(metrics_summary)}")
```

#### Решения
```bash
# 1. Включить производительные оптимизации
LOG_ASYNC_LOGGING=true
LOG_BUFFER_SIZE=1000
LOG_FLUSH_INTERVAL=10
```

```python
# 2. Инициализация оптимизатора
from core.logging import get_performance_optimizer

optimizer = get_performance_optimizer()
await optimizer.initialize()  # Включает асинхронную обработку

# 3. Использование оптимизированного логирования
await optimizer.log_optimized(
    logger_name="my_service",
    level="INFO",
    message="Оптимизированное сообщение",
    extra_data={"key": "value"}
)
```

---

### 4. Метрики не собираются

#### Проблема
Метрики производительности не собираются или не отображаются.

#### Диагностика
```python
from core.logging import get_metrics_collector, LoggingConfig

# Проверка конфигурации метрик
config = LoggingConfig()
print(f"Performance metrics: {config.LOG_PERFORMANCE_METRICS}")
print(f"Timing details: {config.LOG_TIMING_DETAILS}")

# Проверка состояния сборщика метрик
metrics = get_metrics_collector()
print(f"Metrics collector initialized: {metrics is not None}")

# Проверка метрик
try:
    summary = metrics.get_metrics_summary()
    print(f"Available metrics: {list(summary.keys())}")
except Exception as e:
    print(f"Error getting metrics: {e}")
```

#### Решения
```bash
# 1. Включить сбор метрик
LOG_PERFORMANCE_METRICS=true
LOG_TIMING_DETAILS=true
LOG_DATABASE_OPERATIONS=true
```

```python
# 2. Использование MetricsIntegratedLogger
from core.logging import get_metrics_integrated_logger

logger = get_metrics_integrated_logger("my_service")
logger.info("Сообщение с автоматическими метриками")

# 3. Ручное создание метрик
from core.logging import get_metrics_collector

metrics = get_metrics_collector()
metrics.increment_counter("custom_counter", labels={"type": "test"})
metrics.record_histogram("custom_histogram", 123.45)
```

---

### 5. Проблемы с форматированием логов

#### Проблема
Логи отображаются в неправильном формате или без цветов.

#### Диагностика
```python
from core.logging import LoggingConfig

config = LoggingConfig()
print(f"Structured logging: {config.ENABLE_STRUCTURED_LOGGING}")
print(f"Colors enabled: {config.LOG_COLORS}")
print(f"Timestamp format: {config.LOG_TIMESTAMP_FORMAT}")
```

#### Решения
```bash
# 1. Для разработки - цветные логи
ENABLE_STRUCTURED_LOGGING=false
LOG_COLORS=true

# 2. Для продакшн - JSON логи
ENABLE_STRUCTURED_LOGGING=true
LOG_COLORS=false
LOG_TIMESTAMP_FORMAT=ISO8601
```

```python
# 3. Программная настройка форматирования
from core.logging import get_logger, StructuredFormatter, ColoredFormatter
import logging

logger = get_logger(__name__)

# Добавление JSON форматтера
json_handler = logging.StreamHandler()
json_handler.setFormatter(StructuredFormatter())
logger.addHandler(json_handler)

# Добавление цветного форматтера
color_handler = logging.StreamHandler()
color_handler.setFormatter(ColoredFormatter())
logger.addHandler(color_handler)
```

---

### 6. Ошибки при логировании операций БД

#### Проблема
Ошибки при использовании DatabaseLogger или унифицированного менеджера для БД.

#### Диагностика
```python
from core.logging import DatabaseLogger, get_unified_logging_manager
from core.logging.config import get_configuration

# Проверка конфигурации БД
config = get_configuration()
db_settings = config.get_database_settings()
print(f"Database logging enabled: {db_settings['enable_database_logging']}")
print(f"SQL queries logging: {db_settings['log_sql_queries']}")
print(f"Vector operations logging: {db_settings['log_vector_operations']}")

# Проверка логгера БД
try:
    db_logger = DatabaseLogger("postgresql")
    print("DatabaseLogger создан успешно")
except Exception as e:
    print(f"Ошибка создания DatabaseLogger: {e}")

# Проверка унифицированного менеджера
try:
    manager = get_unified_logging_manager()
    print("UnifiedLoggingManager создан успешно")
except Exception as e:
    print(f"Ошибка создания UnifiedLoggingManager: {e}")
```

#### Решения
```bash
# 1. Включить логирование БД в .env
LOG_DATABASE_ENABLE_DATABASE_LOGGING=true
LOG_DATABASE_LOG_SQL_QUERIES=true
LOG_DATABASE_LOG_SQL_PARAMETERS=true
LOG_DATABASE_LOG_VECTOR_OPERATIONS=true
```

```python
# 2. Использование интеграции с SQLAlchemy
from sqlalchemy import create_engine
from core.logging.integration import setup_sqlalchemy_logging

engine = create_engine("postgresql://user:password@localhost/db")
setup_sqlalchemy_logging(engine)

# 3. Использование интеграции с векторными БД
from qdrant_client import QdrantClient
from core.logging.integration import QdrantLoggerMixin

class LoggedQdrantClient(QdrantLoggerMixin, QdrantClient):
    pass

client = LoggedQdrantClient(url="http://localhost:6333")
```

---

### 7. Проблемы с интеграцией FastAPI

#### Проблема
Middleware логирования не работает или вызывает ошибки в FastAPI приложении.

#### Диагностика
```python
from fastapi import FastAPI
from core.logging.config import get_configuration
from core.logging.integration import LoggingMiddleware
import logging

# Проверка конфигурации HTTP
config = get_configuration()
http_settings = config.get_http_settings()
print(f"Request logging enabled: {http_settings['enable_request_logging']}")
print(f"Log request body: {http_settings['log_request_body']}")

# Проверка логгера HTTP
http_logger = logging.getLogger("http")
print(f"HTTP logger level: {http_logger.level}")
print(f"HTTP logger handlers: {[h.__class__.__name__ for h in http_logger.handlers]}")

# Тестирование middleware напрямую
try:
    app = FastAPI()
    middleware = LoggingMiddleware(app)
    print("LoggingMiddleware создан успешно")
except Exception as e:
    print(f"Ошибка создания LoggingMiddleware: {e}")
```

#### Решения
```bash
# 1. Включить логирование HTTP в .env
LOG_HTTP_ENABLE_REQUEST_LOGGING=true
LOG_HTTP_LOG_REQUEST_BODY=true
LOG_HTTP_LOG_RESPONSE_BODY=true
LOG_HTTP_LOG_REQUEST_HEADERS=true
```

```python
# 2. Правильная настройка FastAPI
from fastapi import FastAPI
from core.logging.integration import setup_fastapi_logging

app = FastAPI()

# Добавление middleware с правильными параметрами
setup_fastapi_logging(
    app, 
    exclude_paths=["/health", "/metrics"], 
    exclude_methods=["OPTIONS"]
)

# 3. Использование декоратора для отдельных маршрутов
from fastapi import Depends
from core.logging.integration import LoggingRoute

@app.get("/users/{user_id}", dependencies=[Depends(LoggingRoute())])
async def get_user(user_id: int):
    return {"user_id": user_id, "name": "John Doe"}
```

---

### 8. Проблемы с валидацией конфигурации

#### Проблема
Ошибки валидации конфигурации логирования.

#### Диагностика
```python
from core.logging.config import validate_configuration

# Валидация конфигурации
validator = validate_configuration()
is_valid = validator.validate()

if not is_valid:
    print("Ошибки конфигурации:")
    for error in validator.get_errors():
        print(f"- {error}")
    
    print("\nПредупреждения:")
    for warning in validator.get_warnings():
        print(f"- {warning}")
else:
    print("Конфигурация валидна")

# Проверка доступа к конфигурации
from core.logging.config import get_configuration
try:
    config = get_configuration()
    print("Доступ к конфигурации успешен")
except Exception as e:
    print(f"Ошибка доступа к конфигурации: {e}")
```

#### Решения
```bash
# 1. Исправление некорректных значений в .env
LOG_GENERAL_DEFAULT_LEVEL=INFO  # Вместо неправильного значения
LOG_GENERAL_WORKER_COUNT=1  # Минимум 1
LOG_HANDLER_CONSOLE_STREAM=stdout  # Только stdout или stderr
```

```python
# 2. Программная настройка конфигурации
import os

# Установка корректных значений
os.environ["LOG_GENERAL_DEFAULT_LEVEL"] = "INFO"
os.environ["LOG_GENERAL_WORKER_COUNT"] = "1"
os.environ["LOG_HANDLER_CONSOLE_STREAM"] = "stdout"

# 3. Создание файла логов, если директория не существует
import os
from pathlib import Path

log_dir = Path("logs")
if not log_dir.exists():
    log_dir.mkdir(parents=True)
```

---

### 9. Проблемы с асинхронным логированием

#### Проблема
Асинхронное логирование не работает или вызывает ошибки.

#### Диагностика
```python
from core.logging.config import get_configuration
import asyncio

# Проверка конфигурации асинхронного логирования
config = get_configuration()
async_settings = config.get_async_logging_settings()
print(f"Async logging enabled: {async_settings['enable_async_logging']}")
print(f"Worker count: {async_settings['worker_count']}")
print(f"Batch size: {async_settings['batch_size']}")

# Проверка оптимизированного логирования
from core.logging.optimized.async_logging import AsyncLogger
try:
    logger = AsyncLogger("test")
    print("AsyncLogger создан успешно")
    
    # Проверка инициализации
    async def test_async_logger():
        await logger.initialize()
        await logger.log("INFO", "Test message")
        await logger.shutdown()
    
    asyncio.run(test_async_logger())
    print("Асинхронное логирование работает")
except Exception as e:
    print(f"Ошибка асинхронного логирования: {e}")
```

#### Решения
```bash
# 1. Настройка асинхронного логирования в .env
LOG_GENERAL_ENABLE_ASYNC_LOGGING=true
LOG_GENERAL_WORKER_COUNT=2
LOG_GENERAL_FLUSH_INTERVAL=0.5
LOG_GENERAL_BATCH_SIZE=100
LOG_GENERAL_QUEUE_SIZE=1000
```

```python
# 2. Правильная инициализация и завершение
from core.logging.optimized.async_logging import AsyncLogger
import asyncio

async def main():
    # Создание и инициализация логгера
    logger = AsyncLogger("my_service")
    await logger.initialize()
    
    try:
        # Использование логгера
        await logger.log("INFO", "Сообщение 1")
        await logger.log("ERROR", "Сообщение 2", {"error_code": "E123"})
    finally:
        # Важно: корректное завершение
        await logger.shutdown()

# Запуск в асинхронном контексте
asyncio.run(main())

# 3. Использование в FastAPI
from fastapi import FastAPI
from core.logging.optimized.async_logging import AsyncLogger

app = FastAPI()
logger = None

@app.on_event("startup")
async def startup_event():
    global logger
    logger = AsyncLogger("api")
    await logger.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    global logger
    if logger:
        await logger.shutdown()
```

---

### 10. Проблемы с интеграцией векторных БД

#### Проблема
Логирование операций с векторными БД не работает или вызывает ошибки.

#### Диагностика
```python
from core.logging.config import get_configuration

# Проверка конфигурации БД
config = get_configuration()
db_settings = config.get_database_settings()
print(f"Database logging enabled: {db_settings['enable_database_logging']}")
print(f"Vector operations logging: {db_settings['log_vector_operations']}")

# Проверка интеграции с Qdrant
try:
    from qdrant_client import QdrantClient
    from core.logging.integration import QdrantLoggerMixin
    
    class TestQdrantClient(QdrantLoggerMixin, QdrantClient):
        pass
    
    client = TestQdrantClient(location=":memory:")
    print("QdrantLoggerMixin интегрирован успешно")
except Exception as e:
    print(f"Ошибка интеграции с Qdrant: {e}")

# Проверка декоратора
from core.logging.integration import log_vector_db_operation

@log_vector_db_operation(db_type="test", operation="test_op")
def test_function():
    return "test"

try:
    result = test_function()
    print(f"Декоратор log_vector_db_operation работает: {result}")
except Exception as e:
    print(f"Ошибка декоратора: {e}")
```

#### Решения
```bash
# 1. Включить логирование векторных БД в .env
LOG_DATABASE_ENABLE_DATABASE_LOGGING=true
LOG_DATABASE_LOG_VECTOR_OPERATIONS=true
LOG_DATABASE_SLOW_QUERY_THRESHOLD_MS=1000
```

```python
# 2. Правильная интеграция с Qdrant
from qdrant_client import QdrantClient
from core.logging.integration import QdrantLoggerMixin

# Создание подкласса с правильным порядком наследования
class LoggedQdrantClient(QdrantLoggerMixin, QdrantClient):
    pass

# Создание клиента
client = LoggedQdrantClient(url="http://localhost:6333")

# 3. Правильное использование декоратора
from core.logging.integration import log_vector_db_operation

# Декоратор для функции
@log_vector_db_operation(db_type="qdrant", operation="search")
async def search_documents(query: str, limit: int = 10):
    # Код функции
    pass

# 4. Ручное логирование операций
from core.logging.specialized.database import VectorDbLogger
import logging

logger = logging.getLogger("vector_db")
vector_db_logger = VectorDbLogger(
    logger=logger,
    db_type="qdrant",
    log_operations=True,
    slow_query_threshold_ms=1000
)

# Логирование операции
vector_db_logger.log_operation(
    operation="search",
    params={"collection": "documents", "limit": 10},
    duration_ms=45.5
)
```

---

## 🔧 Инструменты диагностики

### 1. Полная диагностика системы логирования

```python
import os
import sys
from core.logging import (
    LoggingConfig, get_logger, get_unified_logging_manager,
    get_performance_optimizer, get_metrics_collector
)

def diagnose_logging_system():
    """Полная диагностика системы логирования"""
    
    print("🔍 ДИАГНОСТИКА СИСТЕМЫ ЛОГИРОВАНИЯ")
    print("=" * 50)
    
    # 1. Проверка конфигурации
    print("\n1. КОНФИГУРАЦИЯ:")
    try:
        config = LoggingConfig()
        print(f"   ✅ Конфигурация загружена")
        print(f"   📊 LOG_LEVEL: {config.LOG_LEVEL}")
        print(f"   📊 STRUCTURED_LOGGING: {config.ENABLE_STRUCTURED_LOGGING}")
        print(f"   📊 CORRELATION_ID: {config.LOG_CORRELATION_ID}")
        print(f"   📊 DATABASE_OPERATIONS: {config.LOG_DATABASE_OPERATIONS}")
        print(f"   📊 PERFORMANCE_METRICS: {config.LOG_PERFORMANCE_METRICS}")
    except Exception as e:
        print(f"   ❌ Ошибка конфигурации: {e}")
    
    # 2. Проверка базового логгера
    print("\n2. БАЗОВЫЙ ЛОГГЕР:")
    try:
        logger = get_logger("diagnostic")
        print(f"   ✅ Логгер создан")
        print(f"   📊 Level: {logger.level}")
        print(f"   📊 Handlers: {len(logger.handlers)}")
        
        # Тест логирования
        logger.info("Тестовое сообщение диагностики")
        print(f"   ✅ Тестовое логирование выполнено")
    except Exception as e:
        print(f"   ❌ Ошибка базового логгера: {e}")
    
    # 3. Проверка унифицированного менеджера
    print("\n3. УНИФИЦИРОВАННЫЙ МЕНЕДЖЕР:")
    try:
        manager = get_unified_logging_manager()
        print(f"   ✅ Менеджер создан")
        
        health = manager.get_health_status()
        print(f"   📊 Health status: {health}")
    except Exception as e:
        print(f"   ❌ Ошибка менеджера: {e}")
    
    # 4. Проверка производительности
    print("\n4. ПРОИЗВОДИТЕЛЬНОСТЬ:")
    try:
        optimizer = get_performance_optimizer()
        print(f"   ✅ Оптимизатор создан")
        
        stats = optimizer.get_performance_summary()
        print(f"   📊 Performance stats: {stats}")
    except Exception as e:
        print(f"   ❌ Ошибка оптимизатора: {e}")
    
    # 5. Проверка метрик
    print("\n5. МЕТРИКИ:")
    try:
        metrics = get_metrics_collector()
        print(f"   ✅ Сборщик метрик создан")
        
        # Тест метрики
        metrics.increment_counter("diagnostic_test", labels={"status": "success"})
        print(f"   ✅ Тестовая метрика создана")
    except Exception as e:
        print(f"   ❌ Ошибка метрик: {e}")
    
    # 6. Проверка переменных окружения
    print("\n6. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    logging_env_vars = [
        "LOG_LEVEL", "ENABLE_STRUCTURED_LOGGING", "LOG_CORRELATION_ID",
        "LOG_DATABASE_OPERATIONS", "LOG_PERFORMANCE_METRICS"
    ]
    
    for var in logging_env_vars:
        value = os.environ.get(var, "НЕ УСТАНОВЛЕНО")
        print(f"   📊 {var}: {value}")
    
    print("\n" + "=" * 50)
    print("🔍 ДИАГНОСТИКА ЗАВЕРШЕНА")

# Запуск диагностики
if __name__ == "__main__":
    diagnose_logging_system()
```

### 2. Тест производительности

```python
import time
import asyncio
from core.logging import get_logger, get_performance_optimizer

async def performance_test():
    """Тест производительности логирования"""
    
    logger = get_logger("performance_test")
    optimizer = get_performance_optimizer()
    
    # Инициализация оптимизатора
    await optimizer.initialize()
    
    # Тест обычного логирования
    start_time = time.time()
    for i in range(1000):
        logger.info(f"Test message {i}")
    normal_time = time.time() - start_time
    
    # Тест оптимизированного логирования
    start_time = time.time()
    for i in range(1000):
        await optimizer.log_optimized(
            logger_name="performance_test",
            level="INFO",
            message=f"Optimized message {i}",
            extra_data={"iteration": i}
        )
    optimized_time = time.time() - start_time
    
    print(f"Обычное логирование: {normal_time:.3f}s")
    print(f"Оптимизированное логирование: {optimized_time:.3f}s")
    print(f"Ускорение: {normal_time/optimized_time:.2f}x")

# Запуск теста
if __name__ == "__main__":
    asyncio.run(performance_test())
```

---

## ⚡ Быстрые исправления

### Сброс конфигурации логирования
```python
import os

# Удаление всех переменных логирования
logging_vars = [k for k in os.environ.keys() if k.startswith('LOG_')]
for var in logging_vars:
    del os.environ[var]

# Установка минимальных настроек
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['ENABLE_STRUCTURED_LOGGING'] = 'false'
```

### Принудительное включение отладки
```python
import logging
import os

# Глобальная установка DEBUG уровня
os.environ['LOG_LEVEL'] = 'DEBUG'
logging.getLogger().setLevel(logging.DEBUG)

# Включение всех компонентов
os.environ['LOG_CORRELATION_ID'] = 'true'
os.environ['LOG_DATABASE_OPERATIONS'] = 'true'
os.environ['LOG_PERFORMANCE_METRICS'] = 'true'
```

### Тестирование всех компонентов
```python
from core.logging import *

# Тест базового логирования
logger = get_logger("test")
logger.info("Test message")

# Тест correlation ID
with CorrelationContext.with_correlation_id():
    logger.info("Message with correlation ID")

# Тест database logging
db_logger = DatabaseLogger("test_db")
db_logger.log_operation("test_op", 100.0, True)

# Тест метрик
metrics = get_metrics_collector()
metrics.increment_counter("test_counter")

print("✅ Все компоненты работают")
```

---

## 🆘 Когда обратиться за помощью

Если проблема не решается:

1. **Проверьте все конфигурационные файлы** (.env, .env.local, .env.example)
2. **Запустите полную диагностику** (код выше)
3. **Проверьте логи ошибок** в консоли или файлах
4. **Создайте minimal reproducible example**
5. **Обратитесь к команде разработки** с детальным описанием проблемы

**Не забудьте приложить:**
- Конфигурацию логирования
- Сообщения об ошибках
- Результаты диагностики
- Версию Python и зависимостей 