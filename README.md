# 🏗️ RAG Construction Materials API

Профессиональный API для управления строительными материалами с **продвинутым семантическим поиском**, **мульти-БД поддержкой** и **интеллектуальной аналитикой**.

## 🚀 Ключевые возможности / Key Features

### 🔍 Продвинутый поиск / Advanced Search
- **🧠 4 типа поиска**: Vector (семантический), SQL (текстовый), Fuzzy (нечеткий), Hybrid (комбинированный)
- **🎯 Интеллектуальная фильтрация**: по категориям, единицам измерения, SKU паттернам, диапазонам дат
- **💡 Автодополнение**: предложения на основе популярных запросов и статистики
- **⚡ Подсветка текста**: HTML highlight найденных совпадений
- **📊 Поисковая аналитика**: детальная статистика и метрики производительности

### 🗄️ Мульти-БД архитектура / Multi-Database Architecture
- **🔵 PostgreSQL**: основная реляционная БД с Alembic миграциями
- **🟠 Векторные БД**: Qdrant (Cloud/Local), Weaviate, Pinecone с единым интерфейсом
- **🔴 Redis**: кеширование, сессии, rate limiting, аналитика
- **🔄 Легкое переключение**: между БД через конфигурацию
- **📈 Fallback-стратегия**: автоматическое переключение при отказе основной БД

### 🛡️ Безопасность и производительность / Security & Performance
- **⚡ Rate Limiting**: защита от DDoS через Redis
- **📝 Централизованное логирование**: всех операций и запросов
- **🔒 CORS настройка**: для продакшн среды
- **📊 Health Checks**: детальная диагностика всех БД подключений
- **🚫 Ограничения размера**: защита от атак (50MB лимит файлов)

### 📁 Обработка файлов / File Processing
- **📄 CSV/Excel поддержка**: автоматический парсинг прайс-листов
- **🔄 Batch операции**: эффективная загрузка больших файлов
- **✅ Валидация данных**: через Pydantic с детальными ошибками
- **🧹 Автоматическая очистка**: нормализация и дедупликация данных

## ⚙️ Конфигурация окружения

**🔥 ВАЖНО: Файл `.env.local` уже настроен и готов к работе!**

**📍 Расположение конфигурации:**
```
/Users/etronicspy/rag-stroyactiv-pyton/.env.local
```

В проекте используются **реальные базы данных**:
- ✅ **Qdrant Cloud** - векторная БД для семантического поиска (настроена и подключена)
- ✅ **OpenAI API** - для генерации эмбеддингов (ключ настроен)

**Файл `.env.local` содержит следующие переменные:**
```bash
# OpenAI Configuration
OPENAI_API_KEY=my_apy_key

# Qdrant Configuration
QDRANT_URL=my_url
QDRANT_API_KEY=my_api_key


```

**🎯 Все настройки готовы к использованию! Никакой дополнительной настройки не требуется.**

### 🔧 Централизованная конфигурация

Проект использует **продвинутую систему конфигурации** с поддержкой:
- 🔄 **Легкое переключение** между разными БД (Qdrant Cloud/Local, Weaviate, Pinecone)
- 🤖 **Множество ИИ провайдеров** (OpenAI, Azure OpenAI, HuggingFace, Ollama)
- 🛡️ **Безопасное управление** чувствительными данными
- ⚙️ **Фабрики клиентов** для автоматического создания подключений

Подробнее: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

## 🌐 API Endpoints

### 🔍 Продвинутый поиск / Advanced Search
- `POST /api/v1/search/advanced` - Основной продвинутый поиск с фильтрацией
- `GET /api/v1/search/suggestions` - Автодополнение и предложения запросов  
- `GET /api/v1/search/popular-queries` - Популярные поисковые запросы
- `GET /api/v1/search/analytics` - Детальная аналитика поиска
- `GET /api/v1/search/categories` - Доступные категории материалов
- `GET /api/v1/search/units` - Доступные единицы измерения
- `POST /api/v1/search/fuzzy` - Специализированный нечеткий поиск
- `GET /api/v1/search/health` - Проверка здоровья поискового сервиса

