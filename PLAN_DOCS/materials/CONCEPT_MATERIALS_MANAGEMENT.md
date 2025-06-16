# 📋 Концепция управления справочными материалами

Документация по концепции добавления и управления справочными материалами в системе RAG для строительных материалов.

---

## 🎯 **Общая концепция**

Система RAG для строительных материалов реализует **многоуровневую архитектуру** добавления справочных материалов с использованием искусственного интеллекта для семантического поиска и сопоставления:

1. **Гибридная архитектура БД**: Векторная (Qdrant) + Реляционная (PostgreSQL)
2. **ИИ-интеграция**: OpenAI embeddings для семантического поиска
3. **Множественные форматы входных данных**: API, CSV, Excel, JSON
4. **Автоматическая категоризация и обогащение данных**

---

## 🏗️ **Структура записи материала**

### **Основные поля материала:**

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | `string` | ✅ | UUID4 - уникальный идентификатор |
| `name` | `string` | ✅ | Название материала (2-200 символов) |
| `use_category` | `string` | ✅ | Категория использования материала |
| `unit` | `string` | ✅ | Единица измерения |
| `sku` | `string` | ❌ | SKU/артикул (3-50 символов) |
| `description` | `string` | ❌ | Описание материала |
| `embedding` | `array[float]` | ✅ | Векторное представление (1536 измерений) |
| `created_at` | `datetime` | ✅ | Дата создания (ISO 8601) |
| `updated_at` | `datetime` | ✅ | Дата обновления (ISO 8601) |

### **Пример структуры:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Цемент портландский М400",
  "use_category": "Цемент",  
  "unit": "кг",
  "sku": "CEM400",
  "description": "Высококачественный портландцемент",
  "embedding": [0.023, -0.156, ...], // 1536 dimensions
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### **Валидация полей (Pydantic модель):**
```python
class MaterialCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    use_category: str = Field(..., max_length=200)
    unit: str
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None
```

---

## 🤖 **Взаимодействие с искусственным интеллектом**

### **1. Генерация эмбеддингов**
- **Технология**: OpenAI text-embedding-3-small (1536 измерений)
- **Входные данные**: `{name} {use_category} {description}`
- **Процесс**: 
  ```python
  text_for_embedding = f"{name} {use_category} {description}".strip()
  embedding = await openai.embeddings.create(
      input=text_for_embedding,
      model="text-embedding-3-small",
      dimensions=1536
  )
  ```

### **2. Автоматическая категоризация**
Система использует **словарь ключевых слов** для автоматического определения категорий:

```python
category_mapping = {
    "цемент": "Цемент",
    "бетон": "Бетон", 
    "кирпич": "Кирпич",
    "блок": "Блоки",
    "газобетон": "Газобетон",
    "пеноблок": "Пеноблоки",
    "арматура": "Арматура",
    "металл": "Металлопрокат",
    "труба": "Трубы",
    "профиль": "Профили",
    "лист": "Листовые материалы",
    "утеплитель": "Утеплители",
    "изоляция": "Изоляционные материалы",
    "кровля": "Кровельные материалы",
    "черепица": "Черепица",
    "профнастил": "Профнастил",
    "сайдинг": "Сайдинг",
    "гипсокартон": "Гипсокартон",
    "фанера": "Фанера",
    "доска": "Пиломатериалы",
    "брус": "Пиломатериалы",
    "краска": "Лакокрасочные материалы",
    "грунт": "Грунтовки",
    "клей": "Клеи",
    "герметик": "Герметики",
    "смесь": "Сухие смеси",
    "раствор": "Растворы",
    "штукатурка": "Штукатурки",
    "шпатлевка": "Шпатлевки",
    "плитка": "Плитка",
    "керамогранит": "Керамогранит",
    "ламинат": "Ламинат",
    "линолеум": "Линолеум",
    "паркет": "Паркет"
}
```

### **3. Автоматическое определение единиц измерения**
```python
unit_mapping = {
    "цемент": "кг",
    "песок": "м³",
    "щебень": "м³",
    "бетон": "м³",
    "доска": "м³",
    "брус": "м³",
    "кирпич": "шт",
    "блок": "шт",
    "плитка": "м²",
    "краска": "кг",
    "эмаль": "кг",
    "лист": "м²",
    "рулон": "м²",
    "труба": "м",
    "кабель": "м",
    "провод": "м"
}
```

