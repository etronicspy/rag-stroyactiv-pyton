# Этап 3: PostgreSQL адаптер и гибридный поиск

## 📋 Обзор

Этап 3 реализует полную поддержку PostgreSQL как реляционной БД и создает гибридный репозиторий, объединяющий векторный поиск (Qdrant) с SQL-поиском (PostgreSQL) для максимальной эффективности.

## 🎯 Цели этапа

- ✅ Полная реализация PostgreSQL адаптера с SQLAlchemy 2.0
- ✅ Гибридный репозиторий для работы с двумя БД одновременно
- ✅ Fallback стратегия поиска (vector → SQL при 0 результатах)
- ✅ Alembic миграции для управления схемой БД
- ✅ Триграммный поиск и полнотекстовый поиск в PostgreSQL
- ✅ Comprehensive тестирование и документация

## 🏗️ Архитектурные компоненты

### 1. PostgreSQL Адаптер (`core/database/adapters/postgresql_adapter.py`)

```python
class PostgreSQLDatabase(IRelationalDatabase):
    """PostgreSQL adapter with SQLAlchemy 2.0 and async/await support."""
    
    # Key features:
    - Async SQLAlchemy 2.0 engine
    - Connection pooling
    - Transaction management
    - Hybrid search with trigram similarity
    - Health monitoring
```

**Основные возможности:**
- **SQLAlchemy 2.0**: Современный async/await подход
- **Connection Pooling**: Оптимизированное управление соединениями
- **Триграммный поиск**: Fuzzy matching с pg_trgm
- **Полнотекстовый поиск**: GIN индексы для быстрого поиска
- **Транзакции**: Полная поддержка ACID транзакций

### 2. Модели данных

#### MaterialModel
```python
class MaterialModel(Base):
    __tablename__ = "materials"
    
    # Primary fields
    id: UUID (primary key)
    name: String(200) + GIN index
    use_category: String(200) + index
    unit: String(50)
    sku: String(50) + unique index
    description: Text + GIN index
    
    # Vector support
    embedding: ARRAY(REAL)  # pgvector ready
    
    # Full-text search
    search_vector: Text + GIN index
    
    # Metadata
    created_at: DateTime
    updated_at: DateTime
```

#### RawProductModel
```python
class RawProductModel(Base):
    __tablename__ = "raw_products"
    
    # Supplier data
    supplier_id: Integer + index
    pricelistid: Integer + index
    
    # Pricing information
    unit_price: Numeric(10, 2)
    buy_price: Numeric(10, 2)
    sale_price: Numeric(10, 2)
    
    # Processing status
    is_processed: Boolean + index
```

### 3. Гибридный репозиторий (`core/repositories/hybrid_materials.py`)

```python
class HybridMaterialsRepository(BaseRepository):
    """Hybrid repository using both vector and relational databases."""
    
    def __init__(self, vector_db: IVectorDatabase, relational_db: IRelationalDatabase):
        # Dual database support
        
    async def search_materials_hybrid(self, query: str) -> List[Dict]:
        # Advanced hybrid search with weighted scoring
        
    async def search_materials(self, query: str) -> List[Material]:
        # Fallback strategy: vector → SQL if 0 results
```

**Стратегии поиска:**

1. **Vector Search** (primary): Семантический поиск в Qdrant
2. **SQL Hybrid Search** (fallback): Триграммный + ILIKE поиск
3. **Combined Search**: Объединение результатов с весовыми коэффициентами

### 4. Alembic миграции

```bash
# Структура миграций
alembic/
├── env.py              # Async environment
├── script.py.mako      # Migration template
└── versions/           # Migration files
    └── 001_initial_schema.py
```

**Команды миграций:**
```bash
# Создать миграцию
alembic revision --autogenerate -m "Initial schema"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

## 🔍 Поисковые возможности

### 1. Гибридный поиск

```python
# Продвинутый гибридный поиск
results = await hybrid_repo.search_materials_hybrid(
    query="цемент портландский",
    limit=10,
    vector_weight=0.7,      # Вес векторного поиска
    sql_weight=0.3,         # Вес SQL поиска
    min_vector_score=0.6,   # Минимальный score для векторов
    min_sql_similarity=0.3  # Минимальное сходство для SQL
)
```

### 2. Fallback стратегия

```python
# Автоматический fallback
results = await hybrid_repo.search_materials("редкий материал")
# 1. Пробует векторный поиск
# 2. Если 0 результатов → переключается на SQL поиск
# 3. Возвращает лучшие результаты
```

### 3. Триграммный поиск (fuzzy matching)

```python
# PostgreSQL триграммный поиск
results = await postgresql_db.search_materials_hybrid(
    query="цемнт",  # Опечатка в "цемент"
    similarity_threshold=0.3
)
# Найдет "цемент" благодаря триграммному сходству
```

## 📊 Производительность

### Оптимизации

1. **Индексы PostgreSQL:**
   - GIN индексы для триграммного поиска
   - B-tree индексы для точных совпадений
   - Composite индексы для частых запросов

2. **Connection Pooling:**
   - Настраиваемый размер пула
   - Автоматическое переиспользование соединений
   - Graceful handling переполнения

3. **Параллельные операции:**
   - Concurrent поиск в обеих БД
   - Async/await для всех операций
   - Batch операции для массовых вставок

### Метрики производительности

```python
# Пример результатов тестирования
Vector search:    0.045s (15 results)
SQL search:       0.023s (12 results)  
Hybrid search:    0.067s (18 results)
```

## 🧪 Тестирование

### Unit тесты

```bash
# PostgreSQL адаптер
pytest tests/test_postgresql_adapter.py -v

