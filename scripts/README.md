# Scripts Directory

Папка содержит вспомогательные скрипты для разработки и тестирования системы.

## Файлы

### 📊 Данные
- **`materials_database.json`** - Экспорт всех материалов из БД (62 материала, 21 категория)

### 🧪 Тестирование
- **`test_sku_assignment.py`** - Основной скрипт для тестирования назначения SKU материалам
- **`test_sku_search.py`** - Тест двухэтапного поиска SKU (векторный + фильтрация)
- **`test_sku_collection_check.py`** - Проверка коллекции материалов в Qdrant
- **`test_enhanced_storage.py`** - Тест расширенного сохранения с новыми полями (color, normalized_color, normalized_parsed_unit, unit_coefficient)

### 🔄 Обслуживание
- **`regenerate_embeddings.py`** - Регенерация эмбеддингов для всех справочных материалов

## Использование

Все скрипты должны запускаться из корня проекта:

```bash
# Запуск из корня проекта
cd /path/to/rag-stroyactiv-pyton

# Тестирование назначения SKU
python scripts/test_sku_assignment.py

# Регенерация эмбеддингов
python scripts/regenerate_embeddings.py

# Проверка коллекции
python scripts/test_sku_collection_check.py

# Тест расширенного сохранения
python scripts/test_enhanced_storage.py
```

## Статус

- ✅ Этап 5: CombinedEmbeddingService - завершен
- ✅ Этап 6: Двухэтапный поиск SKU - завершен
- ✅ Регенерация эмбеддингов - завершена (62 материала)
- ✅ Этап 7: Расширенное сохранение в БД - завершен
- ✅ Этап 8: Полный API пайплайн - завершен
- 🎯 Проект готов к продакшн использованию

## Новые скрипты

### test_stage_8_full_pipeline.py
Comprehensive тест для проверки всего Stage 8 - Full API Pipeline:
- Проверка health endpoint
- Тестирование batch processing (малые, средние, большие batch)
- Проверка статистики и мониторинга
- Тестирование валидации данных
- Проверка retry функциональности
- Тестирование concurrent requests
- Генерация детального отчета

```bash
# Запуск тестов всего pipeline
python scripts/test_stage_8_full_pipeline.py

# Проверка результатов
ls test_results/
```

**Особенности:**
- Полное покрытие всех API endpoints
- Автоматическое ожидание завершения обработки
- Детальная отчетность и статистика
- Проверка граничных случаев
- Тестирование concurrent обработки 