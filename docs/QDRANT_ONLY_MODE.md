# Qdrant-Only Mode / Режим только с Qdrant

## Описание / Description

Qdrant-Only Mode позволяет запускать приложение только с векторной БД Qdrant, используя заглушки (mocks) для PostgreSQL и Redis. Это полезно для:

- **Быстрого тестирования** без настройки всех БД
- **Разработки** с фокусом на векторный поиск
- **Демонстрации** возможностей RAG без инфраструктуры
- **CI/CD пайплайнов** с минимальными зависимостями

Qdrant-Only Mode allows running the application with only Qdrant vector database, using mocks for PostgreSQL and Redis. This is useful for:

- **Fast testing** without setting up all databases
- **Development** focusing on vector search
- **Demos** of RAG capabilities without infrastructure
- **CI/CD pipelines** with minimal dependencies

## Настройка / Configuration

### 1. Конфигурация через переменные окружения / Environment Variables

```bash
# Включить режим только с Qdrant
QDRANT_ONLY_MODE=true

# Включить fallback на mock БД
ENABLE_FALLBACK_DATABASES=true

# Отключить подключения к реальным БД
DISABLE_REDIS_CONNECTION=true
DISABLE_POSTGRESQL_CONNECTION=true

# Обязательные настройки Qdrant
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION_NAME=materials

# Обязательные настройки OpenAI для эмбеддингов
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=text-embedding-3-small
```

### 2. Использование готового примера конфигурации / Using Configuration Example

Скопируйте файл примера конфигурации:
```bash
cp configs/qdrant-only.env.example .env
```

Отредактируйте `.env` файл и укажите ваши ключи:
- `QDRANT_URL` - URL вашего Qdrant кластера
- `QDRANT_API_KEY` - API ключ для Qdrant
- `OPENAI_API_KEY` - API ключ для OpenAI

## Возможности / Features

### ✅ Работает / Works
- 🔍 **Векторный поиск** через Qdrant
- 📊 **Эмбеддинги** через OpenAI/HuggingFace
- 📁 **Загрузка файлов** (CSV, Excel)
- 🏥 **Health checks** с информацией о mock БД
- 🔄 **API эндпоинты** для материалов
- 📝 **Логирование** всех операций
- ⚡ **Быстрые тесты** без таймаутов

### 🔧 Mock заглушки / Mock Stubs
- 🗄️ **PostgreSQL** - имитация SQL операций
- 🗂️ **Redis** - имитация кеширования
- 🤖 **AI Client** - генерация детерминированных эмбеддингов
- 📈 **Метрики** - базовая статистика

### ❌ Ограничения / Limitations
- 🚫 **Нет реального SQL поиска** (только mock результаты)
- 🚫 **Нет постоянного кеширования** (только в памяти)
- 🚫 **Нет миграций БД** (auto-migrate=false)
- 🚫 **Нет персистентных данных** в PostgreSQL

## Запуск / Running

### 1. Установка зависимостей / Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Запуск сервера / Start Server
```bash
# С конфигурацией из .env файла
uvicorn main:app --reload --port 8000

# Или с explicit переменными
QDRANT_ONLY_MODE=true uvicorn main:app --reload
```

### 3. Проверка работы / Health Check
```bash
# Базовая проверка
curl http://localhost:8000/api/v1/health/

# Детальная проверка всех БД
curl http://localhost:8000/api/v1/health/detailed

# Проверка только БД
curl http://localhost:8000/api/v1/health/databases
```

## Тестирование / Testing

### Быстрые тесты / Fast Tests
```bash
# Тесты mock БД
pytest tests/test_qdrant_only_mode.py -v

# Все быстрые тесты
pytest tests/test_*_fast.py -v

# Прямые тесты сервисов
pytest tests/test_services_direct.py -v
```

### Интеграционные тесты / Integration Tests
```bash
# Тесты API с timeout
pytest tests/test_*.py --timeout=10 -v
```

