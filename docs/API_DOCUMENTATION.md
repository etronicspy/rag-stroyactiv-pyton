# 📚 API Documentation - RAG Construction Materials API

Полная документация API для управления строительными материалами с продвинутым семантическим поиском и мульти-БД поддержкой.

## 🌐 Базовая информация

- **Base URL**: `http://localhost:8000`
- **API Version**: `v1`
- **API Prefix**: `/api/v1`
- **Content-Type**: `application/json; charset=utf-8`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🎯 Режимы развертывания

### 🔧 Development Mode (Текущий)
**Qdrant-Only режим для локальной разработки**

Система настроена для работы только с Qdrant векторной БД с mock-адаптерами для PostgreSQL и Redis:

```bash
# Переменные окружения для Development режима (по умолчанию)
QDRANT_ONLY_MODE=true
ENABLE_FALLBACK_DATABASES=true
DISABLE_REDIS_CONNECTION=true
DISABLE_POSTGRESQL_CONNECTION=true
```

**Особенности Development режима:**
- ✅ **Быстрый старт** без PostgreSQL/Redis инфраструктуры
- ✅ **Полная функциональность** через Qdrant + mock адаптеры
- ✅ **Fallback стратегии** при недоступности реальных БД
- ✅ **Автоматическое переключение** на mock-реализации
- ✅ **Все API эндпоинты работают** без изменений
- ✅ **Идеально для разработки** и тестирования

### 🚀 Production Mode (Планируемый)
**Полная мульти-БД архитектура для продакшн среды**

```bash
# Переменные окружения для Production режима
QDRANT_ONLY_MODE=false
DATABASE_URL=postgresql://user:pass@localhost:5432/materials
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=https://cluster.qdrant.tech:6333
```

**Компоненты Production режима:**
- 🎯 **PostgreSQL** - основная реляционная БД для структурированных данных
- 🎯 **Qdrant** - векторная БД для семантического поиска
- 🎯 **Redis** - кеширование и управление сессиями
- 🎯 **OpenAI** - генерация эмбеддингов

---

## 📊 Структура API

### **Всего эндпоинтов**: 31
- **Все эндпоинты активны** (подключены в main.py)
- **Advanced Search полностью функционален**

### **HTTP методы**:
- **GET**: 23 эндпоинта
- **POST**: 14 эндпоинтов  
- **PUT**: 1 эндпоинт
- **DELETE**: 5 эндпоинтов
- **PATCH**: 1 эндпоинт

---

## 🏠 Root Endpoints

### GET /
Приветственное сообщение и информация об API.

**Параметры**: Нет

**Ответ**:
```json
{
  "message": "Welcome to Construction Materials API",
  "version": "1.0.0",
  "docs_url": "/docs"
}
```

---

## 🏥 Health Check Endpoints

### GET /api/v1/health/
Базовая проверка здоровья приложения.

**Ответ**:
```json
{
  "status": "healthy",
  "service": "Construction Materials API",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "uptime_seconds": 3600
}
```

### GET /api/v1/health/detailed
Детальная проверка всех сервисов включая mock адаптеры.

**Ответ в Development режиме (Qdrant-Only)**:
```json
{
  "status": "healthy",
  "vector_database": {
    "type": "qdrant_cloud",
    "status": "healthy",
    "details": {
      "url": "https://your-cluster.qdrant.tech:6333",
      "collections_count": 1,
      "collection_exists": true,
      "points_count": 1250
    }
  },
  "postgresql": {
    "type": "mock",
    "status": "healthy",
    "message": "Using mock PostgreSQL adapter (Development mode)"
  },
  "redis": {
    "type": "mock", 
    "status": "healthy",
    "message": "Using mock Redis adapter (Development mode)"
  },
  "ai_service": {
    "type": "openai",
    "status": "healthy",
    "model": "text-embedding-ada-002"
  }
}
```

### GET /api/v1/health/databases
Проверка здоровья всех баз данных.

**HTTP статусы**: 
- 200 (healthy)
- 207 (degraded) 
- 503 (unhealthy)

