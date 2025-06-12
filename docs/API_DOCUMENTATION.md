# 📚 API Documentation - RAG Construction Materials API

Полная документация API для управления строительными материалами с продвинутым семантическим поиском и мульти-БД поддержкой.

## 🌐 Базовая информация

- **Base URL**: `http://localhost:8000`
- **API Version**: `v1`
- **API Prefix**: `/api/v1`
- **Content-Type**: `application/json; charset=utf-8`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔍 Продвинутый поиск / Advanced Search

### POST /api/v1/search/advanced
Основной эндпоинт для продвинутого поиска материалов с множественными фильтрами и настройками.

#### Параметры запроса:
```json
{
  "query": "цемент для фундамента",
  "search_type": "hybrid",
  "filters": {
    "categories": ["Cement", "Concrete"],
    "units": ["bag", "kg"], 
    "sku_pattern": "CEM-*",
    "created_after": "2024-01-01",
    "created_before": "2024-12-31",
    "updated_after": "2024-01-01",
    "updated_before": "2024-12-31",
    "similarity_threshold": 0.7
  },
  "sort_options": [
    {"field": "relevance", "direction": "desc"},
    {"field": "name", "direction": "asc"}
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "use_cursor": false
  },
  "highlight": {
    "enabled": true,
    "fields": ["name", "description", "use_category"]
  }
}
```

#### Пример ответа:
```json
{
  "results": [
    {
      "id": "uuid-123",
      "name": "Портландцемент М500",
      "description": "Высококачественный цемент для фундамента",
      "use_category": "Cement",
      "unit": "bag",
      "sku": "CEM-M500-001",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "score": 0.95,
      "search_type": "vector",
      "highlights": {
        "name": "Портландцемент М500",
        "description": "Высококачественный <mark>цемент</mark> для <mark>фундамента</mark>"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_results": 42,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false,
    "next_cursor": "eyJpZCI6InV1aWQtMTIzIn0="
  },
  "search_metadata": {
    "query": "цемент для фундамента",
    "search_types_used": ["vector", "sql"],
    "total_search_time_ms": 145,
    "filters_applied": ["categories", "similarity_threshold"],
    "results_by_type": {
      "vector": 35,
      "sql": 5,
      "fuzzy": 2
    }
  }
}
```

#### Типы поиска:
- `vector` - семантический поиск через векторные эмбеддинги
- `sql` - традиционный текстовый поиск PostgreSQL
- `fuzzy` - нечеткий поиск с алгоритмами Levenshtein
- `hybrid` - комбинация всех типов с весовыми коэффициентами

#### Curl пример:
```bash
curl -X POST "http://localhost:8000/api/v1/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "цемент М500", 
    "search_type": "hybrid",
    "pagination": {"page": 1, "page_size": 10}
  }'
```

### GET /api/v1/search/suggestions
Автодополнение поисковых запросов на основе популярных запросов и названий материалов.

#### Параметры:
- `query` (string, required) - частичный поисковый запрос
- `limit` (integer, optional) - количество предложений (по умолчанию: 10)
- `suggestion_types` (array, optional) - типы предложений: `["popular", "materials", "categories"]`

#### Пример запроса:
```bash
GET /api/v1/search/suggestions?query=цем&limit=5&suggestion_types=popular,materials
```

#### Пример ответа:
```json
{
  "suggestions": [
    {
      "text": "цемент М500",
      "type": "popular",
      "score": 0.95,
      "metadata": {
        "search_count": 145,
        "avg_results": 23
      }
    },
    {
      "text": "цементно-песчаная смесь",
      "type": "materials", 
      "score": 0.87,
      "metadata": {
        "material_count": 12
      }
    }
  ],
  "query": "цем",
  "total_suggestions": 2
}
```

### GET /api/v1/search/popular-queries
Получение списка популярных поисковых запросов с аналитикой.

#### Параметры:
- `limit` (integer, optional) - количество запросов (по умолчанию: 20)
- `period` (string, optional) - период: `["today", "week", "month", "all"]`

#### Пример ответа:
```json
{
  "popular_queries": [
    {
      "query": "цемент М500",
      "search_count": 145,
      "avg_results": 23,
      "avg_search_time_ms": 120,
      "last_searched": "2024-01-15T10:30:00Z"
    }
  ],
  "period": "week",
  "total_queries": 15
}
```

### GET /api/v1/search/analytics
Детальная аналитика поисковых запросов с метриками производительности.

