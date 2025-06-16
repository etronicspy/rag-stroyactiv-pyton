# RAG Construction Materials API

Система поиска и управления строительными материалами с использованием векторного поиска и RAG (Retrieval-Augmented Generation).

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Настройка окружения
Скопируйте `.env.example` в `.env.local` и настройте переменные:
```bash
cp .env.example .env.local
```

### Запуск приложения
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📋 API Эндпоинты

### 🏠 Основные эндпоинты
- `GET /` - Приветственное сообщение
- `GET /docs` - Swagger UI документация
- `GET /openapi.json` - OpenAPI схема

### 🏥 Health Check эндпоинты
- `GET /api/v1/health/` - Базовая проверка здоровья
- `GET /api/v1/health/detailed` - Детальная проверка всех сервисов
- `GET /api/v1/health/databases` - Проверка здоровья всех баз данных

### 📦 Materials API
- `GET /api/v1/materials/` - Получить список материалов
- `POST /api/v1/materials/` - Создать новый материал
- `GET /api/v1/materials/{id}` - Получить материал по ID
- `PUT /api/v1/materials/{id}` - Обновить материал
- `DELETE /api/v1/materials/{id}` - Удалить материал
- `POST /api/v1/materials/batch` - Создать материалы пакетом
- `POST /api/v1/materials/import` - Импорт материалов из JSON
- `POST /api/v1/materials/search` - Поиск материалов
- `GET /api/v1/materials/health` - Проверка здоровья сервиса материалов

### 💰 Prices API
- `POST /api/v1/prices/process` - Обработка прайс-листа
- `GET /api/v1/prices/{supplier_id}/latest` - Получить последний прайс-лист поставщика
- `GET /api/v1/prices/{supplier_id}/all` - Получить все прайс-листы поставщика
- `DELETE /api/v1/prices/{supplier_id}` - Удалить прайс-листы поставщика
- `GET /api/v1/prices/{supplier_id}/pricelist/{pricelistid}` - Получить продукты по ID прайс-листа
- `PATCH /api/v1/prices/{supplier_id}/product/{product_id}/process` - Отметить продукт как обработанный

### 🔍 Search API
- `GET /api/v1/search/` - Простой поиск материалов
- `POST /api/v1/search/advanced` - Продвинутый поиск с фильтрацией
- `GET /api/v1/search/suggestions` - Предложения для автодополнения
- `GET /api/v1/search/categories` - Получить доступные категории
- `GET /api/v1/search/units` - Получить доступные единицы измерения

### 📚 Reference API
- `POST /api/v1/reference/categories/` - Создать категорию
- `GET /api/v1/reference/categories/` - Получить список категорий
- `DELETE /api/v1/reference/categories/{category_id}` - Удалить категорию по ID
- `POST /api/v1/reference/units/` - Создать единицу измерения
- `GET /api/v1/reference/units/` - Получить список единиц измерения
- `DELETE /api/v1/reference/units/{unit_id}` - Удалить единицу измерения по ID

### 📊 Monitoring
- `GET /api/v1/monitoring/health` - Комплексная проверка здоровья системы

## 🛠 Примеры использования

### Создание материала
```bash
curl -X POST "http://localhost:8000/api/v1/materials/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Цемент портландский М400",
    "use_category": "Цемент",
    "unit": "кг",
    "description": "Высококачественный портландцемент"
  }'
```

### Поиск материалов
```bash
curl -X GET "http://localhost:8000/api/v1/search/?q=цемент&limit=10"
```

### Загрузка прайс-листа
```bash
curl -X POST "http://localhost:8000/api/v1/prices/process" \
  -F "file=@price_list.csv" \
  -F "supplier_id=SUPPLIER_001"
```

### Продвинутый поиск
```bash
curl -X POST "http://localhost:8000/api/v1/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "цемент",
    "search_type": "hybrid",
    "limit": 10,
    "categories": ["Цемент"],
    "units": ["кг"]
  }'
```

### Получение предложений для автодополнения
```bash
curl "http://localhost:8000/api/v1/search/suggestions?q=цем&limit=5"
```

### Проверка здоровья системы
```bash
curl "http://localhost:8000/api/v1/monitoring/health"
```

## 🏗 Архитектура

### 🎯 Режимы развертывания

#### 🔧 Development Mode (Текущий)
**Qdrant-Only режим для локальной разработки**
- **Qdrant Cloud** - векторная база данных (основная)
- **Mock PostgreSQL** - адаптер для совместимости
- **Mock Redis** - адаптер для кеширования
- **OpenAI** - генерация эмбеддингов

#### 🚀 Production Mode (Планируемый)
**Полная мульти-БД архитектура**
- **PostgreSQL** - основная реляционная база данных  
- **Qdrant** - векторная база данных для семантического поиска
- **Redis** - кеширование и управление сессиями
- **OpenAI** - генерация эмбеддингов

### Структура проекта
```
├── api/routes/          # API роуты
├── core/               # Основная логика
│   ├── config/         # Конфигурация
│   ├── database/       # Адаптеры БД
│   ├── schemas/        # Pydantic модели
│   └── middleware/     # Middleware компоненты
├── services/           # Бизнес-логика
├── tests/              # Тесты
└── utils/              # Утилиты
```

## 🧪 Тестирование

### Запуск всех тестов
```bash
pytest
```

### Запуск конкретных типов тестов
```bash
# Unit тесты
pytest tests/unit/

# Интеграционные тесты
pytest tests/integration/

# Тесты производительности
pytest tests/performance/
```

## 📝 Документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI схема**: http://localhost:8000/openapi.json

## 🔧 Конфигурация

### Development Mode (по умолчанию)
```bash
# Основные переменные окружения для разработки
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your_qdrant_key
OPENAI_API_KEY=your_openai_key
QDRANT_ONLY_MODE=true
ENABLE_FALLBACK_DATABASES=true
```

### Production Mode (планируемый)
```bash
# Переменные для продакшн развертывания
QDRANT_ONLY_MODE=false
DATABASE_URL=postgresql://user:pass@localhost:5432/materials
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your_qdrant_key
OPENAI_API_KEY=your_openai_key
```

## 📊 Мониторинг

Система включает встроенный мониторинг:
- Health checks для всех компонентов
- Метрики производительности  
- Логирование операций
- Automatic fallback strategies

## 🚀 Развертывание

### Development (локально)
```bash
# Клонирование и установка
git clone <repository>
cd rag-stroyactiv-pyton
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env.local
# Отредактируйте .env.local с вашими API ключами

# Запуск
python -m uvicorn main:app --reload
```

### Production
Для продакшн развертывания рекомендуется:
- Настроить PostgreSQL и Redis
- Использовать Gunicorn с Uvicorn workers
- Настроить reverse proxy (nginx)
- Включить HTTPS
- Настроить мониторинг и логирование

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License