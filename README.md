# RAG Construction Materials API

API для управления строительными материалами с семантическим поиском и обработкой прайс-листов.

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

3. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env под свои нужды
```

4. Запустите MongoDB:
```bash
# Убедитесь, что MongoDB запущен на localhost:27017
```

5. Запустите приложение:
```bash
uvicorn main:app --reload
```

API будет доступно по адресу: http://localhost:8000
Swagger документация: http://localhost:8000/docs

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