### 🔍 Базовый поиск / Basic Search  
- `POST /api/v1/search` - Семантический поиск по материалам

### 📄 Обработка прайс-листов / Price Processing
- `POST /api/v1/prices/process` - Обработка и валидация прайс-листов
- `GET /api/v1/prices/templates` - Шаблоны CSV/Excel файлов
- `POST /api/v1/prices/validate` - Предварительная валидация файлов

### 🗂️ Справочные данные / Reference Data
#### Материалы / Materials
- `GET /api/v1/reference/materials` - Список материалов с фильтрацией
- `GET /api/v1/reference/materials/{id}` - Получение материала по ID
- `POST /api/v1/reference/materials` - Создание материала
- `PUT /api/v1/reference/materials/{id}` - Обновление материала
- `DELETE /api/v1/reference/materials/{id}` - Удаление материала
- `POST /api/v1/reference/materials/batch` - Batch создание материалов

#### Категории / Categories
- `GET /api/v1/reference/categories` - Список категорий
- `POST /api/v1/reference/categories` - Создание категории
- `DELETE /api/v1/reference/categories/{name}` - Удаление категории

#### Единицы измерения / Units
- `GET /api/v1/reference/units` - Список единиц измерения
- `POST /api/v1/reference/units` - Создание единицы измерения
- `DELETE /api/v1/reference/units/{name}` - Удаление единицы измерения

### 📊 Мониторинг и диагностика / Monitoring & Health
- `GET /api/v1/health` - Комплексная проверка здоровья всех систем
- `GET /api/v1/health/config` - Статус конфигурации и подключений
- `GET /api/v1/health/detailed` - Детальная диагностика каждой БД
- `GET /api/v1/health/metrics` - Метрики производительности системы

## 🚀 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd rag-construction-materials
```

### 2. Создание виртуального окружения
```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/MacOS
.venv\Scripts\activate  # для Windows
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
**Переменные окружения уже настроены!**
- Файл `.env.local` готов к использованию
- Содержит настройки для реальных баз данных
- Никаких дополнительных настроек не требуется

**Быстрая проверка подключения:**
```bash
python check_db_connection.py
```

### 4. Инициализация базы данных
```bash
# Применение миграций
alembic upgrade head

# Заполнение справочными данными
python -c "from core.database.init_db import init_database; init_database()"
```

### 5. Запуск приложения
```bash
uvicorn main:app --reload
```

**Доступные адреса:**
- API: http://localhost:8000
- Swagger документация: http://localhost:8000/docs
- ReDoc документация: http://localhost:8000/redoc

## 🧪 Тестирование

### Базовые тесты
```bash
# Запуск всех тестов
pytest

# Запуск с подробным выводом
pytest -v

# Запуск тестов с покрытием
pytest --cov=. --cov-report=html
```

### Специализированные тесты
```bash
# Тесты подключения к БД
pytest tests/test_real_db_connection.py -v

# Тесты продвинутого поиска  
pytest tests/test_advanced_search.py -v

# Тесты прайс-листов
pytest tests/test_prices.py -v

# Тесты middleware и безопасности
pytest tests/test_middleware.py -v

# Тесты мониторинга
pytest tests/test_monitoring.py -v
```

### Демонстрационные скрипты
```bash
# Демо продвинутого поиска
python utils/demo/demo_advanced_search_simple.py

# Простое демо поиска
python utils/demo_advanced_search_simple.py

# Демо обработки прайс-листов
python utils/demo_price_processing.py
```

## 📊 Форматы данных

