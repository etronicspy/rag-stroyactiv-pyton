# Migration Guide: From Legacy to New Multi-Database Architecture

Руководство по миграции с legacy архитектуры на новую мульти-БД архитектуру.

## 📋 Overview / Обзор

Этот документ описывает процесс миграции с текущей архитектуры на новую мульти-БД архитектуру с dependency injection.

### Что изменилось:

**До (Legacy):**
```python
# services/materials.py
class MaterialsService:
    def __init__(self):
        self.qdrant_client = get_vector_db_client()  # Direct import
        self.ai_client = get_ai_client()             # Direct import
```

**После (New Architecture):**
```python
# services/materials_new.py
class MaterialsService(BaseRepository):
    def __init__(self, vector_db: IVectorDatabase = None, ai_client = None):
        super().__init__(vector_db=vector_db, ai_client=ai_client)  # DI
```

## 🔄 Migration Steps / Этапы миграции

### Этап 1: Обновление сервисов

#### 1.1 Обновить импорты

**Старый код:**
```python
from core.config import get_vector_db_client, get_ai_client
from services.materials import MaterialsService
```

**Новый код:**
```python
from core.dependencies.database import get_vector_db_dependency, get_ai_client_dependency
from services.materials_new import MaterialsService
```

#### 1.2 Обновить инициализацию сервиса

**Старый код:**
```python
materials_service = MaterialsService()  # Автоматическая инициализация
```

**Новый код:**
```python
# В FastAPI routes с dependency injection
def get_materials_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
) -> MaterialsService:
    return MaterialsService(vector_db=vector_db, ai_client=ai_client)

# В обычном коде
vector_db = get_vector_db_dependency()
ai_client = get_ai_client_dependency()
materials_service = MaterialsService(vector_db=vector_db, ai_client=ai_client)
```

### Этап 2: Обновление API routes

#### 2.1 Старая структура routes

```python
# api/routes/materials.py
router = APIRouter()
materials_service = MaterialsService()  # Global instance

@router.post("/")
async def create_material(material: MaterialCreate):
    return await materials_service.create_material(material)
```

#### 2.2 Новая структура routes

```python
# api/routes/materials_refactored.py
router = APIRouter()

def get_materials_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
) -> MaterialsService:
    return MaterialsService(vector_db=vector_db, ai_client=ai_client)

@router.post("/")
async def create_material(
    material: MaterialCreate,
    service: MaterialsService = Depends(get_materials_service)
):
    return await service.create_material(material)
```

### Этап 3: Обновление обработки ошибок

#### 3.1 Старая обработка ошибок

