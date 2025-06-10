# Конфигурация проекта

## 🎯 Обзор

Вся конфигурация проекта централизована в `core/config.py` и поддерживает гибкое переключение между различными базами данных и провайдерами ИИ.

## 📁 Структура конфигурации

```
core/
├── config.py           # Основная конфигурация
├── models/             # Модели данных
└── schemas/            # Pydantic схемы
```

## ⚙️ Переменные окружения

### Основные настройки

```bash
# Окружение проекта
PROJECT_NAME="RAG Construction Materials API"
VERSION="1.0.0"
ENVIRONMENT="development"  # development, staging, production

# CORS настройки
BACKEND_CORS_ORIGINS=[]
```

### База данных (Vector DB)

```bash
# Тип векторной базы данных
DATABASE_TYPE="qdrant_cloud"  # qdrant_cloud, qdrant_local, weaviate, pinecone

# Qdrant настройки
QDRANT_URL="https://your-cluster.qdrant.io"
QDRANT_API_KEY="your-api-key"
QDRANT_COLLECTION_NAME="materials"
QDRANT_VECTOR_SIZE=384
QDRANT_TIMEOUT=30

# Альтернативные векторные БД (опционально)
WEAVIATE_URL=""
WEAVIATE_API_KEY=""
PINECONE_API_KEY=""
PINECONE_ENVIRONMENT=""
```

### ИИ провайдер

```bash
# Тип провайдера ИИ
AI_PROVIDER="openai"  # openai, azure_openai, huggingface, ollama

# OpenAI настройки
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="text-embedding-ada-002"
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=30

# Azure OpenAI (опционально)
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_MODEL=""

# HuggingFace (опционально)
HUGGINGFACE_MODEL="sentence-transformers/all-MiniLM-L6-v2"
HUGGINGFACE_DEVICE="cpu"

# Ollama (опционально)
OLLAMA_URL=""
OLLAMA_MODEL=""
```



### Производительность

```bash
# Настройки производительности
MAX_UPLOAD_SIZE=52428800  # 50MB
BATCH_SIZE=100
MAX_CONCURRENT_UPLOADS=5
```

## 🏗️ Фабрики клиентов

### Векторная база данных

```python
from core.config import get_vector_db_client

# Автоматически создает клиент для настроенной БД
client = get_vector_db_client()
```

### ИИ провайдер

```python
from core.config import get_ai_client

# Автоматически создает клиент для настроенного провайдера
ai_client = get_ai_client()
```



## 🔄 Переключение между провайдерами

### Смена векторной БД

1. **Qdrant Cloud → Qdrant Local:**
```bash
DATABASE_TYPE="qdrant_local"
QDRANT_URL="http://localhost:6333"
QDRANT_API_KEY=""  # Не требуется для локального
```

2. **Qdrant → Weaviate:**
```bash
DATABASE_TYPE="weaviate"
WEAVIATE_URL="http://localhost:8080"
WEAVIATE_API_KEY="your-weaviate-key"
```

### Смена ИИ провайдера

1. **OpenAI → HuggingFace:**
```bash
AI_PROVIDER="huggingface"
HUGGINGFACE_MODEL="sentence-transformers/all-MiniLM-L6-v2"
HUGGINGFACE_DEVICE="cpu"
```

2. **OpenAI → Azure OpenAI:**
```bash
AI_PROVIDER="azure_openai"
AZURE_OPENAI_API_KEY="your-azure-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_MODEL="text-embedding-ada-002"
```

## 🛡️ Безопасность

### Принципы безопасности

1. **Никогда не коммитьте `.env.local`** в репозиторий
2. **Используйте разные ключи** для разных окружений
3. **Ротируйте ключи** регулярно
4. **Ограничивайте права доступа** ключей

### Проверка конфигурации

```python
from core.config import settings

# Проверка производственного окружения
if settings.is_production():
    # Дополнительные проверки безопасности
    pass

# Проверка тестового окружения
if settings.is_testing():
    # Настройки для тестов
    pass
```

## 📊 Мониторинг конфигурации

### Health Check

```bash
# Базовая проверка здоровья
curl http://localhost:8000/api/v1/health

# Детальная проверка конфигурации
curl http://localhost:8000/api/v1/health/config
```

### Быстрая диагностика

```bash
# Скрипт для проверки всех подключений
python check_db_connection.py
```

## 🔧 Примеры конфигураций

### Разработка (Development)

```bash
ENVIRONMENT="development"
DATABASE_TYPE="qdrant_cloud"
AI_PROVIDER="openai"
```

### Тестирование (Testing)

```bash
ENVIRONMENT="testing"
DATABASE_TYPE="qdrant_cloud"
AI_PROVIDER="huggingface"  # Не требует ключей
```

### Производство (Production)

```bash
ENVIRONMENT="production"
DATABASE_TYPE="qdrant_cloud"
AI_PROVIDER="openai"
```

## 🚀 Миграция между конфигурациями

### Шаги миграции

1. **Бэкап данных** из текущей БД
2. **Обновление переменных** окружения
3. **Тестирование подключений** с помощью `check_db_connection.py`
4. **Перенос данных** в новую БД
5. **Проверка работоспособности** приложения

### Инструменты для миграции

```bash
# Создание резервной копии
python tools/backup_data.py

# Миграция данных
python tools/migrate_data.py --from qdrant --to weaviate

# Проверка после миграции
python tools/verify_migration.py
```

## 📝 Примеры использования

### В сервисах

```python
# services/materials.py
from core.config import get_vector_db_client, get_ai_client, settings

class MaterialsService:
    def __init__(self):
        self.vector_client = get_vector_db_client()
        self.ai_client = get_ai_client()
        self.config = settings.get_vector_db_config()
```

### В тестах

```python
# tests/conftest.py
from core.config import settings

@pytest.fixture
def test_settings():
    # Переопределение настроек для тестов
    settings.ENVIRONMENT = "testing"
    settings.DATABASE_TYPE = "qdrant_local"
    return settings
```

## ❓ FAQ

**Q: Как добавить новый провайдер ИИ?**
A: Добавьте новый тип в `AIProvider` enum и реализуйте в `get_ai_client()`.

**Q: Можно ли использовать несколько векторных БД одновременно?**
A: Нет, поддерживается одна активная БД, но можно легко переключаться.

**Q: Как обновить модель эмбеддингов?**
A: Измените `OPENAI_MODEL` или `HUGGINGFACE_MODEL` в `.env.local`.

**Q: Безопасно ли хранить ключи в переменных окружения?**
A: Да, если файл `.env.local` не попадает в репозиторий и сервер защищен. 