### **4. Качество и характеристики эмбеддингов**
- **Размерность**: 1536 (OpenAI text-embedding-3-small)
- **Нормализация**: Векторы нормализованы для косинусной метрики
- **Диапазон значений**: Обычно от -0.1 до 0.1
- **Метрика расстояния**: Cosine similarity
- **Хранение**: Qdrant векторная БД

---

## 📊 **Алгоритм действий при добавлении материала**

### **Этап 1: Валидация входных данных**
```python
# 1. Проверка обязательных полей
required_fields = ["name", "use_category", "unit"]

# 2. Валидация длины строк
name: 2-200 символов
sku: 3-50 символов (если указан)
use_category: максимум 200 символов

# 3. Проверка формата данных
# Pydantic автоматически валидирует типы данных
```

### **Этап 2: Автоматическое обогащение данных**
```python
# 1. Генерация UUID4 для id
material.id = str(uuid.uuid4())

# 2. Автоматическая категоризация (если не указана)
if not material.use_category:
    material.use_category = infer_category(material.name)

# 3. Определение единицы измерения (если не указана) 
if not material.unit:
    material.unit = infer_unit(material.name)

# 4. Создание базового описания (если не указано)
if not material.description:
    material.description = f"{material.name} - качественный строительный материал"

# 5. Установка временных меток
material.created_at = datetime.utcnow()
material.updated_at = datetime.utcnow()
```

### **Этап 3: Генерация ИИ-эмбеддинга**
```python
async def create_embedding(material):
    # Формируем текст для эмбеддинга
    text = f"{material.name} {material.use_category} {material.description}".strip()
    
    # Генерируем эмбеддинг через OpenAI
    response = await ai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small", 
        dimensions=1536
    )
    
    # Получаем нормализованный вектор
    embedding = response.data[0].embedding
    
    return embedding
```

### **Этап 4: Сохранение в базы данных**
```python
# 1. Основное хранилище - Векторная БД (Qdrant)
vector_data = {
    "id": material.id,
    "vector": material.embedding,
    "payload": {
        "name": material.name,
        "use_category": material.use_category,
        "unit": material.unit,
        "sku": material.sku,
        "description": material.description,
        "created_at": material.created_at.isoformat(),
        "updated_at": material.updated_at.isoformat()
    }
}
await vector_db.upsert(collection_name="materials", vectors=[vector_data])

# 2. Резервное хранилище - Реляционная БД (PostgreSQL) 
await postgresql_db.insert_material(material)
```

### **Этап 5: Верификация и логирование**
```python
# 1. Проверка успешности сохранения
saved_material = await vector_db.get_by_id("materials", material.id)

# 2. Логирование операции
logger.info(f"Material created: {material.name} (ID: {material.id})")

# 3. Обновление метрик
metrics_collector.increment("materials_created")
```

---

## 🎬 **Сценарии добавления материалов**

### **Сценарий 1: Единичное создание через API**
**Endpoint**: `POST /api/v1/materials/`

**Запрос:**
```http
POST /api/v1/materials/
Content-Type: application/json

{
  "name": "Портландцемент М500",
  "use_category": "Цемент",
  "unit": "кг",
  "description": "Высококачественный цемент"
}
```

**Процесс:**
1. Валидация входных данных через Pydantic
2. Генерация UUID4 для ID
3. Создание эмбеддинга через OpenAI
4. Сохранение в Qdrant и PostgreSQL
5. Возврат созданного материала с embedding

**Результат:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Портландцемент М500",
  "use_category": "Цемент",
  "unit": "кг", 
  "description": "Высококачественный цемент",
  "embedding": [0.023, -0.156, ...],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### **Сценарий 2: Массовая загрузка через CSV/Excel**
**Endpoint**: `POST /api/v1/prices/process`

**Запрос:**
```http
POST /api/v1/prices/process
Content-Type: multipart/form-data

file: pricelist.csv
supplier_id: "supplier_001"
```

**Формат CSV (Legacy):**
```csv
name,use_category,unit,price,description
"Цемент М400","Цемент","кг",150.00,"Портландцемент марки 400"
"Песок речной","Песок","м³",800.00,"Песок для строительных работ"
"Кирпич красный","Кирпич","шт",12.50,"Керамический строительный кирпич"
```