#### Параметры:
- `period` (string, optional) - период анализа
- `group_by` (string, optional) - группировка: `["search_type", "category", "day"]`

#### Пример ответа:
```json
{
  "analytics": {
    "total_searches": 1250,
    "unique_queries": 345,
    "avg_search_time_ms": 142,
    "avg_results_per_query": 18.5,
    "search_types_distribution": {
      "hybrid": 0.45,
      "vector": 0.30,
      "sql": 0.20,
      "fuzzy": 0.05
    },
    "top_categories": [
      {"category": "Cement", "searches": 420},
      {"category": "Steel", "searches": 315}
    ]
  },
  "period": "week"
}
```

### POST /api/v1/search/fuzzy
Специализированный эндпоинт для нечеткого поиска с настраиваемыми алгоритмами.

#### Параметры запроса:
```json
{
  "query": "портландцмент", 
  "algorithms": ["levenshtein", "sequence_matcher"],
  "similarity_threshold": 0.6,
  "max_distance": 3,
  "field_weights": {
    "name": 0.4,
    "description": 0.3,
    "use_category": 0.2,
    "sku": 0.1
  }
}
```

## 🔍 Базовый поиск / Basic Search

### POST /api/v1/search
Простой семантический поиск материалов (legacy endpoint).

#### Параметры запроса:
```json
{
  "query": "портландцемент",
  "limit": 10,
  "similarity_threshold": 0.7
}
```

#### Пример ответа:
```json
{
  "results": [
    {
      "id": "uuid-123",
      "name": "Портландцемент М500",
      "description": "Высококачественный цемент",
      "use_category": "Cement",
      "unit": "bag",
      "score": 0.95
    }
  ],
  "total": 1,
  "query": "портландцемент"
}
```

## 📄 Обработка прайс-листов / Price Processing

### POST /api/v1/prices/process
Загрузка и обработка прайс-листов в форматах CSV и Excel.

#### Параметры:
- `file` (file, required) - файл прайс-листа (CSV, XLS, XLSX)
- `supplier_name` (string, optional) - название поставщика
- `batch_size` (integer, optional) - размер батча для обработки (по умолчанию: 100)
- `validate_only` (boolean, optional) - только валидация без сохранения

#### Пример запроса (multipart/form-data):
```bash
curl -X POST "http://localhost:8000/api/v1/prices/process" \
  -F "file=@pricelist.xlsx" \
  -F "supplier_name=ООО Стройматериалы" \
  -F "batch_size=50"
```

#### Пример ответа:
```json
{
  "status": "success",
  "summary": {
    "total_rows": 150,
    "processed_rows": 145,
    "skipped_rows": 5,
    "created_materials": 120,
    "updated_materials": 25,
    "errors": 0
  },
  "processing_time": "2.45s",
  "supplier_name": "ООО Стройматериалы",
  "collection_name": "supplier_ooo_stroymateriay",
  "validation_errors": [],
  "warnings": [
    "Row 3: Missing description field",
    "Row 7: Unknown unit 'шт.' converted to 'pcs'"
  ]
}
```

### GET /api/v1/prices/templates
Получение шаблонов для создания прайс-листов.

#### Пример ответа:
```json
{
  "templates": {
    "csv": {
      "url": "/api/v1/prices/templates/csv",
      "filename": "pricelist_template.csv",
      "description": "CSV шаблон с обязательными полями"
    },
    "excel": {
      "url": "/api/v1/prices/templates/excel", 
      "filename": "pricelist_template.xlsx",
      "description": "Excel шаблон с примерами данных"
    }
  },
  "required_fields": ["name", "category", "unit"],
  "optional_fields": ["description", "sku", "price", "supplier"]
}
```

### POST /api/v1/prices/validate
Предварительная валидация файла прайс-листа без сохранения.

#### Параметры:
- `file` (file, required) - файл для валидации

#### Пример ответа:
```json
{
  "validation_result": {
    "is_valid": true,
    "total_rows": 100,
    "valid_rows": 95,
    "invalid_rows": 5,
    "errors": [
      {
        "row": 3,
        "field": "category",
        "error": "Category 'Unknown' is not in allowed list"
      }
    ],
    "warnings": [
      {
        "row": 7,
        "field": "unit", 
        "warning": "Unit 'шт.' will be converted to 'pcs'"
      }
    ]
  }
}
```

## 🗂️ Справочные данные / Reference Data

### Материалы / Materials

