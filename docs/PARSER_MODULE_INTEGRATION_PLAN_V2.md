# Parser Module Integration Plan V2.0

## 🎯 Executive Summary

**Status**: В ПЛАНИРОВАНИИ (предыдущий план имел критические недостатки)

**Цель**: Полная интеграция `parser_module/` в архитектуру проекта с устранением sys.path хаков, соблюдением всех правил проекта и созданием production-ready решения.

**Критические проблемы предыдущего плана**:
- Неполная интеграция с конфигурационной системой
- Игнорирование правил именования файлов (75+ конфликтов)
- Отсутствие интеграции с модульной системой логирования
- Недооценка времени выполнения (4-6ч → 12-16ч)
- Отсутствие миграционной стратегии

**Новая реалистичная оценка**: 12-16 часов разработки

## 🏗️ Архитектурная Цель

### Финальная структура интеграции:
```
core/parsers/
├── __init__.py                     # Экспорты и интерфейсы
├── interfaces/
│   ├── __init__.py
│   ├── parser_interface.py         # ABC интерфейсы
│   └── ai_parser_interface.py      # AI-специфичные интерфейсы
├── services/
│   ├── __init__.py
│   ├── ai_parser_service.py        # Основной AI парсинг
│   ├── material_parser_service.py  # Парсинг материалов
│   └── batch_parser_service.py     # Батч обработка
├── config/
│   ├── __init__.py
│   ├── parser_config_manager.py    # Конфигурация парсера
│   ├── system_prompts_manager.py   # Управление промптами
│   └── units_config_manager.py     # Конфигурация единиц
└── README.md                       # Документация модуля
```

## 📋 Подробный План Выполнения

### **Этап 1: Архитектурная Подготовка (3-4 часа)**

#### **Шаг 1.1: Аудит конфликтов имен файлов (30 минут)**
- [ ] Запустить `scripts/check_filename_conflicts.py --strict`
- [ ] Проверить все предлагаемые имена файлов на конфликты
- [ ] Создать finalized список безопасных имен
- [ ] Добавить в `.cursor/rules/filename-conflicts.mdc` специфичные правила для парсеров

#### **Шаг 1.2: Интеграция с конфигурационной системой (2 часа)**
- [ ] Создать `core/config/parsers.py` с полной конфигурацией парсера
- [ ] Интегрировать с `core/config/factories.py` для создания клиентов
- [ ] Добавить все parser настройки в `env.example`
- [ ] Создать валидацию через Pydantic в `core/config/parsers.py`
- [ ] Добавить константы в `core/config/constants.py`:
  ```python
  class ParserConstants:
      DEFAULT_BATCH_SIZE = 10
      MAX_RETRY_ATTEMPTS = 3
      CONFIDENCE_THRESHOLD = 0.85
      EMBEDDING_CACHE_TTL = 3600
  ```

#### **Шаг 1.3: Создание ABC интерфейсов (1 час)**
- [ ] `core/parsers/interfaces/parser_interface.py` - базовый интерфейс
- [ ] `core/parsers/interfaces/ai_parser_interface.py` - AI-специфичный интерфейс
- [ ] Определить контракты для всех parser операций
- [ ] Добавить типизацию с Generic типами

#### **Шаг 1.4: Интеграция с системой логирования (30 минут)**
- [ ] Создать `core/logging/specialized/parsers/` директорию
- [ ] Добавить специализированные логгеры для AI операций
- [ ] Интеграция с `core/logging/metrics/` для отслеживания производительности
- [ ] Создать correlation ID для трассировки batch операций

### **Этап 2: Перенос и Адаптация Кода (4-5 часов)**

#### **Шаг 2.1: Создание целевой структуры (1 час)**
- [ ] Создать все директории `core/parsers/`
- [ ] Создать `__init__.py` файлы с экспортами
- [ ] Перенести файлы с безопасными именами:
  - `ai_parser.py` → `core/parsers/services/ai_parser_service.py`
  - `material_parser.py` → `core/parsers/services/material_parser_service.py`
  - `parser_config.py` → `core/parsers/config/parser_config_manager.py`
  - `system_prompts.py` → `core/parsers/config/system_prompts_manager.py`
  - `units_config.py` → `core/parsers/config/units_config_manager.py`

