# 🏗️ RAG Construction Materials API

Профессиональный API для управления строительными материалами с **продвинутым семантическим поиском**, **мульти-БД поддержкой** и **интеллектуальной аналитикой**.

## 🚀 Ключевые возможности / Key Features

### 🔍 Семантический поиск / Semantic Search
- **🧠 Fallback стратегия**: Vector search (семантический) → SQL LIKE search (если 0 результатов)
- **⚡ Быстрый поиск**: Через эмбеддинги OpenAI text-embedding-ada-002
- **🎯 Точные результаты**: Семантическое понимание запросов на русском языке
- **📊 Простой API**: GET `/api/v1/search/?q=цемент&limit=10`

### 🗄️ Мульти-БД архитектура / Multi-Database Architecture
- **🔵 Qdrant-Only Mode** (Рекомендуемый): Работа только с Qdrant + mock адаптеры
- **🟠 Векторные БД**: Qdrant (Cloud/Local), Weaviate, Pinecone с единым интерфейсом
- **🔴 Mock адаптеры**: Полная совместимость PostgreSQL и Redis API без реальных БД
- **🔄 Автоматическое переключение**: Fallback на mock-реализации при недоступности БД
- **📈 Graceful degradation**: Система работает даже при отказе компонентов

### 🛡️ Безопасность и производительность / Security & Performance
- **🚀 BodyCacheMiddleware**: Решение проблемы зависания FastAPI через единое чтение request body
- **⚡ Rate Limiting**: Защита от DDoS через Redis (или mock)
- **📝 Централизованное логирование**: Всех операций и запросов с полным логированием body
- **🔒 CORS настройка**: Для продакшн среды
- **🛡️ XSS/SQL Injection защита**: Полная валидация входящих данных с поддержкой кириллицы
- **📊 Health Checks**: Детальная диагностика всех БД подключений
- **🚫 Ограничения размера**: Защита от атак (50MB лимит файлов)
- **⏱️ Таймауты и retry**: Предотвращение зависаний с автоматическими повторами

### 📁 Обработка файлов / File Processing
- **📄 CSV/Excel поддержка**: Автоматический парсинг прайс-листов (2 формата)
- **🔄 Batch операции**: Эффективная загрузка больших файлов (до 1000 элементов)
- **✅ Валидация данных**: Через Pydantic с детальными ошибками
- **🧹 Автоматическая очистка**: Нормализация и дедупликация данных

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

# Qdrant-Only Mode (Рекомендуемый)
QDRANT_ONLY_MODE=true
ENABLE_FALLBACK_DATABASES=true
DISABLE_REDIS_CONNECTION=true
DISABLE_POSTGRESQL_CONNECTION=true
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

### **Всего эндпоинтов**: 44
- **Активные**: 44 (все подключены в main.py)
- **Продвинутый поиск**: 8 эндпоинтов (подключены и готовы к использованию)

### 🏠 Основные эндпоинты / Core Endpoints
- `GET /` - Приветственное сообщение и информация об API
- `GET /docs` - Swagger UI документация
- `GET /redoc` - ReDoc документация

### 🏥 Мониторинг здоровья / Health Monitoring
- `GET /api/v1/health/` - Базовая проверка здоровья
- `GET /api/v1/health/detailed` - Детальная проверка всех сервисов (включая mock)
- `GET /api/v1/health/databases` - Проверка здоровья всех БД
- `GET /api/v1/health/metrics` - Метрики производительности
- `GET /api/v1/health/performance` - Детальные метрики производительности
- `GET /api/v1/health/config` - Статус конфигурации системы

### 📊 Мониторинг производительности / Performance Monitoring
- `GET /api/v1/monitoring/health` - Комплексная проверка системы
- `GET /api/v1/monitoring/pools` - Метрики пулов подключений
- `GET /api/v1/monitoring/pools/history` - История корректировок пулов
- `GET /api/v1/monitoring/pools/recommendations` - Рекомендации по оптимизации
- `POST /api/v1/monitoring/pools/{pool_name}/resize` - Ручное изменение размера пула
- `GET /api/v1/monitoring/pools/stats` - Сводная статистика пулов
- `GET /api/v1/monitoring/optimizations` - Метрики оптимизации
- `GET /api/v1/monitoring/middleware/stats` - Статистика middleware
- `POST /api/v1/monitoring/optimizations/benchmark` - Запуск бенчмарка

### 🔍 Поиск материалов / Materials Search
- `GET /api/v1/search/` - **Простой семантический поиск** (основной эндпоинт)
- `POST /api/v1/materials/search` - Поиск через POST с телом запроса

