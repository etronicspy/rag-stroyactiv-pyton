# API Endpoints Tree - Construction Materials RAG API

Полное дерево всех эндпоинтов API с описанием параметров, тел запросов и ответов.

## 🌟 Базовая информация
- **Версия API**: v1
- **Базовый URL**: `/api/v1`
- **Формат ответов**: JSON (UTF-8)
- **Аутентификация**: Не требуется (пока)
- **Rate Limiting**: Настраивается через environment variables

---

## 📊 Структура API дерева

```
RAG Construction Materials API
├── / (root)
│   └── GET / - Welcome message and API info
│
├── /api/v1/health/ - Мониторинг здоровья системы
│   ├── GET / - Basic health check
│   ├── GET /detailed - Detailed health check (all services)
│   ├── GET /databases - Database health check
│   ├── GET /metrics - Metrics endpoint
│   ├── GET /performance - Performance metrics
│   └── GET /config - Configuration status
│
├── /api/v1/monitoring/ - Мониторинг производительности
│   ├── GET /health - System health check
│   ├── GET /pools - Connection pool metrics
│   │   └── Query: pool_name (optional)
│   ├── GET /pools/history - Pool adjustment history
│   │   ├── Query: pool_name (optional)
│   │   └── Query: limit (1-200, default: 50)
│   ├── GET /pools/recommendations - Pool optimization recommendations
│   ├── POST /pools/{pool_name}/resize - Manual pool resize
│   │   ├── Path: pool_name
│   │   ├── Query: new_size (1-100, required)
│   │   └── Query: reason (optional, default: "Manual resize via API")
│   ├── GET /pools/stats - Pool statistics summary
│   ├── GET /optimizations - Optimization metrics and statistics
│   ├── GET /middleware/stats - Middleware performance statistics
│   └── POST /optimizations/benchmark - Run optimization benchmark
│
├── /api/v1/reference/ - Справочники и категории
│   ├── POST /categories/ - Create new category
│   │   └── Body: {"name": "string", "description": "string"}
│   ├── GET /categories/ - Get all categories
│   ├── DELETE /categories/{name} - Delete category
│   │   └── Path: name (category name)
│   ├── POST /units/ - Create new unit
│   │   └── Body: {"name": "string", "description": "string"}
│   ├── GET /units/ - Get all units
│   └── DELETE /units/{name} - Delete unit
│       └── Path: name (unit name)
│
├── /api/v1/materials/ - Управление материалами
│   ├── POST / - Create material
│   │   └── Body: MaterialCreate {
│   │       name: string (2-200 chars, required)
│   │       use_category: string (max 200 chars, required)
│   │       unit: string (required)
│   │       sku: string (3-50 chars, optional)
│   │       description: string (optional)
│   │   }
│   ├── GET /{material_id} - Get material by ID
│   │   └── Path: material_id (string)
│   ├── POST /search - Search materials
│   │   └── Body: MaterialSearchQuery {
│   │       query: string (min 1 char, required)
│   │       limit: int (1-100, default: 10)
│   │   }
│   ├── GET / - Get all materials with filtering
│   │   ├── Query: skip (int, default: 0)
│   │   ├── Query: limit (int, default: 10)
│   │   └── Query: category (string, optional)
│   ├── PUT /{material_id} - Update material
│   │   ├── Path: material_id (string)
│   │   └── Body: MaterialUpdate {
│   │       name: string (2-200 chars, optional)
│   │       use_category: string (optional)
│   │       unit: string (optional)
│   │       sku: string (3-50 chars, optional)
│   │       description: string (optional)
│   │   }
│   ├── DELETE /{material_id} - Delete material
│   │   └── Path: material_id (string)
│   ├── POST /batch - Create materials in batch
│   │   └── Body: MaterialBatchCreate {
│   │       materials: MaterialCreate[] (1-1000 items)
│   │       batch_size: int (1-500, default: 100)
│   │   }
│   ├── POST /import - Import materials from JSON
│   │   └── Body: MaterialImportRequest {
│   │       materials: MaterialImportItem[] (1-1000 items)
│   │       default_use_category: string (default: "Стройматериалы")
│   │       default_unit: string (default: "шт")
│   │       batch_size: int (1-500, default: 100)
│   │   }
│   └── GET /health - Materials service health check
│
├── /api/v1/prices/ - Управление прайс-листами
│   ├── POST /process - Process price list file
│   │   ├── Body (form-data):
│   │   │   ├── file: UploadFile (CSV/Excel, max 50MB)
│   │   │   ├── supplier_id: string (required)
│   │   │   └── pricelistid: int (optional)
│   │   └── Supported formats:
│   │       ├── Legacy: name, use_category, unit, price, description
│   │       └── Extended: name, sku, use_category, unit_price, 
│   │           unit_price_currency, unit_calc_price, buy_price, 
│   │           sale_price, calc_unit, count, date_price_change
│   ├── GET /{supplier_id}/latest - Get latest price list
│   │   └── Path: supplier_id (string)
│   ├── GET /{supplier_id}/all - Get all price lists
│   │   └── Path: supplier_id (string)
│   ├── DELETE /{supplier_id} - Delete supplier price lists
│   │   └── Path: supplier_id (string)
│   ├── GET /{supplier_id}/pricelist/{pricelistid} - Get by pricelist ID
│   │   ├── Path: supplier_id (string)
│   │   └── Path: pricelistid (int)
│   └── PATCH /{supplier_id}/product/{product_id}/process - Mark as processed
│       ├── Path: supplier_id (string)
│       └── Path: product_id (string)
│
├── /api/v1/search/ - Поиск материалов (включая продвинутый поиск)
│   ├── GET / - Simple search materials
│   │   ├── Query: q (string, required, search query)
│   │   └── Query: limit (int, default: 10, max results)
│   ├── POST /advanced - Advanced search with filtering
│   │   └── Body: AdvancedSearchQuery {
│   │       query: string (optional)
│   │       search_type: "vector"|"sql"|"hybrid"|"fuzzy" (default: "hybrid")
│   │       filters: MaterialFilterOptions {
│   │           categories: string[] (optional)
│   │           units: string[] (optional)
│   │           sku_pattern: string (optional, supports wildcards)
│   │           created_after: datetime (optional)
│   │           created_before: datetime (optional)
│   │           updated_after: datetime (optional)
│   │           updated_before: datetime (optional)
│   │           search_fields: string[] (default: ["name", "description", "use_category"])
│   │           min_similarity: float (0.0-1.0, default: 0.3)
│   │       }
│   │       sort_by: SortOption[] {
│   │           field: string (required)
│   │           direction: "asc"|"desc" (default: "asc")
│   │       }
│   │       pagination: PaginationOptions {
│   │           page: int (>=1, default: 1)
│   │           page_size: int (1-100, default: 20)
│   │           cursor: string (optional)
│   │       }
│   │       fuzzy_threshold: float (0.0-1.0, default: 0.8)
│   │       include_suggestions: bool (default: false)
│   │       highlight_matches: bool (default: false)
│   │   }
│   ├── GET /suggestions - Search autocomplete suggestions
│   │   ├── Query: q (string, min 1 char, required)
│   │   └── Query: limit (int, 1-20, default: 8)
│   ├── GET /categories - Get available categories
│   └── GET /units - Get available units
│

```

