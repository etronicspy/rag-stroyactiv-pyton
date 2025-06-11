# Утилиты RAG системы строительных материалов

Эта папка содержит утилиты для работы с RAG системой строительных материалов.

## 📁 Структура утилит

### 🔧 Основные утилиты

#### `load_materials.py`
**Массовая загрузка материалов из JSON файлов**
- Поддержка batch-загрузки с оптимизацией производительности
- Автоматическая категоризация материалов по ключевым словам
- Import API для загрузки данных в формате `{article, name}`
- Поддержка argparse для удобной работы из командной строки

```bash
# Загрузка материалов с batch размером 50
python utils/load_materials.py data/materials.json --batch-size 50 --base-url http://localhost:8000

# Программное использование
from utils import MaterialsLoader
loader = MaterialsLoader()
await loader.load_from_json_file("data.json", batch_size=100)
```

#### `material_matcher.py`
**Семантическое сопоставление материалов**
- Класс `MaterialMatcher` для сравнения материалов из прайс-листов с эталонными
- Использует семантический поиск по названиям и единицам измерения
- Создает коллекцию `material_matches` с результатами сопоставления
- Генерирует отчеты в JSON формате с детальной статистикой

```python
from utils import MaterialMatcher

matcher = MaterialMatcher()
matches = await matcher.match_materials("Поставщик_Строй_Материалы")
```

#### `create_test_data.py`
**Создание тестовых данных**
- Массовое создание категорий, единиц измерения и материалов
- Поддержка русского языка и UTF-8 кодировки
- Создание данных через API эндпоинты

```python
from utils import create_sample_data

await create_sample_data()
```

### 📊 Утилиты анализа и отчетов

#### `material_summary.py`
**Быстрый анализ результатов сопоставления**
- Оптимизированный просмотр без сохранения в базу данных
- Статистика по уровням уверенности (высокая/средняя/низкая)
- Анализ единиц измерения и категорий
- Детальный отчет с лучшими совпадениями

```python
from utils.material_summary import show_material_matches

await show_material_matches("Поставщик_Строй_Материалы")
```

#### `save_matches.py` 
**Полное сохранение результатов сопоставления**
- Сохранение всех деталей сопоставления в векторную базу
- Батчевое получение embeddings для оптимизации
- Резервное копирование в JSON файлы
- Детальная статистика и анализ лучших совпадений

```python
from utils.save_matches import save_and_view_matches

await save_and_view_matches("Поставщик_Строй_Материалы")
```

#### `save_simple_matches.py`
**Упрощенное сохранение результатов**
- Сохранение только ключевых полей (имена, единицы, артикулы)
- Генерация уникальных артикулов для материалов
- Экспорт в CSV формат для удобства
- Оптимизированная структура для быстрого доступа

```bash
python utils/save_simple_matches.py
# Создает CSV файл: simple_matches_YYYYMMDD_HHMMSS.csv
```

### 🔍 Утилиты просмотра данных

#### `show_material.py`
**Просмотр структуры конкретного материала**
- Показывает полную структуру материала из API
- Отображение embedding информации
- Анализ vector данных (min/max/norm)
- JSON структуру для отладки

```bash
python utils/show_material.py
# Показывает материал с ID: 042f031f-eac0-4f21-b409-e7cd962e4e0e
```

#### `show_real_material.py` 
**Сравнение структуры импортированного материала**
- Показывает структуру материала после импорта
- Сравнение с Qdrant структурой хранения
- Анализ vector нормализации
- Проверка соответствия API возвращаемых данных

```bash
python utils/show_real_material.py
# Показывает материал с ID: 7aabea8d-9556-4da7-92d0-998410c536c0
```

#### `view_collection.py`
**Просмотр содержимого коллекций**
- Отображение всех коллекций в базе данных
- Детальная информация о каждой коллекции
- Статистика по количеству точек

```python
from utils import view_collection

await view_collection("materials")
```

### 🧪 Тестовые утилиты

#### `test_russian_search.py`
**Тестирование поиска на русском языке**
- Проверка корректности кодировки UTF-8
- Тестирование семантического поиска русских терминов
- Валидация ответов API

```python
from utils import test_russian_search

await test_russian_search()
```

#### `test_all_services.py`
**Комплексное тестирование сервисов**
- Тестирование всех API эндпоинтов
- Проверка создания и получения данных
- Валидация структуры ответов

```python
from utils import test_all_services

await test_all_services()
```

#### `test_collection.py`
**Тестирование коллекций**
- Проверка создания и удаления коллекций
- Валидация структуры данных в коллекциях

