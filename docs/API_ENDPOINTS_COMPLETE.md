# RAG Construction Materials API - Полная документация эндпоинтов

## Обзор

RAG Construction Materials API предоставляет комплексное решение для управления строительными материалами с поддержкой векторного поиска, пакетной обработки и интеллектуальной аналитики.

**Базовый URL**: `http://localhost:8000/api/v1`

**Версия API**: 1.0.0

**Документация Swagger**: `http://localhost:8000/docs`

## Содержание

1. [Materials API](#materials-api) - Управление материалами
2. [Search API](#search-api) - Поиск и фильтрация
3. [Enhanced Processing API](#enhanced-processing-api) - Пакетная обработка
4. [Health API](#health-api) - Мониторинг состояния
5. [Tunnel API](#tunnel-api) - Управление SSH туннелем
6. [Reference API](#reference-api) - Справочные данные
7. [Prices API](#prices-api) - Управление ценами
8. [Модели данных](#модели-данных)
9. [Коды ошибок](#коды-ошибок)

---

## Materials API

**Базовый путь**: `/api/v1/materials/`

Управление строительными материалами с поддержкой CRUD операций, загрузки файлов и экспорта данных.

### 1. Получить список материалов

```http
GET /api/v1/materials/
```

**Параметры запроса:**
- `skip` (int, optional): Количество записей для пропуска (по умолчанию: 0)
- `limit` (int, optional): Максимальное количество записей (по умолчанию: 100, макс: 1000)
- `category` (str, optional): Фильтр по категории
- `unit` (str, optional): Фильтр по единице измерения
- `search` (str, optional): Поисковый запрос

**Пример запроса:**
```bash
curl "http://localhost:8000/api/v1/materials/?skip=0&limit=10&category=cement"
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "materials": [
      {
        "id": "uuid-string",
        "name": "Цемент М400",
        "category": "cement",
        "unit": "т",
        "price": 5500.00,
        "description": "Портландцемент марки М400",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 150,
    "skip": 0,
    "limit": 10
  },
  "message": "Materials retrieved successfully"
}
```

### 2. Создать материал

```http
POST /api/v1/materials/
```

**Тело запроса:**
```json
{
  "name": "Кирпич керамический",
  "category": "brick",
  "unit": "шт",
  "price": 15.50,
  "description": "Кирпич керамический рядовой",
  "properties": {
    "size": "250x120x65",
    "weight": "2.5 кг",
    "strength": "М150"
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "id": "new-uuid-string",
    "name": "Кирпич керамический",
    "category": "brick",
    "unit": "шт",
    "price": 15.50,
    "description": "Кирпич керамический рядовой",
    "properties": {
      "size": "250x120x65",
      "weight": "2.5 кг",
      "strength": "М150"
    },
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  },
  "message": "Material created successfully"
}
```

### 3. Получить материал по ID

```http
GET /api/v1/materials/{material_id}
```

**Параметры пути:**
- `material_id` (str): UUID материала

**Ответ:** Аналогичен созданию материала

### 4. Обновить материал

```http
PUT /api/v1/materials/{material_id}
```

**Тело запроса:** Аналогично созданию материала

### 5. Удалить материал

```http
DELETE /api/v1/materials/{material_id}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Material deleted successfully"
}
```

### 6. Загрузить файл с материалами

```http
POST /api/v1/materials/upload
```

**Content-Type**: `multipart/form-data`

**Параметры:**
- `file`: Файл (Excel, CSV, JSON)
- `file_type` (optional): Тип файла (auto-detect если не указан)
- `batch_size` (optional): Размер пакета для обработки (по умолчанию: 100)

**Пример запроса:**
```bash
curl -X POST \
  -F "file=@materials.xlsx" \
  -F "batch_size=50" \
  "http://localhost:8000/api/v1/materials/upload"
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "upload_id": "upload-uuid",
    "filename": "materials.xlsx",
    "total_rows": 500,
    "processed_rows": 500,
    "successful_imports": 485,
    "failed_imports": 15,
    "processing_time": 45.2,
    "errors": [
      {
        "row": 23,
        "error": "Invalid price format",
        "data": {"name": "Material X", "price": "invalid"}
      }
    ]
  },
  "message": "File uploaded and processed successfully"
}
```

### 7. Экспортировать материалы

```http
GET /api/v1/materials/export
```

**Параметры запроса:**
- `format` (str): Формат экспорта (excel, csv, json)
- `category` (str, optional): Фильтр по категории
- `unit` (str, optional): Фильтр по единице измерения
- `include_properties` (bool, optional): Включить дополнительные свойства

**Ответ:** Файл в указанном формате

### 8. Проверка состояния Materials API

```http
GET /api/v1/materials/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "database_connection": "ok",
  "vector_db_connection": "ok",
  "cache_status": "ok",
  "total_materials": 1250,
  "version": "1.0.0"
}
```

---

## Search API

**Базовый путь**: `/api/v1/search/`

Интеллектуальный поиск материалов с поддержкой векторного поиска, фильтрации и аналитики.

### 1. Базовый поиск

```http
POST /api/v1/search/
```

**Тело запроса:**
```json
{
  "query": "цемент портландский",
  "search_type": "hybrid",
  "limit": 20,
  "categories": ["cement", "concrete"],
  "units": ["т", "кг"],
  "fuzzy_threshold": 0.7
}
```

**Параметры:**
- `query` (str): Поисковый запрос
- `search_type` (str): Тип поиска (vector, sql, fuzzy, hybrid)
- `limit` (int): Максимальное количество результатов (по умолчанию: 10)
- `categories` (list, optional): Фильтр по категориям
- `units` (list, optional): Фильтр по единицам измерения
- `fuzzy_threshold` (float, optional): Порог нечеткого поиска (0.0-1.0)

**Ответ:**
```json
{
  "success": true,
  "data": {
    "materials": [
      {
        "id": "uuid-string",
        "name": "Цемент портландский М400",
        "category": "cement",
        "unit": "т",
        "price": 5500.00,
        "description": "Портландцемент общестроительного назначения",
        "similarity_score": 0.95,
        "match_type": "semantic"
      }
    ],
    "total": 15,
    "search_time": 0.045,
    "suggestions": [
      "цемент м500",
      "портландцемент",
      "цемент белый"
    ],
    "query_params": {
      "query": "цемент портландский",
      "search_type": "hybrid",
      "applied_filters": {
        "categories": ["cement"],
        "units": ["т"]
      }
    }
  },
  "message": "Search completed successfully"
}
```

### 2. Продвинутый поиск

```http
POST /api/v1/search/advanced
```

**Тело запроса:**
```json
{
  "query": "кирпич красный",
  "filters": {
    "categories": ["brick"],
    "units": ["шт", "м3"],
    "price_range": {
      "min": 10.0,
      "max": 50.0
    },
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "sku_pattern": "BR-*",
    "min_similarity": 0.8
  },
  "sorting": [
    {
      "field": "price",
      "direction": "asc"
    },
    {
      "field": "name",
      "direction": "asc"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 25
  },
  "highlighting": {
    "enabled": true,
    "fields": ["name", "description"]
  },
  "analytics": {
    "include_facets": true,
    "include_aggregations": true
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "materials": [
      {
        "id": "uuid-string",
        "name": "<em>Кирпич</em> керамический <em>красный</em>",
        "category": "brick",
        "unit": "шт",
        "price": 25.50,
        "similarity_score": 0.92,
        "highlighted_fields": {
          "name": "<em>Кирпич</em> керамический <em>красный</em>",
          "description": "<em>Кирпич</em> для кладки стен"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "size": 25,
      "total": 45,
      "pages": 2
    },
    "facets": {
      "categories": {
        "brick": 45,
        "block": 12
      },
      "price_ranges": {
        "10-20": 15,
        "20-30": 20,
        "30-50": 10
      }
    },
    "aggregations": {
      "avg_price": 28.75,
      "min_price": 15.00,
      "max_price": 45.00
    },
    "search_time": 0.078
  },
  "message": "Advanced search completed successfully"
}
```

### 3. Получить подсказки для поиска

```http
GET /api/v1/search/suggestions
```

**Параметры запроса:**
- `q` (str): Частичный поисковый запрос
- `limit` (int, optional): Максимальное количество подсказок (по умолчанию: 10)
- `category` (str, optional): Фильтр по категории

**Пример запроса:**
```bash
curl "http://localhost:8000/api/v1/search/suggestions?q=цем&limit=5"
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "text": "цемент м400",
        "type": "material_name",
        "frequency": 150,
        "category": "cement"
      },
      {
        "text": "цемент портландский",
        "type": "material_name",
        "frequency": 120,
        "category": "cement"
      },
      {
        "text": "цемент белый",
        "type": "material_name",
        "frequency": 85,
        "category": "cement"
      }
    ],
    "query": "цем",
    "total_suggestions": 3
  },
  "message": "Suggestions retrieved successfully"
}
```

### 4. Получить список категорий

```http
GET /api/v1/search/categories
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "name": "cement",
        "display_name": "Цемент",
        "count": 150,
        "description": "Цементы и вяжущие материалы"
      },
      {
        "name": "brick",
        "display_name": "Кирпич",
        "count": 200,
        "description": "Кирпич и блоки"
      }
    ],
    "total_categories": 15
  },
  "message": "Categories retrieved successfully"
}
```

### 5. Получить список единиц измерения

```http
GET /api/v1/search/units
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "units": [
      {
        "name": "т",
        "display_name": "Тонна",
        "count": 300,
        "type": "weight"
      },
      {
        "name": "м3",
        "display_name": "Кубический метр",
        "count": 250,
        "type": "volume"
      },
      {
        "name": "шт",
        "display_name": "Штука",
        "count": 400,
        "type": "piece"
      }
    ],
    "total_units": 12
  },
  "message": "Units retrieved successfully"
}
```

---

## Enhanced Processing API

**Базовый путь**: `/api/v1/processing/`

Асинхронная пакетная обработка материалов с мониторингом прогресса и управлением результатами.

### 1. Запустить пакетную обработку

```http
POST /api/v1/processing/
```

**Тело запроса:**
```json
{
  "materials": [
    {
      "name": "Цемент М400",
      "category": "cement",
      "unit": "т",
      "price": 5500.00,
      "description": "Портландцемент марки М400"
    },
    {
      "name": "Кирпич красный",
      "category": "brick",
      "unit": "шт",
      "price": 25.50,
      "description": "Кирпич керамический"
    }
  ],
  "processing_options": {
    "generate_embeddings": true,
    "validate_data": true,
    "enrich_metadata": true,
    "batch_size": 100,
    "priority": "normal"
  },
  "callback_url": "https://example.com/webhook/processing-complete"
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "request_id": "proc-uuid-string",
    "status": "queued",
    "total_materials": 2,
    "estimated_completion_time": "2024-01-15T12:15:00Z",
    "created_at": "2024-01-15T12:00:00Z"
  },
  "message": "Batch processing started successfully"
}
```

### 2. Получить статус обработки

```http
GET /api/v1/processing/status/{request_id}
```

**Параметры пути:**
- `request_id` (str): UUID запроса на обработку

**Ответ:**
```json
{
  "success": true,
  "data": {
    "request_id": "proc-uuid-string",
    "status": "processing",
    "progress": {
      "total": 2,
      "processed": 1,
      "successful": 1,
      "failed": 0,
      "percentage": 50.0
    },
    "current_stage": "generating_embeddings",
    "estimated_completion_time": "2024-01-15T12:10:00Z",
    "started_at": "2024-01-15T12:00:00Z",
    "processing_time": 600,
    "errors": []
  },
  "message": "Processing status retrieved successfully"
}
```

**Возможные статусы:**
- `queued` - В очереди на обработку
- `processing` - Выполняется обработка
- `completed` - Обработка завершена успешно
- `failed` - Обработка завершена с ошибками
- `cancelled` - Обработка отменена

### 3. Получить результаты обработки

```http
GET /api/v1/processing/results/{request_id}
```

**Параметры запроса:**
- `page` (int, optional): Номер страницы (по умолчанию: 1)
- `size` (int, optional): Размер страницы (по умолчанию: 50)
- `status_filter` (str, optional): Фильтр по статусу (success, failed, all)

**Ответ:**
```json
{
  "success": true,
  "data": {
    "request_id": "proc-uuid-string",
    "total_materials": 2,
    "results": [
      {
        "material_id": "mat-uuid-1",
        "original_data": {
          "name": "Цемент М400",
          "category": "cement"
        },
        "processed_data": {
          "id": "mat-uuid-1",
          "name": "Цемент М400",
          "category": "cement",
          "embedding_vector": [0.1, 0.2, 0.3],
          "enriched_metadata": {
            "strength_class": "M400",
            "type": "portland_cement"
          }
        },
        "status": "success",
        "processing_time": 1.2,
        "created_at": "2024-01-15T12:01:00Z"
      },
      {
        "material_id": null,
        "original_data": {
          "name": "Кирпич красный",
          "category": "brick"
        },
        "processed_data": null,
        "status": "failed",
        "error": "Invalid price format",
        "processing_time": 0.5,
        "created_at": "2024-01-15T12:01:30Z"
      }
    ],
    "summary": {
      "successful": 1,
      "failed": 1,
      "total": 2
    },
    "pagination": {
      "page": 1,
      "size": 50,
      "total": 2,
      "pages": 1
    }
  },
  "message": "Processing results retrieved successfully"
}
```

### 4. Получить статистику обработки

```http
GET /api/v1/processing/statistics
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "total_requests": 150,
    "completed_requests": 140,
    "failed_requests": 8,
    "active_requests": 2,
    "success_rate": 0.933,
    "average_processing_time": 45.2,
    "total_materials_processed": 15000,
    "materials_per_hour": 1200,
    "queue_length": 5,
    "last_24h_stats": {
      "requests": 25,
      "materials": 2500,
      "success_rate": 0.96
    },
    "performance_metrics": {
      "avg_embedding_time": 0.8,
      "avg_validation_time": 0.3,
      "avg_enrichment_time": 1.2
    }
  },
  "message": "Processing statistics retrieved successfully"
}
```

### 5. Повторить обработку неуспешных материалов

```http
POST /api/v1/processing/retry
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "message": "Retry started for 15 materials",
    "retry_count": 15,
    "new_request_id": "retry-uuid-string"
  },
  "message": "Retry operation started successfully"
}
```

### 6. Очистить старые записи обработки

```http
DELETE /api/v1/processing/cleanup
```

**Параметры запроса:**
- `days_old` (int, optional): Количество дней для удаления (по умолчанию: 30)

**Ответ:**
```json
{
  "success": true,
  "data": {
    "message": "Cleanup completed: 50 records deleted",
    "deleted_count": 50,
    "days_old": 30
  },
  "message": "Cleanup operation completed successfully"
}
```

### 7. Проверка состояния Processing API

```http
GET /api/v1/processing/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "service_stats": {
    "active_jobs": 2,
    "completed_jobs": 140,
    "failed_jobs": 8,
    "queue_length": 5,
    "config": {
      "max_concurrent_batches": 10,
      "max_batch_size": 1000
    }
  },
  "version": "1.0.0"
}
```

---

## Health API

**Базовый путь**: `/api/v1/health/`

Мониторинг состояния всех компонентов системы.

### 1. Базовая проверка состояния

```http
GET /api/v1/health/
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime": 86400,
  "basic_checks": {
    "api": "ok",
    "database": "ok",
    "cache": "ok"
  }
}
```

### 2. Полная проверка состояния

```http
GET /api/v1/health/full
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime": 86400,
  "detailed_checks": {
    "database": {
      "status": "ok",
      "response_time": 0.005,
      "connection_pool": {
        "active": 5,
        "idle": 15,
        "total": 20
      }
    },
    "vector_database": {
      "status": "ok",
      "response_time": 0.012,
      "collections": {
        "materials": {
          "status": "ok",
          "points_count": 15000,
          "last_update": "2024-01-15T11:45:00Z"
        }
      }
    },
    "redis_cache": {
      "status": "ok",
      "response_time": 0.002,
      "memory_usage": "45MB",
      "connected_clients": 8
    },
    "ai_services": {
      "openai": {
        "status": "ok",
        "response_time": 0.150,
        "rate_limit_remaining": 4500
      }
    },
    "system_resources": {
      "cpu_usage": 25.5,
      "memory_usage": 68.2,
      "disk_usage": 45.0
    }
  },
  "performance_metrics": {
    "requests_per_minute": 120,
    "average_response_time": 0.085,
    "error_rate": 0.002
  }
}
```

---

## Tunnel API

**Базовый путь**: `/api/v1/tunnel/`

Управление SSH туннелем для безопасного подключения к удаленным ресурсам.

### 1. Запустить SSH туннель

```http
POST /api/v1/tunnel/start
```

**Тело запроса:**
```json
{
  "ssh_host": "remote-server.com",
  "ssh_port": 22,
  "ssh_username": "user",
  "ssh_password": "password",
  "local_port": 5432,
  "remote_host": "localhost",
  "remote_port": 5432,
  "timeout": 30
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "tunnel_id": "tunnel-uuid",
    "status": "connected",
    "local_port": 5432,
    "remote_endpoint": "remote-server.com:5432",
    "started_at": "2024-01-15T12:00:00Z",
    "connection_info": {
      "ssh_host": "remote-server.com",
      "ssh_port": 22,
      "local_bind_port": 5432
    }
  },
  "message": "SSH tunnel started successfully"
}
```

### 2. Получить статус туннеля

```http
GET /api/v1/tunnel/status
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "tunnel_id": "tunnel-uuid",
    "status": "connected",
    "uptime": 3600,
    "connection_info": {
      "ssh_host": "remote-server.com",
      "ssh_port": 22,
      "local_bind_port": 5432,
      "remote_host": "localhost",
      "remote_port": 5432
    },
    "metrics": {
      "bytes_sent": 1048576,
      "bytes_received": 2097152,
      "connections_count": 25,
      "last_activity": "2024-01-15T12:30:00Z"
    },
    "started_at": "2024-01-15T12:00:00Z"
  },
  "message": "Tunnel status retrieved successfully"
}
```

### 3. Остановить SSH туннель

```http
POST /api/v1/tunnel/stop
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "tunnel_id": "tunnel-uuid",
    "status": "disconnected",
    "final_metrics": {
      "total_uptime": 3600,
      "total_bytes_sent": 1048576,
      "total_bytes_received": 2097152,
      "total_connections": 25
    },
    "stopped_at": "2024-01-15T13:00:00Z"
  },
  "message": "SSH tunnel stopped successfully"
}
```

### 4. Получить конфигурацию туннеля

```http
GET /api/v1/tunnel/config
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "tunnel_id": "tunnel-uuid",
    "configuration": {
      "ssh_host": "remote-server.com",
      "ssh_port": 22,
      "ssh_username": "user",
      "local_port": 5432,
      "remote_host": "localhost",
      "remote_port": 5432,
      "timeout": 30,
      "keepalive": 60,
      "compression": true
    },
    "created_at": "2024-01-15T12:00:00Z"
  },
  "message": "Tunnel configuration retrieved successfully"
}
```

### 5. Проверка состояния Tunnel API

```http
GET /api/v1/tunnel/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "tunnel_status": "connected",
  "connection_health": "stable",
  "metrics": {
    "uptime": 3600,
    "connection_count": 25,
    "last_heartbeat": "2024-01-15T12:30:00Z"
  },
  "version": "1.0.0"
}
```

---

## Reference API

**Базовый путь**: `/api/v1/reference/`

Справочные данные для категорий и единиц измерения.

### 1. Получить все категории

```http
GET /api/v1/reference/categories
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": "cat-uuid-1",
        "name": "cement",
        "display_name": "Цемент",
        "description": "Цементы и вяжущие материалы",
        "parent_id": null,
        "level": 0,
        "materials_count": 150,
        "created_at": "2024-01-01T00:00:00Z"
      },
      {
        "id": "cat-uuid-2",
        "name": "brick",
        "display_name": "Кирпич",
        "description": "Кирпич и блоки",
        "parent_id": null,
        "level": 0,
        "materials_count": 200,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 15
  },
  "message": "Categories retrieved successfully"
}
```

### 2. Получить все единицы измерения

```http
GET /api/v1/reference/units
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "units": [
      {
        "id": "unit-uuid-1",
        "name": "т",
        "display_name": "Тонна",
        "description": "Единица измерения массы",
        "type": "weight",
        "base_unit": "кг",
        "conversion_factor": 1000,
        "materials_count": 300,
        "created_at": "2024-01-01T00:00:00Z"
      },
      {
        "id": "unit-uuid-2",
        "name": "м3",
        "display_name": "Кубический метр",
        "description": "Единица измерения объема",
        "type": "volume",
        "base_unit": "л",
        "conversion_factor": 1000,
        "materials_count": 250,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 12
  },
  "message": "Units retrieved successfully"
}
```

---

## Prices API

**Базовый путь**: `/api/v1/prices/`

Управление ценами материалов с поддержкой истории изменений.

### 1. Получить цены материала

```http
GET /api/v1/prices/{material_id}
```

**Параметры пути:**
- `material_id` (str): UUID материала

**Параметры запроса:**
- `include_history` (bool, optional): Включить историю цен
- `date_from` (str, optional): Начальная дата для истории (ISO format)
- `date_to` (str, optional): Конечная дата для истории (ISO format)

**Ответ:**
```json
{
  "success": true,
  "data": {
    "material_id": "mat-uuid-1",
    "current_price": 5500.00,
    "currency": "RUB",
    "last_updated": "2024-01-15T10:00:00Z",
    "price_history": [
      {
        "price": 5500.00,
        "effective_date": "2024-01-15T10:00:00Z",
        "change_reason": "market_update",
        "updated_by": "system"
      },
      {
        "price": 5300.00,
        "effective_date": "2024-01-01T00:00:00Z",
        "change_reason": "initial_price",
        "updated_by": "admin"
      }
    ],
    "price_statistics": {
      "min_price": 5300.00,
      "max_price": 5500.00,
      "avg_price": 5400.00,
      "price_changes_count": 2
    }
  },
  "message": "Material prices retrieved successfully"
}
```

### 2. Обновить цену материала

```http
PUT /api/v1/prices/{material_id}
```

**Тело запроса:**
```json
{
  "price": 5600.00,
  "effective_date": "2024-01-16T00:00:00Z",
  "change_reason": "supplier_update",
  "notes": "Цена обновлена согласно новому прайс-листу поставщика"
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "material_id": "mat-uuid-1",
    "old_price": 5500.00,
    "new_price": 5600.00,
    "price_change": 100.00,
    "price_change_percent": 1.82,
    "effective_date": "2024-01-16T00:00:00Z",
    "updated_at": "2024-01-15T15:00:00Z"
  },
  "message": "Material price updated successfully"
}
```

---

## Модели данных

### StandardResponse
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### Material
```json
{
  "id": "uuid-string",
  "name": "Название материала",
  "category": "category_name",
  "unit": "unit_name",
  "price": 100.50,
  "description": "Описание материала",
  "properties": {
    "custom_field": "value"
  },
  "sku": "SKU-12345",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### SearchResult
```json
{
  "materials": [],
  "total": 100,
  "search_time": 0.045,
  "suggestions": [],
  "facets": {},
  "aggregations": {}
}
```

### ProcessingStatus
```json
{
  "request_id": "uuid-string",
  "status": "processing",
  "progress": {
    "total": 100,
    "processed": 50,
    "successful": 45,
    "failed": 5,
    "percentage": 50.0
  },
  "current_stage": "generating_embeddings",
  "estimated_completion_time": "2024-01-15T12:30:00Z"
}
```

---

## Коды ошибок

### HTTP Status Codes

- **200 OK** - Успешный запрос
- **201 Created** - Ресурс создан успешно
- **400 Bad Request** - Некорректный запрос
- **401 Unauthorized** - Требуется аутентификация
- **403 Forbidden** - Доступ запрещен
- **404 Not Found** - Ресурс не найден
- **422 Unprocessable Entity** - Ошибка валидации данных
- **429 Too Many Requests** - Превышен лимит запросов
- **500 Internal Server Error** - Внутренняя ошибка сервера
- **503 Service Unavailable** - Сервис временно недоступен

### Формат ошибки
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "field": "price",
      "issue": "must be greater than 0"
    }
  },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### Основные коды ошибок

- **VALIDATION_ERROR** - Ошибка валидации входных данных
- **RESOURCE_NOT_FOUND** - Запрашиваемый ресурс не найден
- **DUPLICATE_RESOURCE** - Попытка создания дублирующего ресурса
- **DATABASE_ERROR** - Ошибка базы данных
- **EXTERNAL_SERVICE_ERROR** - Ошибка внешнего сервиса
- **RATE_LIMIT_EXCEEDED** - Превышен лимит запросов
- **PROCESSING_ERROR** - Ошибка обработки данных
- **TUNNEL_CONNECTION_ERROR** - Ошибка SSH туннеля

---

## Примеры использования

### Создание и поиск материала

```bash
# 1. Создать материал
curl -X POST "http://localhost:8000/api/v1/materials/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Цемент М500",
    "category": "cement",
    "unit": "т",
    "price": 6000.00,
    "description": "Портландцемент высокой прочности"
  }'

# 2. Найти материал
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "цемент м500",
    "search_type": "hybrid",
    "limit": 10
  }'
```

### Пакетная обработка материалов

```bash
# 1. Запустить обработку
curl -X POST "http://localhost:8000/api/v1/processing/" \
  -H "Content-Type: application/json" \
  -d '{
    "materials": [
      {"name": "Материал 1", "category": "cement", "price": 100},
      {"name": "Материал 2", "category": "brick", "price": 200}
    ],
    "processing_options": {
      "generate_embeddings": true,
      "validate_data": true
    }
  }'

# 2. Проверить статус (используйте request_id из ответа)
curl "http://localhost:8000/api/v1/processing/status/{request_id}"

# 3. Получить результаты
curl "http://localhost:8000/api/v1/processing/results/{request_id}"
```

### Мониторинг состояния системы

```bash
# Базовая проверка
curl "http://localhost:8000/api/v1/health/"

# Полная диагностика
curl "http://localhost:8000/api/v1/health/full"

# Статистика обработки
curl "http://localhost:8000/api/v1/processing/statistics"
```

---

## Заключение

RAG Construction Materials API предоставляет мощный и гибкий интерфейс для управления строительными материалами. API поддерживает:

- **CRUD операции** с материалами
- **Интеллектуальный поиск** с векторными эмбеддингами
- **Пакетную обработку** больших объемов данных
- **Мониторинг** состояния всех компонентов
- **Безопасное подключение** через SSH туннели
- **Управление справочными данными**
- **Историю изменения цен**

Для получения актуальной документации и интерактивного тестирования используйте Swagger UI по адресу: `http://localhost:8000/docs`

**Версия документации**: 1.0.0  
**Дата обновления**: 2024-01-15