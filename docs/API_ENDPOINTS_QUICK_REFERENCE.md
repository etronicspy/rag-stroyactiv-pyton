# RAG Construction Materials API - Краткий справочник эндпоинтов

## Базовая информация

**Базовый URL**: `http://localhost:8000/api/v1`  
**Документация**: `http://localhost:8000/docs`  
**OpenAPI Schema**: `http://localhost:8000/api/v1/openapi.json`

---

## Materials API (`/materials/`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/` | Получить список материалов |
| `POST` | `/` | Создать новый материал |
| `GET` | `/{id}` | Получить материал по ID |
| `PUT` | `/{id}` | Обновить материал |
| `DELETE` | `/{id}` | Удалить материал |
| `POST` | `/upload` | Загрузить файл с материалами |
| `GET` | `/export` | Экспортировать материалы |
| `GET` | `/health` | Проверка состояния Materials API |

**Основные параметры:**
- `skip`, `limit` - пагинация
- `category`, `unit` - фильтрация
- `search` - поиск по тексту

---

## Search API (`/search/`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/` | Базовый поиск материалов |
| `POST` | `/advanced` | Продвинутый поиск с фильтрами |
| `GET` | `/suggestions` | Получить подсказки для поиска |
| `GET` | `/categories` | Список доступных категорий |
| `GET` | `/units` | Список единиц измерения |

**Типы поиска:**
- `vector` - векторный поиск
- `sql` - SQL поиск
- `fuzzy` - нечеткий поиск
- `hybrid` - гибридный поиск

---

## Enhanced Processing API (`/processing/`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/` | Запустить пакетную обработку |
| `GET` | `/status/{request_id}` | Получить статус обработки |
| `GET` | `/results/{request_id}` | Получить результаты обработки |
| `GET` | `/statistics` | Статистика обработки |
| `POST` | `/retry` | Повторить неуспешные операции |
| `DELETE` | `/cleanup` | Очистить старые записи |
| `GET` | `/health` | Проверка состояния Processing API |

**Статусы обработки:**
- `queued` - в очереди
- `processing` - выполняется
- `completed` - завершено
- `failed` - ошибка
- `cancelled` - отменено

---

## Health API (`/health/`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/` | Базовая проверка состояния |
| `GET` | `/full` | Полная диагностика системы |

**Проверяемые компоненты:**
- Database (PostgreSQL)
- Vector Database (Qdrant)
- Cache (Redis)
- AI Services (OpenAI)
- System Resources

---

## Tunnel API (`/tunnel/`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/start` | Запустить SSH туннель |
| `GET` | `/status` | Получить статус туннеля |
| `POST` | `/stop` | Остановить SSH туннель |
| `GET` | `/config` | Получить конфигурацию туннеля |
| `GET` | `/health` | Проверка состояния Tunnel API |

**Статусы туннеля:**
- `connected` - подключен
- `disconnected` - отключен
- `connecting` - подключается
- `error` - ошибка

---

## Reference API (`/reference/`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/categories` | Получить все категории |
| `GET` | `/units` | Получить все единицы измерения |

---

## Prices API (`/prices/`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/{material_id}` | Получить цены материала |
| `PUT` | `/{material_id}` | Обновить цену материала |

---

## Быстрые примеры

### Создать материал
```bash
curl -X POST "http://localhost:8000/api/v1/materials/" \
  -H "Content-Type: application/json" \
  -d '{"name":"Цемент М400","category":"cement","unit":"т","price":5500}'
```

### Найти материалы
```bash
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{"query":"цемент","search_type":"hybrid","limit":10}'
```

### Запустить пакетную обработку
```bash
curl -X POST "http://localhost:8000/api/v1/processing/" \
  -H "Content-Type: application/json" \
  -d '{"materials":[{"name":"Материал 1","category":"cement","price":100}]}'
```

### Проверить состояние системы
```bash
curl "http://localhost:8000/api/v1/health/full"
```

### Загрузить файл с материалами
```bash
curl -X POST -F "file=@materials.xlsx" \
  "http://localhost:8000/api/v1/materials/upload"
```

---

## Коды ответов

| Код | Описание |
|-----|----------|
| `200` | Успешно |
| `201` | Создано |
| `400` | Некорректный запрос |
| `404` | Не найдено |
| `422` | Ошибка валидации |
| `500` | Внутренняя ошибка |

---

## Формат стандартного ответа

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

---

## Полезные ссылки

- [Полная документация API](./API_ENDPOINTS_COMPLETE.md)
- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)
- [OpenAPI Schema](http://localhost:8000/api/v1/openapi.json)

**Версия**: 1.0.0  
**Обновлено**: 2024-01-15