---

## 🔍 Детальное описание эндпоинтов

### 🏠 Root Endpoints

#### `GET /`
**Описание**: Приветственное сообщение и информация об API  
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

### 🏥 Health Check Endpoints

#### `GET /api/v1/health/`
**Описание**: Базовая проверка здоровья приложения  
**Параметры**: Нет  
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

#### `GET /api/v1/health/detailed`
**Описание**: Детальная проверка всех сервисов  
**Параметры**: Нет  
**Ответ**:
```json
{
  "status": "healthy",
  "vector_database": {...},
  "postgresql": {...},
  "redis": {...},
  "ai_service": {...}
}
```

#### `GET /api/v1/health/databases`
**Описание**: Проверка здоровья всех баз данных  
**Параметры**: Нет  
**HTTP статусы**: 200 (healthy), 207 (degraded), 503 (unhealthy)

#### `GET /api/v1/health/config`
**Описание**: Статус конфигурации системы  
**Параметры**: Нет

---

### 📊 Monitoring Endpoints

#### `GET /api/v1/monitoring/health`
**Описание**: Комплексная проверка здоровья системы  
**Параметры**: Нет  
**HTTP статусы**: 200 (healthy), 207 (degraded), 503 (unhealthy)


---

### 📚 Reference Endpoints

