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

# Проверка DatabaseLogger
try:
    db_logger = DatabaseLogger("postgresql")
    print(f"DatabaseLogger создан: {db_logger is not None}")
except Exception as e:
    print(f"Ошибка создания DatabaseLogger: {e}")

# Проверка UnifiedLoggingManager
try:
    manager = get_unified_logging_manager()
    health = manager.get_health_status()
    print(f"Manager health: {health}")
except Exception as e:
    print(f"Ошибка UnifiedLoggingManager: {e}")
```

#### Решения
```bash
# 1. Включить логирование БД
LOG_DATABASE_OPERATIONS=true
LOG_SQL_QUERIES=false  # Включить только для отладки
LOG_VECTOR_OPERATIONS=true
```

```python
# 2. Правильное использование DatabaseLogger
from core.logging import DatabaseLogger, CorrelationContext

with CorrelationContext.with_correlation_id():
    db_logger = DatabaseLogger("postgresql")
    
    # Правильно - все обязательные параметры
    db_logger.log_operation(
        operation="select_users",
        duration_ms=25.5,
        success=True,
        record_count=10
    )
    
    # Неправильно - отсутствуют обязательные параметры
    # db_logger.log_operation("select_users")  # Ошибка!

# 3. Использование контекстного менеджера
from core.logging import get_unified_logging_manager

manager = get_unified_logging_manager()

# Автоматическое логирование с контекстом
with manager.database_operation_context("postgresql", "select_operation"):
    result = await database.select_users()
    # Операция автоматически логируется
```

---

### 7. Проблемы с совместимостью со старым кодом

#### Проблема
Старый код с импортами из `core.monitoring` не работает.

#### Диагностика
```python
# Проверка доступности старых импортов
try:
    from core.monitoring.logger import get_logger
    print("✅ Старые импорты работают")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")

# Проверка новых импортов
try:
    from core.logging import get_logger
    print("✅ Новые импорты работают")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
```

#### Решения
```python
# 1. Использование новых импортов (рекомендуется)
from core.logging import (
    get_logger,
    CorrelationContext,
    DatabaseLogger,
    get_unified_logging_manager
)

# 2. Если старые импорты не работают, проверьте наличие файлов
import os
monitoring_path = "core/monitoring"
if os.path.exists(monitoring_path):
    print("✅ core/monitoring существует")
else:
    print("❌ core/monitoring отсутствует - используйте core.logging")

# 3. Постепенная миграция
# Этап 1: Замена импортов
# - from core.monitoring.logger import get_logger
# + from core.logging import get_logger

# Этап 2: Добавление новых возможностей
from core.logging import get_performance_optimizer, get_metrics_collector

optimizer = get_performance_optimizer()
metrics = get_metrics_collector()
```

---

### 8. Ошибки конфигурации

#### Проблема
Ошибки при загрузке или валидации конфигурации логирования.

#### Диагностика
```python
from core.logging import LoggingConfig
from pydantic import ValidationError

try:
    config = LoggingConfig()
    print("✅ Конфигурация загружена успешно")
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")
    print(f"STRUCTURED_LOGGING: {config.ENABLE_STRUCTURED_LOGGING}")
except ValidationError as e:
    print(f"❌ Ошибка валидации конфигурации: {e}")
except Exception as e:
    print(f"❌ Ошибка загрузки конфигурации: {e}")
```

#### Решения
```bash
# 1. Проверить формат переменных окружения
LOG_LEVEL=INFO                    # Не "info"
ENABLE_STRUCTURED_LOGGING=true    # Не "True"
LOG_EXCLUDE_PATHS=["health","docs"]  # JSON формат для списков

# 2. Проверить допустимые значения
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_TIMESTAMP_FORMAT=ISO8601|RFC3339|timestamp
```

```python
# 3. Создание конфигурации с валидацией
from core.logging import LoggingConfig, LogLevel

try:
    config = LoggingConfig(
        LOG_LEVEL=LogLevel.DEBUG,
        ENABLE_STRUCTURED_LOGGING=True,
        LOG_CORRELATION_ID=True
    )
    print("✅ Конфигурация создана")
except Exception as e:
    print(f"❌ Ошибка создания конфигурации: {e}")
    
    # Создание с минимальными настройками
    config = LoggingConfig(LOG_LEVEL=LogLevel.INFO)
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