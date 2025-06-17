# 🚀 RAG Construction Materials API - Документация

## 📋 Обзор

API для управления и семантического поиска строительных материалов с использованием векторных баз данных и AI-эмбеддингов.

**Base URL**: `http://localhost:8000/api/v1`

---

## 🏥 Health & Monitoring

### `GET /health/`
Базовая проверка статуса API

**Response:**
```json
{
    "status": "healthy",
    "service": "RAG Construction Materials API",
    "version": "1.0.0",
    "timestamp": "2025-06-16T16:46:29.421964Z"
}
```

### `GET /health/full` 
Полная диагностика всех систем

**Response:**
```json
{
    "overall_status": "healthy",
    "databases": {
        "vector_db": {
            "type": "qdrant_cloud",
            "status": "healthy",
            "response_time_ms": 156.3
        },
        "relational_db": {
            "type": "postgresql",
            "status": "healthy"
        }
    },
    "connection_pools": {
        "qdrant_pool": {"status": "healthy"},
        "postgresql_pool": {"status": "healthy"}
    }
}
```

---

## 📦 Materials Management

### `POST /materials/`
Создание нового материала

**Request:**
```json
{
    "name": "Портландцемент М500",
    "use_category": "Цемент",
    "unit": "мешок",
    "description": "Высокопрочный цемент"
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Портландцемент М500",
    "use_category": "Цемент",
    "unit": "мешок",
    "embedding": [0.023, -0.156, ...],
    "created_at": "2025-06-16T16:46:29.421964Z"
}
```

### `GET /materials/{id}`
Получение материала по ID

### `PUT /materials/{id}`
Обновление материала

### `DELETE /materials/{id}` 
Удаление материала

### `GET /materials/`
Список материалов с пагинацией

**Parameters:**
- `skip`: пропустить записи (default: 0)
- `limit`: максимум записей (default: 10, max: 100)
- `category`: фильтр по категории

### `POST /materials/batch`
Пакетное создание материалов

### `POST /materials/import`
Импорт материалов из JSON

---

## 🔍 Search Operations

### `GET /search/`
Простой поиск материалов

**Parameters:**
- `q`: поисковый запрос (обязательный)
- `limit`: максимум результатов (default: 10)

**Example:**
```
GET /search/?q=цемент&limit=5
```

### `POST /search/advanced`
Продвинутый поиск с настройками

**Request:**
```json
{
    "query": "высокопрочный цемент для фундамента",
    "search_type": "hybrid",
    "limit": 25,
    "categories": ["Цемент"],
    "units": ["мешок", "т"]
}
```

**Search Types:**
- `vector`: семантический поиск (AI-powered)
- `sql`: точный текстовый поиск
- `fuzzy`: нечеткий поиск с опечатками
- `hybrid`: комбинированный (рекомендуется)

### `GET /search/suggestions`
Автодополнение поиска

### `GET /search/categories`
Доступные категории материалов

### `GET /search/units`
Единицы измерения

---

## 💰 Price Management

### `POST /prices/process`
Обработка прайс-листа

**Request:**
```bash
curl -X POST "/api/v1/prices/process" \
  -F "file=@pricelist.csv" \
  -F "supplier_id=SUPPLIER001"
```

### `GET /prices/{supplier_id}/latest`
Последний прайс-лист поставщика

### `GET /prices/{supplier_id}/all` 
Все прайс-листы поставщика

### `DELETE /prices/{supplier_id}`
Удаление прайс-листов

### `PATCH /prices/{supplier_id}/product/{id}/process`
Отметить продукт как обработанный

---

## 📚 Reference Data

### `GET /reference/categories/`
Список категорий

### `POST /reference/categories/`
Создание категории

**Request:**
```json
{
    "name": "Кирпич",
    "description": "Керамические и силикатные кирпичи"
}
```

### `DELETE /reference/categories/{id}`
Удаление категории

### `GET /reference/units/`
Список единиц измерения

### `POST /reference/units/`
Создание единицы измерения

### `DELETE /reference/units/{id}`
Удаление единицы

---

## 🔄 Fallback Strategy

API использует fallback стратегию для максимальной надежности:

1. **Vector Search** → семантический поиск в Qdrant
2. **SQL LIKE Search** → если 0 результатов, SQL поиск
3. **Mock Mode** → если БД недоступна

---

## 📊 Response Codes

- `200` - Успешно
- `201` - Создано
- `400` - Ошибка валидации
- `404` - Не найдено
- `500` - Ошибка сервера
- `503` - Сервис недоступен

---

## 🚀 Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

**Обновлено**: $(date +%Y-%m-%d) 