#### `POST /api/v1/reference/categories/`
**Описание**: Создание новой категории  
**Request Body**:
```json
{
  "name": "string",
  "description": "string"
}
```

#### `GET /api/v1/reference/categories/`
**Описание**: Получение всех категорий  
**Параметры**: Нет  
**Response**: `Category[]`

#### `DELETE /api/v1/reference/categories/{name}`
**Описание**: Удаление категории  
**Path параметры**:
- `name` (string): Имя категории

#### `POST /api/v1/reference/units/`
**Описание**: Создание новой единицы измерения  
**Request Body**:
```json
{
  "name": "string",
  "description": "string"
}
```

#### `GET /api/v1/reference/units/`
**Описание**: Получение всех единиц измерения  
**Параметры**: Нет  
**Response**: `Unit[]`

#### `DELETE /api/v1/reference/units/{name}`
**Описание**: Удаление единицы измерения  
**Path параметры**:
- `name` (string): Имя единицы

---

### 🧱 Materials Endpoints

#### `POST /api/v1/materials/`
**Описание**: Создание материала с семантическим эмбеддингом  
**Request Body** (MaterialCreate):
```json
{
  "name": "string",           // 2-200 символов, обязательно
  "use_category": "string",   // макс 200 символов, обязательно
  "unit": "string",           // обязательно
  "sku": "string",           // 3-50 символов, опционально
  "description": "string"     // опционально
}
```

#### `GET /api/v1/materials/{material_id}`
**Описание**: Получение материала по ID  
**Path параметры**:
- `material_id` (string): Идентификатор материала

#### `POST /api/v1/materials/search`
**Описание**: Поиск материалов с fallback стратегией  
**Request Body** (MaterialSearchQuery):
```json
{
  "query": "string",     // мин 1 символ, обязательно
  "limit": 10           // 1-100, по умолчанию 10
}
```

#### `GET /api/v1/materials/`
**Описание**: Получение всех материалов с фильтрацией  
**Query параметры**:
- `skip` (int, default: 0): Количество пропускаемых материалов
- `limit` (int, default: 10): Максимальное количество материалов
- `category` (string, optional): Фильтр по категории

#### `PUT /api/v1/materials/{material_id}`
**Описание**: Обновление материала с новым эмбеддингом  
**Path параметры**:
- `material_id` (string): Идентификатор материала  
**Request Body** (MaterialUpdate):
```json
{
  "name": "string",           // 2-200 символов, опционально
  "use_category": "string",   // опционально
  "unit": "string",           // опционально
  "sku": "string",           // 3-50 символов, опционально
  "description": "string"     // опционально
}
```

#### `DELETE /api/v1/materials/{material_id}`
**Описание**: Удаление материала  
**Path параметры**:
- `material_id` (string): Идентификатор материала

#### `POST /api/v1/materials/batch`
**Описание**: Массовое создание материалов  
**Request Body** (MaterialBatchCreate):
```json
{
  "materials": [MaterialCreate],  // 1-1000 элементов
  "batch_size": 100              // 1-500, по умолчанию 100
}
```

#### `POST /api/v1/materials/import`
**Описание**: Импорт материалов из JSON  
**Request Body** (MaterialImportRequest):
```json
{
  "materials": [MaterialImportItem],     // 1-1000 элементов
  "default_use_category": "Стройматериалы", // по умолчанию
  "default_unit": "шт",                  // по умолчанию
  "batch_size": 100                      // 1-500, по умолчанию 100
}
```

#### `GET /api/v1/materials/health`
**Описание**: Проверка здоровья сервиса материалов  
**Параметры**: Нет

---

### 💰 Price List Endpoints

#### `POST /api/v1/prices/process`
**Описание**: Обработка прайс-листа (CSV/Excel)  
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

#### `GET /api/v1/prices/{supplier_id}/latest`
**Описание**: Получение последнего прайс-листа поставщика  
**Path параметры**:
- `supplier_id` (string): Идентификатор поставщика

#### `GET /api/v1/prices/{supplier_id}/all`
**Описание**: Получение всех прайс-листов поставщика  
**Path параметры**:
- `supplier_id` (string): Идентификатор поставщика