#### **Шаг 2.2: Адаптация конфигурации (2 часа)**
- [ ] Заменить все hardcoded значения константами
- [ ] Интегрировать с `core/config/base.py` через dependency injection
- [ ] Добавить `@lru_cache` для клиентов OpenAI
- [ ] Создать factory методы в `core/config/factories.py`
- [ ] Добавить валидацию всех env переменных

#### **Шаг 2.3: Интеграция с логированием (1 час)**
- [ ] Заменить все `print()` на structured logging
- [ ] Добавить correlation ID для трассировки
- [ ] Интегрировать с `core/logging/specialized/` логгерами
- [ ] Добавить метрики производительности

#### **Шаг 2.4: Реализация ABC интерфейсов (1 час)**
- [ ] Адаптировать все parser классы к ABC интерфейсам
- [ ] Добавить type hints для всех методов
- [ ] Создать generic типы для результатов парсинга
- [ ] Добавить docstrings в Google style

### **Этап 3: Миграция Зависимостей (2-3 часа)**

#### **Шаг 3.1: Создание миграционной совместимости (1 час)**
- [ ] Создать `core/parsers/legacy_compatibility.py`
- [ ] Добавить compatibility imports в `core/parsers/__init__.py`
- [ ] Создать deprecation warnings для старых импортов
- [ ] Документировать миграционный путь

#### **Шаг 3.2: Обновление services/enhanced_parser_integration.py (1 час)**
- [ ] **УДАЛИТЬ** все sys.path хаки
- [ ] Заменить на clean imports:
  ```python
  from core.parsers.services.material_parser_service import MaterialParserService
  from core.parsers.config.parser_config_manager import ParserConfigManager
  ```
- [ ] Адаптировать к новой архитектуре
- [ ] Добавить dependency injection

#### **Шаг 3.3: Обновление зависимых сервисов (1 час)**
- [ ] Обновить `services/material_processing_pipeline.py`
- [ ] Обновить все imports в `services/__init__.py`
- [ ] Проверить все файлы на наличие прямых импортов из `parser_module/`
- [ ] Обновить health checks в `api/routes/health_unified.py`

### **Этап 4: Тестирование и Валидация (2-3 часа)**

#### **Шаг 4.1: Unit тесты (1 час)**
- [ ] Создать `tests/unit/parsers/` директорию
- [ ] `test_ai_parser_service.py` - тесты AI парсера
- [ ] `test_material_parser_service.py` - тесты материалов
- [ ] `test_parser_config_manager.py` - тесты конфигурации
- [ ] Mock все внешние API (OpenAI, embeddings)
- [ ] Добавить parametrized тесты для edge cases

#### **Шаг 4.2: Integration тесты (1 час)**
- [ ] Создать `tests/integration/test_parser_integration.py`
- [ ] Тестирование с реальными API (feature flags)
- [ ] Тестирование конфигурационной системы
- [ ] Проверка логирования и метрик
- [ ] Batch processing тесты

#### **Шаг 4.3: Performance тесты (1 час)**
- [ ] Создать `tests/performance/test_parser_performance.py`
- [ ] Бенчмарки для batch обработки
- [ ] Memory usage тесты
- [ ] Timeout и retry тесты
- [ ] Сравнение с предыдущей версией

### **Этап 5: Документация и Финализация (1-2 часа)**

#### **Шаг 5.1: Создание документации (1 час)**
- [ ] Обновить `docs/ARCHITECTURE.md` с новой parser архитектурой
- [ ] Создать `docs/PARSER_MIGRATION_GUIDE.md`
- [ ] Обновить `docs/API_DOCUMENTATION.md`
- [ ] Создать examples в `core/parsers/README.md`
- [ ] Добавить OpenAPI schemas для новых endpoints