### 🧱 Управление материалами / Materials Management
- `POST /api/v1/materials/` - Создание материала с эмбеддингом
- `GET /api/v1/materials/{material_id}` - Получение материала по ID
- `GET /api/v1/materials/` - Получение всех материалов с фильтрацией
- `PUT /api/v1/materials/{material_id}` - Обновление материала
- `DELETE /api/v1/materials/{material_id}` - Удаление материала
- `POST /api/v1/materials/batch` - Массовое создание материалов
- `POST /api/v1/materials/import` - Импорт материалов из JSON
- `GET /api/v1/materials/health` - Проверка здоровья сервиса

### 💰 Обработка прайс-листов / Price Lists Processing
- `POST /api/v1/prices/process` - **Обработка CSV/Excel файлов** (2 формата)
- `GET /api/v1/prices/{supplier_id}/latest` - Последний прайс-лист поставщика
- `GET /api/v1/prices/{supplier_id}/all` - Все прайс-листы поставщика
- `DELETE /api/v1/prices/{supplier_id}` - Удаление прайс-листов поставщика
- `GET /api/v1/prices/{supplier_id}/pricelist/{pricelistid}` - Прайс-лист по ID
- `PATCH /api/v1/prices/{supplier_id}/product/{product_id}/process` - Отметка как обработанного

### 📚 Справочники / Reference Data
#### Категории / Categories
- `POST /api/v1/reference/categories/` - Создание категории
- `GET /api/v1/reference/categories/` - Получение всех категорий
- `DELETE /api/v1/reference/categories/{name}` - Удаление категории

#### Единицы измерения / Units
- `POST /api/v1/reference/units/` - Создание единицы измерения
- `GET /api/v1/reference/units/` - Получение всех единиц
- `DELETE /api/v1/reference/units/{name}` - Удаление единицы

### 🔍 Продвинутый поиск / Advanced Search ✅ ПОДКЛЮЧЕН
> **✅ ГОТОВО**: Все эндпоинты advanced search подключены и готовы к использованию

- `POST /api/v1/search/advanced` - **Продвинутый поиск** с фильтрацией по категориям и единицам
- `GET /api/v1/search/suggestions?q=цем&limit=5` - Автодополнение запросов
- `GET /api/v1/search/popular-queries` - Популярные запросы (mock данные)
- `GET /api/v1/search/analytics` - Аналитика поиска (mock данные)
- `GET /api/v1/search/categories` - **Доступные категории** (из реальных данных)
- `GET /api/v1/search/units` - **Доступные единицы измерения** (из реальных данных)
- `POST /api/v1/search/fuzzy` - Нечеткий поиск с порогом схожести
- `GET /api/v1/search/health` - Здоровье поискового сервиса

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
# Применение миграций (если используется PostgreSQL)
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
# Тесты Qdrant-only режима
pytest tests/test_qdrant_only_mode.py -v

# Тесты интеграции Qdrant-only
pytest tests/test_qdrant_only_integration.py -v

# Тесты подключения к БД
pytest tests/test_real_db_connection.py -v

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
```

## 💡 Примеры использования

### Простой поиск материалов
```bash
# GET запрос - самый простой способ
curl "http://localhost:8000/api/v1/search/?q=цемент&limit=5"

# POST запрос через materials
curl -X POST "http://localhost:8000/api/v1/materials/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "цемент портландский", "limit": 10}'
```

### Продвинутый поиск материалов
```bash
# Получение доступных категорий
curl "http://localhost:8000/api/v1/search/categories"

# Получение единиц измерения
curl "http://localhost:8000/api/v1/search/units"

# Продвинутый поиск с фильтрацией
curl -X POST "http://localhost:8000/api/v1/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "цемент",
    "search_type": "hybrid",
    "limit": 5,
    "categories": ["Цемент"],
    "units": ["кг"]
  }'

# Автодополнение запросов
curl "http://localhost:8000/api/v1/search/suggestions?q=цем&limit=5"

# Популярные запросы
curl "http://localhost:8000/api/v1/search/popular-queries"

# Аналитика поиска
curl "http://localhost:8000/api/v1/search/analytics"
```

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

### Загрузка прайс-листа
```bash
curl -X POST "http://localhost:8000/api/v1/prices/process" \
  -F "file=@pricelist.csv" \
  -F "supplier_id=supplier_001" \
  -F "pricelistid=12345"
```

### Проверка здоровья системы
```bash
# Базовая проверка
curl "http://localhost:8000/api/v1/health/"

# Детальная проверка (включая mock адаптеры)
curl "http://localhost:8000/api/v1/health/detailed"