**Формат CSV (Расширенный):**
```csv
name,sku,use_category,unit_price,unit_price_currency,calc_unit,count
"Кирпич керамический","SKU001","Кирпич",12.50,"RUB","шт",1000
"Блок газобетонный","SKU002","Блоки",85.00,"RUB","м³",50
```

**Процесс:**
1. Чтение и парсинг CSV/Excel файла
2. Определение формата данных (Legacy/Extended)
3. Batch-валидация всех записей
4. Автоматическая категоризация (если нужно)
5. Batch-генерация эмбеддингов
6. Массовое сохранение в БД

**Результат:**
```json
{
  "message": "Price list processed successfully",
  "supplier_id": "supplier_001",
  "materials_processed": 150,
  "upload_date": "2025-06-16T19:15:30.123456Z"
}
```

### **Сценарий 3: Импорт из JSON**
**Endpoint**: `POST /api/v1/materials/import`

**Запрос:**
```http
POST /api/v1/materials/import
Content-Type: application/json

{
  "materials": [
    {"sku": "CEM001", "name": "Цемент портландский М500"},
    {"sku": "CEM002", "name": "Цемент белый декоративный"},
    {"sku": "BRK001", "name": "Кирпич керамический красный"}
  ],
  "default_use_category": "Стройматериалы",
  "default_unit": "кг",
  "batch_size": 100
}
```

**Процесс:**
1. Парсинг JSON с материалами
2. Применение default значений
3. Автоматическая категоризация по названию
4. Batch-создание эмбеддингов
5. Массовое сохранение

**Результат:**
```json
{
  "success": true,
  "total_processed": 3,
  "successful_materials": [...],
  "failed_materials": [],
  "processing_time_seconds": 2.45,
  "errors": []
}
```

### **Сценарий 4: Batch создание с готовыми данными**
**Endpoint**: `POST /api/v1/materials/batch`

**Запрос:**
```http
POST /api/v1/materials/batch
Content-Type: application/json

{
  "materials": [
    {
      "name": "Цемент портландский М500",
      "use_category": "Цемент", 
      "unit": "кг",
      "description": "Высококачественный цемент"
    },
    {
      "name": "Песок речной мытый",
      "use_category": "Песок",
      "unit": "м³", 
      "description": "Чистый речной песок"
    }
  ],
  "batch_size": 100
}
```

**Процесс:**
1. Валидация всех материалов
2. Batch-генерация UUID и эмбеддингов
3. Parallel-сохранение в БД
4. Сбор статистики успешности

---

## 🔍 **Особенности ИИ-взаимодействия**

### **1. Семантический поиск с fallback-стратегией**
```python
# Алгоритм поиска (приоритет по убыванию):
1. Vector search (семантический поиск по эмбеддингам)
   - Поиск по векторному сходству в Qdrant
   - Cosine similarity > 0.6
   
2. SQL LIKE search (текстовый поиск, если vector не дал результатов)  
   - PostgreSQL полнотекстовый поиск
   - LIKE операторы с wildcard
   
3. Combined hybrid search (комбинированный результат)
   - Объединение результатов с весами
   - Дедупликация и ранжирование
```

### **2. Кэширование эмбеддингов**

**LRU-кэш для эмбеддингов:**
```python
class OptimizedEmbeddingService:
    def __init__(self):
        self.ai_client = get_ai_client()
        self._batch_size = 50
    
    @lru_cache(maxsize=128)
    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    async def get_embedding(self, text: str) -> List[float]:
        cache_key = self._get_cache_key(text)
        cached_vector = vector_cache.get(cache_key)
        if cached_vector is not None:
            return cached_vector
        # ... генерация нового эмбеддинга
```

**Batch-обработка для массовых операций:**
```python
async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
    # Разделение на кэшированные и новые тексты
    cached_embeddings = []
    uncached_texts = []
    
    # Batch-запрос к OpenAI для некэшированных
    if uncached_texts:
        response = await self.ai_client.embeddings.create(
            input=uncached_texts,
            model="text-embedding-3-small",
            dimensions=1536
        )
        # Сохранение в кэш и возврат результатов
```

