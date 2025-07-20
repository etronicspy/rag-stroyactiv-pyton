# 🔧 Миграция констант в переменные окружения

## Обзор

Все hardcoded константы из `core/config/constants.py` были перенесены в переменные окружения для обеспечения гибкости конфигурации и соблюдения принципов безопасности.

## ✅ Выполненные изменения

### 1. Обновлен файл `core/config/constants.py`

Все константы теперь читаются из переменных окружения с fallback значениями:

```python
# Было:
class DefaultTimeouts:
    DATABASE = 30

# Стало:
class DefaultTimeouts:
    DATABASE = get_env_int("DEFAULT_TIMEOUT_DATABASE", 30)
```

### 2. Добавлены переменные окружения в `env.example`

Все константы теперь доступны как переменные окружения:

```env
# --- Default Timeouts ---
DEFAULT_TIMEOUT_DATABASE=30
DEFAULT_TIMEOUT_AI_CLIENT=30
DEFAULT_TIMEOUT_CONNECTION_POOL=30
DEFAULT_TIMEOUT_REDIS=10
DEFAULT_TIMEOUT_SSH_TUNNEL=30

# --- Default Ports ---
DEFAULT_PORT_POSTGRESQL=5432
DEFAULT_PORT_REDIS=6379
DEFAULT_PORT_SSH_TUNNEL_LOCAL=5435

# --- File Size Limits ---
FILE_SIZE_MAX_UPLOAD_BYTES=52428800
FILE_SIZE_MAX_UPLOAD_MB=50
FILE_SIZE_MAX_CONFIG_FILE_BYTES=104857600
FILE_SIZE_MAX_CONFIG_FILE_MB=100

# --- Database Names ---
DATABASE_NAME_QDRANT_COLLECTION=materials
DATABASE_NAME_WEAVIATE_CLASS=Material
DATABASE_NAME_PINECONE_INDEX=materials
DATABASE_NAME_POSTGRESQL_DB=stbr_rag1
DATABASE_NAME_REDIS_KEY_PREFIX=rag:

# --- Model Names ---
MODEL_NAME_OPENAI_EMBEDDING=text-embedding-3-small
MODEL_NAME_HUGGINGFACE_DEFAULT=sentence-transformers/all-MiniLM-L6-v2
MODEL_NAME_AZURE_API_VERSION=2023-05-15

# --- Connection Pool Settings ---
CONNECTION_POOL_POSTGRESQL_POOL_SIZE=10
CONNECTION_POOL_POSTGRESQL_MAX_OVERFLOW=20
CONNECTION_POOL_REDIS_MAX_CONNECTIONS=50
CONNECTION_POOL_BATCH_SIZE=100
CONNECTION_POOL_MAX_CONCURRENT_UPLOADS=5

# --- Rate Limiting Settings ---
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_BURST_LIMIT=10

# --- SSH Tunnel Defaults ---
SSH_DEFAULT_REMOTE_HOST=31.130.148.200
SSH_DEFAULT_REMOTE_USER=root
SSH_DEFAULT_KEY_PATH=~/.ssh/postgres_key
SSH_DEFAULT_RETRY_ATTEMPTS=3
SSH_DEFAULT_RETRY_DELAY=5
SSH_DEFAULT_KEEP_ALIVE=60

# --- Cache Settings ---
CACHE_REDIS_DEFAULT_TTL=3600

# --- Parser Constants ---
PARSER_CONSTANT_DEFAULT_OPENAI_MODEL=gpt-4o-mini
PARSER_CONSTANT_DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
PARSER_CONSTANT_DEFAULT_EMBEDDING_DIMENSIONS=1536
PARSER_CONSTANT_DEFAULT_BATCH_SIZE=10
PARSER_CONSTANT_MAX_BATCH_SIZE=50
PARSER_CONSTANT_MIN_BATCH_SIZE=1
PARSER_CONSTANT_DEFAULT_CONFIDENCE_THRESHOLD=0.85
PARSER_CONSTANT_MIN_CONFIDENCE_THRESHOLD=0.1
PARSER_CONSTANT_MAX_CONFIDENCE_THRESHOLD=1.0
PARSER_CONSTANT_DEFAULT_PARSER_TIMEOUT=30
PARSER_CONSTANT_DEFAULT_AI_REQUEST_TIMEOUT=45
PARSER_CONSTANT_DEFAULT_BATCH_TIMEOUT=300
PARSER_CONSTANT_DEFAULT_RETRY_ATTEMPTS=3
PARSER_CONSTANT_MAX_RETRY_ATTEMPTS=10
PARSER_CONSTANT_DEFAULT_CACHE_TTL=3600
PARSER_CONSTANT_DEFAULT_EMBEDDING_CACHE_TTL=86400

# --- Collection Names ---
COLLECTION_NAME_CONSTRUCTION_COLORS=construction_colors
COLLECTION_NAME_CONSTRUCTION_UNITS=construction_units
COLLECTION_NAME_CONSTRUCTION_CATEGORIES=construction_categories
```