# Метрики мониторинга
curl "http://localhost:8000/api/v1/monitoring/pools"
```

## 🎯 Особенности архитектуры

### 🚀 Middleware Stack (Производственная стабильность)
- **BodyCacheMiddleware**: Единое чтение request body - решение проблемы зависания FastAPI
- **SecurityMiddleware**: Полная валидация XSS/SQL injection с поддержкой кириллицы
- **LoggingMiddleware**: Централизованное логирование всех запросов и ответов
- **RateLimitMiddleware**: Защита от DDoS атак через Redis (или mock)
- **CompressionMiddleware**: Оптимизация трафика с Brotli и gzip сжатием
- **Порядок выполнения**: LIFO (Last In First Out) для корректной обработки

### 🔵 Qdrant-Only Mode (Рекомендуемый)
- **Полная функциональность** через одну векторную БД
- **Mock адаптеры** для PostgreSQL и Redis
- **Автоматическое переключение** при недоступности реальных БД
- **Все API эндпоинты работают** без изменений
- **Простота развертывания** - нужен только Qdrant

### 🔄 Fallback стратегии
1. **Поиск**: Vector search → SQL LIKE search (если 0 результатов)
2. **БД подключения**: Реальные БД → Mock адаптеры
3. **Rate limiting**: Redis → Mock Redis (без потери функциональности)

### 🛡️ Mock адаптеры
- **MockPostgreSQLDatabase**: Полная совместимость с PostgreSQL API
- **MockRedisClient**: Полная совместимость с Redis API
- **MockAIClient**: Детерминированная генерация эмбеддингов
- **Автоматическое обнаружение**: Система сама определяет когда использовать mock

### 📊 Мониторинг и метрики
- **Health checks**: Для всех компонентов включая mock
- **Pool management**: Автоматическое масштабирование подключений
- **Performance metrics**: Детальная статистика производительности
- **Middleware stats**: Мониторинг всех middleware компонентов

## 📚 Документация

### Основная документация
- [📊 API Endpoints Tree](docs/API_ENDPOINTS_TREE.md) - Полное дерево всех эндпоинтов
- [📚 API Documentation](docs/API_DOCUMENTATION.md) - Детальная документация API
- [🔵 Qdrant-Only Mode](docs/QDRANT_ONLY_MODE.md) - Руководство по Qdrant-only режиму
- [⚙️ Configuration](docs/CONFIGURATION.md) - Настройка конфигурации

### Техническая документация
- [🏗️ Database Architecture](docs/DATABASE_ARCHITECTURE.md) - Архитектура БД
- [🚀 Unified Body Reading Solution](docs/UNIFIED_BODY_READING_SOLUTION.md) - Решение проблемы зависания FastAPI
- [🔄 Migration Guide](docs/MIGRATION_GUIDE.md) - Руководство по миграции
- [🧪 Testing Guide](docs/TESTING_GUIDE.md) - Руководство по тестированию
- [🛠️ Utilities Overview](docs/UTILITIES_OVERVIEW.md) - Обзор утилит

### Примеры и демо
- [📝 API Examples](docs/API_EXAMPLES.md) - Примеры использования API
- [📦 Batch Materials Loading](docs/BATCH_MATERIALS_LOADING.md) - Массовая загрузка
- [🔍 Advanced Search](docs/STAGE_5_ADVANCED_SEARCH.md) - Продвинутый поиск

## 🔧 Конфигурация

### Qdrant-only режим (Рекомендуемый)
```bash
# .env файл
QDRANT_ONLY_MODE=true
ENABLE_FALLBACK_DATABASES=true
DISABLE_REDIS_CONNECTION=true
DISABLE_POSTGRESQL_CONNECTION=true

# Qdrant настройки
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION_NAME=materials

# OpenAI для эмбеддингов
OPENAI_API_KEY=your-openai-key
```

### Multi-Database режим
```bash
# PostgreSQL
POSTGRESQL_URL=postgresql://user:pass@localhost:5432/materials

# Redis
REDIS_URL=redis://localhost:6379/0

# Векторная БД (выбрать одну)
DATABASE_TYPE=QDRANT_CLOUD  # или QDRANT_LOCAL, WEAVIATE, PINECONE
```

## 🚀 HTTP статус коды

- **200**: Успешный запрос
- **201**: Ресурс успешно создан
- **207**: Multi-status (частично успешно)
- **400**: Ошибка валидации данных
- **404**: Ресурс не найден
- **500**: Внутренняя ошибка сервера
- **503**: Сервис недоступен

## 🎯 Лимиты и ограничения

### Размеры данных
- **Максимальный размер файла**: 50MB
- **Максимальное количество элементов в batch**: 1000
- **Максимальная длина имени материала**: 200 символов
- **Максимальная длина SKU**: 50 символов

### Rate Limiting
- Настраивается через environment variables
- Поддержка burst protection
- Headers с информацией о лимитах
- Работает с mock Redis в Qdrant-only режиме

### Поддерживаемые форматы файлов
- **CSV**: UTF-8 encoding
- **Excel**: .xls, .xlsx форматы
- **Два формата прайс-листов**: Legacy и расширенный

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Поддержка

- 📧 **Issues**: Используйте систему Issues в репозитории
- 📚 **Документация**: Полная документация в папке `docs/`
- 🔍 **Swagger UI**: http://localhost:8000/docs для интерактивного тестирования

---

**🎯 Готов к использованию из коробки!**  
**🔄 Последнее обновление**: 2024-01-01  
**�� Версия API**: v1 