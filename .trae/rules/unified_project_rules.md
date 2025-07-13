# 🎯 Unified Project Rules for RAG Construction Materials API

> Сборный файл правил для Trae IDE, объединяющий все правила из .cursor/rules/

## 🐍 Python Development Standards

### Language & Style
- **Python 3.9+** обязательно
- **FastAPI** фреймворк с async/await везде где возможно
- **Строгое соблюдение PEP 8**
- **Type hints** для всех функций, методов и переменных
- **Docstrings** для всех публичных функций, классов и методов
- **Pydantic модели**: обязательные примеры (example, schema_extra) для автодокументации

### Architecture Patterns
- **Dependency injection** для БД подключений с @lru_cache
- **Абстрактные интерфейсы (ABC)** для БД операций
- **SQLAlchemy 2.0+** с async для работы с PostgreSQL
- **Alembic миграции** для схемы БД
- **Repository pattern** для каждого типа БД

### FastAPI Specific
- **UTF8JSONResponse** для всех ответов API
- **Валидация** всех входящих данных через Pydantic
- **Middleware** логирования всех входящих запросов

## 🌐 API Design Principles

### Versioning & Structure
- **Версионирование /api/v1/**, pydantic модели
- **UTF-8 ответы**, обработка ошибок для всех БД
- **Описательные имена модулей**: `material_routes.py` вместо `routes.py`

### Data Formats
- **CSV/Excel**: обязательные поля (name, description), ограничение 50MB
- **Валидация** всех входящих данных через Pydantic
- **Обязательные примеры** в Pydantic схемах

### Search & Filtering
- **Fallback-стратегия**: vector_search → если 0 результатов → SQL LIKE поиск

### Security
- **Rate limiting** через Redis для всех эндпоинтов
- **CORS конфигурация** для продакшн среды
- **Ограничение размера** запросов и файлов (защита от атак)

## 🗄️ Database Architecture

### Architectural Patterns
- **Repository pattern** для каждого типа БД
- **Dependency injection** для БД подключений с @lru_cache
- **Абстрактные интерфейсы (ABC)** для БД операций
- **Фабрики клиентов** с автоматическим переключением БД
- **Runtime переключение БД** через конфигурацию

### Vector Databases
- **Обязательные методы**: search, upsert, delete, batch_upsert, get_by_id
- **Поддержка**: Qdrant, Weaviate, Pinecone с единым интерфейсом
- **Батчинг** для загрузки эмбеддингов
- **Логирование** всех операций с векторной БД

### Relational Databases
- **PostgreSQL**: SQLAlchemy 2.0+ с async, Alembic миграции

### Caching
- **Redis**: для кеширования и сессий

### Configuration & Connections
- **Connection pooling** для производительности
- **Timeout и retry** для всех БД
- **Легкое переключение** через .env файлы

## 🚨 CRITICAL: Filename Conflict Prevention

### ЗАПРЕЩЕННЫЕ ИМЕНА ФАЙЛОВ
**НИКОГДА не используйте эти имена для Python файлов:**

```
os.py, sys.py, time.py, json.py, logging.py, typing.py, 
pathlib.py, collections.py, functools.py, itertools.py,
operator.py, re.py, math.py, datetime.py, random.py,
string.py, io.py, csv.py, sqlite3.py, urllib.py, http.py,
email.py, html.py, xml.py, multiprocessing.py, threading.py,
asyncio.py, subprocess.py, shutil.py, tempfile.py, glob.py,
pickle.py, copy.py, heapq.py, bisect.py, array.py, struct.py,
binascii.py, base64.py, hashlib.py, hmac.py, secrets.py,
uuid.py, decimal.py, fractions.py, statistics.py, socket.py,
ssl.py, select.py, signal.py, mmap.py, ctypes.py, platform.py,
getpass.py, traceback.py, warnings.py, contextlib.py, abc.py,
atexit.py, weakref.py, gc.py, inspect.py, types.py, enum.py,
dataclasses.py, keyword.py, token.py, tokenize.py, ast.py,
unittest.py, doctest.py, pdb.py, profile.py, pstats.py,
timeit.py, cProfile.py, trace.py, test.py
```

### РЕКОМЕНДУЕМЫЕ АЛЬТЕРНАТИВЫ
```
core/
├── config/
│   ├── app_settings.py      # НЕ config.py
│   ├── database_config.py   # НЕ db.py
│   ├── log_config.py        # НЕ logging.py
│   └── type_definitions.py  # НЕ types.py
├── exceptions/
│   ├── api_exceptions.py    # НЕ exceptions.py
│   └── database_exceptions.py
└── services/
    ├── material_service.py  # НЕ service.py
    └── search_service.py
```

## 🔒 Security Rules

### ❌ КАТЕГОРИЧЕСКИЙ ЗАПРЕТ HARDCODED ЗНАЧЕНИЙ
**КРИТИЧЕСКОЕ ПРАВИЛО**: Полный запрет hardcoded конфигурационных значений в коде

#### Обязательные требования:
- **ВСЕ настройки** должны читаться из переменных окружения
- **ОБЯЗАТЕЛЬНОЕ** использование констант вместо магических чисел
- **СТРОГАЯ** валидация всех env переменных через Pydantic
- **ЦЕНТРАЛИЗАЦИЯ** конфигурации в core/config модулях

#### Правильные примеры:
```python
# ✅ ПРАВИЛЬНО: Через переменные окружения
timeout = settings.DATABASE_TIMEOUT
port = settings.SSH_TUNNEL_LOCAL_PORT

# ✅ ПРАВИЛЬНО: Константы в core/config/constants.py
from core.config.constants import DefaultTimeouts
timeout = DefaultTimeouts.DATABASE

# ❌ НЕПРАВИЛЬНО: Hardcoded значения
timeout = 30  
port = 5432
```

### Configuration Security
- **.env файлы** для каждой среды
- **Ротация паролей** и ключей БД
- **Валидация входящих данных** (защита от инъекций)
- **Ограничение размера** запросов и файлов

## 🧪 Testing Strategy

### Main Testing Framework
- **pytest** с фикстурами для каждого типа БД
- **Моки** для внешних БД в unit тестах
- **Интеграционные тесты** на реальных БД

### Test Types
- **Functional тесты**: mock-клиенты для изоляции от реальных API
- **Integration тесты**: реальные API при наличии рабочих ключей
- **Unit тесты**: изоляция зависимостей через моки
- **Performance тесты**: load testing для критических эндпоинтов

### Test Data Management
- **Фикстуры** для каждого типа БД
- **Генерация тестовых данных**
- **Очистка данных** после тестов
- **Изоляция тестовых сред**

## 🏗️ Project Structure

### Architecture
- **Структура**: api/routes, core/config, services
- **Централизованная конфигурация** из core/config
- **Версионирование API** (/api/v1/)
- **Описательные имена модулей**

### Data Processing
- **Поддержка CSV и Excel** для прайс-листов
- **Обязательные примеры** в Pydantic схемах
- **Именование моделей**: `material_models.py`, `response_models.py`

### Performance
- **Батчинг** для загрузки эмбеддингов
- **Избегание циклических импортов** через правильное именование файлов

## 📊 Monitoring & Logging

### Health Checks
- **Health checks** для всех подключений БД
- **Детальная диагностика** всех БД

### Logging Operations
- **Логирование операций** с каждой БД
- **Логирование подключений** к внешним API с деталями ошибок
- **LOG_LEVEL=DEBUG** для детальной диагностики

## 🛠️ Development Environment

### Environment Setup
- **Файл .env.local** с рабочими настройками реальных API
- **Не создавать новые .env файлы** без необходимости
- **Фокус на логике приложения**, не на конфигурации API ключей

### Debugging
- **Увеличенные timeout значения** при отладке подключений
- **Timeout и retry настройки** для стабильности
- **Fallback стратегии** для graceful degradation

## 📚 Documentation Standards

### Language Standards
- **Код и идентификаторы**: только английский язык
- **Документация, комментарии, README**: русский и английский

### Required Documentation
- **ADR** (Architecture Decision Records) для архитектурных изменений
- **README** для каждого модуля со сложной логикой
- **Inline-комментарии** для нетривиальных алгоритмов

### Docstrings Requirements
- **Google style** для Python
- **Обязательные секции**: Args, Returns, Raises, Example
- **Все публичные классы, методы и функции**
- **Все API эндпоинты** с примерами запросов/ответов

### API Documentation
- **OpenAPI спецификация** с описаниями всех эндпоинтов
- **Примеры запросов и ответов** в Pydantic моделях
- **Описание HTTP статус кодов**
- **Теги и группировка** эндпоинтов по модулям

## ⚙️ Environment & Configuration

### Configuration Protection
- **Файл .env.local защищен** от редактирования
- **env.example как шаблон** для демонстрации настроек
- **Не изменять .env.local** без крайней необходимости

### Configuration Management
- **core/config/base.py** - основные настройки с Pydantic валидацией
- **core/config/constants.py** - константы вместо магических чисел
- **core/config/database.py** - конфигурации БД
- **core/config/ai.py** - настройки AI провайдеров

### Environment Variables Requirements
- **Все** настройки должны иметь значения по умолчанию или быть обязательными
- **Обязательная** валидация через Pydantic field_validator
- **Типизация** всех переменных (str, int, bool, List[str])
- **Документация** каждой переменной через Field(description="...")

## 🔄 Git Workflow

### Branching Strategy
- **main** - продакшн готовый код, только через PR
- **develop** - основная ветка разработки
- **feature/** - новые функции (feature/vector-search-optimization)
- **fix/** - исправления багов (fix/database-connection-timeout)
- **hotfix/** - критические исправления в продакшн

### Commit Message Conventions
```
type(scope): description

[optional body]
[optional footer]
```

**Типы коммитов:**
- **feat**: новая функциональность
- **fix**: исправление бага
- **docs**: изменения в документации
- **style**: форматирование, отсутствие изменений кода
- **refactor**: рефакторинг кода без изменения функциональности
- **test**: добавление/изменение тестов
- **chore**: обновление зависимостей, конфигурации

### Pull Request Requirements
- **Четкое название** и описание изменений
- **Связанные Issues** и ссылки на задачи
- **Обязательная самопроверка** перед review
- **Все тесты проходят** локально
- **Обновлена документация** при необходимости

### Branch Protection
- **main ветка**: запрет прямых push, обязательный PR review
- **develop ветка**: обязательное прохождение тестов
- **Линейная история коммитов** предпочтительна

## 🚀 Best Practices Summary

### Code Quality
1. **Строгое соблюдение** PEP 8 и type hints
2. **Обязательные docstrings** для всех публичных элементов
3. **Безопасные имена файлов** - избегать конфликтов с stdlib
4. **Централизованная конфигурация** через переменные окружения
5. **Repository pattern** для всех БД операций

### Security
1. **Категорический запрет** hardcoded значений
2. **Валидация всех входящих данных** через Pydantic
3. **Rate limiting** и CORS для API
4. **Защита .env файлов** от случайного изменения
5. **Ротация ключей** и паролей БД

### Performance
1. **Батчинг** для загрузки эмбеддингов
2. **Connection pooling** для БД
3. **Timeout и retry** настройки
4. **Fallback стратегии** для graceful degradation
5. **Кеширование** через Redis

### Testing
1. **pytest** как основной фреймворк
2. **Моки** для внешних зависимостей
3. **Интеграционные тесты** на реальных БД
4. **Фикстуры** для каждого типа БД
5. **CI/CD интеграция** с автоматическими проверками

### Documentation
1. **Documentation-First** подход для новых features
2. **ADR** для всех архитектурных решений
3. **OpenAPI** спецификация с примерами
4. **README** для каждого сложного модуля
5. **Inline комментарии** для нетривиальных алгоритмов

---

> 📝 **Примечание**: Этот файл объединяет все правила из .cursor/rules/ для использования в Trae IDE. Все правила сохранены в полном объеме без изменений, только реорганизованы для лучшей структуры и читаемости.

> 🔄 **Обновление**: При изменении правил в .cursor/rules/ необходимо обновить этот сборный файл для поддержания синхронизации.