### GET /api/v1/health/config
Статус конфигурации системы.

---

## 📊 Monitoring Endpoints

### GET /api/v1/monitoring/health
Комплексная проверка здоровья системы.

**HTTP статусы**: 200 (healthy), 207 (degraded), 503 (unhealthy)

---

## 📚 Reference Endpoints

### POST /api/v1/reference/categories/
Создание новой категории.

**Request Body**:
```json
{
  "name": "string",
  "description": "string"
}
```

**Ответ**:
```json
{
  "name": "Цемент",
  "description": "Вяжущие материалы на основе портландцемента"
}
```

### GET /api/v1/reference/categories/
Получение всех категорий.

**Ответ**:
```json
[
  {
    "name": "Цемент",
    "description": "Вяжущие материалы"
  },
  {
    "name": "Кирпич", 
    "description": "Керамические изделия"
  }
]
```

### DELETE /api/v1/reference/categories/{name}
Удаление категории.

**Path параметры**:
- `name` (string): Имя категории

### POST /api/v1/reference/units/
Создание новой единицы измерения.

**Request Body**:
```json
{
  "name": "кг",
  "description": "Килограмм"
}
```

### GET /api/v1/reference/units/
Получение всех единиц измерения.

### DELETE /api/v1/reference/units/{name}
Удаление единицы измерения.

---

## 🧱 Materials Endpoints

### POST /api/v1/materials/
Создание материала с семантическим эмбеддингом.

**Request Body** (MaterialCreate):
```json
{
  "name": "Цемент портландский М400",
  "use_category": "Цемент",
  "unit": "кг",
  "sku": "CEM001",
  "description": "Портландцемент марки М400 для общестроительных работ"
}
```

**Ответ**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Цемент портландский М400",
  "use_category": "Цемент",
  "unit": "кг",
  "sku": "CEM001",
  "description": "Портландцемент марки М400 для общестроительных работ",
  "embedding": [0.1, 0.2, -0.3, 0.4, -0.5, "... (total: 1536 dimensions)"],
  "created_at": "2024-01-01T12:00:00.000Z",
  "updated_at": "2024-01-01T12:00:00.000Z"
}
```

### GET /api/v1/materials/{material_id}
Получение материала по ID.

**Path параметры**:
- `material_id` (string): Идентификатор материала

### POST /api/v1/materials/search
Поиск материалов с fallback стратегией (vector → SQL LIKE).

**Request Body** (MaterialSearchQuery):
```json
{
  "query": "цемент портландский",
  "limit": 10
}
```

**Ответ**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Цемент портландский М400",
    "use_category": "Цемент",
    "unit": "кг",
    "sku": "CEM001",
    "description": "Портландцемент марки М400",
    "created_at": "2024-01-01T12:00:00.000Z",
    "updated_at": "2024-01-01T12:00:00.000Z"
  }
]
```

### GET /api/v1/materials/
Получение всех материалов с фильтрацией.

**Query параметры**:
- `skip` (int, default: 0): Количество пропускаемых материалов
- `limit` (int, default: 10): Максимальное количество материалов  
- `category` (string, optional): Фильтр по категории

**Особенности ответа**:
- Поле `embedding` теперь всегда показывает информативный превью вместо `null`
- Для материалов с векторами: первые 5 значений + "... (total: N dimensions)"
- Для материалов без векторов: "... (embeddings available, total: 1536 dimensions)"

### PUT /api/v1/materials/{material_id}
Обновление материала с новым эмбеддингом.

**Path параметры**:
- `material_id` (string): Идентификатор материала

**Request Body** (MaterialUpdate):
```json
{
  "name": "Цемент портландский М500",
  "description": "Обновленное описание"
}
```

### DELETE /api/v1/materials/{material_id}
Удаление материала.

### POST /api/v1/materials/batch
Массовое создание материалов.

