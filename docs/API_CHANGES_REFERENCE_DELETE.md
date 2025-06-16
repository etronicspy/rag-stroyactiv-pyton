# Изменения API для удаления категорий и единиц измерения

## Обзор изменений

Данные изменения переводят API эндпоинты удаления категорий и единиц измерения с использования имен на использование ID (UUID).

## Мотивация

1. **Уникальность**: UUID гарантирует уникальную идентификацию записи
2. **Безопасность**: Исключает случайное удаление при дубликатах имен
3. **Стандартизация**: Приводит API к единообразному использованию ID
4. **Производительность**: Удаление по ID быстрее, чем поиск по имени

## Изменения в схемах данных

### core/schemas/materials.py
- Добавлено поле `id: Optional[str] = None` в схемы `Category` и `Unit`
- ID представляет UUID из Qdrant

## Изменения в сервисах

### services/materials.py

#### CategoryService
- `create_category()`: теперь возвращает объект с заполненным ID
- `get_categories()`: возвращает категории с ID
- `delete_category(category_id: str)`: удаление только по ID

#### UnitService
- `create_unit()`: теперь возвращает объект с заполненным ID
- `get_units()`: возвращает единицы с ID
- `delete_unit(unit_id: str)`: удаление только по ID

## Изменения в API эндпоинтах

### api/routes/reference.py

#### Эндпоинты удаления
- `DELETE /api/v1/reference/categories/{category_id}` - удаление категории по ID
- `DELETE /api/v1/reference/units/{unit_id}` - удаление единицы по ID

## Примеры использования

### Создание и удаление категории по ID
```bash
# Создание
curl -X POST "http://localhost:8000/api/v1/reference/categories/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Цемент", "description": "Вяжущие материалы"}'

# Ответ содержит ID
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Цемент",
  "description": "Вяжущие материалы",
  "created_at": "2024-01-01T12:00:00.000Z",
  "updated_at": "2024-01-01T12:00:00.000Z"
}

# Удаление по ID (единственный способ)
curl -X DELETE "http://localhost:8000/api/v1/reference/categories/550e8400-e29b-41d4-a716-446655440000"
```

### Создание и удаление единицы по ID
```bash
# Создание
curl -X POST "http://localhost:8000/api/v1/reference/units/" \
     -H "Content-Type: application/json" \
     -d '{"name": "кг", "description": "Килограмм"}'

# Удаление по ID (единственный способ)
curl -X DELETE "http://localhost:8000/api/v1/reference/units/{unit_id}"
```

## ⚠️ BREAKING CHANGE

**Legacy эндпоинты удалены!**

Следующие эндпоинты больше не поддерживаются:
- ❌ `DELETE /api/v1/reference/categories/by-name/{name}`
- ❌ `DELETE /api/v1/reference/units/by-name/{name}`

## Обязательная миграция

Все существующие интеграции должны быть обновлены для использования только ID-based эндпоинтов:

### Алгоритм миграции:
1. При создании категории/единицы - сохраняйте полученный `id` из ответа
2. Используйте `id` для удаления вместо `name`
3. Обновите все скрипты и интеграции

### Пример миграции:
```bash
# СТАРЫЙ СПОСОБ (больше не работает)
DELETE /api/v1/reference/categories/by-name/Цемент

# НОВЫЙ СПОСОБ (обязательный)
DELETE /api/v1/reference/categories/550e8400-e29b-41d4-a716-446655440000
```

## Обновления в документации

- ✅ `docs/API_ENDPOINTS_TREE.md` - обновлена структура эндпоинтов
- ✅ `docs/API_DOCUMENTATION.md` - добавлены примеры для новых эндпоинтов
- ✅ `README.md` - обновлен список API эндпоинтов
- ✅ `tests/integration/test_materials_workflow.py` - обновлены тесты для использования legacy эндпоинтов

## Версионирование

⚠️ **BREAKING CHANGE** - данные изменения несовместимы с предыдущими версиями.
Legacy эндпоинты полностью удалены из API.

## Дата внесения изменений

Декабрь 2024 