### Материал / Material
```json
{
  "id": "uuid-string",
  "name": "Портландцемент М500",
  "category": "Cement", 
  "unit": "bag",
  "description": "Высококачественный цемент для строительных работ",
  "sku": "CEM-M500-001",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Продвинутый поисковый запрос / Advanced Search Query
```json
{
  "query": "цемент для фундамента",
  "search_type": "hybrid",
  "filters": {
    "categories": ["Cement", "Concrete"],
    "units": ["bag", "kg"],
    "sku_pattern": "CEM-*",
    "created_after": "2024-01-01",
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
    "fields": ["name", "description"]
  }
}
```

### Прайс-лист / Price List
Поддерживаются форматы **CSV и Excel** (xls, xlsx) со следующими колонками:

**Обязательные:**
- `name` - название материала
- `category` - категория
- `unit` - единица измерения  

**Опциональные:**
- `description` - описание
- `sku` - артикул
- `price` - цена
- `supplier` - поставщик

## 🏗️ Архитектура проекта

### 📁 Структура проекта
```
├── api/                    # API маршруты
│   └── routes/            
│       ├── advanced_search.py    # Продвинутый поиск
│       ├── health.py             # Мониторинг и диагностика
│       ├── materials.py          # Управление материалами
│       ├── prices.py            # Обработка прайс-листов
│       └── reference.py         # Справочники
├── core/                   # Ядро системы
│   ├── config.py          # Централизованная конфигурация
│   ├── database/          # Адаптеры и фабрики БД
│   ├── dependencies/      # Dependency injection
│   ├── middleware/        # Middleware компоненты
│   ├── models/           # SQLAlchemy модели
│   ├── monitoring/       # Логирование и метрики
│   ├── repositories/     # Repository pattern
│   └── schemas/          # Pydantic схемы
├── services/              # Бизнес-логика
│   ├── advanced_search.py        # Поисковый движок
│   ├── materials.py              # Сервис материалов
│   └── price_processor.py        # Обработка прайс-листов
├── tests/                 # Тесты
├── utils/                # Утилиты и демо скрипты
├── docs/                 # Документация
└── alembic/              # Миграции БД
```

### 🔄 Паттерны проектирования
- **Repository Pattern** - абстрактные интерфейсы для всех БД
- **Factory Pattern** - создание клиентов БД
- **Dependency Injection** - управление зависимостями с `@lru_cache`
- **Strategy Pattern** - различные стратегии поиска
- **Observer Pattern** - система мониторинга и логирования

## 🚀 Этапы разработки / Development Stages

### ✅ Stage 1: Базовая архитектура и векторная БД (Completed)
- Настройка Qdrant векторной базы данных
- Базовые модели данных и схемы
- Простой векторный поиск материалов
- Начальная структура проекта

### ✅ Stage 2: Реляционная БД и гибридный поиск (Completed)  
- Интеграция PostgreSQL для структурированных данных
- Гибридный репозиторий (векторный + реляционный поиск)
- Расширенные API эндпоинты
- Улучшенная обработка ошибок

### ✅ Stage 3: Загрузка файлов и обработка данных (Completed)
- Загрузка и парсинг CSV/Excel файлов
- Автоматическая генерация эмбеддингов
- Batch обработка больших файлов  
- Валидация и очистка данных

### ✅ Stage 4: Redis кеширование и производительность (Completed)
- Интеграция Redis для кеширования
- Cache-aside паттерн с автоматической инвалидацией
- Значительное улучшение производительности (до 45x ускорение)
- Мониторинг и аналитика кеша

### ✅ Stage 5: Продвинутый поиск и фильтрация (Completed)
- Комплексные фильтры (категории, даты, единицы измерения, SKU паттерны)
- Fuzzy search с алгоритмами Levenshtein и Sequence Matcher
- Автодополнение и предложения поиска на основе популярных запросов
- Поисковая аналитика и статистика с Redis трекингом
- Гибридный поиск с весовыми коэффициентами
- Text highlighting и cursor-based пагинация
- Мульти-поле сортировка с настраиваемыми направлениями

### ✅ Stage 6: Рефакторинг архитектуры (Completed)
- **Этап 1**: Конфигурация и среды - централизованная система настроек
- **Этап 2**: Доработка интерфейсов - унификация репозиториев
- **Этап 3**: Миграции и БД - Alembic миграции и seed данные
- **Этап 4**: Middleware и безопасность - rate limiting, CORS, логирование
- **Этап 5**: Health checks и мониторинг - комплексная диагностика
- **Этап 6**: Документация и примеры - актуальная документация API

### 📋 Stage 7: Машинное обучение и рекомендации (Future)
- ML-модели для ранжирования результатов поиска
- Персонализированные рекомендации материалов
- Автоматическая категоризация и тегирование
- Предиктивная аналитика спроса
- **Статус**: Задокументировано как будущая возможность ([docs/FUTURE_STAGES.md](docs/FUTURE_STAGES.md))

## 🔧 Утилиты и инструменты

### Демонстрационные скрипты
- `utils/demo/demo_advanced_search_simple.py` - упрощенное демо продвинутого поиска
- `utils/demo_advanced_search_simple.py` - упрощенное демо
- `utils/demo_price_processing.py` - демо обработки прайс-листов

### Инструменты разработки
- `utils/check_db_connection.py` - проверка подключений к БД
- `utils/benchmark_performance.py` - бенчмарки производительности
- `utils/export_materials.py` - экспорт данных в различные форматы

## 📚 Документация

### Техническая документация
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - подробная настройка конфигурации
- [docs/DATABASE_ARCHITECTURE.md](docs/DATABASE_ARCHITECTURE.md) - архитектура БД
- [docs/STAGE_5_ADVANCED_SEARCH.md](docs/STAGE_5_ADVANCED_SEARCH.md) - продвинутый поиск
- [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) - руководство по миграциям
- [docs/UTILITIES.md](docs/UTILITIES.md) - описание утилит

### Этапы разработки
- [docs/STAGE_3_POSTGRESQL_HYBRID.md](docs/STAGE_3_POSTGRESQL_HYBRID.md) - гибридный поиск
- [docs/STAGE_4_REDIS_CACHING.md](docs/STAGE_4_REDIS_CACHING.md) - Redis кеширование
- [docs/STAGE_7_REFACTORING.md](docs/STAGE_7_REFACTORING.md) - рефакторинг архитектуры
- [docs/FUTURE_STAGES.md](docs/FUTURE_STAGES.md) - планы развития

### Руководства
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - настройка среды разработки
- [REFACTORING_PLAN.md](REFACTORING_PLAN.md) - план рефакторинга
- [docs/BATCH_MATERIALS_LOADING.md](docs/BATCH_MATERIALS_LOADING.md) - загрузка больших файлов

## 🤝 Разработка

### Требования к коду
- Python 3.9+, FastAPI, async/await везде  
- PEP 8, type hints, docstrings для всех функций
- Код и идентификаторы: только английский язык
- Pydantic модели с примерами для автодокументации

### Архитектурные принципы
- Repository pattern для каждого типа БД
- Dependency injection с `@lru_cache`
- Абстрактные интерфейсы (ABC) для БД операций
- Версионирование API `/api/v1/`
- UTF-8 ответы, обработка ошибок для всех БД

### Тестирование
- pytest с фикстурами для каждого типа БД
- Моки для внешних БД в unit тестах
- Интеграционные тесты на реальных БД
- Health checks для всех подключений БД

### Безопасность
- Rate limiting через Redis для всех эндпоинтов
- CORS конфигурация для продакшн среды
- Middleware логирования всех входящих запросов
- Ограничение размера запросов и файлов (защита от атак)
- Валидация входящих данных (защита от инъекций)

## 📧 Поддержка

Для получения поддержки или сообщения об ошибках, пожалуйста, используйте систему Issues в репозитории.

---

**🎯 Проект готов к продакшн использованию!** Все системы протестированы и оптимизированы для высокой производительности и надежности. 