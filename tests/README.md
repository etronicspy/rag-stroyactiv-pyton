# 🧪 Тестовая система RAG Construction Materials API

## 📖 Обзор

Тестовая система организована по принципу разделения на типы тестов с автоматическим переключением между mock и реальными БД. Система поддерживает четыре основных типа тестов:

- **Unit тесты** - быстрые тесты с моками
- **Integration тесты** - тесты с реальными БД
- **Functional тесты** - end-to-end сценарии
- **Performance тесты** - тесты производительности

## 📁 Структура

```
tests/
├── conftest.py                 # Единая конфигурация всех тестов
├── pytest.ini                 # Конфигурация pytest
├── README.md                   # Документация (этот файл)
├── unit/                       # Unit тесты с моками
│   ├── __init__.py
│   ├── test_api_endpoints.py   # Тесты API эндпоинтов
│   ├── test_services.py        # Тесты сервисов
│   ├── test_middleware.py      # Тесты middleware
│   └── test_utils.py          # Тесты утилит
├── integration/                # Интеграционные тесты
│   ├── __init__.py
│   ├── test_materials_workflow.py    # Workflow материалов
│   ├── test_database_operations.py  # Операции с БД
│   ├── test_file_processing.py      # Обработка файлов
│   └── test_vector_search.py        # Векторный поиск
├── functional/                 # Функциональные тесты
│   ├── __init__.py
│   ├── test_complete_workflows.py   # Полные сценарии
│   └── test_api_scenarios.py        # API сценарии
├── performance/                # Тесты производительности
│   ├── __init__.py
│   ├── test_load_testing.py         # Нагрузочные тесты
│   ├── test_optimization.py         # Тесты оптимизации
│   └── test_monitoring.py           # Мониторинг
├── fixtures/                   # Общие фикстуры
│   ├── __init__.py
│   ├── data_fixtures.py        # Тестовые данные
│   ├── mock_fixtures.py        # Mock объекты
│   └── database_fixtures.py    # БД фикстуры
└── data/                      # Тестовые данные файлы
    ├── *.csv
    ├── *.json
    └── test_data_helper.py
```

## 🚀 Быстрый старт

### Установка зависимостей
```bash
make install-test-deps
```

### Запуск тестов
```bash
# Быстрые unit тесты
make test-unit

# Интеграционные тесты
make test-integration

# Все тесты
make test-all

# Тесты с анализом покрытия
make test-coverage
```

## 🎯 Типы тестов

### Unit тесты
- **Маркер**: `@pytest.mark.unit`
- **Режим**: Автоматические моки
- **Скорость**: Очень быстрые (< 1 сек на тест)
- **Назначение**: Тестирование изолированной логики

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_material_service_create(client_mock):
    """Unit тест создания материала"""
    # Тест с автоматическими моками
```

### Integration тесты
- **Маркер**: `@pytest.mark.integration`
- **Режим**: Реальные БД подключения
- **Скорость**: Средние (1-10 сек на тест)
- **Назначение**: Тестирование взаимодействия компонентов

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_materials_database_workflow(client_real):
    """Интеграционный тест полного workflow"""
    # Тест с реальными БД
```

### Functional тесты
- **Маркер**: `@pytest.mark.functional`
- **Режим**: Полные end-to-end сценарии
- **Скорость**: Медленные (5-30 сек на тест)
- **Назначение**: Тестирование пользовательских сценариев

### Performance тесты
- **Маркер**: `@pytest.mark.performance`
- **Режим**: Нагрузочное тестирование
- **Скорость**: Очень медленные (30+ сек на тест)
- **Назначение**: Тестирование производительности

## 🔧 Конфигурация

### Переключение режимов

Система автоматически определяет режим тестирования:

```bash
# Mock режим (по умолчанию)
pytest -m unit

# Реальные БД
TEST_MODE=real pytest -m integration
```

### Переменные окружения

Основные переменные в `tests/conftest.py`:

- `TEST_MODE` - режим тестирования (`mock`/`real`)
- `QDRANT_URL` - URL Qdrant для тестов
- `QDRANT_API_KEY` - API ключ Qdrant
- `DISABLE_REDIS_CONNECTION` - отключить Redis
- `DISABLE_POSTGRESQL_CONNECTION` - отключить PostgreSQL

## 📝 Написание тестов

### Соглашения о именовании

