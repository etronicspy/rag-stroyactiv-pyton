# 🚀 RAG Construction Materials API - Полная документация

## 📋 Обзор API

RAG Construction Materials API предоставляет мощные возможности для поиска, управления и анализа строительных материалов с использованием AI и векторных баз данных.

### 🎯 Основные возможности
- 🧠 **AI-powered семантический поиск** материалов
- 🗄️ **Векторная база данных** для быстрого поиска
- 📦 **Batch операции** для массовых загрузок
- 🏷️ **Система категорий** и единиц измерения
- 📊 **Детальная аналитика** и мониторинг
- 🔍 **Продвинутый поиск** с настройками

### 🌐 Base URL
```
https://localhost:8000/api/v1
```

---

## 🔍 Health Check & Monitoring

### `GET /health/`
🔍 **Basic Health Check** - Быстрая проверка статуса API

**Response Example:**
```json
{
    "status": "healthy",
    "service": "RAG Construction Materials API",
    "version": "1.0.0",
    "environment": "production",
    "timestamp": "2025-06-16T16:46:29.421964Z",
    "uptime_seconds": 3600
}
```

### `GET /health/detailed`
🔍 **Detailed Health Check** - Комплексная диагностика системы

**Response Example:**
```json
{
    "overall_status": "healthy",
    "timestamp": "2025-06-16T16:46:29.421964Z",
    "total_check_time_ms": 245.7,
    "service_info": {...},
    "databases": {
        "vector_db": {
            "type": "qdrant_cloud",
            "status": "healthy",
            "response_time_ms": 156.3,
            "details": {
                "collections_count": 3,
                "total_vectors": 15420,
                "memory_usage": "245MB"
            }
        }
    },
    "ai_service": {
        "type": "openai",
        "status": "healthy",
        "response_time_ms": 89.2
    }
}
```

### `GET /health/databases`
🗄️ **Database Health Check** - Проверка состояния баз данных

---

## 🔧 Materials Management

### `POST /materials/`
➕ **Create Material** - Создание нового строительного материала

**Request Body:**
```json
{
    "name": "Портландцемент М500 Д0",
    "use_category": "Цемент",
    "unit": "мешок",
    "sku": "CEM500-001",
    "description": "Высокопрочный цемент для конструкционного бетона без минеральных добавок"
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Портландцемент М500 Д0",
    "use_category": "Цемент",
    "unit": "мешок",
    "sku": "CEM500-001",
    "description": "Высокопрочный цемент для конструкционного бетона без минеральных добавок",
    "embedding": [0.023, -0.156, 0.789, ...],
    "created_at": "2025-06-16T16:46:29.421964Z",
    "updated_at": "2025-06-16T16:46:29.421964Z"
}
```

### `GET /materials/{material_id}`
🔍 **Get Material by ID** - Получение материала по идентификатору

### `PUT /materials/{material_id}`
✏️ **Update Material** - Обновление существующего материала

### `DELETE /materials/{material_id}`
🗑️ **Delete Material** - Удаление материала

**Response:**
```json
{
    "success": true,
    "message": "Material deleted successfully",
    "deleted_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-06-16T17:30:15.123456Z"
}
```

### `GET /materials/`
📋 **List Materials** - Получение списка материалов с пагинацией

**Query Parameters:**
- `skip`: Количество записей для пропуска (default: 0)
- `limit`: Максимальное количество записей (default: 10, max: 100)
- `category`: Фильтр по категории использования

---

## 🔍 Search Operations

### `GET /search/`
🔍 **Simple Material Search** - Упрощенный поиск материалов

**Query Parameters:**
- `q`: Поисковый запрос (обязательный)
- `limit`: Максимальное количество результатов (default: 10, max: 100)

**URL Example:**
```
GET /search/?q=цемент&limit=5
```

### `POST /materials/search`
🔍 **Semantic Material Search** - Семантический поиск материалов

**Request Body:**
```json
{
    "query": "цемент портландский высокой прочности",
    "limit": 20
}
```

**🔄 Fallback Strategy:**
1. **Vector Search**: Семантический поиск по embedding
2. **SQL LIKE Search**: Текстовый поиск при 0 результатах
3. **Fuzzy Matching**: Поиск с учетом опечаток

---

## 🚀 Advanced Search

### `POST /api/v1/search/advanced`
🚀 **Advanced Material Search** - Продвинутый поиск с настройками

**Request Body:**
```json
{
    "query": "цемент портландский высокой прочности",
    "search_type": "hybrid",
    "limit": 25,
    "categories": ["Цемент", "Вяжущие материалы"],
    "units": ["мешок", "т"],
    "fuzzy_threshold": 0.8
}
```

**🔧 Search Types:**
- **vector**: Семантический поиск по embedding (AI-powered)
- **sql**: Точный текстовый поиск по базе данных
- **fuzzy**: Нечеткий поиск с допуском опечаток
- **hybrid**: Комбинированный поиск (рекомендуется)

**Response:**
```json
{
    "results": [...],
    "total_count": 15,
    "search_time_ms": 245.7,
    "suggestions": [
        {
            "text": "цемент портландский М500",
            "score": 0.9,
            "type": "category"
        }
    ],
    "query_used": "цемент портландский высокой прочности",
    "search_type_used": "hybrid"
}
```

### `GET /api/v1/search/suggestions`
💡 **Search Suggestions** - Предложения для автодополнения

**Query Parameters:**
- `q`: Начало поискового запроса (min: 1 символ)
- `limit`: Максимальное количество предложений (default: 8, max: 20)

