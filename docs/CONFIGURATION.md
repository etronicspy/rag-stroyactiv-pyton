# ⚙️ Конфигурация проекта

## 📋 Обзор

Система конфигурации проекта централизована в `core/config.py` и использует Pydantic Settings для управления переменными окружения.

## 🔧 Основные настройки

### Переменные окружения
Скопируйте `env.example` в `.env.local` и настройте значения:

```bash
cp env.example .env.local
```

### Обязательные переменные

#### Векторная БД (Qdrant)
```env
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION_NAME=materials
QDRANT_VECTOR_SIZE=1536
```

#### AI Provider (OpenAI)
```env
OPENAI_API_KEY=sk-your_openai_api_key
OPENAI_MODEL=text-embedding-3-small
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=30
```

### Дополнительные БД

#### PostgreSQL (через SSH туннель)
```env
POSTGRESQL_URL=postgresql+asyncpg://user:pass@localhost:5435/stbr_rag1
POSTGRESQL_DATABASE=stbr_rag1
POSTGRESQL_USER=your_user
POSTGRESQL_PASSWORD=your_password
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5435

# SSH туннель
ENABLE_SSH_TUNNEL=true
SSH_TUNNEL_REMOTE_HOST=31.130.148.200
SSH_TUNNEL_REMOTE_USER=root
SSH_TUNNEL_REMOTE_PORT=5432
SSH_TUNNEL_LOCAL_PORT=5435
SSH_TUNNEL_KEY_PATH=~/.ssh/postgres_key
```

> **⚠️ Важно**: Проект работает только с базой данных `stbr_rag1` (ICU локаль ru-RU-x-icu для поддержки русского языка).

#### Redis (кеширование)
```env
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password
REDIS_MAX_CONNECTIONS=50
REDIS_TIMEOUT=5
```

## 🎯 Режимы работы

### Development Mode
```env
ENVIRONMENT=development
QDRANT_ONLY_MODE=false
ENABLE_FALLBACK_DATABASES=true
LOG_LEVEL=DEBUG
```

### Production Mode
```env
ENVIRONMENT=production
QDRANT_ONLY_MODE=false
ENABLE_FALLBACK_DATABASES=false
LOG_LEVEL=INFO
```

## 🔄 Fallback настройки

Система поддерживает fallback к mock-адаптерам:

```env
# Отключить подключения к БД (использовать mock)
DISABLE_REDIS_CONNECTION=true
DISABLE_POSTGRESQL_CONNECTION=false

# Включить fallback при ошибках
ENABLE_FALLBACK_DATABASES=true
```

## 🛡️ Middleware настройки

### Безопасность
```env
MAX_REQUEST_SIZE_MB=50
ENABLE_SECURITY_HEADERS=true
ENABLE_INPUT_VALIDATION=true
```

### Rate Limiting
```env
ENABLE_RATE_LIMITING=true
RATE_LIMIT_RPM=60
RATE_LIMIT_RPH=1000
```

### Логирование
```env
LOG_LEVEL=INFO
LOG_REQUEST_BODY=true
LOG_RESPONSE_BODY=false
ENABLE_STRUCTURED_LOGGING=false
```

## 📊 Производительность

```env
MAX_UPLOAD_SIZE=52428800  # 50MB
BATCH_SIZE=100
MAX_CONCURRENT_UPLOADS=5
```

## 🔧 Использование в коде

### Settings
```python
from core.config import settings

# Получение настроек
db_config = settings.get_vector_db_config()
ai_config = settings.get_ai_config()

# Проверка окружения
if settings.is_production():
    # Production логика
    pass
```

### Dependency Injection
```python
from core.dependencies.database import get_vector_db_dependency

@app.get("/search")
async def search(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency)
):
    return await vector_db.search(...)
```

## 🔍 Проверка конфигурации

### Health Check
```bash
# Проверка основных сервисов
curl http://localhost:8000/api/v1/health/

# Полная диагностика всех систем
curl http://localhost:8000/api/v1/health/full
```

### Логирование
```python
import logging

# Включение DEBUG для диагностики
logging.getLogger("core.config").setLevel(logging.DEBUG)
logging.getLogger("core.database").setLevel(logging.DEBUG)
```

## 🔄 Переключение БД

### Только Qdrant (development)
```env
QDRANT_ONLY_MODE=true
DISABLE_POSTGRESQL_CONNECTION=true
DISABLE_REDIS_CONNECTION=true
```

### Полная архитектура (production)
```env
QDRANT_ONLY_MODE=false
DISABLE_POSTGRESQL_CONNECTION=false
DISABLE_REDIS_CONNECTION=false
```

## 🚨 Troubleshooting

### Ошибки подключения
```bash
# Проверка настроек
echo $QDRANT_URL
echo $OPENAI_API_KEY

# Проверка health check
curl http://localhost:8000/api/v1/health/full
```

### SSH туннель
```bash
# Проверка SSH ключа
ssh -i ~/.ssh/postgres_key root@31.130.148.200

# Проверка туннеля
ENABLE_SSH_TUNNEL=true
SSH_TUNNEL_TIMEOUT=30
```

## 📚 Полный пример .env.local

```env
# === ОСНОВНЫЕ НАСТРОЙКИ ===
PROJECT_NAME=RAG Construction Materials API
VERSION=1.0.0
ENVIRONMENT=development

# === ВЕКТОРНАЯ БД ===
QDRANT_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your_qdrant_key
QDRANT_COLLECTION_NAME=materials

# === AI PROVIDER ===
OPENAI_API_KEY=sk-your_openai_key
OPENAI_MODEL=text-embedding-3-small

# === POSTGRESQL ===
POSTGRESQL_URL=postgresql+asyncpg://user:pass@localhost:5435/stbr_rag1
ENABLE_SSH_TUNNEL=true

# === REDIS ===
REDIS_URL=redis://localhost:6379

# === РЕЖИМ РАБОТЫ ===
QDRANT_ONLY_MODE=false
ENABLE_FALLBACK_DATABASES=true

# === БЕЗОПАСНОСТЬ ===
MAX_REQUEST_SIZE_MB=50
ENABLE_RATE_LIMITING=true
RATE_LIMIT_RPM=60

# === ЛОГИРОВАНИЕ ===
LOG_LEVEL=DEBUG
LOG_REQUEST_BODY=true
```

---

**Обновлено**: $(date +%Y-%m-%d) 