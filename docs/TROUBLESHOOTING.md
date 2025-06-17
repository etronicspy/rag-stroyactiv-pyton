# 🚨 Troubleshooting Guide

## 📋 Обзор

Руководство по диагностике и устранению типичных проблем RAG Construction Materials API.

## 🔧 POST запросы зависают

### Симптомы
- POST/PUT/PATCH запросы не возвращают ответ
- Timeout ошибки на API запросах
- Зависание middleware

### Решение
```bash
# 1. Установите правильную версию greenlet
pip install greenlet==3.0.1

# 2. Запустите БЕЗ --reload флага
uvicorn main:app --host 0.0.0.0 --port 8000

# 3. Проверьте логи на успешное кеширование body
# Должны видеть: "Body cached, size: X bytes"
# НЕ должны видеть: "ASGI callable returned without completing response"
```

### Причина
Проблема была в двойном чтении `request.body()` в middleware, что приводило к зависанию ASGI. Решена через `BodyCacheMiddleware`.

## 🗄️ Проблемы с базами данных

### Проверка статуса БД
```bash
# Базовая проверка
curl http://localhost:8000/api/v1/health/

# Детальная диагностика всех БД
curl http://localhost:8000/api/v1/health/detailed

# Только статус БД
curl http://localhost:8000/api/v1/health/databases
```

### Qdrant подключение
```bash
# Проверка переменных
echo $QDRANT_URL
echo $QDRANT_API_KEY

# Прямая проверка Qdrant
curl -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections"
```

### PostgreSQL через SSH туннель
```bash
# Проверка SSH ключа
ssh -i ~/.ssh/postgres_key root@31.130.148.200 "echo connected"

# Проверка туннеля
ss -tulnp | grep 5435

# Проверка подключения к БД
psql postgresql://user:pass@localhost:5435/stbr_rag1 -c "SELECT 1"
```

### Redis подключение
```bash
# Проверка Redis
redis-cli ping

# Проверка конфигурации
redis-cli config get "*"

# Мониторинг памяти
redis-cli info memory
```

## 🚀 SSH Tunnel Service

### Проблема: Connection Reset
```
ssh_exchange_identification: Connection closed by remote host
```

**Решение:**
```env
# Увеличьте timeout
SSH_TUNNEL_TIMEOUT=60
SSH_TUNNEL_RETRY_ATTEMPTS=5
SSH_TUNNEL_RETRY_DELAY=10

# Включите keep-alive
SSH_TUNNEL_KEEP_ALIVE=60
SSH_TUNNEL_AUTO_RESTART=true
```

### Проблема: Permission Denied
```
Permission denied (publickey)
```

**Решение:**
```bash
# Проверьте права на ключ
chmod 600 ~/.ssh/postgres_key

# Добавьте ключ в agent
ssh-add ~/.ssh/postgres_key

# Проверьте путь к ключу
SSH_TUNNEL_KEY_PATH=/absolute/path/to/key
```

## 🔍 Проблемы поиска

### Векторный поиск не работает
```bash
# Проверка OpenAI ключа
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Проверка коллекции Qdrant
curl -H "api-key: $QDRANT_API_KEY" \
  "$QDRANT_URL/collections/materials"
```

### Fallback к SQL поиску
```python
# Включение fallback стратегии
ENABLE_FALLBACK_DATABASES=true

# Отладка поиска
LOG_LEVEL=DEBUG
```

## ⚡ Проблемы производительности

### Медленные запросы
```bash
# PostgreSQL анализ запросов
EXPLAIN ANALYZE SELECT * FROM materials WHERE name ILIKE '%цемент%';

# Проверка индексов
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'materials';
```

### Cache Hit Rate
```python
# Проверка статистики кеша
stats = await cached_repo.get_cache_stats()
if stats["cache_performance"]["hit_rate"] < 0.7:
    # Увеличить TTL или оптимизировать cache warming
```

## 🔧 Ошибки миграций

### Alembic ошибки
```bash
# Проверка текущей версии
alembic current

# Сброс миграций (ОСТОРОЖНО!)
alembic downgrade base
alembic upgrade head

# Создание новой миграции
alembic revision --autogenerate -m "Fix issue"
```

### Schema conflicts
```sql
-- Проверка схемы
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Проверка индексов
SELECT * FROM pg_indexes WHERE tablename = 'materials';
```

## 📊 Middleware проблемы

### Rate Limiting ошибки
```
429 Too Many Requests
```

**Решение:**
```env
# Отключить или увеличить лимиты
ENABLE_RATE_LIMITING=false
# ИЛИ
RATE_LIMIT_RPM=300
RATE_LIMIT_RPH=5000
```

### Security Middleware ошибки
```
413 Payload Too Large
```

**Решение:**
```env
# Увеличить размер запроса
MAX_REQUEST_SIZE_MB=100
```

## 🚨 Критические ошибки

### 503 Service Unavailable
1. Проверьте health check: `/api/v1/health/detailed`
2. Проверьте логи приложения
3. Включите fallback: `ENABLE_FALLBACK_DATABASES=true`

### 500 Internal Server Error
1. Проверьте логи: `LOG_LEVEL=DEBUG`
2. Проверьте подключения к БД
3. Проверьте API ключи

## 🔍 Диагностические команды

### Проверка окружения
```bash
# Все переменные окружения
env | grep -E "(QDRANT|OPENAI|POSTGRESQL|REDIS|SSH)"

# Проверка портов
netstat -tulnp | grep -E "(6333|5435|6379)"

# Проверка процессов
ps aux | grep -E "(uvicorn|ssh|redis)"
```

### Логирование
```python
import logging

# Включение детального логирования
logging.getLogger("core.database").setLevel(logging.DEBUG)
logging.getLogger("core.middleware").setLevel(logging.DEBUG)
logging.getLogger("services").setLevel(logging.DEBUG)
```

### Health Check Scripts
```bash
#!/bin/bash
# health_check.sh

echo "=== API Health ==="
curl -s http://localhost:8000/api/v1/health/ | jq

echo "=== Database Health ==="
curl -s http://localhost:8000/api/v1/health/databases | jq

echo "=== Detailed Health ==="
curl -s http://localhost:8000/api/v1/health/detailed | jq
```

## 📞 Получение помощи

### Сбор информации для отладки
```bash
# Версия Python
python --version

# Установленные пакеты
pip list | grep -E "(fastapi|qdrant|redis|psycopg|sqlalchemy)"

# Статус API
curl -s http://localhost:8000/api/v1/health/detailed | jq '.'

# Логи приложения (последние 50 строк)
tail -50 app.log
```

### Контрольный список диагностики
- [ ] API отвечает на `/health/`
- [ ] Все БД доступны в `/health/databases`
- [ ] SSH туннель активен (если используется)
- [ ] API ключи настроены корректно
- [ ] Middleware не блокирует запросы
- [ ] Логи не содержат критических ошибок

---

**Обновлено**: $(date +%Y-%m-%d) 