# Гибридный репозиторий
pytest tests/test_hybrid_repository.py -v

# Все тесты этапа 3
pytest tests/ -k "postgresql or hybrid" -v
```

### Integration тесты

```bash
# Требует реальную PostgreSQL БД
pytest tests/test_postgresql_adapter.py::TestPostgreSQLIntegration -v
```

### Демо скрипт

```bash
# Полная демонстрация возможностей
python utils/demo_postgresql_hybrid.py
```

## 🚀 Использование

### 1. Настройка окружения

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
export POSTGRESQL_URL="postgresql+asyncpg://user:password@localhost:5432/materials"
export QDRANT_URL="https://your-cluster.qdrant.io"
export OPENAI_API_KEY="your-api-key"
```

### 2. Инициализация БД

```python
from core.database.factories import DatabaseFactory

# Создание PostgreSQL адаптера
postgresql_db = DatabaseFactory.create_relational_database()

# Создание таблиц
await postgresql_db.create_tables()

# Применение миграций
# alembic upgrade head
```

### 3. Использование гибридного репозитория

```python
from core.repositories.hybrid_materials import HybridMaterialsRepository
from core.database.factories import DatabaseFactory, AIClientFactory

# Создание репозитория
vector_db = DatabaseFactory.create_vector_database()
relational_db = DatabaseFactory.create_relational_database()
ai_client = AIClientFactory.create_ai_client()

hybrid_repo = HybridMaterialsRepository(
    vector_db=vector_db,
    relational_db=relational_db,
    ai_client=ai_client
)

# Создание материала (в обеих БД)
material = await hybrid_repo.create_material(MaterialCreate(
    name="Портландцемент М500",
    use_category="Цемент",
    unit="мешок",
    sku="CEM500",
    description="Высококачественный цемент"
))

# Поиск с fallback стратегией
results = await hybrid_repo.search_materials("цемент")

# Продвинутый гибридный поиск
hybrid_results = await hybrid_repo.search_materials_hybrid(
    query="строительный материал",
    vector_weight=0.7,
    sql_weight=0.3
)
```

## 🔧 Конфигурация

### PostgreSQL настройки

```python
# core/config.py
POSTGRESQL_URL: str = "postgresql+asyncpg://user:password@localhost:5432/materials"
POSTGRESQL_POOL_SIZE: int = 10
POSTGRESQL_MAX_OVERFLOW: int = 20
```

### Alembic настройки

```ini
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://user:password@localhost/dbname
```

## 📈 Мониторинг

### Health checks

```python
# PostgreSQL health
health = await postgresql_db.health_check()
print(f"Status: {health['status']}")
print(f"Pool: {health['connection_pool']}")
print(f"Stats: {health['statistics']}")

# Гибридный репозиторий health
health = await hybrid_repo.health_check()
print(f"Overall: {health['status']}")
print(f"Vector DB: {health['vector_database']['status']}")
print(f"PostgreSQL: {health['relational_database']['status']}")
```

### Метрики производительности

```python
# Статистика БД
stats = await postgresql_db.execute_query("""
    SELECT 
        COUNT(*) as materials_count,
        pg_database_size(current_database()) as db_size_bytes,
        (SELECT COUNT(*) FROM pg_stat_activity) as active_connections
""")
```

## 🔄 Миграция с предыдущих этапов

### Из Этапа 2

1. **Обновление зависимостей:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройка PostgreSQL:**
   ```bash
   # Создание БД
   createdb materials
   
   # Применение миграций
   alembic upgrade head
   ```

3. **Обновление кода:**
   ```python
   # Замена MaterialsService на HybridMaterialsRepository
   from core.repositories.hybrid_materials import HybridMaterialsRepository
   
   # Обновление dependency injection
   from core.dependencies.database import get_hybrid_materials_repository
   ```

## 🐛 Troubleshooting

### Частые проблемы

1. **PostgreSQL connection failed:**
   ```bash
   # Проверка подключения
   psql postgresql://user:password@localhost:5432/materials
   
   # Проверка переменных окружения
   echo $POSTGRESQL_URL
   ```

2. **Alembic migration errors:**
   ```bash
   # Сброс миграций
   alembic downgrade base
   alembic upgrade head
   
   # Проверка схемы
   alembic current
   ```

3. **Hybrid search не работает:**
   ```python
   # Проверка health checks
   health = await hybrid_repo.health_check()
   print(health)
   
   # Проверка индексов
   await postgresql_db.execute_query("SELECT * FROM pg_indexes WHERE tablename = 'materials'")
   ```

## 📚 Дополнительные ресурсы

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [pg_trgm Extension](https://www.postgresql.org/docs/current/pgtrgm.html)

## ✅ Готовность к Этапу 4

После завершения Этапа 3 система готова к:
- Redis кеширование (Этап 4)
- Rate limiting и безопасность (Этап 5)
- Production deployment (Этап 6)

Все компоненты протестированы и готовы к продакшн использованию. 