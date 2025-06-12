# Database Architecture Documentation

Документация по архитектуре мульти-БД системы после рефакторинга этапа 1.

## 🏗️ Архитектура

Новая архитектура поддерживает несколько типов БД с единым интерфейсом:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Services      │    │  Repositories   │
│   Routes        │    │   Layer         │    │   Layer         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                ┌─────────────────┴─────────────────┐
                │         Database Layer            │
                │                                   │
                │  ┌─────────────────────────────┐  │
                │  │      Factories              │  │
                │  │   (@lru_cache)              │  │
                │  └─────────────────────────────┘  │
                │                                   │
                │  ┌─────────────────────────────┐  │
                │  │      Interfaces             │  │
                │  │   (ABC Classes)             │  │
                │  └─────────────────────────────┘  │
                │                                   │
                │  ┌─────────────────────────────┐  │
                │  │      Adapters               │  │
                │  │   (Implementations)         │  │
                │  └─────────────────────────────┘  │
                └───────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────┐         ┌────────▼────┐         ┌────────▼────┐
│  Qdrant    │         │ PostgreSQL  │         │   Redis     │
│ (Vector DB)│         │(Relational) │         │  (Cache)    │
└────────────┘         └─────────────┘         └─────────────┘
```

## 📁 Структура файлов

```
core/
├── database/
│   ├── __init__.py              # Экспорт всех компонентов
│   ├── interfaces.py            # ABC интерфейсы для всех БД
│   ├── exceptions.py            # Иерархия исключений БД
│   ├── factories.py             # Фабрики с @lru_cache
│   └── adapters/
│       ├── __init__.py
│       ├── qdrant_adapter.py    # Реализация для Qdrant
│       ├── postgresql_adapter.py # Заглушка для PostgreSQL
│       └── redis_adapter.py     # Заглушка для Redis
├── repositories/
│   ├── __init__.py              # Экспорт репозиториев
│   ├── interfaces.py            # Интерфейсы бизнес-репозиториев
│   └── base.py                  # Базовый класс репозитория
└── dependencies/
    ├── __init__.py              # Экспорт DI функций
    └── database.py              # DI с @lru_cache
```

## 🔧 Основные компоненты

### 1. Интерфейсы БД (core/database/interfaces.py)

#### IVectorDatabase
Обязательные методы согласно правилам:
- `search(collection_name, query_vector, limit, filter_conditions)`
- `upsert(collection_name, vectors)`
- `delete(collection_name, vector_id)`
- `batch_upsert(collection_name, vectors, batch_size)`
- `get_by_id(collection_name, vector_id)`

#### IRelationalDatabase
- `execute_query(query, params)`
- `execute_command(command, params)` 
- `begin_transaction()`, `commit_transaction()`, `rollback_transaction()`
- `health_check()`

#### ICacheDatabase
- `get(key)`, `set(key, value, expire_seconds)`, `delete(key)`
- `exists(key)`, `health_check()`

### 2. Фабрики клиентов (core/database/factories.py)

#### DatabaseFactory
```python
# Runtime переключение БД
vector_db = DatabaseFactory.create_vector_database(
    db_type="qdrant_cloud",  # Override типа БД
    config_override={"url": "custom://url"}  # Override конфигурации
)

# Кеширование с @lru_cache
cache_info = DatabaseFactory.get_cache_info()
DatabaseFactory.clear_cache()  # Для тестирования
```

#### AIClientFactory
```python
# Поддержка разных AI провайдеров
ai_client = AIClientFactory.create_ai_client(
    provider="openai",  # openai, azure_openai, huggingface, ollama
    config_override={"api_key": "custom_key"}
)
```

### 3. Dependency Injection (core/dependencies/database.py)

```python
from fastapi import Depends
from core.dependencies import get_vector_db_dependency, get_ai_client_dependency

@app.post("/search")
async def search_materials(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
):
    # Использование dependency injection с кешированием
    results = await vector_db.search(...)
```

## 🎯 Ключевые особенности

### 1. Runtime переключение БД
```python
# В коде можно переключать БД без перезапуска
DatabaseFactory.clear_cache()  # Очистить кеш
vector_db = DatabaseFactory.create_vector_database(
    db_type="weaviate",  # Переключиться на Weaviate
    config_override={"url": "http://weaviate-server"}
)
```

### 2. Кеширование подключений
- `@lru_cache` на всех фабричных методах
- Кеширование по параметрам вызова
- Мониторинг кеша: hits/misses/currsize

### 3. Обработка ошибок
```python
try:
    result = await vector_db.search(...)
except ConnectionError as e:
    logger.error(f"DB connection failed: {e.database_type}")
except QueryError as e:
    logger.error(f"Query failed: {e.query}")
except DatabaseError as e:
    logger.error(f"General DB error: {e.message}")
```

### 4. Health Checks
```python
# Проверка здоровья всех БД
health = await vector_db.health_check()
# {
#   "status": "healthy",
#   "database_type": "Qdrant", 
#   "collections_count": 5,
#   "timestamp": "2024-01-01T12:00:00Z"
# }
```

## 📝 Правила разработки

### Соответствие .cursorrules:

1. **Код на английском, документация русский+английский** ✅
2. **@lru_cache для DI клиентов** ✅
3. **Обязательные методы векторных БД**: search, upsert, delete, batch_upsert, get_by_id ✅
4. **Type hints и docstrings везде** ✅
5. **Async/await везде** ✅
6. **ABC интерфейсы для всех БД** ✅
7. **Логирование операций БД** ✅

## 🚀 Статус реализации

### ✅ Реализовано (Этап 1):
- Интерфейсы всех типов БД
- Фабрики с кешированием  
- Dependency injection
- Qdrant адаптер (полная реализация)
- Структурированные исключения
- Базовый репозиторий с логированием

### 🔄 В разработке:
- **Этап 2**: Рефакторинг существующих сервисов
- **Этап 3**: PostgreSQL адаптер и миграции
- **Этап 4**: Redis адаптер и кеширование
- **Этап 5**: Гибридный поиск (vector + SQL)

### 📋 TODO:
- [ ] Тесты для всех адаптеров
- [ ] Метрики производительности  
- [ ] Retry логика для всех БД
- [ ] Connection pooling
- [ ] Конфигурация через environment variables

## 🧪 Тестирование

```bash
# Тесты новой архитектуры
pytest tests/test_database_architecture.py -v

# Интеграционные тесты с реальной Qdrant
pytest tests/test_database_architecture.py::TestQdrantIntegration -v -m integration

# Все тесты
pytest -v
```

## 📚 Примеры использования

### Создание векторного репозитория:
```python
from core.database import get_vector_database
from core.repositories.base import BaseRepository

class MaterialsRepository(BaseRepository):
    def __init__(self):
        vector_db = get_vector_database()
        super().__init__(vector_db=vector_db)
    
    async def search_materials(self, query: str) -> List[Material]:
        embedding = await self.get_embedding(query)
        results = await self.vector_db.search(
            collection_name="materials",
            query_vector=embedding,
            limit=10
        )
        return self.convert_to_materials(results)
```

### Переключение БД в runtime:
```python
# В FastAPI startup event
@app.on_event("startup")
async def startup_event():
    if settings.ENVIRONMENT == "testing":
        DatabaseFactory.clear_cache()
        # Переключиться на тестовую БД
        vector_db = DatabaseFactory.create_vector_database(
            config_override={"url": "http://test-qdrant:6333"}
        )
```

Эта архитектура обеспечивает гибкость, масштабируемость и простоту тестирования согласно всем правилам рефакторинга. 