### 3. Обновлены файлы конфигурации

#### `core/config/base.py`
- Убраны hardcoded значения в SSH tunnel конфигурации
- Обновлены AI настройки для использования констант
- Обновлены performance settings

#### `core/config/parsers.py`
- Все parser константы теперь читаются из переменных окружения
- Добавлены импорты функций для работы с env переменными

#### `services/tunnel/tunnel_config.py`
- SSH tunnel настройки теперь используют константы из constants.py
- Добавлены импорты DefaultTimeouts, DefaultPorts, SSHDefaults

#### `core/database/pool_manager.py`
- Pool configuration теперь использует константы
- Добавлены импорты DefaultTimeouts, ConnectionPools

#### `core/middleware/rate_limiting.py` и `rate_limiting_optimized.py`
- Rate limiting настройки теперь используют константы
- Добавлены импорты RateLimits

## 🔧 Функции для работы с переменными окружения

В `core/config/constants.py` добавлены вспомогательные функции:

```python
def get_env_int(key: str, default: int) -> int:
    """Get integer value from environment variable."""
    return int(os.getenv(key, str(default)))

def get_env_str(key: str, default: str) -> str:
    """Get string value from environment variable."""
    return os.getenv(key, default)

def get_env_float(key: str, default: float) -> float:
    """Get float value from environment variable."""
    return float(os.getenv(key, str(default)))
```

## 📋 Преимущества миграции

### 1. Гибкость конфигурации
- Все настройки можно изменять без перекомпиляции кода
- Разные среды (dev, staging, prod) могут иметь разные значения
- Легкое A/B тестирование различных конфигураций

### 2. Безопасность
- Устранены hardcoded значения в коде
- Соблюдение принципа "configuration as code"
- Централизованное управление конфигурацией

### 3. Масштабируемость
- Легкое переключение между различными конфигурациями
- Поддержка контейнеризации (Docker, Kubernetes)
- Интеграция с системами управления секретами

### 4. Отладка и мониторинг
- Прозрачность конфигурации через переменные окружения
- Легкое логирование текущих настроек
- Возможность динамического изменения параметров

## 🚀 Использование

### Для разработчиков

1. Скопируйте `env.example` в `.env.local`:
```bash
cp env.example .env.local
```

2. Настройте необходимые переменные в `.env.local`

3. Все константы автоматически будут читаться из переменных окружения

### Для операций

1. Установите переменные окружения в production среде
2. Используйте системы управления секретами (HashiCorp Vault, AWS Secrets Manager)
3. Настройте CI/CD для автоматического деплоя конфигурации

## 🔍 Проверка конфигурации

Для проверки текущих значений констант можно использовать:

```python
from core.config.constants import DefaultTimeouts, DefaultPorts, FileSizeLimits

print(f"Database timeout: {DefaultTimeouts.DATABASE}")
print(f"PostgreSQL port: {DefaultPorts.POSTGRESQL}")
print(f"Max upload size: {FileSizeLimits.MAX_UPLOAD_MB}MB")
```

## 📝 Backward Compatibility

Все изменения обратно совместимы:
- Fallback значения соответствуют старым hardcoded значениям
- API констант остался неизменным
- Существующий код продолжит работать без изменений

## 🎯 Следующие шаги

1. **Тестирование**: Проверить работу всех модулей с новыми переменными окружения
2. **Документация**: Обновить документацию по развертыванию
3. **CI/CD**: Настроить автоматическое тестирование с различными конфигурациями
4. **Мониторинг**: Добавить мониторинг использования конфигурационных параметров 