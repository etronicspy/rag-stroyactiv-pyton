# RAG Construction Materials API

Система управления и семантического поиска строительных материалов с использованием векторных баз данных и AI-эмбеддингов.

## 🚀 Быстрый старт

### Требования
- Python 3.9+
- OpenAI API ключ
- Qdrant Cloud аккаунт

### Установка
```bash
# Клонирование репозитория
git clone <repository-url>
cd rag-stroyactiv-pyton

# Установка зависимостей
pip install -r requirements.txt

# Настройка окружения
cp env.example .env.local
# Отредактируйте .env.local с вашими API ключами
```

### Запуск
```bash
# Production (рекомендуется)
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Development (с автоперезагрузкой)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> **⚠️ Важно**: Для стабильности POST запросов рекомендуется запуск без `--reload` флага.

## 🏗 Архитектура

### Текущий режим: Hybrid Multi-Database
- **Qdrant Cloud** - векторная база для семантического поиска
- **PostgreSQL** - реляционная база (через SSH туннель)
- **Redis** - кеширование и сессии
- **OpenAI** - генерация эмбеддингов

### Fallback стратегия
При недоступности основных БД система автоматически переключается на mock-адаптеры для обеспечения непрерывной работы.

## 📋 API Эндпоинты

### 🏥 Health & Monitoring
```
GET  /api/v1/health/              # Базовая проверка
GET  /api/v1/health/detailed      # Детальная диагностика
GET  /api/v1/health/databases     # Статус всех БД
GET  /api/v1/monitoring/health    # Комплексный мониторинг
```

### 📦 Materials
```
GET    /api/v1/materials/                    # Список материалов
POST   /api/v1/materials/                    # Создать материал
GET    /api/v1/materials/{id}                # Получить по ID
PUT    /api/v1/materials/{id}                # Обновить материал
DELETE /api/v1/materials/{id}                # Удалить материал
POST   /api/v1/materials/batch               # Пакетное создание
POST   /api/v1/materials/import              # Импорт из JSON
POST   /api/v1/materials/search              # Поиск материалов
```

### 💰 Prices
```
POST   /api/v1/prices/process                      # Обработка прайс-листа
GET    /api/v1/prices/{supplier_id}/latest         # Последний прайс-лист
GET    /api/v1/prices/{supplier_id}/all            # Все прайс-листы
DELETE /api/v1/prices/{supplier_id}                # Удалить прайс-листы
PATCH  /api/v1/prices/{supplier_id}/product/{id}/process  # Отметить обработанным
```

### 🔍 Search
```
GET  /api/v1/search/                          # Простой поиск
POST /api/v1/search/advanced                  # Продвинутый поиск
GET  /api/v1/search/suggestions               # Автодополнение
GET  /api/v1/search/categories                # Доступные категории
GET  /api/v1/search/units                     # Единицы измерения
```

### 📚 Reference Data
```
GET    /api/v1/reference/categories/          # Список категорий
POST   /api/v1/reference/categories/          # Создать категорию
DELETE /api/v1/reference/categories/{id}      # Удалить категорию
GET    /api/v1/reference/units/               # Список единиц измерения
POST   /api/v1/reference/units/               # Создать единицу
DELETE /api/v1/reference/units/{id}           # Удалить единицу
```

## 🛠 Примеры использования

### Создание материала
```bash
curl -X POST "http://localhost:8000/api/v1/materials/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Цемент М500",
    "use_category": "Цемент",
    "unit": "мешок",
    "description": "Портландцемент высокой прочности"
  }'
```

### Семантический поиск
```bash
curl -X POST "http://localhost:8000/api/v1/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "высокопрочный цемент для фундамента",
    "search_type": "hybrid",
    "limit": 5
  }'
```

### Загрузка прайс-листа
```bash
curl -X POST "http://localhost:8000/api/v1/prices/process" \
  -F "file=@pricelist.csv" \
  -F "supplier_id=SUPPLIER001"
```

## ⚙️ Конфигурация

### Основные переменные
```bash
# Векторная БД
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your_qdrant_key

# AI Provider
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=text-embedding-3-small

# PostgreSQL (через SSH туннель)
POSTGRESQL_URL=postgresql+asyncpg://user:pass@localhost:5435/stbr_rag1
ENABLE_SSH_TUNNEL=true

# Redis
REDIS_URL=redis://localhost:6379

# Fallback
ENABLE_FALLBACK_DATABASES=true
```

### Режимы работы
- `QDRANT_ONLY_MODE=true` - только векторная БД
- `ENABLE_FALLBACK_DATABASES=true` - автоматический fallback
- `DISABLE_REDIS_CONNECTION=true` - отключить Redis

## 🧪 Тестирование

```bash
# Все тесты
pytest

# По категориям
pytest tests/unit/          # Модульные тесты
pytest tests/integration/   # Интеграционные тесты
pytest tests/functional/    # Функциональные тесты

# С покрытием
pytest --cov=. --cov-report=html
```

## 🔧 Troubleshooting

### POST запросы зависают
```bash
# 1. Установите правильную версию greenlet
pip install greenlet==3.0.1

# 2. Запустите без --reload
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Проблемы с БД
```bash
# Проверка статуса
curl http://localhost:8000/api/v1/health/detailed

# Включение fallback режима
ENABLE_FALLBACK_DATABASES=true
```

### SSH туннель не работает
```bash
# Проверьте настройки
SSH_TUNNEL_REMOTE_HOST=31.130.148.200
SSH_TUNNEL_KEY_PATH=~/.ssh/postgres_key
ENABLE_SSH_TUNNEL=true
```

## 📚 Документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI**: http://localhost:8000/openapi.json

## 🔄 Развертывание

### Development
```bash
# Локальная разработка
cp env.example .env.local
# Настройте API ключи в .env.local
python -m uvicorn main:app --reload
```

### Production
- Настройте все БД (PostgreSQL, Redis, Qdrant)
- Используйте Gunicorn с Uvicorn workers
- Настройте reverse proxy (nginx)
- Включите HTTPS и мониторинг

## 📄 Лицензия

MIT License