#### GET /api/v1/reference/materials
Получение списка материалов с фильтрацией и пагинацией.

#### Параметры:
- `skip` (integer, optional) - количество пропускаемых записей
- `limit` (integer, optional) - количество возвращаемых записей
- `category` (string, optional) - фильтр по категории
- `unit` (string, optional) - фильтр по единице измерения
- `search` (string, optional) - поиск по названию

#### Пример запроса:
```bash
GET /api/v1/reference/materials?category=Cement&limit=10&skip=0
```

#### Пример ответа:
```json
{
  "materials": [
    {
      "id": "uuid-123",
      "name": "Портландцемент М500",
      "description": "Высококачественный цемент",
      "use_category": "Cement",
      "unit": "bag",
      "sku": "CEM-M500-001",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 45,
  "skip": 0,
  "limit": 10
}
```

#### GET /api/v1/reference/materials/{id}
Получение конкретного материала по ID.

#### Пример ответа:
```json
{
  "id": "uuid-123",
  "name": "Портландцемент М500",
  "description": "Высококачественный цемент для строительных работ",
  "use_category": "Cement",
  "unit": "bag",
  "sku": "CEM-M500-001",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### POST /api/v1/reference/materials
Создание нового материала.

#### Параметры запроса:
```json
{
  "name": "Портландцемент М400",
  "description": "Цемент марки М400 для общестроительных работ",
  "use_category": "Cement",
  "unit": "bag",
  "sku": "CEM-M400-001"
}
```

#### Пример ответа:
```json
{
  "id": "uuid-456",
  "name": "Портландцемент М400",
  "description": "Цемент марки М400 для общестроительных работ",
  "use_category": "Cement",
  "unit": "bag", 
  "sku": "CEM-M400-001",
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### PUT /api/v1/reference/materials/{id}
Обновление существующего материала.

#### POST /api/v1/reference/materials/batch
Batch создание множества материалов.

#### Параметры запроса:
```json
{
  "materials": [
    {
      "name": "Материал 1",
      "use_category": "Cement",
      "unit": "bag"
    },
    {
      "name": "Материал 2", 
      "use_category": "Steel",
      "unit": "kg"
    }
  ],
  "batch_size": 100
}
```

#### DELETE /api/v1/reference/materials/{id}
Удаление материала по ID.

### Категории / Categories

#### GET /api/v1/reference/categories
Получение списка всех доступных категорий.

#### Пример ответа:
```json
{
  "categories": [
    {
      "name": "Cement",
      "description": "Цементы и цементные материалы",
      "materials_count": 45
    },
    {
      "name": "Steel", 
      "description": "Металлические конструкции и арматура",
      "materials_count": 32
    }
  ],
  "total": 2
}
```

#### POST /api/v1/reference/categories
Создание новой категории.

#### Параметры запроса:
```json
{
  "name": "Concrete",
  "description": "Бетонные смеси и растворы"
}
```

#### DELETE /api/v1/reference/categories/{name}
Удаление категории по названию.

### Единицы измерения / Units

#### GET /api/v1/reference/units
Получение списка всех единиц измерения.

#### Пример ответа:
```json
{
  "units": [
    {
      "name": "kg",
      "description": "Килограммы",
      "materials_count": 120
    },
    {
      "name": "bag",
      "description": "Мешки",
      "materials_count": 45
    }
  ],
  "total": 2
}
```

#### POST /api/v1/reference/units
Создание новой единицы измерения.

#### DELETE /api/v1/reference/units/{name}
Удаление единицы измерения.

## 📊 Мониторинг и диагностика / Monitoring & Health

### GET /api/v1/health
Комплексная проверка здоровья всех компонентов системы.

#### Пример ответа:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "details": "PostgreSQL connection successful"
    },
    "vector_db": {
      "status": "healthy", 
      "response_time_ms": 45,
      "details": "Qdrant connection successful, collections: 3"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 8,
      "details": "Redis connection successful, memory usage: 45MB"
    },
    "ai_service": {
      "status": "healthy",
      "response_time_ms": 156,
      "details": "OpenAI API connection successful"
    }
  },
  "overall_response_time_ms": 221
}
```

### GET /api/v1/health/detailed
Детальная диагностика каждого компонента с расширенной информацией.

#### Пример ответа:
```json
{
  "status": "healthy",
  "components": {
    "postgresql": {
      "status": "healthy",
      "connection_pool": {
        "active": 2,
        "idle": 8,
        "total": 10
      },
      "tables": {
        "materials": 1250,
        "categories": 15,
        "units": 8
      },
      "last_migration": "003_add_categories_units"
    },
    "qdrant": {
      "status": "healthy",
      "collections": [
        {
          "name": "materials",
          "vectors_count": 1250,
          "indexed_vectors": 1250,
          "points_count": 1250
        }
      ],
      "cluster_info": {
        "node_id": "node-1",
        "version": "1.7.0"
      }
    }
  }
}
```

### GET /api/v1/health/config
Проверка статуса конфигурации и подключений.

### GET /api/v1/health/metrics
Метрики производительности системы.

#### Пример ответа:
```json
{
  "metrics": {
    "requests_per_minute": 45,
    "avg_response_time_ms": 142,
    "cache_hit_rate": 0.85,
    "search_operations": {
      "total": 1250,
      "successful": 1245,
      "failed": 5,
      "avg_time_ms": 120
    },
    "database_operations": {
      "reads": 3450,
      "writes": 125,
      "avg_read_time_ms": 25,
      "avg_write_time_ms": 85
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔐 Коды ошибок и обработка

### Стандартные HTTP коды:
- `200` - Успешный запрос
- `201` - Ресурс создан
- `400` - Некорректный запрос
- `404` - Ресурс не найден
- `422` - Ошибка валидации
- `429` - Превышен лимит запросов
- `500` - Внутренняя ошибка сервера

### Формат ошибок:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for field 'category'",
    "details": {
      "field": "category",
      "value": "Unknown",
      "allowed_values": ["Cement", "Steel", "Concrete"]
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-uuid-123"
}
```

### Специфичные коды ошибок:
- `SEARCH_TIMEOUT` - Превышено время ожидания поиска
- `VECTOR_DB_UNAVAILABLE` - Векторная БД недоступна
- `FILE_TOO_LARGE` - Файл превышает лимит 50MB
- `INVALID_FILE_FORMAT` - Неподдерживаемый формат файла
- `RATE_LIMIT_EXCEEDED` - Превышен лимит запросов

## 📋 Примеры использования

### Python с requests:
```python
import requests
import json

# Продвинутый поиск
search_data = {
    "query": "цемент М500",
    "search_type": "hybrid",
    "filters": {
        "categories": ["Cement"],
        "similarity_threshold": 0.7
    },
    "pagination": {"page": 1, "page_size": 10}
}

response = requests.post(
    "http://localhost:8000/api/v1/search/advanced",
    json=search_data
)
results = response.json()
```

### JavaScript с fetch:
```javascript
// Загрузка прайс-листа
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('supplier_name', 'ООО Строймат');

fetch('http://localhost:8000/api/v1/prices/process', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Curl примеры:
```bash
# Получение популярных запросов
curl -X GET "http://localhost:8000/api/v1/search/popular-queries?limit=5"

# Создание материала
curl -X POST "http://localhost:8000/api/v1/reference/materials" \
  -H "Content-Type: application/json" \
  -d '{"name": "Цемент М500", "use_category": "Cement", "unit": "bag"}'

# Проверка здоровья системы
curl -X GET "http://localhost:8000/api/v1/health"
```

## 📊 Лимиты и ограничения

### Rate Limiting:
- **Общие запросы**: 100 запросов/минуту на IP
- **Поиск**: 50 запросов/минуту на IP
- **Загрузка файлов**: 10 запросов/минуту на IP

### Размеры данных:
- **Максимальный размер файла**: 50MB
- **Максимальный размер запроса**: 10MB
- **Максимальное количество результатов**: 1000 на запрос
- **Максимальная длина запроса**: 1000 символов

### Timeout:
- **Поиск**: 30 секунд
- **Загрузка файла**: 300 секунд
- **Health checks**: 10 секунд

## 🔧 Настройки производительности

### Кеширование:
- **Search suggestions**: 1 час TTL
- **Popular queries**: 24 часа TTL
- **Categories/Units**: 1 час TTL
- **Health checks**: 5 минут TTL

### Батчинг:
- **Batch uploads**: рекомендуется 50-100 записей
- **Vector operations**: автоматическое батчинг по 100 векторов
- **Database operations**: connection pooling с 10 соединениями

---

**📚 Документация обновлена для версии API v1**  
**🔄 Последнее обновление**: 2024-01-15  
**📧 Поддержка**: используйте систему Issues в репозитории 