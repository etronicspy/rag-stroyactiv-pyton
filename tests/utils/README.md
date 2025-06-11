# Тесты утилит системы строительных материалов

Эта папка содержит тесты для всех утилит системы управления строительными материалами.

## Структура тестов

```
tests/utils/
├── __init__.py                             # Инициализация пакета тестов
├── conftest.py                             # Конфигурация pytest и фикстуры
├── test_runner.py                          # Утилита для запуска тестов
├── test_simple.py                          # Простые базовые тесты
├── test_load_materials_standalone.py       # Автономные тесты загрузки материалов
└── README.md                               # Эта документация
```

## Типы тестов

### Unit тесты
- **Описание**: Тесты отдельных функций и классов без внешних зависимостей
- **Используют**: Моки и заглушки
- **Быстрые и независимые**

### Интеграционные тесты  
- **Описание**: Тесты взаимодействия с реальными сервисами
- **Требуют**: Запущенные API сервер, Qdrant и настроенные переменные окружения
- **Маркер**: `@pytest.mark.integration`

## Запуск тестов

### Быстрый запуск

```bash
# Все тесты утилит
python tests/utils/test_runner.py all

# Только unit тесты (быстро)
python tests/utils/test_runner.py unit

# Только интеграционные тесты (требуют сервисы)
python tests/utils/test_runner.py integration

# Проверка окружения
python tests/utils/test_runner.py check
```

### Детальный запуск

```bash
# С анализом покрытия кода
python tests/utils/test_runner.py coverage

# Конкретный тест
python tests/utils/test_runner.py all --test test_load_materials.py

# Прямой запуск pytest
pytest tests/utils/ -v
```

### Запуск без интеграционных тестов

```bash
# Пропускает тесты, требующие запущенных сервисов
pytest tests/utils/ -v -m "not integration"
```

## Фикстуры и конфигурация

### Основные фикстуры (`conftest.py`)

- **`event_loop`**: Асинхронный event loop для всей сессии
- **`mock_env_vars`**: Мокирование переменных окружения
- **`temp_materials_data`**: Тестовые данные материалов
- **`sample_search_results`**: Образцы результатов поиска
- **`skip_if_no_api`**: Пропуск тестов если API недоступен
- **`skip_if_no_qdrant`**: Пропуск тестов если Qdrant недоступен

### Маркеры pytest

- **`integration`**: Интеграционные тесты
- **`slow`**: Медленные тесты
- **`api`**: Тесты, требующие API сервер

## Тестируемые утилиты

### 1. test_simple.py

**Описание**: Простые базовые тесты без внешних зависимостей

**Тесты**:
- ✅ Операции с путями и файлами
- ✅ Обработка JSON данных
- ✅ Строковые операции для материалов
- ✅ Настройка окружения
- ✅ Базовая асинхронная функциональность
- ✅ Использование фикстур
- ✅ Вспомогательные функции (форматирование, обрезка текста, генерация ID)

### 2. test_load_materials_standalone.py

**Утилита**: `utils/load_materials.py` (автономные тесты)

**Тесты**:
- ⚠️ Структура класса MaterialsLoader (может быть пропущен)
- ✅ Логика конвертации JSON формата
- ✅ Автоматическая категоризация материалов
- ✅ Определение единиц измерения
- ✅ Обработка JSON файлов
- ✅ Мокированное взаимодействие с API

## Требования для тестов

### Обязательные зависимости

```bash
pip install pytest pytest-asyncio
```

### Опциональные зависимости

```bash
pip install pytest-cov  # Для анализа покрытия
pip install requests    # Для проверки сервисов
```

### Переменные окружения

Для интеграционных тестов:

```bash
export OPENAI_API_KEY="your-openai-key"
export QDRANT_URL="http://localhost:6333"
export QDRANT_API_KEY="your-qdrant-key"  # Опционально
```

### Запущенные сервисы

Для интеграционных тестов:

1. **API сервер**: `http://localhost:8000`
2. **Qdrant**: `http://localhost:6333`

## Примеры использования

### 1. Разработка новой утилиты

```bash
# 1. Создайте новый файл теста
touch tests/utils/test_new_utility.py

# 2. Напишите unit тесты с моками
# 3. Запустите unit тесты
python tests/utils/test_runner.py unit --test test_new_utility.py

# 4. Добавьте интеграционные тесты
# 5. Запустите все тесты
python tests/utils/test_runner.py all --test test_new_utility.py
```

### 2. Отладка проблем

```bash
# Проверьте окружение
python tests/utils/test_runner.py check

# Запустите unit тесты (быстро)
python tests/utils/test_runner.py unit

# Если unit тесты проходят, запустите интеграционные
python tests/utils/test_runner.py integration
```

### 3. CI/CD интеграция

```bash
# В CI запускайте только unit тесты
pytest tests/utils/ -v -m "not integration" --tb=short

# В ночных билдах с поднятыми сервисами
pytest tests/utils/ -v --tb=short
```

## Отчеты и анализ

### Покрытие кода

```bash
# Генерация HTML отчета
python tests/utils/test_runner.py coverage

# Отчет сохраняется в htmlcov/index.html
open htmlcov/index.html
```

### JUnit XML для CI

```bash
pytest tests/utils/ --junitxml=test-results.xml
```

## Добавление новых тестов

### Шаблон для нового теста

```python
#!/usr/bin/env python3
"""
Тесты для утилиты [название]
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Импорт утилиты
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.your_utility import YourClass


class TestYourUtility:
    """Unit тесты"""
    
    @pytest.fixture
    def utility(self):
        return YourClass()
    
    def test_basic_functionality(self, utility):
        # Тест базовой функциональности
        pass
    
    @pytest.mark.asyncio
    async def test_async_functionality(self, utility):
        # Тест асинхронной функциональности
        pass


class TestYourUtilityIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.integration
    def test_real_integration(self):
        # Тест с реальными сервисами
        pass
```

## Решение проблем

### Частые проблемы

1. **ImportError**: Проверьте PYTHONPATH в conftest.py
2. **Сервисы недоступны**: Используйте unit тесты или поднимите сервисы
3. **Медленные тесты**: Используйте моки вместо реальных вызовов

### Полезные команды

```bash
# Подробный вывод с логами
pytest tests/utils/ -v -s

# Остановка на первой ошибке
pytest tests/utils/ -x

# Запуск только неудачных тестов
pytest tests/utils/ --lf

# Параллельный запуск (требует pytest-xdist)
pytest tests/utils/ -n auto
```

---

**Автор**: Система RAG для строительных материалов  
**Последнее обновление**: $(date +%Y-%m-%d) 