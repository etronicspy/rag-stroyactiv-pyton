# 📚 Руководство по системе логирования RAG Construction Materials API

## 🏗️ Обзор архитектуры

Система логирования построена на модульной архитектуре с четким разделением ответственности:

```
core/logging/
├── base/          # Базовые компоненты и интерфейсы
├── context/       # Управление correlation ID и контекстом
├── handlers/      # Специализированные логгеры
├── metrics/       # Сбор метрик и производительности
└── managers/      # Унифицированное управление
```

## 🚀 Быстрый старт

### 1. Базовое использование

```python
from core.logging import get_logger

# Создание логгера
logger = get_logger(__name__)

# Основные уровни логирования
logger.debug("Детальная информация для отладки")
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.critical("Критическая ошибка")

# Логирование исключений
try:
    result = risky_operation()
except Exception as e:
    logger.exception("Ошибка при выполнении операции")
```

### 2. Конфигурация через переменные окружения

```bash
# .env файл
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGGING=true
LOG_CORRELATION_ID=true
LOG_DATABASE_OPERATIONS=true
LOG_PERFORMANCE_METRICS=true
```

```python
# Использование конфигурации
from core.logging import LoggingConfig

config = LoggingConfig()
print(f"Уровень логирования: {config.LOG_LEVEL}")
print(f"Structured logging: {config.ENABLE_STRUCTURED_LOGGING}")
```

## 🔧 Основные компоненты

### 1. Correlation ID (Трассировка запросов)

```python
from core.logging import get_logger, CorrelationContext

logger = get_logger(__name__)

# Автоматическое создание correlation ID
with CorrelationContext.with_correlation_id():
    logger.info("Этот лог будет содержать correlation ID")
    
    # Все операции внутри контекста получат тот же correlation ID
    process_user_request()
    query_database()

# Ручное управление correlation ID
from core.logging import set_correlation_id, get_correlation_id

set_correlation_id("custom-request-123")
logger.info("Лог с пользовательским correlation ID")
current_id = get_correlation_id()  # "custom-request-123"
```

### 2. Логирование операций БД

```python
from core.logging import DatabaseLogger

# Создание логгера для конкретной БД
db_logger = DatabaseLogger("postgresql")

# Логирование операций
db_logger.log_operation(
    operation="select_users",
    duration_ms=25.5,
    success=True,
    record_count=150,
    query="SELECT * FROM users WHERE active = true"
)

# Логирование ошибок БД
db_logger.log_operation(
    operation="insert_user",
    duration_ms=1500.0,
    success=False,
    error="duplicate key value violates unique constraint",
    sql_state="23505"
)
```

### 3. Логирование HTTP запросов

```python
from core.logging import RequestLogger

request_logger = RequestLogger()

# Логирование HTTP запросов
request_logger.log_request(
    method="POST",
    path="/api/v1/users",
    status_code=201,
    response_time_ms=150.5,
    user_id="user_123",
    ip_address="192.168.1.100"
)

# Логирование ошибок API
request_logger.log_request(
    method="GET",
    path="/api/v1/users/999",
    status_code=404,
    response_time_ms=50.0,
    error="User not found"
)
```

## 📊 Метрики и производительность

### 1. Сбор метрик

```python
from core.logging import get_metrics_collector

metrics = get_metrics_collector()

# Счетчики
metrics.increment_counter("http_requests_total", labels={
    "method": "GET",
    "endpoint": "/api/users",
    "status": "200"
})

# Гистограммы (для времени выполнения)
metrics.record_histogram("request_duration_ms", 125.5, labels={
    "endpoint": "/api/users"
})

# Gauge метрики
metrics.set_gauge("active_connections", 42)
```

### 2. Производительные оптимизации

```python
from core.logging import get_performance_optimizer

# Инициализация оптимизатора
optimizer = get_performance_optimizer()
await optimizer.initialize()

# Декоратор для автоматического логирования производительности
from core.logging.metrics.performance import performance_optimized_log

@performance_optimized_log
async def fetch_user_data(user_id: int):
    """Функция будет автоматически логироваться с метриками производительности"""
    return await database.get_user(user_id)

# Ручное логирование с оптимизацией
await optimizer.log_optimized(
    logger_name="user_service",
    level="INFO",
    message="Пользователь загружен",
    extra_data={"user_id": 123, "load_time": 45.2}
)
```

## 🔗 Унифицированное управление

### 1. Unified Logging Manager