### **3. Оптимизация производительности ИИ**

**Parallel processing для больших объемов:**
```python
# Параллельная обработка материалов
async def process_materials_parallel(materials: List[Material]):
    tasks = []
    semaphore = asyncio.Semaphore(5)  # Ограничение конкурентности
    
    async def process_single(material):
        async with semaphore:
            return await create_material_with_embedding(material)
    
    for material in materials:
        tasks.append(process_single(material))
    
    return await asyncio.gather(*tasks)
```

---

## 📈 **Мониторинг и аналитика**

### **1. Логирование операций**
```python
# Детальное логирование всех этапов
logger.info(f"Material creation started: {material.name}")
logger.info(f"Embedding generated: {len(embedding)} dimensions")
logger.info(f"Saved to vector DB: {material.id}")
logger.info(f"Material created successfully: {processing_time:.2f}s")
```

### **2. Метрики производительности**
```python
# Сбор метрик через metrics_collector
metrics_collector.increment("materials_created")
metrics_collector.histogram("embedding_generation_time", processing_time)
metrics_collector.histogram("material_creation_total_time", total_time)
```

### **3. Health checks**
```python
# Проверка здоровья всех компонентов
async def health_check():
    checks = {
        "vector_db": await vector_db.health_check(),
        "postgresql_db": await postgresql_db.health_check(), 
        "ai_client": await ai_client.health_check(),
        "embedding_service": await embedding_service.health_check()
    }
    return checks
```

### **4. Качество автоматической категоризации**
```python
# Отслеживание точности автоматической категоризации
def track_categorization_accuracy():
    manual_categories = get_manual_categories()
    auto_categories = get_auto_categories()
    
    accuracy = calculate_accuracy(manual_categories, auto_categories)
    metrics_collector.gauge("categorization_accuracy", accuracy)
```

---

## 🔧 **Конфигурация и настройки**

### **Настройки AI Provider:**
```python
# OpenAI Configuration
AI_PROVIDER = "openai"
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "text-embedding-3-small"  
OPENAI_DIMENSIONS = 1536
OPENAI_MAX_RETRIES = 3
OPENAI_TIMEOUT = 30.0
```

### **Настройки векторной БД:**
```python
# Qdrant Configuration
QDRANT_URL = "http://localhost:6333"
QDRANT_API_KEY = "qdrant-api-key"
QDRANT_COLLECTION_NAME = "materials"
VECTOR_DIMENSIONS = 1536
DISTANCE_METRIC = "Cosine"
```

### **Batch настройки:**
```python
# Batch Processing Limits
MAX_BATCH_SIZE = 500
DEFAULT_BATCH_SIZE = 100
MAX_FILE_SIZE_MB = 50
MAX_CONCURRENT_REQUESTS = 5
```

---

## 🚨 **Обработка ошибок и восстановление**

### **Типичные ошибки и решения:**

1. **Ошибка генерации эмбеддинга:**
   ```python
   try:
       embedding = await ai_client.get_embedding(text)
   except AIServiceError:
       # Fallback: использовать mock embedding или повторить позже
       embedding = create_mock_embedding(text)
   ```

2. **Ошибка сохранения в векторной БД:**
   ```python
   try:
       await vector_db.upsert(material)
   except VectorDBError:
       # Fallback: сохранить только в PostgreSQL
       await postgresql_db.save(material)
   ```

3. **Валидационные ошибки:**
   ```python
   try:
       material = MaterialCreate(**data)
   except ValidationError as e:
       # Логировать ошибку и вернуть детали
       logger.error(f"Validation failed: {e}")
       return {"error": "Invalid data", "details": e.errors()}
   ```

---

## 📝 **Заключение**

Данная концепция обеспечивает:

✅ **Масштабируемость** - Batch-обработка и параллельные операции  
✅ **Интеллектуальность** - Автоматическая категоризация и семантический поиск  
✅ **Гибкость** - Множественные форматы входных данных  
✅ **Надежность** - Fallback-стратегии и error handling  
✅ **Производительность** - Кэширование и оптимизация ИИ-запросов  
✅ **Мониторинг** - Полное логирование и метрики  

Система готова к промышленному использованию для управления большими каталогами строительных материалов с максимальной автоматизацией благодаря интеграции с современными ИИ-технологиями. 