**Request Body** (MaterialBatchCreate):
```json
{
  "materials": [
    {
      "name": "Цемент М400",
      "use_category": "Цемент",
      "unit": "кг"
    },
    {
      "name": "Цемент М500", 
      "use_category": "Цемент",
      "unit": "кг"
    }
  ],
  "batch_size": 100
}
```

**Ответ**:
```json
{
  "success": true,
  "total_processed": 2,
  "successful_creates": 2,
  "failed_creates": 0,
  "processing_time_seconds": 1.25,
  "errors": [],
  "created_materials": [...]
}
```

### POST /api/v1/materials/import
Импорт материалов из JSON.

**Request Body** (MaterialImportRequest):
```json
{
  "materials": [
    {
      "sku": "CEM001",
      "name": "Цемент М400"
    }
  ],
  "default_use_category": "Стройматериалы",
  "default_unit": "шт",
  "batch_size": 100
}
```

### GET /api/v1/materials/health
Проверка здоровья сервиса материалов.

---

## 💰 Price List Endpoints

### POST /api/v1/prices/process
Обработка прайс-листа (CSV/Excel) с поддержкой двух форматов.

**Content-Type**: `multipart/form-data`

**Form Parameters**:
- `file` (UploadFile): CSV или Excel файл (макс 50MB)
- `supplier_id` (string): Идентификатор поставщика (обязательно)
- `pricelistid` (int): ID прайс-листа (опционально)

**Поддерживаемые форматы**:

*Legacy формат*:
- `name`: Название материала (обязательно)
- `use_category`: Категория материала (обязательно)
- `unit`: Единица измерения (обязательно)
- `price`: Цена (обязательно)
- `description`: Описание (опционально)

*Расширенный формат*:
- `name`: Название продукта (обязательно)
- `sku`: Артикул (опционально)
- `use_category`: Категория (опционально)
- `unit_price`: Основная цена (обязательно)
- `unit_price_currency`: Валюта (опционально, по умолчанию RUB)
- `unit_calc_price`: Расчетная цена (опционально)
- `buy_price`: Закупочная цена (опционально)
- `sale_price`: Продажная цена (опционально)
- `calc_unit`: Единица расчета (обязательно для нового формата)
- `count`: Количество (опционально, по умолчанию 1)
- `date_price_change`: Дата изменения цены (опционально)

**Ответ для legacy формата**:
```json
{
  "message": "Price list processed successfully",
  "supplier_id": "supplier_001",
  "materials_processed": 150,
  "upload_date": "2024-01-01T12:00:00.000Z"
}
```

**Ответ для расширенного формата**:
```json
{
  "message": "Raw product list processed successfully",
  "supplier_id": "supplier_001", 
  "pricelistid": 12345,
  "raw_products_processed": 150,
  "upload_date": "2024-01-01T12:00:00.000Z"
}
```

### GET /api/v1/prices/{supplier_id}/latest
Получение последнего прайс-листа поставщика.

**Path параметры**:
- `supplier_id` (string): Идентификатор поставщика

**Ответ**:
```json
{
  "supplier_id": "supplier_001",
  "total_count": 150,
  "raw_products": [...],
  "upload_date": "2024-01-01T12:00:00.000Z"
}
```

### GET /api/v1/prices/{supplier_id}/all
Получение всех прайс-листов поставщика (сгруппированных по дате загрузки).

### DELETE /api/v1/prices/{supplier_id}
Удаление всех прайс-листов поставщика.

### GET /api/v1/prices/{supplier_id}/pricelist/{pricelistid}
Получение продуктов по конкретному ID прайс-листа.

**Path параметры**:
- `supplier_id` (string): Идентификатор поставщика
- `pricelistid` (int): ID прайс-листа

### PATCH /api/v1/prices/{supplier_id}/product/{product_id}/process
Отметка продукта как обработанного.

**Path параметры**:
- `supplier_id` (string): Идентификатор поставщика
- `product_id` (string): ID продукта

---

## 🔍 Search Endpoints

### GET /api/v1/search/
Простой поиск материалов с семантическим поиском и fallback стратегией.

**Query параметры**:
- `q` (string, required): Поисковый запрос
- `limit` (int, default: 10): Максимальное количество результатов