#### `DELETE /api/v1/prices/{supplier_id}`
**Описание**: Удаление всех прайс-листов поставщика  
**Path параметры**:
- `supplier_id` (string): Идентификатор поставщика

#### `GET /api/v1/prices/{supplier_id}/pricelist/{pricelistid}`
**Описание**: Получение продуктов по конкретному ID прайс-листа  
**Path параметры**:
- `supplier_id` (string): Идентификатор поставщика
- `pricelistid` (int): ID прайс-листа

#### `PATCH /api/v1/prices/{supplier_id}/product/{product_id}/process`
**Описание**: Отметка продукта как обработанного  
**Path параметры**:
- `supplier_id` (string): Идентификатор поставщика
- `product_id` (string): ID продукта

---

### 🔍 Search Endpoints

#### `GET /api/v1/search/`
**Описание**: Простой поиск материалов с семантическим поиском  
**Query параметры**:
- `q` (string, required): Поисковый запрос
- `limit` (int, default: 10): Максимальное количество результатов

---

### 🔍 Advanced Search Endpoints

**✅ Все эндпоинты advanced search активны и функциональны**

#### `POST /api/v1/search/advanced`
**Описание**: Продвинутый поиск с комплексной фильтрацией  
**Request Body** (AdvancedSearchQuery):
```json
{
  "query": "цемент портландский",
  "search_type": "hybrid",  // "vector"|"sql"|"hybrid"|"fuzzy"
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

#### `GET /api/v1/search/suggestions`
**Описание**: Предложения для автодополнения  
**Query параметры**:
- `q` (string, min 1 char): Запрос для предложений
- `limit` (int, 1-20, default: 8): Максимальное количество предложений

#### `GET /api/v1/search/categories`
**Описание**: Получение доступных категорий  
**Параметры**: Нет

#### `GET /api/v1/search/units`
**Описание**: Получение доступных единиц измерения  
**Параметры**: Нет


#### `GET /api/v1/search/health`
**Описание**: Проверка здоровья сервиса поиска  
**Параметры**: Нет

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
  "embedding": [0.1, 0.2, ...],  // Опционально
  "created_at": "2024-01-01T12:00:00.000Z",
  "updated_at": "2024-01-01T12:00:00.000Z"
}
```

### AdvancedSearchQuery
```json
{
  "query": "string",
  "search_type": "hybrid",
  "filters": {
    "categories": ["string"],
    "units": ["string"],
    "sku_pattern": "string",
    "created_after": "datetime",
    "created_before": "datetime",
    "updated_after": "datetime", 
    "updated_before": "datetime",
    "search_fields": ["name", "description", "use_category"],
    "min_similarity": 0.3
  },
  "sort_by": [
    {"field": "string", "direction": "asc|desc"}
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "cursor": "string"
  },
  "fuzzy_threshold": 0.8,
  "include_suggestions": false,
  "highlight_matches": false
}
```

### SearchResponse
```json
{
  "results": [
    {
      "material": Material,
      "score": 0.95,
      "search_type": "vector",
      "highlights": [
        {
          "field": "name",
          "original": "цемент портландский",
          "highlighted": "<mark>цемент</mark> <mark>портландский</mark>"
        }
      ]
    }
  ],
  "total_count": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "search_time_ms": 45.67,
  "suggestions": [SearchSuggestion],
  "filters_applied": {...},
  "next_cursor": "string"
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

### Поддержка форматов файлов
- **CSV**: UTF-8 encoding
- **Excel**: .xls, .xlsx форматы
- **Максимальный размер**: 50MB

### Rate Limiting
- Настраивается через environment variables
- Поддержка burst protection
- Headers с информацией о лимитах

### Middleware
- **Security**: XSS protection, SQL injection protection
- **Compression**: Brotli и gzip
- **Logging**: Структурированное логирование
- **CORS**: Настраиваемые правила

### Кеширование
- **Redis**: Для кеширования результатов поиска
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

### Загрузка прайс-листа
```bash
curl -X POST "http://localhost:8000/api/v1/prices/process" \
  -F "file=@pricelist.csv" \
  -F "supplier_id=supplier_001" \
  -F "pricelistid=12345"
```

---

*Документ создан автоматически на основе анализа кода приложения*