```python
from core.logging import get_unified_logging_manager

manager = get_unified_logging_manager()

# Логирование операций БД с метриками
manager.log_database_operation(
    db_type="postgresql",
    operation="complex_query",
    duration_ms=750.0,  
    success=True,
    record_count=500,
    correlation_id="req-123"
)

# Контекстный менеджер для автоматического логирования
with manager.database_operation_context("redis", "cache_set"):
    await redis_client.set("key", "value")
    # Операция будет автоматически залогирована с длительностью

# Логирование HTTP запросов
manager.log_http_request(
    method="POST",
    path="/api/v1/materials",
    status_code=201,
    response_time_ms=200.0,
    request_size=1024,
    response_size=512
)
```

### 2. Интеграция с метриками

```python
from core.logging import get_metrics_integrated_logger

# Логгер с автоматическим сбором метрик
logger = get_metrics_integrated_logger("user_service")

# Все операции логирования автоматически создают метрики
logger.info("Пользователь создан", extra={
    "user_id": 123,
    "email": "user@example.com"
})
# Автоматически создается метрика: user_service_info_logs_total

logger.error("Ошибка создания пользователя", extra={
    "error_code": "VALIDATION_ERROR",
    "user_data": {"email": "invalid-email"}
})
# Автоматически создается метрика: user_service_error_logs_total
```

## 🎛️ Конфигурация

### 1. Основные настройки

```python
from core.logging import LoggingConfig, LogLevel

config = LoggingConfig(
    LOG_LEVEL=LogLevel.INFO,
    ENABLE_STRUCTURED_LOGGING=True,
    LOG_CORRELATION_ID=True,
    LOG_DATABASE_OPERATIONS=True,
    LOG_PERFORMANCE_METRICS=True
)
```

### 2. Переменные окружения

```bash
# Основные настройки
LOG_LEVEL=INFO                          # Уровень логирования
ENABLE_STRUCTURED_LOGGING=true          # JSON формат для продакшн
LOG_COLORS=true                         # Цветное логирование в консоли
LOG_FILE=/var/log/app.log              # Файл для записи логов

# HTTP логирование
ENABLE_REQUEST_LOGGING=true             # Логирование HTTP запросов
LOG_REQUEST_BODY=false                  # Логирование тел запросов
LOG_RESPONSE_BODY=false                 # Логирование тел ответов
LOG_REQUEST_HEADERS=true                # Логирование заголовков
LOG_MAX_BODY_SIZE=65536                 # Максимальный размер тела (байт)

# Correlation ID
LOG_CORRELATION_ID=true                 # Включить correlation ID
LOG_CORRELATION_ID_HEADER=true          # Передавать в заголовках

# База данных
LOG_DATABASE_OPERATIONS=true            # Логирование операций БД
LOG_SQL_QUERIES=false                   # Логирование SQL запросов
LOG_VECTOR_OPERATIONS=true              # Логирование векторных операций

# Производительность
LOG_PERFORMANCE_METRICS=true            # Метрики производительности
LOG_TIMING_DETAILS=true                 # Детальные метрики времени
LOG_SLOW_OPERATION_THRESHOLD_MS=1000    # Порог медленных операций

# Безопасность
LOG_SECURITY_EVENTS=true                # События безопасности
LOG_BLOCKED_REQUESTS=true               # Заблокированные запросы

# Исключения
LOG_EXCLUDE_PATHS=["/health","/metrics","/docs"]  # Исключить пути
LOG_EXCLUDE_HEADERS=["user-agent","accept-encoding"] # Исключить заголовки
```

### 3. Программная конфигурация

```python
from core.logging import LoggingConfig
from core.config import get_settings

# Получение конфигурации
settings = get_settings()
logging_config = settings.logging  # Если интегрировано в основную конфигурацию

# Или создание отдельной конфигурации
from core.config.logging import LoggingConfig

config = LoggingConfig(
    LOG_LEVEL="DEBUG",
    ENABLE_STRUCTURED_LOGGING=False,
    LOG_DATABASE_OPERATIONS=True
)
```

## 📝 Форматирование логов

### 1. Структурированное логирование (JSON)

```python
from core.logging import get_logger, StructuredFormatter

logger = get_logger(__name__)

# При ENABLE_STRUCTURED_LOGGING=true
logger.info("Пользователь создан", extra={
    "user_id": 123,
    "email": "user@example.com",
    "timestamp": "2024-01-15T10:30:00Z",
    "correlation_id": "req-456"
})

# Вывод в JSON:
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "logger": "user_service",
    "message": "Пользователь создан",
    "correlation_id": "req-456",
    "user_id": 123,
    "email": "user@example.com"
}
```