**Пример запроса**:
```bash
GET /api/v1/search/?q=цемент портландский&limit=5
```

**Ответ**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Цемент портландский М400",
    "use_category": "Цемент",
    "unit": "кг",
    "sku": "CEM001",
    "description": "Портландцемент марки М400",
    "created_at": "2024-01-01T12:00:00.000Z",
    "updated_at": "2024-01-01T12:00:00.000Z"
  }
]
```

---

## 🔍 Advanced Search Endpoints

### POST /api/v1/search/advanced
Продвинутый поиск с комплексной фильтрацией и сортировкой.

**Request Body** (AdvancedSearchQuery):
```json
{
  "query": "цемент портландский",
  "search_type": "hybrid",
  "filters": {
    "categories": ["Цемент"],
    "units": ["кг"],
    "sku_pattern": "CEM*",
    "created_after": "2024-01-01T00:00:00",
    "created_before": "2024-12-31T23:59:59",
    "search_fields": ["name", "description"],
    "min_similarity": 0.5
  },
  "sort_by": [
    {"field": "relevance", "direction": "desc"},
    {"field": "created_at", "direction": "desc"}
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "cursor": "eyJpZCI6InRlc3QtaWQifQ=="
  },
  "fuzzy_threshold": 0.8,
  "include_suggestions": true,
  "highlight_matches": true
}
```

**Ответ** (SearchResponse):
```json
{
  "results": [
    {
      "material": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Цемент портландский М400",
        "use_category": "Цемент",
        "unit": "кг"
      },
      "score": 0.95,
      "search_type": "vector",
      "highlights": [
        {
          "field": "name",
          "original": "Цемент портландский М400",
          "highlighted": "<mark>Цемент</mark> <mark>портландский</mark> М400"
        }
      ]
    }
  ],
  "total_count": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "search_time_ms": 45.67,
  "suggestions": [...],
  "filters_applied": {...},
  "next_cursor": "string"
}
```

### GET /api/v1/search/suggestions
Предложения для автодополнения.

**Query параметры**:
- `q` (string, min 1 char): Запрос для предложений
- `limit` (int, 1-20, default: 8): Максимальное количество предложений

### GET /api/v1/search/popular-queries
Статистика популярных запросов.

### GET /api/v1/search/analytics
Аналитика поиска.

### GET /api/v1/search/categories
Получение доступных категорий.

### GET /api/v1/search/units
Получение доступных единиц измерения.

### POST /api/v1/search/fuzzy
Нечеткий поиск.

### GET /api/v1/search/health
Проверка здоровья сервиса поиска.

---

## 📝 Схемы данных

### MaterialCreate
```json
{
  "name": "string",           // 2-200 символов, обязательно
  "use_category": "string",   // макс 200 символов, обязательно  
  "unit": "string",           // обязательно
  "sku": "string",           // 3-50 символов, опционально
  "description": "string"     // опционально
}
```

### Material (Response)
```json
{
  "id": "string",
  "name": "string",
  "use_category": "string",
  "unit": "string", 
  "sku": "string",
  "description": "string",
      "embedding": [0.1, 0.2, -0.3, 0.4, -0.5, "... (total: 1536 dimensions)"],  // Всегда показывается, не null
  "created_at": "2024-01-01T12:00:00.000Z",
  "updated_at": "2024-01-01T12:00:00.000Z"
}
```

### RawProduct (для прайс-листов)
```json
{
  "id": "string",
  "name": "string",
  "sku": "string",
  "use_category": "string",
  "unit_price": 1500.00,
  "unit_price_currency": "RUB",
  "unit_calc_price": 1450.00,
  "buy_price": 1200.00,
  "sale_price": 1800.00,
  "calc_unit": "кг",
  "count": 1,
  "date_price_change": "2024-01-01",
  "pricelistid": 12345,
  "supplier_id": "supplier_001",
  "is_processed": false,
  "created": "2024-01-01T12:00:00.000Z",
  "modified": "2024-01-01T12:00:00.000Z",
  "upload_date": "2024-01-01T12:00:00.000Z"
}
```

---

## 🚀 HTTP статус коды

- **200**: Успешный запрос
- **201**: Ресурс успешно создан
- **207**: Multi-status (частично успешно)
- **400**: Ошибка валидации данных
- **404**: Ресурс не найден
- **500**: Внутренняя ошибка сервера
- **503**: Сервис недоступен

---

## 🎯 Особенности API

### Fallback стратегия поиска
1. **Vector search** - семантический поиск через эмбеддинги
2. **SQL LIKE search** - если vector search вернул 0 результатов

### Mock адаптеры в Qdrant-only режиме
- **MockPostgreSQLDatabase**: Симуляция PostgreSQL операций
- **MockRedisClient**: Полная совместимость с Redis API
- **MockAIClient**: Детерминированная генерация эмбеддингов

### Поддержка форматов файлов
- **CSV**: UTF-8 encoding
- **Excel**: .xls, .xlsx форматы
- **Максимальный размер**: 50MB

### Rate Limiting
- Настраивается через environment variables
- Поддержка burst protection
- Headers с информацией о лимитах
- Работает с mock Redis в Qdrant-only режиме

### Middleware
- **Security**: XSS protection, SQL injection protection
- **Compression**: Brotli и gzip
- **Logging**: Структурированное логирование
- **CORS**: Настраиваемые правила

### Кеширование
- **Redis**: Для кеширования результатов поиска (или mock)
- **Vector Cache**: Для векторных операций
- **Connection Pooling**: Автоматическое масштабирование

---

## 💡 Примеры использования

### Создание материала
```bash
curl -X POST "http://localhost:8000/api/v1/materials/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Цемент портландский М400",
    "use_category": "Цемент",
    "unit": "кг",
    "sku": "CEM001",
    "description": "Портландцемент марки М400"
  }'
