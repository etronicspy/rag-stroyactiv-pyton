# 🔧 План отладки и подготовки проекта к рабочему состоянию

*Дата создания: 13 декабря 2024*  
*Статус: Готов к выполнению*

## 📋 Краткий анализ текущего состояния

### 🔍 Обнаруженные проблемы:

1. **КРИТИЧЕСКАЯ: Проблемы с подключением к БД**
   - Файл `.env.local` существует с рабочими настройками реальных API
   - `QDRANT_URL`, `QDRANT_API_KEY`, `OPENAI_API_KEY` настроены на реальные сервисы
   - Приложение не может корректно подключиться к настроенным БД
   - Ошибка: `[Errno 8] nodename nor servname provided, or not known`

2. **Проблемы с PostgreSQL адаптером**
   - Неправильная реализация async context manager
   - Ошибка: `'coroutine' object does not support the asynchronous context manager protocol`

3. **Functional тесты подключаются к реальным БД**
   - Должны использовать mock-объекты для изоляции
   - 4 из 4 функциональных тестов падают

4. **Отсутствующие импорты в integration тестах**
   - Ошибки импорта `Mock`, `DatabaseInitializer`

## 🎯 План отладки и подготовки (поэтапно)

### Этап 1: Настройка конфигурации (Критический - 15 минут)

#### 1.1 Проверка существующего файла .env.local
- [x] Файл `.env.local` уже существует с рабочими настройками
- [x] `QDRANT_URL`, `QDRANT_API_KEY`, `OPENAI_API_KEY` настроены на реальные API
- [x] Проверить дополнительные настройки для отладки
- [x] Добавить fallback и debug-режимы при необходимости

#### 1.2 Проверка переменных окружения
```bash
# Уже настроены (используют реальные API):
QDRANT_URL=<реальный URL Qdrant>
QDRANT_API_KEY=<реальный API ключ Qdrant>
OPENAI_API_KEY=<реальный API ключ OpenAI>

# Возможные дополнительные настройки для отладки:
ENVIRONMENT=development
LOG_LEVEL=DEBUG
ENABLE_FALLBACK_DATABASES=true
AUTO_MIGRATE=true
AUTO_SEED=true

# Отладочные настройки
LOG_LEVEL=DEBUG
ENABLE_FALLBACK_DATABASES=true
DISABLE_REDIS_CONNECTION=true  
DISABLE_POSTGRESQL_CONNECTION=true
QDRANT_TIMEOUT=60
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=5
ENABLE_RATE_LIMITING=false
ENABLE_REQUEST_LOGGING=true
```

### Этап 2: Исправление PostgreSQL адаптера (Критический - 10 минут)

#### 2.1 Исправление async context manager
- [x] Исправить метод создания engine в `postgresql_adapter.py`
- [x] Убедиться что `create_async_engine` возвращает правильный объект
- [x] Добавить proper async context manager support

### Этап 3: Исправление тестов (20 минут)

#### 3.1 Functional тесты
- [x] Переключить на использование mock клиентов
- [x] Убрать реальные подключения к Qdrant
- [x] Обновить фикстуры для использования заглушек

#### 3.2 Integration тесты  
- [x] Добавить отсутствующие импорты:
  ```python
  from unittest.mock import Mock
  from core.database.init_db import DatabaseInitializer
  ```
- [x] Исправить фикстуры для правильной работы с async

#### 3.3 Исправление мелких проблем в тестах
- [x] Исправить проверку на "empty" в тестах обработки файлов
- [x] Обновить middleware тесты для соответствия API

### Этап 4: Проверка и запуск (15 минут)

#### 4.1 Проверка запуска приложения
- [ ] Запустить `uvicorn main:app --reload`
- [ ] Проверить что приложение запускается без ошибок
- [ ] Проверить health endpoints

#### 4.2 Проверка тестов
- [ ] Запустить полный набор тестов
- [ ] Убедиться что критические тесты проходят
- [ ] Проверить что mock-режим работает корректно

#### 4.3 Проверка основной функциональности
- [ ] Протестировать API endpoints через Swagger
- [ ] Проверить загрузку файлов в mock-режиме  
- [ ] Убедиться что поиск работает с заглушками

## 🚀 Готовые решения для быстрого исправления

### Решение 1: Проверка конфигурации .env.local
**Статус**: Файл `.env.local` существует с рабочими настройками реальных API

**Подтвержденные настройки:**
- ✅ `QDRANT_URL` - настроен на реальный Qdrant API
- ✅ `QDRANT_API_KEY` - действующий API ключ Qdrant
- ✅ `OPENAI_API_KEY` - действующий API ключ OpenAI

**Возможные дополнительные настройки для отладки:**
```env
# Режим отладки и логирования
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Настройки подключения
QDRANT_TIMEOUT=60
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=5

# Fallback настройки
ENABLE_FALLBACK_DATABASES=true
```

### Решение 2: Исправление PostgreSQL адаптера
```python
# В postgresql_adapter.py, метод __init__
async def __init__(self, connection_string: str, pool_size: int = 5):
    self.connection_string = connection_string
    self.pool_size = pool_size
    self.engine = create_async_engine(
        connection_string,
        pool_size=pool_size,
        pool_pre_ping=True,
        echo=False
    )
    # Убрать await отсюда - engine не нужно awaited при создании
```

### Решение 3: Mock фикстуры для functional тестов
```python
@pytest.fixture
async def mock_qdrant_client():
    """Mock Qdrant client for functional tests"""
    mock_client = Mock()
    mock_client.get_collections.return_value = Mock()
    mock_client.search.return_value = []
    return mock_client
```

## ⏱️ Временные рамки

| Этап | Время | Приоритет |
|------|-------|-----------|
| Этап 1: Конфигурация | 15 мин | Критический |
| Этап 2: PostgreSQL | 10 мин | Критический |  
| Этап 3: Тесты | 20 мин | Высокий |
| Этап 4: Проверка | 15 мин | Средний |
| **ИТОГО** | **60 мин** | |

## 🎯 Ожидаемые результаты

После выполнения плана отладки:

✅ **Приложение запускается без ошибок в mock-режиме**  
✅ **API доступно через http://localhost:8000**  
✅ **Swagger документация работает на /docs**  
✅ **Health checks возвращают статус OK**  
✅ **Unit тесты проходят (92% success rate)**  
✅ **Performance тесты стабильны (91% success rate)**  
✅ **Functional тесты работают в mock-режиме**  
✅ **Проект готов к отладке и дальнейшей разработке**  

## 🔄 Следующие шаги (после подготовки к работе)

1. **Настройка реальных БД** (когда будет нужно для продакшн)
2. **Доработка remaining тестов** (integration, middleware)
3. **Настройка CI/CD pipeline**
4. **Добавление coverage отчетов**

## ℹ️ Дополнительная информация

**Файл конфигурации**: `.env.local` уже существует в корне проекта с рабочими настройками реальных API.

**Подтвержденные рабочие настройки:**
- `QDRANT_URL` - подключение к реальному Qdrant API
- `QDRANT_API_KEY` - действующий API ключ для Qdrant
- `OPENAI_API_KEY` - действующий API ключ для OpenAI

**Проблема**: Несмотря на правильные настройки API, приложение не может корректно подключиться к сервисам. Требуется отладка логики подключения и обработки ошибок.

---

**Статус**: Готов к выполнению  
**Тип**: План отладки и подготовки к работе  
**Приоритет**: Критический  
**Время выполнения**: 1 час 