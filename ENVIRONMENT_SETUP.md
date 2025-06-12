# 🔧 Environment Setup Guide

## Настройка окружения для RAG Construction Materials API

### 📋 Шаги настройки

#### 1. Копирование примера конфигурации
```bash
# Скопируйте файл с примерами
cp env.example .env.local

# Отредактируйте файл с вашими настройками
nano .env.local  # или любой другой редактор
```

#### 2. Заполнение обязательных параметров

**Минимально необходимые настройки:**
```env
# Vector Database (Qdrant)
QDRANT_URL=https://your-cluster-url.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key

# OpenAI для эмбеддингов
OPENAI_API_KEY=sk-your_openai_api_key

# Среда разработки
ENVIRONMENT=development
```

### 🗂️ Типы конфигурационных файлов

| Файл | Назначение | Коммитится в Git |
|------|------------|------------------|
| `env.example` | Примеры всех переменных | ✅ Да |
| `.env.local` | Локальная разработка | ❌ Нет |
| `.env.development` | Development среда | ❌ Нет |  
| `.env.production` | Production среда | ❌ Нет |

### 🔀 Приоритет загрузки конфигурации

1. `.env.local` (высший приоритет)
2. `.env.development` 
3. `.env.production`
4. `.env` (fallback)

### 🏗️ Конфигурация по средам

#### Development (Разработка)
```env
ENVIRONMENT=development

# Vector DB
QDRANT_URL=https://dev-cluster.qdrant.io:6333
QDRANT_API_KEY=dev_api_key

# PostgreSQL (локальная БД)
POSTGRESQL_URL=postgresql+asyncpg://dev_user:dev_pass@localhost:5432/materials_dev

# Redis (локальный)
REDIS_URL=redis://localhost:6379

# OpenAI
OPENAI_API_KEY=sk-dev_key
OPENAI_MODEL=text-embedding-3-small

# CORS (разрешить все для разработки)
BACKEND_CORS_ORIGINS=["*"]

# Logging
LOG_LEVEL=DEBUG
```

#### Production (Продакшн)
```env
ENVIRONMENT=production

# Vector DB
QDRANT_URL=https://prod-cluster.qdrant.io:6333
QDRANT_API_KEY=prod_api_key

# PostgreSQL (managed БД)
POSTGRESQL_URL=postgresql+asyncpg://prod_user:secure_pass@prod-db.aws.com:5432/materials

# Redis (managed cache)
REDIS_URL=redis://prod-cache.aws.com:6379
REDIS_PASSWORD=secure_redis_pass

# OpenAI
OPENAI_API_KEY=sk-prod_key
OPENAI_MODEL=text-embedding-3-small

# CORS (только нужные домены)
BACKEND_CORS_ORIGINS=["https://yourdomain.com", "https://api.yourdomain.com"]

# Security
SECRET_KEY=very_secure_production_key
JWT_EXPIRE_MINUTES=30

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 🔍 Валидация конфигурации

API автоматически валидирует:
- ✅ Формат URL для Qdrant, PostgreSQL, Redis
- ✅ Формат OpenAI API ключа (должен начинаться с `sk-`)
- ✅ Допустимые значения ENVIRONMENT
- ✅ Размер MAX_UPLOAD_SIZE (не более 100MB)

### 🚀 Запуск с разными конфигурациями

```bash
# Локальная разработка
cp env.example .env.local 
# Отредактируйте .env.local
uvicorn main:app --reload

# Development среда
cp env.example .env.development
# Отредактируйте .env.development  
ENVIRONMENT=development uvicorn main:app

# Production среда
cp env.example .env.production
# Отредактируйте .env.production
ENVIRONMENT=production uvicorn main:app --host 0.0.0.0 --port 8000
```

### 🔐 Безопасность

**❌ НИКОГДА не коммитьте файлы с реальными секретами:**
- `.env.local`
- `.env.development` 
- `.env.production`
- `.env`

**✅ Безопасные практики:**
- Используйте `env.example` для документации
- Храните секреты в переменных окружения
- Ротируйте API ключи регулярно
- Используйте разные ключи для разных сред

### 🆘 Troubleshooting

#### Проблема: "QDRANT_URL must be a valid HTTP/HTTPS URL"
**Решение:** Убедитесь что URL начинается с `http://` или `https://`

#### Проблема: "OPENAI_API_KEY must start with 'sk-'"
**Решение:** Проверьте формат ключа OpenAI

#### Проблема: Конфигурация не загружается
**Решение:** 
1. Проверьте имя файла (.env.local)
2. Проверьте права доступа к файлу
3. Убедитесь что файл находится в корне проекта

### 📊 Проверка конфигурации

Используйте health check endpoint для проверки:
```bash
curl http://localhost:8000/api/v1/health/config
```

Он покажет:
- ✅ Какие настройки загружены
- ❌ Какие настройки отсутствуют
- 🔧 Какие БД доступны 