```

### Поиск материалов
```bash
curl -X POST "http://localhost:8000/api/v1/materials/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "цемент портландский",
    "limit": 10
  }'
```

### Простой поиск через GET
```bash
curl "http://localhost:8000/api/v1/search/?q=цемент&limit=5"
```

### Загрузка прайс-листа
```bash
curl -X POST "http://localhost:8000/api/v1/prices/process" \
  -F "file=@pricelist.csv" \
  -F "supplier_id=supplier_001" \
  -F "pricelistid=12345"
```

### Проверка здоровья системы
```bash
curl "http://localhost:8000/api/v1/health/detailed"
```

### Получение метрик мониторинга
```bash
curl "http://localhost:8000/api/v1/monitoring/pools"
```

---

## 🔧 Конфигурация

### Qdrant-only режим
```bash
# .env файл
QDRANT_ONLY_MODE=true
ENABLE_FALLBACK_DATABASES=true
DISABLE_REDIS_CONNECTION=true
DISABLE_POSTGRESQL_CONNECTION=true

# Qdrant настройки
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION_NAME=materials

# OpenAI для эмбеддингов
OPENAI_API_KEY=your-openai-key
```

### Multi-Database режим
```bash
# PostgreSQL
POSTGRESQL_URL=postgresql://user:pass@localhost:5432/materials

# Redis
REDIS_URL=redis://localhost:6379/0

# Векторная БД (выбрать одну)
DATABASE_TYPE=QDRANT_CLOUD  # или QDRANT_LOCAL, WEAVIATE, PINECONE
```

---

## 🧪 Тестирование API

### Базовые тесты
```bash
# Проверка здоровья
curl "http://localhost:8000/api/v1/health/"

# Создание материала
curl -X POST "http://localhost:8000/api/v1/materials/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Тест", "use_category": "Тест", "unit": "шт"}'

# Поиск материалов
curl "http://localhost:8000/api/v1/search/?q=тест&limit=1"
```

### Swagger UI
Откройте http://localhost:8000/docs для интерактивного тестирования всех эндпоинтов.

---

*Документация обновлена на основе анализа реального кода приложения* 