#### `check_db_connection.py`
**Проверка подключения к базе данных**
- Тестирование соединения с Qdrant
- Проверка конфигурации OpenAI API
- Валидация настроек окружения

```python
from utils import check_connection

await check_connection()
```

### 🗄️ Утилиты управления данными

#### `cleanup_collections.py`
**Интерактивная очистка коллекций Qdrant**
- 🎯 Интерактивный интерфейс с выбором типа операции
- 🔒 Безопасная очистка с подтверждением от пользователя  
- 📋 Показ списка коллекций перед удалением
- 🔄 Пересоздание коллекций с правильными параметрами

**Доступные операции:**
1. **Очистить только коллекцию materials** - удаляет основную коллекцию материалов
2. **Очистить коллекции с прайсами** - удаляет все коллекции supplier_*_prices
3. **Очистить ВСЕ коллекции** - полная очистка базы данных (с подтверждением)
4. **Пересоздать коллекцию materials** - удаляет и создает заново с правильной конфигурацией

```bash
# Интерактивный режим
python utils/cleanup_collections.py

# Пример интерфейса:
# 1. Очистить только коллекцию materials  
# 2. Очистить коллекции с прайсами
# 3. Очистить ВСЕ коллекции
# 4. Пересоздать коллекцию materials
# 0. Выход
```

**Безопасность:**
- ⚠️ Запрашивает подтверждение перед критическими операциями
- 📊 Показывает статистику коллекций перед удалением
- 🚫 Возможность отменить операцию на любом этапе

## 🚀 Использование

### Импорт через модуль utils
```python
# Импорт конкретных функций
from utils import MaterialMatcher, MaterialsLoader, create_sample_data, test_russian_search

# Импорт всего модуля
import utils

matcher = utils.MaterialMatcher()
loader = utils.MaterialsLoader()
```

### Запуск утилит напрямую
```bash
# Загрузка материалов
python utils/load_materials.py data.json --batch-size 100

# Сопоставление материалов  
python utils/material_matcher.py

# Создание тестовых данных
python utils/create_test_data.py

# Анализ результатов
python utils/material_summary.py

# Сохранение результатов
python utils/save_matches.py
python utils/save_simple_matches.py

# Просмотр данных
python utils/show_material.py
python utils/show_real_material.py
python utils/view_collection.py

# Тестирование
python utils/test_russian_search.py
python utils/test_all_services.py
python utils/check_db_connection.py

# Очистка
python utils/cleanup_collections.py
```

## 📁 Файлы вывода

Утилиты создают следующие файлы:
- `matches_report_*.json` - отчеты сопоставления материалов
- `simple_matches_*.csv` - упрощенные результаты в CSV
- `saved_matches_*.json` - резервные копии полных результатов
- Логи выводятся в консоль с уровнями INFO/DEBUG/ERROR

## ⚠️ Важные заметки

1. **Зависимости**: Все утилиты требуют активированного виртуального окружения (.venv)

2. **Конфигурация**: Убедитесь что настроены переменные окружения:
   - `OPENAI_API_KEY` - ключ OpenAI API
   - `QDRANT_URL` - URL Qdrant базы данных  
   - `QDRANT_API_KEY` - ключ Qdrant API

3. **Безопасность**: Утилиты очистки коллекций необратимо удаляют данные

4. **Кодировка**: Все утилиты поддерживают UTF-8 для корректной работы с русским языком

5. **Производительность**: Утилиты оптимизированы для batch-обработки больших объемов данных

## 🔧 Конфигурация

### Файл `__init__.py`
Центральный файл для импорта всех утилит. Содержит:
- Экспорт всех основных классов и функций
- Конфигурацию общих сервисов
- Утилиты для работы с базой данных

### Файл `common.py`
Общие функции и классы:
- Сервисы для работы с Qdrant и OpenAI
- Утилиты форматирования и валидации
- Общие константы и настройки

## 📈 Примеры использования

### Полный цикл работы с материалами
```bash
# 1. Загрузить материалы
python utils/load_materials.py materials.json --batch-size 50

# 2. Выполнить сопоставление
python utils/material_matcher.py

# 3. Просмотреть результаты
python utils/material_summary.py

# 4. Сохранить результаты
python utils/save_simple_matches.py

# 5. Проверить данные
python utils/view_collection.py
```

### Отладка и тестирование
```bash
# Проверить подключения
python utils/check_db_connection.py

# Тестировать поиск
python utils/test_russian_search.py

# Посмотреть структуру материала
python utils/show_material.py

# Очистить при необходимости
python utils/cleanup_collections.py
``` 