```python
def test_[component]_[action]_[expected_result]():
    """
    Тест [описание на русском]
    Test [description in English]
    """
```

### Структура тестовой функции

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_create_material_success():
    """Unit тест успешного создания материала"""
    # Arrange - подготовка данных
    material_data = {"name": "Test Material", "price": 100.0}
    
    # Act - выполнение действия
    result = await service.create_material(material_data)
    
    # Assert - проверка результата
    assert result.name == "Test Material"
    assert result.price == 100.0
```

### Использование фикстур

```python
def test_with_fixtures(sample_material, mock_database_services):
    """Пример использования фикстур"""
    # sample_material - готовые тестовые данные
    # mock_database_services - замоканные сервисы
    pass
```

## 🔍 Фикстуры

### Основные фикстуры

- `client_mock` - тестовый клиент с моками
- `client_real` - тестовый клиент с реальными БД
- `client` - автоматический выбор клиента
- `sample_material` - образец материала
- `sample_price_data` - образцы ценовых данных
- `test_supplier_id` - ID тестового поставщика

### Mock фикстуры

- `mock_materials_service` - Mock сервиса материалов
- `mock_vector_db` - Mock векторной БД
- `mock_qdrant_client` - Mock Qdrant клиента
- `mock_openai_client` - Mock OpenAI клиента

### Фикстуры данных

Все тестовые данные централизованы в `fixtures/data_fixtures.py`:

```python
from tests.fixtures.data_fixtures import TestDataProvider

# Получение образцов материалов
materials = TestDataProvider.get_sample_materials()

# Получение CSV данных
csv_data = TestDataProvider.get_price_list_csv_data()
```

## 🛠 Команды Makefile

### Основные команды
- `make test-unit` - Unit тесты
- `make test-integration` - Интеграционные тесты
- `make test-functional` - Функциональные тесты
- `make test-performance` - Тесты производительности
- `make test-all` - Все тесты

### Дополнительные команды
- `make test-coverage` - Тесты с анализом покрытия
- `make test-fast` - Только быстрые тесты
- `make test-verbose` - Детальный вывод
- `make clean-test` - Очистка тестовых файлов

### Комбинированные команды
- `make test-quick` - Быстрые unit тесты
- `make test-ci` - Тесты для CI/CD
- `make test-full` - Полный цикл тестирования

## 📊 Анализ покрытия

```bash
# Генерация отчета о покрытии
make test-coverage

# Просмотр HTML отчета
open htmlcov/index.html
```

## 🐛 Отладка тестов

### Запуск конкретного теста
```bash
pytest tests/unit/test_api_endpoints.py::test_health_check -v
```

### Запуск тестов по паттерну
```bash
make test-pattern PATTERN="material"
```

### Детальный вывод
```bash
make test-verbose
```

### Остановка на первой ошибке
```bash
pytest -x tests/
```

## 🔄 CI/CD интеграция

### GitHub Actions пример
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: make install-test-deps
      - name: Run unit tests
        run: make test-unit
      - name: Run integration tests
        run: make test-integration
        env:
          TEST_MODE: real
          QDRANT_URL: ${{ secrets.QDRANT_URL }}
          QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
```

## 📈 Метрики и мониторинг

### Метрики производительности
- Время выполнения тестов
- Покрытие кода
- Количество пройденных/неудачных тестов
- Использование памяти

### Мониторинг в реальном времени
```bash
# Профилирование тестов
make test-profile

# Мониторинг ресурсов
pytest --profile-svg tests/
```

## 🚨 Устранение неполадок

### Частые проблемы

1. **Тесты падают с ошибкой подключения к БД**
   - Проверьте переменные окружения
   - Убедитесь что БД доступны
   - Используйте `TEST_MODE=mock` для unit тестов

2. **Медленные тесты**
   - Используйте `make test-fast` для исключения медленных тестов
   - Проверьте маркировку `@pytest.mark.slow`

3. **Проблемы с фикстурами**
   - Проверьте импорты в `conftest.py`
   - Убедитесь что фикстуры правильно помечены

### Получение помощи
```bash
# Список всех команд
make help

# Валидация тестов
make test-validate

# Проверка зависимостей  
make check-deps
```

## 📚 Дополнительные ресурсы

- [Документация pytest](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [AsyncMock руководство](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.AsyncMock)

---

**Последнее обновление**: 2024  
**Версия**: 1.0  
**Статус**: Активная разработка 