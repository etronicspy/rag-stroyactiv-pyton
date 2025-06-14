# 🧪 План тестирования REST API - Construction Materials API

*Дата создания: 2025-01-13*  
*Версия: 1.0*  
*Статус: В разработке*

## 📋 Содержание

1. [Обзор системы](#обзор-системы)
2. [Области тестирования](#области-тестирования)
3. [Типы тестов](#типы-тестов)
4. [Тестовые сценарии](#тестовые-сценарии)
5. [Стратегия тестирования](#стратегия-тестирования)
6. [Инфраструктура](#инфраструктура)
7. [План выполнения](#план-выполнения)
8. [Критерии приемки](#критерии-приемки)

---

## 🎯 Обзор системы

**Construction Materials API** - это мульти-БД RAG система для управления строительными материалами с поддержкой:

- **FastAPI** framework с async/await
- **Векторные БД**: Qdrant, Weaviate, Pinecone
- **Реляционные БД**: PostgreSQL
- **Кеширование**: Redis
- **AI интеграции**: OpenAI, Azure OpenAI, HuggingFace
- **Обработка файлов**: CSV/Excel прайс-листы

### Ключевые эндпоинты:

| Группа | Префикс | Описание |
|--------|---------|----------|
| Health | `/api/v1/health` | Мониторинг состояния системы |
| Materials | `/api/v1/materials` | CRUD операции с материалами |
| Prices | `/api/v1/prices` | Обработка прайс-листов |
| Search | `/api/v1/search` | Поиск и расширенный поиск |
| Monitoring | `/api/v1/monitoring` | Метрики и мониторинг |
| Reference | `/api/v1/reference` | Справочные данные |

---

## 🔍 Области тестирования

### 1. **Функциональное тестирование**
- CRUD операции для всех ресурсов
- Векторный поиск с fallback стратегией
- Обработка файлов (CSV/Excel)
- Валидация входных данных
- Обработка ошибок

### 2. **Интеграционное тестирование**
- Взаимодействие с векторными БД
- Интеграция с AI провайдерами
- Обработка файловых загрузок
- Middleware взаимодействие
- Кеширование данных

### 3. **Безопасность**
- Валидация входных данных
- Rate limiting
- CORS настройки
- Защита от SQL инъекций
- Защита от XSS атак
- Максимальный размер запросов

### 4. **Производительность**
- Время отклика API
- Throughput под нагрузкой
- Векторный поиск производительность
- Batch операции
- Кеширование эффективность

### 5. **Надежность**
- Graceful degradation
- Fallback механизмы
- Health checks
- Connection pooling
- Retry логика

---

## 🧪 Типы тестов

### **Unit тесты** (Изолированные)
```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_material_success(mock_vector_db, mock_ai_client):
    """Тест успешного создания материала"""
    # Тест с моками
```

**Покрытие:**
- Бизнес-логика сервисов
- Валидация данных
- Обработка исключений
- Утилитарные функции

### **Integration тесты** (С реальными БД)
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_vector_search_integration(real_qdrant_client):
    """Тест интеграции с векторной БД"""
    # Тест с реальными подключениями
```

**Покрытие:**
- Подключения к БД
- AI интеграции
- Файловые операции
- Middleware цепочки

### **Functional тесты** (End-to-End)
```python
@pytest.mark.functional
@pytest.mark.asyncio
async def test_complete_material_workflow(api_client):
    """Полный workflow работы с материалом"""
    # Создание → Поиск → Обновление → Удаление
```

**Покрытие:**
- Полные пользовательские сценарии
- API к API взаимодействие
- Комплексные workflow

### **Performance тесты**
```python
@pytest.mark.performance
async def test_concurrent_search_requests(api_client):
    """Тест производительности одновременных запросов"""
    # Нагрузочное тестирование
```

**Покрытие:**
- Нагрузочные тесты
- Стресс тестирование
- Оптимизация производительности

---

## 🎬 Тестовые сценарии

### **1. Health Check Endpoints**

#### **GET /api/v1/health/**
```http
GET /api/v1/health/
Expected: 200 OK
```

**Тестовые случаи:**
- ✅ Базовая проверка здоровья
- ✅ Проверка времени отклика
- ✅ Корректный формат ответа

#### **GET /api/v1/health/detailed**
```http
GET /api/v1/health/detailed
Expected: 200 OK with detailed metrics
```

**Тестовые случаи:**
- ✅ Детальная информация о всех компонентах
- ✅ Статусы всех БД подключений
- ✅ Производительные метрики

#### **GET /api/v1/health/databases**
```http
GET /api/v1/health/databases
Expected: 200 OK with DB status
```

**Тестовые случаи:**
- ✅ Статус Qdrant подключения
- ✅ Статус PostgreSQL (если настроен)
- ✅ Статус Redis кеша
- ⚠️ Fallback при недоступности БД

### **2. Materials Management**

#### **POST /api/v1/materials/**
```http
POST /api/v1/materials/
Content-Type: application/json

{
  "name": "Цемент М400",
  "description": "Портландцемент марки 400",
  "use_category": "Цемент",
  "unit": "т"
}
```

**Тестовые случаи:**
- ✅ Успешное создание материала
- ✅ Валидация обязательных полей
- ❌ Создание с пустым именем
- ❌ Создание с невалидной категорией
- ✅ Автоматическая генерация embedding
- ✅ Сохранение в векторную БД

#### **GET /api/v1/materials/{material_id}**
```http
GET /api/v1/materials/123e4567-e89b-12d3-a456-426614174000
Expected: 200 OK or 404 Not Found
```

**Тестовые случаи:**
- ✅ Получение существующего материала
- ❌ Получение несуществующего материала
- ❌ Невалидный формат ID
- ✅ Корректная структура ответа

#### **POST /api/v1/materials/search**
```http
POST /api/v1/materials/search
Content-Type: application/json

{
  "query": "цемент",
  "limit": 10
}
```

**Тестовые случаи:**
- ✅ Векторный поиск по тексту
- ✅ Fallback к SQL поиску при 0 результатов
- ✅ Ограничение количества результатов
- ✅ Релевантность результатов
- ⚠️ Обработка пустых запросов

#### **PUT /api/v1/materials/{material_id}**
```http
PUT /api/v1/materials/123e4567-e89b-12d3-a456-426614174000
Content-Type: application/json

{
  "name": "Цемент М500",
  "description": "Обновленное описание"
}
```

**Тестовые случаи:**
- ✅ Успешное обновление
- ✅ Перегенерация embedding при изменении
- ❌ Обновление несуществующего материала
- ✅ Частичное обновление полей

#### **DELETE /api/v1/materials/{material_id}**
```http
DELETE /api/v1/materials/123e4567-e89b-12d3-a456-426614174000
Expected: 204 No Content
```

**Тестовые случаи:**
- ✅ Успешное удаление
- ❌ Удаление несуществующего материала
- ✅ Удаление из векторной БД

#### **POST /api/v1/materials/batch**
```http
POST /api/v1/materials/batch
Content-Type: application/json

{
  "materials": [
    {"name": "Материал 1", "description": "...", "use_category": "...", "unit": "..."},
    {"name": "Материал 2", "description": "...", "use_category": "...", "unit": "..."}
  ]
}
```

**Тестовые случаи:**
- ✅ Batch создание материалов
- ✅ Частичная обработка при ошибках
- ✅ Контроль лимитов batch размера
- ⚠️ Rollback при критических ошибках

### **3. Price Lists Management**

#### **POST /api/v1/prices/process**
```http
POST /api/v1/prices/process
Content-Type: multipart/form-data

file: price_list.csv
supplier_id: "supplier_123"
pricelistid: 1
```

**Тестовые случаи:**
- ✅ Обработка CSV файлов
- ✅ Обработка Excel файлов (.xls, .xlsx)
- ❌ Неподдерживаемые форматы файлов
- ❌ Файлы размером > 50MB
- ✅ Валидация структуры прайс-листа
- ❌ Прайс-листы с неправильными заголовками
- ✅ Сохранение в supplier-specific коллекцию
- ✅ Автоматическая генерация pricelistid

#### **GET /api/v1/prices/{supplier_id}/latest**
```http
GET /api/v1/prices/supplier_123/latest
Expected: 200 OK with latest price list
```

**Тестовые случаи:**
- ✅ Получение последнего прайс-листа
- ❌ Несуществующий поставщик
- ✅ Корректная структура ответа

#### **DELETE /api/v1/prices/{supplier_id}**
```http
DELETE /api/v1/prices/supplier_123
Expected: 200 OK
```

**Тестовые случаи:**
- ✅ Удаление всех прайс-листов поставщика
- ❌ Несуществующий поставщик
- ✅ Каскадное удаление из БД

### **4. Advanced Search**

#### **POST /api/v1/search/advanced**
```http
POST /api/v1/search/advanced
Content-Type: application/json

{
  "query": "цемент",
  "search_type": "hybrid",
  "limit": 20,
  "categories": ["Цемент", "Бетон"],
  "fuzzy_threshold": 0.8
}
```

**Тестовые случаи:**
- ✅ Векторный поиск
- ✅ SQL поиск
- ✅ Fuzzy поиск
- ✅ Гибридный поиск
- ✅ Фильтрация по категориям
- ✅ Фильтрация по единицам измерения
- ✅ Настройка порога схожести

#### **GET /api/v1/search/suggestions**
```http
GET /api/v1/search/suggestions?q=цем&limit=8
Expected: 200 OK with suggestions
```

**Тестовые случаи:**
- ✅ Автодополнение запросов
- ✅ Ограничение количества предложений
- ✅ Релевантность предложений

### **5. Monitoring & Metrics**

#### **GET /api/v1/monitoring/metrics**
```http
GET /api/v1/monitoring/metrics
Expected: 200 OK with system metrics
```

**Тестовые случаи:**
- ✅ Получение системных метрик
- ✅ Метрики производительности
- ✅ Статистика использования API

---

## 🚀 Стратегия тестирования

### **Уровни тестирования:**

1. **Unit Tests (70%)** - Быстрые, изолированные тесты
2. **Integration Tests (20%)** - Тесты компонентной интеграции  
3. **E2E Tests (10%)** - Полные пользовательские сценарии

### **Покрытие кода:**
- **Целевое покрытие**: 90%+
- **Критическая логика**: 95%+
- **Исключения из покрытия**: Mock классы, конфигурационные файлы

### **Стратегия mock'ов:**

#### **Unit тесты** - Полные моки
```python
@pytest.fixture
def mock_vector_db():
    return MockVectorDatabase()

@pytest.fixture  
def mock_ai_client():
    return MockAIClient()
```

#### **Integration тесты** - Реальные подключения
```python
@pytest.fixture
def real_qdrant_client():
    return QdrantVectorStore(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
```

### **Параллельное выполнение:**
```bash
# Параллельное выполнение тестов
pytest tests/ -n auto --dist worksteal

# Параллельное выполнение по группам
pytest tests/unit/ tests/performance/ -v
```

---

## 🛠️ Инфраструктура

### **Тестовые окружения:**

#### **Local Development**
```bash
# Переменные для локальной разработки
export TEST_MODE=mock
export ENVIRONMENT=test
export QDRANT_ONLY_MODE=true
export DISABLE_REDIS_CONNECTION=true
export DISABLE_POSTGRESQL_CONNECTION=true
```

#### **CI/CD Pipeline**
```bash
# Переменные для CI
export TEST_MODE=integration
export QDRANT_URL=$CI_QDRANT_URL
export QDRANT_API_KEY=$CI_QDRANT_API_KEY
export OPENAI_API_KEY=$CI_OPENAI_API_KEY
```

#### **Staging Environment**
```bash
# Переменные для staging
export TEST_MODE=full
export ENVIRONMENT=staging
export ENABLE_FALLBACK_DATABASES=true
```

### **Docker конфигурация:**
```dockerfile
# Dockerfile.test
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

COPY . .
CMD ["pytest", "tests/", "-v", "--cov=."]
```

### **Database fixtures:**
```python
@pytest.fixture(scope="session")
async def test_database():
    """Подготовка тестовой БД"""
    # Создание временной коллекции в Qdrant
    # Подготовка тестовых данных
    yield
    # Очистка после тестов
```

---

## 📋 План выполнения

### **Фаза 1: Подготовка инфраструктуры** (1 неделя)
- [ ] Настройка тестовых окружений
- [ ] Конфигурация CI/CD pipeline
- [ ] Подготовка тестовых данных
- [ ] Mock объекты и fixtures

### **Фаза 2: Unit тестирование** (2 недели)
- [ ] Тесты API endpoints (63 теста)
- [ ] Тесты сервисов (25 тестов)
- [ ] Тесты middleware (16 тестов)
- [ ] Тесты утилит (15 тестов)

### **Фаза 3: Integration тестирование** (2 недели)
- [ ] Тесты БД интеграций (41 тест)
- [ ] Тесты AI провайдеров (12 тестов)
- [ ] Тесты файловых операций (18 тестов)
- [ ] Тесты векторного поиска (22 теста)

### **Фаза 4: Functional тестирование** (1 неделя)
- [ ] End-to-end сценарии (15 тестов)
- [ ] Комплексные workflow (10 тестов)
- [ ] Интеграционные сценарии (8 тестов)

### **Фаза 5: Performance тестирование** (1 неделя)
- [ ] Нагрузочные тесты (20 тестов)
- [ ] Стресс тестирование (10 тестов)
- [ ] Оптимизация производительности (15 тестов)

### **Фаза 6: Security тестирование** (1 неделя)
- [ ] Валидация входных данных (25 тестов)
- [ ] Rate limiting (8 тестов)
- [ ] Тесты безопасности (12 тестов)

---

## ✅ Критерии приемки

### **Количественные критерии:**

| Метрика | Цель | Текущее состояние |
|---------|------|-------------------|
| Code Coverage | ≥ 90% | 65% |
| Unit Tests | 150+ тестов | 63 теста |
| Integration Tests | 80+ тестов | 20 тестов |
| Performance Tests | 45+ тестов | 35 тестов |
| Test Execution Time | < 5 минут | 4.5 минут |
| Success Rate | ≥ 95% | 85% |

### **Качественные критерии:**

#### **✅ Функциональные требования:**
- [ ] Все CRUD операции покрыты тестами
- [ ] Векторный поиск с fallback работает корректно
- [ ] Обработка файлов (CSV/Excel) протестирована
- [ ] Health checks покрывают все компоненты
- [ ] Error handling протестирован для всех сценариев

#### **✅ Производительные требования:**
- [ ] API отвечает < 200ms для простых операций
- [ ] Поиск выполняется < 500ms
- [ ] Batch операции обрабатывают 100+ элементов
- [ ] Система выдерживает 1000+ concurrent requests

#### **✅ Надежность:**
- [ ] Graceful degradation при недоступности БД
- [ ] Fallback механизмы работают корректно
- [ ] Connection pooling настроен и протестирован
- [ ] Retry логика покрыта тестами

#### **✅ Безопасность:**
- [ ] Валидация всех входящих данных
- [ ] Rate limiting работает корректно
- [ ] Защита от распространенных атак
- [ ] Логирование security событий

---

## 📊 Мониторинг выполнения

### **Ежедневные метрики:**
```bash
# Запуск дневного отчета
make test-daily-report

# Результат:
# Tests run: 156/200 (78%)
# Success rate: 89%
# Coverage: 87%
# Execution time: 4.2 minutes
```

### **Еженедельные отчеты:**
- Прогресс по фазам выполнения
- Новые найденные баги
- Изменения в архитектуре
- Обновления тестовых планов

### **Интеграция с CI/CD:**
```yaml
# .github/workflows/test.yml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          make test-unit
          make test-integration
          make test-performance
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

---

## 📚 Ресурсы и документация

### **Тестовые данные:**
- `tests/data/materials.json` - Тестовые материалы
- `tests/data/price_lists/` - Образцы прайс-листов
- `tests/fixtures/` - Фикстуры для тестов

### **Конфигурационные файлы:**
- `pytest.ini` - Основная конфигурация pytest
- `tests/conftest.py` - Глобальные фикстуры
- `.env.test` - Переменные для тестового окружения

### **Документация:**
- `tests/README.md` - Руководство по тестированию
- `TESTS_STATUS_REPORT.md` - Текущий статус тестов
- `TESTS_OPTIMIZATION_PLAN.md` - План оптимизации

### **Команды для запуска:**
```bash
# Все тесты
make test

# Быстрые тесты
make test-fast

# Полное тестирование
make test-full

# С покрытием кода
make test-coverage

# Performance тесты
make test-performance
```

---

**📝 Заключение:**

Данный план тестирования обеспечивает комплексную проверку всех аспектов Construction Materials API, включая функциональность, производительность, безопасность и надежность. План рассчитан на 8 недель выполнения с постепенным увеличением покрытия от текущих 51% до целевых 95%.