### 2. Цветное логирование (разработка)

```python
# При LOG_COLORS=true и ENABLE_STRUCTURED_LOGGING=false
logger.debug("Отладочная информация")    # Серый
logger.info("Информация")                # Белый
logger.warning("Предупреждение")         # Желтый
logger.error("Ошибка")                   # Красный
logger.critical("Критическая ошибка")    # Красный жирный
```

## 🔍 Отладка и мониторинг

### 1. Health checks

```python
from core.logging import get_unified_logging_manager

manager = get_unified_logging_manager()

# Проверка состояния системы логирования
health_status = manager.get_health_status()
print(f"Логирование: {health_status.logging_status}")
print(f"Метрики: {health_status.metrics_status}")
print(f"Производительность: {health_status.performance_status}")
```

### 2. Статистика производительности

```python
from core.logging import get_performance_optimizer

optimizer = get_performance_optimizer()

# Получение статистики
stats = optimizer.get_performance_summary()
print(f"Logs per second: {stats.logs_per_second}")
print(f"Average log time: {stats.average_log_time_ms}ms")
print(f"Cache hit rate: {stats.cache_hit_rate}%")
```

### 3. Мониторинг метрик

```python
from core.logging import get_metrics_collector

metrics = get_metrics_collector()

# Статистика метрик
metrics_stats = metrics.get_metrics_summary()
for metric_name, stats in metrics_stats.items():
    print(f"{metric_name}: {stats.count} записей")
```

## 🔄 Миграция от старой системы

### 1. Обратная совместимость

Старый код продолжает работать без изменений:

```python
# Старый код (продолжает работать)
from core.monitoring.logger import get_logger
from core.monitoring.context import CorrelationContext

# Новый код (рекомендуется)
from core.logging import get_logger, CorrelationContext
```

### 2. Постепенная миграция

```python
# Этап 1: Замена импортов
- from core.monitoring.logger import get_logger
+ from core.logging import get_logger

# Этап 2: Использование новых возможностей
from core.logging import get_unified_logging_manager, get_metrics_collector

manager = get_unified_logging_manager()
metrics = get_metrics_collector()

# Этап 3: Оптимизация производительности
from core.logging import get_performance_optimizer

optimizer = get_performance_optimizer()
await optimizer.initialize()
```

## 🚀 Лучшие практики

### 1. Структура логов

```python
# ✅ Хорошо: Структурированная информация
logger.info("Операция завершена", extra={
    "operation": "create_user",
    "duration_ms": 150.5,
    "user_id": 123,
    "success": True
})

# ❌ Плохо: Неструктурированная информация
logger.info("User 123 created successfully in 150ms")
```

### 2. Использование correlation ID

```python
# ✅ Хорошо: Автоматический correlation ID
with CorrelationContext.with_correlation_id():
    logger.info("Начало обработки запроса")
    result = process_request()
    logger.info("Запрос обработан успешно")

# ❌ Плохо: Без correlation ID
logger.info("Начало обработки запроса")
result = process_request()
logger.info("Запрос обработан успешно")
```

### 3. Производительность

```python
# ✅ Хорошо: Ленивое форматирование
logger.debug("Обработка данных: %s", expensive_operation())

# ❌ Плохо: Принудительное форматирование
logger.debug(f"Обработка данных: {expensive_operation()}")

# ✅ Хорошо: Условное логирование
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Expensive debug info: %s", compute_debug_info())
```

### 4. Обработка ошибок

```python
# ✅ Хорошо: Полная информация об ошибке
try:
    result = risky_operation(user_id=123)
except ValueError as e:
    logger.error("Ошибка валидации", extra={
        "error_type": "ValueError",
        "error_message": str(e),
        "user_id": 123,
        "operation": "risky_operation"
    })
    
# ❌ Плохо: Минимальная информация
try:
    result = risky_operation(user_id=123)
except ValueError as e:
    logger.error("Error occurred")
```

## 🎯 Практические примеры

### 1. API endpoint с полным логированием

