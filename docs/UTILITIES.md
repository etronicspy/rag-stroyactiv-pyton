# Утилиты системы строительных материалов

Полный набор утилит для работы с RAG системой строительных материалов.

## 📋 Обзор

Система включает **17 специализированных утилит**, организованных в папке `utils/`. Каждая утилита решает конкретные задачи по работе с материалами, от загрузки данных до анализа результатов.

## 🗂️ Категории утилит

### 📥 **Загрузка данных**
- `load_materials.py` - Массовая загрузка материалов из JSON
- `create_test_data.py` - Создание тестовых данных

### 🔄 **Сопоставление материалов**  
- `material_matcher.py` - Семантическое сопоставление материалов
- `material_summary.py` - Быстрый анализ результатов
- `save_matches.py` - Полное сохранение результатов
- `save_simple_matches.py` - Упрощенное сохранение результатов

### 👁️ **Просмотр данных**
- `show_material.py` - Структура конкретного материала
- `show_real_material.py` - Анализ импортированного материала
- `view_collection.py` - Просмотр коллекций

### 🧪 **Тестирование**
- `test_russian_search.py` - Тестирование поиска на русском
- `test_all_services.py` - Комплексное тестирование API
- `test_collection.py` - Тестирование коллекций
- `check_db_connection.py` - Проверка подключений

### 🧹 **Управление данными**
- `cleanup_collections.py` - Очистка коллекций

### ⚙️ **Инфраструктура**
- `__init__.py` - Центральный модуль импорта
- `common.py` - Общие функции и сервисы

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install -r requirements.txt
pip install aiohttp  # Для утилит загрузки
```

### Основные команды
```bash
# Загрузить материалы из JSON
python utils/load_materials.py data/materials.json --batch-size 50

# Выполнить сопоставление материалов
python utils/material_matcher.py

# Быстрый анализ результатов
python utils/material_summary.py

# Сохранить упрощенные результаты в CSV
python utils/save_simple_matches.py

# Проверить подключения
python utils/check_db_connection.py
```

## 📖 Детальная документация

Полная документация со всеми примерами и API находится в файле:
**[utils/README.md](../utils/README.md)**

## 🔧 Конфигурация

Для работы утилит требуются переменные окружения:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export QDRANT_URL="https://your-qdrant-instance.qdrant.io"
export QDRANT_API_KEY="your-qdrant-api-key"
```

Подробности в [CONFIGURATION.md](CONFIGURATION.md)

## 📊 Типичные рабочие процессы

### 1. Первоначальная загрузка данных
```bash
# Создать тестовые данные (если нужно)
python utils/create_test_data.py

# Загрузить материалы из файла
python utils/load_materials.py materials.json --batch-size 100

# Проверить результаты
python utils/view_collection.py
```

### 2. Сопоставление материалов прайс-листа
```bash
# Выполнить сопоставление
python utils/material_matcher.py

# Быстрый анализ
python utils/material_summary.py

# Сохранить результаты
python utils/save_simple_matches.py
```

### 3. Отладка и тестирование
```bash
# Проверить подключения
python utils/check_db_connection.py

# Тестировать поиск
python utils/test_russian_search.py

# Посмотреть структуру материала
python utils/show_material.py
```

### 4. Очистка данных
```bash
# Осторожно! Удаляет все коллекции
python utils/cleanup_collections.py
```

## 📁 Выходные файлы

Утилиты создают различные отчеты:

| Файл | Источник | Описание |
|------|----------|----------|
| `simple_matches_*.csv` | `save_simple_matches.py` | Упрощенные результаты |
| `saved_matches_*.json` | `save_matches.py` | Полные результаты |
| `matches_report_*.json` | `material_matcher.py` | Отчеты сопоставления |

## 🎯 Использование в коде

```python
# Импорт основных утилит
from utils import MaterialMatcher, MaterialsLoader
from utils.material_summary import show_material_matches
from utils.common import qdrant_service, embedding_service

# Загрузка материалов
loader = MaterialsLoader()
result = await loader.load_from_json_file("materials.json", batch_size=50)

# Сопоставление
matcher = MaterialMatcher()
matches = await matcher.match_materials("Поставщик_А")

# Анализ
await show_material_matches("Поставщик_А")
```

## ⚠️ Важные замечания

1. **Безопасность**: Утилиты очистки необратимо удаляют данные
2. **Производительность**: Batch-операции оптимизированы для больших объемов
3. **Кодировка**: Полная поддержка UTF-8 и русского языка
4. **API**: Требуется запущенный сервер на `localhost:8000`

## 🔗 Связанные документы

- [Batch загрузка материалов](BATCH_MATERIALS_LOADING.md)
- [Конфигурация системы](CONFIGURATION.md)
- [Детальная документация утилит](../utils/README.md)
- [Основное README](../README.md)

---

> 💡 **Совет**: Начните с `check_db_connection.py` для проверки настроек, затем загрузите тестовые данные через `load_materials.py` 