### `GET /api/v1/search/categories`
🏷️ **Available Categories** - Доступные категории для фильтрации

### `GET /api/v1/search/units`
📏 **Available Units** - Доступные единицы измерения для фильтрации

---

## 📦 Batch Operations

### `POST /materials/batch`
📦 **Batch Create Materials** - Массовое создание материалов

**Request Body:**
```json
{
    "materials": [
        {
            "name": "Портландцемент М500",
            "use_category": "Цемент",
            "unit": "мешок",
            "sku": "CEM500-001",
            "description": "Высокопрочный цемент"
        },
        {
            "name": "Кирпич керамический",
            "use_category": "Кирпич",
            "unit": "шт",
            "sku": "BRICK-001",
            "description": "Полнотелый кирпич"
        }
    ],
    "batch_size": 100
}
```

**Response:**
```json
{
    "success": true,
    "total_processed": 2,
    "successful_materials": [...],
    "failed_materials": [...],
    "processing_time_seconds": 45.6,
    "successful_count": 1,
    "failed_count": 1,
    "success_rate": 50.0,
    "errors": []
}
```

### `POST /materials/import`
📥 **Import Materials from JSON** - Импорт материалов из JSON файла

**Request Body:**
```json
{
    "materials": [
        {
            "sku": "CEM500-001",
            "name": "Портландцемент М500 Д0"
        },
        {
            "sku": "BRICK-001", 
            "name": "Кирпич керамический полнотелый"
        }
    ],
    "default_use_category": "Строительные материалы",
    "default_unit": "единица",
    "batch_size": 100
}
```

---

## 🏷️ Reference Data Management

### Categories

#### `POST /reference/categories/`
🏷️ **Create Category** - Создание новой категории материалов

**Request Body:**
```json
{
    "name": "Цемент",
    "description": "Вяжущие материалы на основе портландцемента для создания бетонных смесей"
}
```

#### `GET /reference/categories/`
📋 **List Categories** - Получение всех категорий материалов

#### `DELETE /reference/categories/{category_id}`
🗑️ **Delete Category** - Удаление категории материалов

### Units

#### `POST /reference/units/`
📏 **Create Unit** - Создание новой единицы измерения

**Request Body:**
```json
{
    "name": "м³",
    "description": "Кубический метр - единица измерения объема сыпучих материалов"
}
```

#### `GET /reference/units/`
📋 **List Units** - Получение всех единиц измерения

#### `DELETE /reference/units/{unit_id}`
🗑️ **Delete Unit** - Удаление единицы измерения

---

## 📊 Response Status Codes

### Success Codes
- **200 OK**: Запрос выполнен успешно
- **201 Created**: Ресурс создан успешно
- **207 Multi-Status**: Частичный успех (для health checks)

### Error Codes
- **400 Bad Request**: Некорректные параметры запроса
- **404 Not Found**: Ресурс не найден
- **413 Payload Too Large**: Превышен лимит размера запроса
- **500 Internal Server Error**: Внутренняя ошибка сервера
- **503 Service Unavailable**: Сервис временно недоступен

---

## 🔧 Common Data Schemas

### Material Schema
```json
{
    "id": "string (UUID)",
    "name": "string (2-200 chars)",
    "use_category": "string",
    "unit": "string",
    "sku": "string (3-50 chars, optional)",
    "description": "string (optional)",
    "embedding": "array[float] (1536 dimensions, optional)",
    "created_at": "datetime (ISO 8601)",
    "updated_at": "datetime (ISO 8601)"
}
```

### Category Schema
```json
{
    "id": "string (UUID, optional)",
    "name": "string",
    "description": "string (optional)",
    "created_at": "datetime (ISO 8601)",
    "updated_at": "datetime (ISO 8601)"
}
```

### Unit Schema
```json
{
    "id": "string (UUID, optional)",
    "name": "string",
    "description": "string (optional)",
    "created_at": "datetime (ISO 8601)",
    "updated_at": "datetime (ISO 8601)"
}
```

---

## 🚀 Getting Started

### 1. Проверка статуса API
```bash
curl -X GET "http://localhost:8000/api/v1/health/"
```

### 2. Создание материала
```bash
curl -X POST "http://localhost:8000/api/v1/materials/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Портландцемент М500",
    "use_category": "Цемент",
    "unit": "мешок",
    "sku": "CEM500-001"
  }'
```

### 3. Поиск материалов
```bash
curl -X GET "http://localhost:8000/api/v1/search/?q=цемент&limit=10"
```

### 4. Продвинутый поиск
```bash
curl -X POST "http://localhost:8000/api/v1/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "цемент М500",
    "search_type": "hybrid",
    "limit": 20
  }'
```

---

## 🎯 Best Practices

### Performance
- Используйте `limit` параметр для ограничения результатов
- Кэшируйте результаты reference endpoints
- Используйте batch операции для массовых загрузок
- Предпочитайте GET /search/ для простых запросов

### Search Optimization
- Используйте "hybrid" search type для лучших результатов
- Добавляйте фильтры по категориям для уточнения поиска
- Используйте suggestions для улучшения UX

### Error Handling
- Всегда проверяйте статус-коды ответов
- Используйте fallback стратегии при ошибках
- Логируйте ошибки для диагностики

---

## 📞 Support & Contact

- **Documentation**: `/docs` (Swagger UI)
- **Health Check**: `/api/v1/health/`
- **OpenAPI Schema**: `/openapi.json`

---

*Документация обновлена: 2025-06-16* 