#### **Шаг 5.2: CHANGELOG и ADR (30 минут)**
- [ ] Обновить `CHANGELOG.md` под раздел "Changed"
- [ ] Создать новый ADR: `docs/adr/20241201-parser-module-integration-v2.md`
- [ ] Документировать breaking changes и миграционный путь
- [ ] Обновить version в `pyproject.toml`

#### **Шаг 5.3: Финальная очистка (30 минут)**
- [ ] Удалить `parser_module/` директорию
- [ ] Очистить неиспользуемые imports
- [ ] Запустить `make check-conflicts` финальную проверку
- [ ] Проверить все тесты проходят

## 🔥 Критические Требования Безопасности

### **Filename Safety Rules** (ОБЯЗАТЕЛЬНО)
- ✅ **НИКОГДА** не использовать: `config.py`, `types.py`, `logging.py`
- ✅ **ВСЕГДА** добавлять описательные префиксы: `parser_config_manager.py`
- ✅ **АВТОМАТИЧЕСКИ** проверять через `scripts/check_filename_conflicts.py`

### **Configuration Safety Rules** (КРИТИЧНО)
- ✅ **ПОЛНЫЙ ЗАПРЕТ** hardcoded значений
- ✅ **ОБЯЗАТЕЛЬНАЯ** валидация через Pydantic
- ✅ **ИСПОЛЬЗОВАТЬ** константы из `core/config/constants.py`
- ✅ **ИНТЕГРИРОВАТЬСЯ** с `core/config/factories.py`

### **Import Safety Rules** (КРИТИЧНО)
- ✅ **УДАЛИТЬ** все sys.path хаки
- ✅ **ИСПОЛЬЗОВАТЬ** только clean imports
- ✅ **ДОБАВИТЬ** compatibility слой для migration

## 📊 Управление Рисками

### **Высокий Риск: Breaking Changes**
- **Митигация**: Создание compatibility слоя
- **Rollback**: Восстановление `parser_module/` из git
- **Мониторинг**: Comprehensive тесты

### **Средний Риск: Performance Degradation**
- **Митигация**: Performance benchmarks
- **Rollback**: Feature flags для переключения
- **Мониторинг**: Metrics в production

### **Низкий Риск: Configuration Issues**
- **Митигация**: Валидация через Pydantic
- **Rollback**: Env переменные по умолчанию
- **Мониторинг**: Health checks

## 🎯 Критерии Успеха

### **Функциональные**
- [ ] Полное удаление sys.path хаков
- [ ] Все тесты проходят (100% coverage критичного кода)
- [ ] Нет hardcoded значений
- [ ] Интеграция с конфигурационной системой
- [ ] Соответствие filename safety rules

### **Производительные**
- [ ] Performance не хуже предыдущей версии
- [ ] Memory usage оптимизирован
- [ ] Batch processing работает корректно
- [ ] Timeout и retry логика функционирует

### **Архитектурные**
- [ ] Соответствие ABC интерфейсам
- [ ] Чистые dependency injection
- [ ] Модульная архитектура
- [ ] Comprehensive логирование

## 🚀 Post-Integration Roadmap

### **Phase 1**: Мониторинг и оптимизация (1-2 недели)
- Мониторинг performance metrics
- Оптимизация batch processing
- Сбор feedback от команды

### **Phase 2**: Расширение функциональности (2-4 недели)
- Добавление новых parser типов
- Улучшение AI промптов
- Интеграция с vector databases

### **Phase 3**: Scaling и Production (4-6 недель)
- Горизонтальное масштабирование
- Advanced caching strategies
- MLOps интеграция

---

**Автор**: AI Assistant  
**Дата**: 2024-12-01  
**Версия**: 2.0  
**Статус**: Ready for Implementation

**Предыдущий план**: `PARSER_MODULE_INTEGRATION_PLAN.md` (deprecated)  
**Связанные документы**: `docs/adr/20241001-parser-module-integration.md` 