```python
try:
    result = await materials_service.create_material(material)
    return result
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

#### 3.2 Новая обработка ошибок

```python
try:
    result = await service.create_material(material)
    return result
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
except ConnectionError as e:
    logger.error(f"Connection error: {e}")
    raise HTTPException(status_code=503, detail=f"Service unavailable: {e.message}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
```

## 📝 Code Changes Checklist / Чеклист изменений

### ✅ Services Layer

- [ ] Обновить `MaterialsService` для использования DI
- [ ] Добавить наследование от `BaseRepository`
- [ ] Обновить методы для использования новых интерфейсов
- [ ] Добавить структурированную обработку ошибок
- [ ] Добавить логирование операций

### ✅ API Routes Layer

- [ ] Обновить routes для использования dependency injection
- [ ] Добавить функции получения сервисов с DI
- [ ] Обновить обработку ошибок с новой иерархией
- [ ] Добавить health check endpoints
- [ ] Обновить документацию API

### ✅ Configuration

- [ ] Обновить конфигурацию для поддержки мульти-БД
- [ ] Добавить настройки PostgreSQL и Redis
- [ ] Обновить factory методы конфигурации
- [ ] Проверить environment variables

### ✅ Testing

- [ ] Обновить тесты для использования моков DI
- [ ] Добавить тесты для новых интерфейсов
- [ ] Добавить тесты обработки ошибок
- [ ] Добавить интеграционные тесты

## 🔧 Configuration Updates / Обновления конфигурации

### Обновить .env файлы

```bash
# Добавить новые настройки БД
POSTGRESQL_URL=postgresql://user:password@localhost/materials
REDIS_URL=redis://localhost:6379

# Обновить существующие настройки
DATABASE_TYPE=qdrant_cloud
AI_PROVIDER=openai
```

### Обновить settings

```python
# core/config.py - уже обновлено
class Settings(BaseSettings):
    # ... existing settings ...
    
    # PostgreSQL settings
    POSTGRESQL_URL: Optional[str] = None
    POSTGRESQL_USER: Optional[str] = None
    # ... other PostgreSQL settings ...
    
    # Redis settings  
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    # ... other Redis settings ...
```

## 🧪 Testing Migration / Тестирование миграции

### 1. Unit Tests

```bash
# Тесты новой архитектуры
pytest tests/test_database_architecture.py -v

# Тесты рефакторенного сервиса
pytest tests/test_materials_refactored.py -v
```

### 2. Integration Tests

```bash
# Интеграционные тесты с реальной БД
pytest tests/test_materials_refactored.py::TestMaterialsServiceRefactored -v -m integration
```

### 3. Demo Script

```bash
# Демонстрация новой архитектуры
python utils/demo_refactored_service.py
```

## 🚀 Deployment Strategy / Стратегия развертывания

### Вариант 1: Постепенная миграция (Рекомендуется)

1. **Этап 1**: Развернуть новую архитектуру параллельно
2. **Этап 2**: Переключить часть endpoints на новую архитектуру
3. **Этап 3**: Постепенно мигрировать все endpoints
4. **Этап 4**: Удалить legacy код

### Вариант 2: Полная миграция

1. Обновить все сервисы и routes одновременно
2. Тщательно протестировать
3. Развернуть все изменения сразу

## 📊 Performance Comparison / Сравнение производительности

### Legacy Architecture

```
MaterialsService.__init__() -> Direct DB connections
├── get_vector_db_client() -> New connection each time
├── get_ai_client() -> New connection each time
└── No caching, no connection pooling
```

### New Architecture

```
MaterialsService.__init__(vector_db, ai_client) -> Injected dependencies
├── @lru_cache on factories -> Cached connections
├── Connection pooling -> Better resource usage
└── Health checks -> Better monitoring
```

### Ожидаемые улучшения:

- **Производительность**: +30-50% за счет кеширования подключений
- **Память**: -20-30% за счет переиспользования объектов
- **Тестируемость**: +100% за счет dependency injection
- **Мониторинг**: +100% за счет health checks

## 🔍 Troubleshooting / Устранение неполадок

### Частые проблемы:

#### 1. Import Errors

**Проблема**: `ImportError: cannot import name 'get_vector_db_dependency'`

**Решение**:
```python
# Убедитесь что импортируете из правильного модуля
from core.dependencies.database import get_vector_db_dependency
```

#### 2. Dependency Injection Errors

**Проблема**: `TypeError: MaterialsService() missing required arguments`

**Решение**:
```python
# Используйте dependency injection в FastAPI
service: MaterialsService = Depends(get_materials_service)

# Или создавайте вручную
vector_db = get_vector_db_dependency()
ai_client = get_ai_client_dependency()
service = MaterialsService(vector_db=vector_db, ai_client=ai_client)
```

#### 3. Database Connection Errors

**Проблема**: `ConnectionError: Failed to connect to database`

**Решение**:
```python
# Проверьте конфигурацию
from core.config import settings
print(settings.get_vector_db_config())

# Проверьте health check
health = await vector_db.health_check()
print(health)
```

## 📚 Additional Resources / Дополнительные ресурсы

- [Database Architecture Documentation](./DATABASE_ARCHITECTURE.md)
- [API Documentation](../api/docs/)
- [Testing Guide](./TESTING.md)
- [Deployment Guide](./DEPLOYMENT.md)

## 🎯 Next Steps / Следующие шаги

После завершения миграции:

1. **Этап 3**: Реализация PostgreSQL адаптера
2. **Этап 4**: Реализация Redis адаптера  
3. **Этап 5**: Гибридный поиск (vector + SQL)
4. **Этап 6**: Оптимизация производительности
5. **Этап 7**: Мониторинг и метрики

---

**Важно**: Всегда тестируйте миграцию на staging среде перед production развертыванием! 