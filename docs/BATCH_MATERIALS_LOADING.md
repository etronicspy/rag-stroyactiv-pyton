# Batch Materials Loading

Руководство по массовой загрузке материалов в систему.

## 🚀 Доступные методы

### 1. Batch API Endpoint

**Endpoint:** `POST /api/v1/materials/batch`

Создание материалов в batch режиме с готовыми данными.

```json
{
  "materials": [
    {
      "name": "Цемент портландский М500",
      "category": "Цемент",
      "unit": "кг",
      "description": "Высококачественный цемент"
    }
  ],
  "batch_size": 100
}
```

### 2. Import API Endpoint

**Endpoint:** `POST /api/v1/materials/import`

Импорт материалов из JSON формата с автоматической категоризацией.

```json
{
  "materials": [
    {
      "article": "CEM0001",
      "name": "Цемент портландский М500"
    }
  ],
  "default_category": "Стройматериалы",
  "default_unit": "шт",
  "batch_size": 100
}
```

## 📊 Автоматическая категоризация

Система автоматически определяет категории и единицы измерения на основе ключевых слов:

### Категории:
- **Цемент** - цемент, бетон
- **Кирпич** - кирпич
- **Блоки** - блок
- **Арматура** - арматура, металл
- **Пиломатериалы** - доска, брус
- **Листовые материалы** - фанера, гипсокартон
- **Плитка** - плитка
- **Лакокрасочные материалы** - краска, эмаль
- **Сухие смеси** - шпатлевка, штукатурка
- **Теплоизоляция** - утеплитель
- **Кровельные материалы** - черепица, профнастил
- **Трубы и фитинги** - труба
- **Электротехника** - кабель, провод
- **Окна и двери** - окно, дверь
- **Крепеж** - саморез, гвоздь, болт

### Единицы измерения:
- **кг** - цемент, краска, эмаль
- **м³** - песок, щебень, бетон, доска, брус
- **шт** - кирпич, блок
- **м²** - плитка, лист, рулон
- **м** - труба, кабель, провод

## 🛠️ Использование утилиты загрузки

### Установка зависимостей
```bash
pip install aiohttp
```

### Загрузка из командной строки
```bash
# Базовое использование
python utils/load_materials.py tests/data/building_materials.json

# С настройками
python utils/load_materials.py tests/data/building_materials.json 50 http://localhost:8000
```

### Программное использование
```python
from utils.load_materials import MaterialsLoader

loader = MaterialsLoader("http://localhost:8000")

# Загрузка из JSON файла
result = await loader.load_from_json_file(
    "tests/data/building_materials.json", 
    batch_size=100
)

# Использование batch API
materials = [
    {
        "name": "Цемент М500",
        "category": "Цемент", 
        "unit": "кг",
        "description": "Описание"
    }
]
result = await loader.load_using_batch_api(materials, batch_size=50)
```

## 📈 Производительность

### Рекомендуемые настройки:

- **Малые файлы** (< 100 материалов): `batch_size = 50`
- **Средние файлы** (100-1000 материалов): `batch_size = 100`
- **Большие файлы** (> 1000 материалов): `batch_size = 200`

### Ожидаемая производительность:
- **500 материалов**: ~15-30 секунд
- **1000 материалов**: ~30-60 секунд
- **5000 материалов**: ~2-5 минут

## 🔍 Пример ответа

```json
{
  "success": true,
  "total_processed": 500,
  "successful_creates": 495,
  "failed_creates": 5,
  "processing_time_seconds": 23.45,
  "errors": [
    "Material 'X': name too short",
    "Batch 3: Failed to generate embedding"
  ],
  "created_materials": [
    {
      "id": "uuid-here",
      "name": "Цемент портландский М500",
      "category": "Цемент",
      "unit": "кг",
      "description": "Артикул: CEM0001",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## 🧪 Тестирование

Запуск тестов для batch функциональности:

```bash
# Все тесты материалов
pytest tests/test_materials.py -v

# Только batch тесты
pytest tests/test_materials.py -k "batch" -v

# Только import тесты  
pytest tests/test_materials.py -k "import" -v
```

## ⚠️ Ограничения

- **Максимум материалов в batch**: 1000
- **Максимальный batch_size**: 500
- **Timeout**: 5 минут на batch
- **Минимальная длина названия**: 2 символа
- **Максимальная длина названия**: 200 символов

## 🚨 Обработка ошибок

Система продолжает обработку даже при ошибках в отдельных материалах:

1. **Validation ошибки** - пропуск материала, продолжение обработки
2. **Embedding ошибки** - повторная попытка, затем пропуск batch
3. **Database ошибки** - откат batch, продолжение со следующим

## 💡 Советы по оптимизации

1. **Предварительная валидация** - проверьте JSON на корректность
2. **Дедупликация** - удалите дубликаты перед загрузкой
3. **Группировка** - сортируйте по категориям для лучшего кэширования
4. **Мониторинг** - следите за логами для выявления проблем

## 📝 Логирование

Система логирует:
- Прогресс обработки батчей
- Количество успешных/неуспешных операций
- Время обработки каждого batch
- Детали ошибок

Пример лога:
```
Processing batch 1/5: 100 materials
Successfully inserted 98 materials
Processing batch 2/5: 100 materials
Error generating embeddings for batch: Rate limit exceeded
Processing batch 3/5: 100 materials
Successfully inserted 100 materials
``` 