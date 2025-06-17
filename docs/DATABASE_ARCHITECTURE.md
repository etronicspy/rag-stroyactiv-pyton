# 🗄️ Database Architecture

## 📋 Обзор

Система использует multi-database архитектуру с поддержкой векторного поиска, реляционных данных и кеширования.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI API Layer                    │
├─────────────────────────────────────────────────────────┤
│                 Services & Repositories                 │
├─────────────────────────────────────────────────────────┤
│              Database Adapters (Interfaces)             │
└────────────┬────────────┬───────────────┬───────────────┘
             │            │               │
        ┌────▼────┐  ┌───▼────┐     ┌────▼────┐
        │ Qdrant  │  │PostgreSQL│     │  Redis  │
        │(Vector) │  │(Relations)│     │ (Cache) │
        └─────────┘  └────────┘     └─────────┘
```

## 💾 Базы данных

### Qdrant (Vector Database)
**Назначение**: Семантический поиск материалов
- **Тип**: Векторная БД
- **Размерность**: 1536 (OpenAI embeddings)
- **Индексирование**: HNSW algorithm
- **Подключение**: Qdrant Cloud

### PostgreSQL (Relational Database)  
**Назначение**: Структурированные данные, отношения
- **Тип**: Реляционная БД
- **Подключение**: Через SSH туннель
- **ORM**: SQLAlchemy 2.0 (async)
- **Миграции**: Alembic

### Redis (Cache Database)
**Назначение**: Кеширование, сессии
- **Тип**: In-memory БД
- **TTL**: Настраиваемые периоды
- **Паттерны**: Cache-aside

## 📊 Модели данных

### Materials
```sql
CREATE TABLE materials (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    use_category VARCHAR(200),
    unit VARCHAR(50),
    description TEXT,
    embedding REAL[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Raw Products (Price Data)
```sql
CREATE TABLE raw_products (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER,
    pricelistid INTEGER,
    name VARCHAR(500),
    unit_price NUMERIC(10,2),
    is_processed BOOLEAN DEFAULT FALSE
);
```

### Reference Data
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE units (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(10)
);
```

## 🔧 Adapters

### Vector Database Interface
```python
class IVectorDatabase(ABC):
    async def search(self, collection_name, query_vector, limit)
    async def upsert(self, collection_name, vectors)
    async def delete(self, collection_name, vector_id)
    async def health_check(self)
```

### Relational Database Interface
```python
class IRelationalDatabase(ABC):
    async def execute_query(self, query, params)
    async def execute_command(self, command, params)
    async def health_check(self)
```

### Cache Database Interface
```python
class ICacheDatabase(ABC):
    async def get(self, key)
    async def set(self, key, value, ttl)
    async def delete(self, key)
    async def health_check(self)
```

## 🔄 Repository Pattern

### Base Repository
```python
class BaseRepository:
    def __init__(self, vector_db, relational_db=None, cache_db=None):
        self.vector_db = vector_db
        self.relational_db = relational_db
        self.cache_db = cache_db
    
    async def health_check(self):
        # Проверка всех доступных БД
```

### Hybrid Repository
```python
class HybridMaterialsRepository(BaseRepository):
    async def search_materials(self, query: str):
        # 1. Vector search (primary)
        # 2. SQL search (fallback)
        # 3. Combined results
```

## 🎯 Search Strategy

### Fallback Chain
1. **Vector Search**: Семантический поиск в Qdrant
2. **SQL LIKE Search**: Текстовый поиск при 0 результатов
3. **Mock Response**: При недоступности БД

### Caching Strategy
1. **Search Results**: TTL 5 минут
2. **Material Data**: TTL 60 минут  
3. **Reference Data**: TTL 24 часа

## 🚀 Dependency Injection

```python
from core.dependencies.database import (
    get_vector_db_dependency,
    get_relational_db_dependency,
    get_cache_db_dependency
)

@app.post("/search")
async def search(
    vector_db = Depends(get_vector_db_dependency),
    cache_db = Depends(get_cache_db_dependency)
):
    # Использование injected dependencies
```

## 🔧 Configuration

### Production Setup
```env
# Vector DB
QDRANT_URL=https://cluster.qdrant.tech:6333
QDRANT_API_KEY=your_key

# PostgreSQL via SSH
POSTGRESQL_URL=postgresql://user:pass@localhost:5435/db
ENABLE_SSH_TUNNEL=true

# Redis
REDIS_URL=redis://localhost:6379
```

### Development Setup
```env
# Упрощенная конфигурация
QDRANT_ONLY_MODE=false
ENABLE_FALLBACK_DATABASES=true
DISABLE_REDIS_CONNECTION=false
```

## 🏥 Health Checks

### Database Status
```bash
curl http://localhost:8000/api/v1/health/databases
```

**Response:**
```json
{
    "vector_database": {
        "type": "Qdrant",
        "status": "healthy",
        "response_time_ms": 45.2
    },
    "relational_database": {
        "type": "PostgreSQL", 
        "status": "healthy"
    },
    "cache_database": {
        "type": "Redis",
        "status": "healthy"
    }
}
```

## ⚡ Performance

### Optimization Techniques
- **Connection Pooling**: Для PostgreSQL и Redis
- **Batch Operations**: Массовые операции с векторами
- **Index Usage**: GIN индексы для полнотекстового поиска
- **Cache Warming**: Предзагрузка популярных запросов

### Metrics
- Search latency: <100ms (cached), <500ms (uncached)
- Insert throughput: 1000+ materials/second
- Cache hit rate: >80% for search operations

## 🔄 Migration

### Alembic Commands
```bash
# Применить миграции
alembic upgrade head

# Создать новую миграцию
alembic revision --autogenerate -m "Add new table"

# Откат миграции
alembic downgrade -1
```

## 🚨 Troubleshooting

### Connection Issues
```bash
# Проверка подключений
curl http://localhost:8000/api/v1/health/full

# SSH туннель статус  
ssh -i ~/.ssh/key user@host "echo connected"
```

### Performance Issues
```bash
# PostgreSQL query analysis
EXPLAIN ANALYZE SELECT * FROM materials WHERE name ILIKE '%цемент%';

# Redis memory usage
redis-cli info memory
```

---

**Обновлено**: $(date +%Y-%m-%d) 