## API Endpoints

### Поиск материалов / Search Materials
```bash
# Векторный поиск через Qdrant
curl -X POST "http://localhost:8000/api/v1/materials/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "бетон", "limit": 5}'

# Fallback SQL поиск (mock результаты)
curl -X POST "http://localhost:8000/api/v1/materials/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "unknown material", "limit": 5}'
```

### Загрузка файлов / Upload Files
```bash
# Загрузка прайс-листа
curl -X POST "http://localhost:8000/api/v1/materials/upload" \
  -F "file=@data/sample_materials.csv"
```

### Справочники / Reference Data
```bash
# Категории (mock данные)
curl "http://localhost:8000/api/v1/reference/categories"

# Единицы измерения (mock данные)
curl "http://localhost:8000/api/v1/reference/units"
```

## Логи / Logs

При запуске в Qdrant-only режиме вы увидите:
```
INFO: 🔧 MockRelationalAdapter initialized
INFO: 🔧 MockCacheAdapter initialized
INFO: PostgreSQL connection disabled, using mock database
INFO: Redis connection disabled, using mock cache
INFO: Qdrant-only mode enabled, fallback databases active
```

## Диагностика / Diagnostics

### Health Check Response
```json
{
  "status": "healthy",
  "databases": {
    "vector_db": {
      "type": "qdrant_cloud",
      "status": "healthy",
      "details": {
        "collections_count": 1,
        "points_count": 1000
      }
    },
    "relational_db": {
      "type": "postgresql",
      "status": "mock",
      "details": {
        "type": "mock_postgresql",
        "message": "Using mock PostgreSQL adapter (fallback mode)"
      }
    },
    "cache_db": {
      "type": "redis",
      "status": "mock",
      "details": {
        "type": "mock_redis",
        "message": "Using mock Redis adapter (fallback mode)"
      }
    }
  }
}
```

## Переход на полную конфигурацию / Migration to Full Setup

Для перехода на полную конфигурацию со всеми БД:

1. **Настройте PostgreSQL**:
```bash
DISABLE_POSTGRESQL_CONNECTION=false
POSTGRESQL_URL=postgresql://user:pass@localhost:5432/materials
```

2. **Настройте Redis**:
```bash
DISABLE_REDIS_CONNECTION=false
REDIS_URL=redis://localhost:6379
```

3. **Отключите Qdrant-only режим**:
```bash
QDRANT_ONLY_MODE=false
ENABLE_FALLBACK_DATABASES=false
```

4. **Включите миграции**:
```bash
AUTO_MIGRATE=true
AUTO_SEED=true
```

## Решение проблем / Troubleshooting

### Частые проблемы / Common Issues

1. **Тесты зависают**
   - Убедитесь, что `QDRANT_ONLY_MODE=true`
   - Проверьте, что mock адаптеры инициализируются

2. **Ошибки подключения к Qdrant**
   - Проверьте `QDRANT_URL` и `QDRANT_API_KEY`
   - Убедитесь, что коллекция создана

3. **Отсутствуют результаты поиска**
   - Загрузите данные через `/api/v1/materials/upload`
   - Проверьте индексацию в Qdrant

4. **Ошибки с эмбеддингами**
   - Проверьте `OPENAI_API_KEY`
   - Убедитесь, что модель доступна

### Отладка / Debug Mode

Включите детальное логирование:
```bash
LOG_LEVEL=DEBUG
LOG_REQUEST_BODY=true
```

## Преимущества / Benefits

- ⚡ **Быстрый старт** - нет необходимости настраивать PostgreSQL и Redis
- 🧪 **Идеально для тестов** - детерминированные mock данные
- 🔄 **Fallback стратегия** - автоматическое переключение на mock
- 📊 **Сохранение функциональности** - все API работают
- 🏗️ **Готовность к production** - легкое переключение на реальные БД 