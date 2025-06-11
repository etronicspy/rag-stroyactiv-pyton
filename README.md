# RAG Construction Materials API

API для управления строительными материалами с семантическим поиском и обработкой прайс-листов.

## ⚙️ Конфигурация окружения

**🔥 ВАЖНО: Файл `.env.local` уже настроен и готов к работе!**

**📍 Расположение конфигурации:**
```
/Users/etronicspy/rag-stroyactiv-pyton/.env.local
```

В проекте используются **реальные базы данных**:
- ✅ **Qdrant Cloud** - векторная БД для семантического поиска (настроена и подключена)
- ✅ **OpenAI API** - для генерации эмбеддингов (ключ настроен)

**Файл `.env.local` содержит следующие переменные:**
```bash
# OpenAI Configuration
OPENAI_API_KEY=my_apy_key

# Qdrant Configuration
QDRANT_URL=my_url
QDRANT_API_KEY=my_api_key


```

**🎯 Все настройки готовы к использованию! Никакой дополнительной настройки не требуется.**

### 🔧 Централизованная конфигурация

Проект использует **продвинутую систему конфигурации** с поддержкой:
- 🔄 **Легкое переключение** между разными БД (Qdrant Cloud/Local, Weaviate, Pinecone)
- 🤖 **Множество ИИ провайдеров** (OpenAI, Azure OpenAI, HuggingFace, Ollama)
- 🛡️ **Безопасное управление** чувствительными данными
- ⚙️ **Фабрики клиентов** для автоматического создания подключений

Подробнее: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

## Функциональность

### Поиск
- `POST /api/v1/search` - Семантический поиск по материалам

### Обработка прайс-листов
- `POST /api/v1/prices/process` - Обработка и валидация прайс-листов

### Справочные данные
#### Материалы
- `GET /api/v1/reference/materials` - Список материалов с фильтрацией
- `GET /api/v1/reference/materials/{id}` - Получение материала по ID
- `POST /api/v1/reference/materials` - Создание материала
- `PUT /api/v1/reference/materials/{id}` - Обновление материала
- `DELETE /api/v1/reference/materials/{id}` - Удаление материала

#### Категории
- `GET /api/v1/reference/categories` - Список категорий
- `POST /api/v1/reference/categories` - Создание категории
- `DELETE /api/v1/reference/categories/{name}` - Удаление категории

#### Единицы измерения
- `GET /api/v1/reference/units` - Список единиц измерения
- `POST /api/v1/reference/units` - Создание единицы измерения
- `DELETE /api/v1/reference/units/{name}` - Удаление единицы измерения

### Мониторинг
- `GET /api/v1/health` - Проверка здоровья системы
- `GET /api/v1/health/config` - Статус конфигурации

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd rag-construction-materials
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/MacOS
.venv\Scripts\activate  # для Windows
pip install -r requirements.txt
```

3. **Переменные окружения уже настроены!**
   - Файл `.env.local` готов к использованию
   - Содержит настройки для реальных баз данных
   - Никаких дополнительных настроек не требуется

   **Быстрая проверка подключения:**
   ```bash
   python check_db_connection.py
   ```

4. Запустите приложение:
```bash
uvicorn main:app --reload
```

API будет доступно по адресу: http://localhost:8000
Swagger документация: http://localhost:8000/docs

## 🧪 Тестирование на реальной БД

Проект настроен для работы с **реальными базами данных**:

```bash
# Запуск всех тестов (используют реальную Qdrant Cloud)
pytest

# Запуск тестов подключения к БД
pytest tests/test_real_db_connection.py -v

# Запуск тестов прайс-листов на реальной БД
pytest tests/test_prices.py -v
```

**Особенности тестирования:**
- ✅ Используется реальная Qdrant Cloud база данных
- 🧹 Автоматическая очистка тестовых коллекций
- 🔒 Безопасная изоляция тестовых данных
- 📊 Подробное логирование операций с БД

## Форматы данных

### Материал
```json
{
  "name": "Портландцемент М500",
  "category": "Cement",
  "unit": "bag",
  "description": "Высококачественный цемент для строительных работ"
}
```

### Прайс-лист
Поддерживаются форматы CSV и Excel (xls, xlsx) со следующими обязательными колонками:
- name
- category
- unit
- description (опционально)

## Разработка

## 🔧 Утилиты

Система включает **17 специализированных утилит** для работы с материалами, сопоставления прайс-листов, тестирования и администрирования.

📖 **Полная документация**: [docs/UTILITIES.md](docs/UTILITIES.md)

### Основные утилиты:

| Категория | Утилиты | Описание |
|-----------|---------|----------|
| **📥 Загрузка** | `load_materials.py`, `create_test_data.py` | Массовая загрузка из JSON, создание тестовых данных |
| **🔄 Сопоставление** | `material_matcher.py`, `material_summary.py` | Семантическое сопоставление материалов и анализ |
| **👁️ Просмотр** | `show_material.py`, `view_collection.py` | Исследование структуры данных |
| **🧪 Тестирование** | `test_russian_search.py`, `check_db_connection.py` | Комплексное тестирование системы |

### Быстрый старт:
```bash
# Проверить подключения
python utils/check_db_connection.py

# Загрузить материалы
python utils/load_materials.py materials.json --batch-size 50

# Выполнить сопоставление
python utils/material_matcher.py

# Быстрый анализ
python utils/material_summary.py
```

### Структура проекта
```
.
├── api/
│   └── routes/
│       ├── health.py
│       ├── prices.py
│       ├── reference.py
│       └── search.py
├── core/
│   ├── config.py
│   ├── models/
│   │   └── materials.py
│   └── schemas/
│       └── materials.py
├── services/
│   ├── materials.py
│   └── price_processor.py
├── utils/
│   ├── check_db_connection.py
│   └── view_collection.py
├── tests/
│   └── ...
├── .env
├── main.py
└── requirements.txt
```

### Запуск тестов
```bash
pytest
```

## Лицензия
MIT 