```python
from fastapi import FastAPI, HTTPException
from core.logging import get_logger, get_unified_logging_manager, CorrelationContext

app = FastAPI()
logger = get_logger(__name__)
log_manager = get_unified_logging_manager()

@app.post("/api/v1/users")
async def create_user(user_data: UserCreateSchema):
    with CorrelationContext.with_correlation_id():
        logger.info("Создание пользователя", extra={
            "email": user_data.email,
            "user_type": user_data.user_type
        })
        
        try:
            # Логирование операции БД
            with log_manager.database_operation_context("postgresql", "create_user"):
                user = await user_service.create_user(user_data)
            
            logger.info("Пользователь создан успешно", extra={
                "user_id": user.id,
                "email": user.email
            })
            
            return user
            
        except ValueError as e:
            logger.error("Ошибка валидации при создании пользователя", extra={
                "error": str(e),
                "user_data": user_data.dict()
            })
            raise HTTPException(status_code=400, detail=str(e))
        
        except Exception as e:
            logger.exception("Неожиданная ошибка при создании пользователя")
            raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. Сервис с метриками

```python
from core.logging import get_logger, get_metrics_collector
from core.logging.metrics.performance import performance_optimized_log

logger = get_logger(__name__)
metrics = get_metrics_collector()

class UserService:
    
    @performance_optimized_log
    async def get_user(self, user_id: int) -> User:
        """Получение пользователя с автоматическим логированием производительности"""
        
        # Метрика запроса
        metrics.increment_counter("user_requests_total", labels={
            "operation": "get_user"
        })
        
        try:
            user = await self.user_repository.get_by_id(user_id)
            
            if not user:
                metrics.increment_counter("user_not_found_total")
                logger.warning("Пользователь не найден", extra={"user_id": user_id})
                return None
            
            # Метрика успешного получения
            metrics.increment_counter("user_requests_success_total")
            logger.info("Пользователь получен", extra={
                "user_id": user_id,
                "user_type": user.user_type
            })
            
            return user
            
        except Exception as e:
            metrics.increment_counter("user_requests_error_total")
            logger.exception("Ошибка получения пользователя", extra={
                "user_id": user_id
            })
            raise
```

### 3. Middleware с логированием

```python
from fastapi import Request, Response
from core.logging import get_logger, RequestLogger, CorrelationContext

logger = get_logger(__name__)
request_logger = RequestLogger()

async def logging_middleware(request: Request, call_next):
    # Создание correlation ID для запроса
    with CorrelationContext.with_correlation_id():
        start_time = time.time()
        
        # Логирование входящего запроса
        logger.info("Входящий запрос", extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host
        })
        
        try:
            response = await call_next(request)
            
            # Вычисление времени выполнения
            process_time = (time.time() - start_time) * 1000
            
            # Логирование ответа
            request_logger.log_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time_ms=process_time,
                client_ip=request.client.host
            )
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            
            # Логирование ошибки
            request_logger.log_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                response_time_ms=process_time,
                client_ip=request.client.host,
                error=str(e)
            )
            
            logger.exception("Ошибка обработки запроса")
            raise
```

## 🔧 Troubleshooting

### Распространенные проблемы и решения

#### 1. Логи не отображаются
```python
# Проверка уровня логирования
from core.logging import LoggingConfig
config = LoggingConfig()
print(f"Текущий уровень: {config.LOG_LEVEL}")

# Установка уровня DEBUG
import os
os.environ["LOG_LEVEL"] = "DEBUG"
```

#### 2. Проблемы с производительностью
```python
# Включение оптимизатора производительности
from core.logging import get_performance_optimizer
optimizer = get_performance_optimizer()
await optimizer.initialize()

# Проверка статистики
stats = optimizer.get_performance_summary()
print(f"Logs per second: {stats.logs_per_second}")
```

#### 3. Отсутствие correlation ID
```python
# Убедитесь, что correlation ID включен
LOG_CORRELATION_ID=true

# Проверка текущего correlation ID
from core.logging import get_correlation_id
print(f"Current correlation ID: {get_correlation_id()}")
```

#### 4. Проблемы с метриками
```python
# Проверка состояния метрик
from core.logging import get_metrics_collector
metrics = get_metrics_collector()
summary = metrics.get_metrics_summary()
print(f"Metrics status: {summary}")
```

---

## 📞 Поддержка

Для получения дополнительной помощи:
1. Проверьте [Troubleshooting Guide](TROUBLESHOOTING_LOGGING.md)
2. Изучите [исходный код](../core/logging/)
3. Создайте issue в репозитории проекта

**Система логирования готова к использованию!** 🚀 