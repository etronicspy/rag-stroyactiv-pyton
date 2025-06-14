# План миграции RAG Construction Materials API на Python 3.11+

## 📋 Обзор миграции

**Цель:** Безопасный переход с Python 3.9+ на Python 3.11+ для получения:
- 15-25% прироста производительности async операций
- Улучшенных error messages и debugging
- Современного синтаксиса и возможностей
- Лучшей совместимости с новыми библиотеками

**Временные рамки:** 2-3 недели
**Риски:** Низкие (все основные зависимости поддерживают 3.11+)

---

## 🎯 Этап 1: Подготовка и анализ (2-3 дня)

### 1.1 Аудит совместимости зависимостей
- [ ] Проверить все зависимости из `requirements.txt` на совместимость с Python 3.11+
- [ ] Обновить версии библиотек до последних стабильных:
  ```
  fastapi>=0.104.1 → fastapi>=0.108.0
  pydantic>=2.5.3 → pydantic>=2.6.0
  sqlalchemy>=2.0.23 → sqlalchemy>=2.0.25
  qdrant-client>=1.6.4 → qdrant-client>=1.7.0
  ```
- [ ] Создать `requirements-py311.txt` для тестирования

### 1.2 Настройка окружения для тестирования
- [ ] Установить Python 3.11 параллельно с текущей версией
- [ ] Создать виртуальное окружение для Python 3.11:
  ```bash
  python3.11 -m venv .venv-py311
  source .venv-py311/bin/activate
  pip install -r requirements-py311.txt
  ```
- [ ] Настроить IDE для работы с Python 3.11

### 1.3 Backup и версионирование
- [ ] Создать ветку `feature/python-3.11-migration`
- [ ] Создать backup текущего состояния
- [ ] Зафиксировать текущие версии в lockfile

---

## 🔧 Этап 2: Обновление кода (1 неделя)

### 2.1 Унификация типов и импортов
**Priority: HIGH** - Затрагивает весь проект

#### Задачи:
- [ ] **Заменить устаревшие импорты типов** (25+ файлов):
  ```python
  # БЫЛО:
  from typing import Dict, List, Any, Optional, Union
  
  # СТАЛО:
  from typing import Any, Optional  # только то что нужно
  # dict, list используем встроенные
  ```

- [ ] **Обновить type hints во всех модулях:**
  ```python
  # БЫЛО:
  def process_materials(data: List[Dict[str, Any]]) -> Dict[str, List[Material]]
  
  # СТАЛО:
  def process_materials(data: list[dict[str, Any]]) -> dict[str, list[Material]]
  ```

#### Файлы для обновления:
```
├── services/ (все .py файлы)
├── core/ (все .py файлы)  
├── api/ (все .py файлы)
├── utils/ (все .py файлы)
└── tests/ (все .py файлы)
```

### 2.2 Добавление современного синтаксиса Python 3.11+

#### 2.2.1 Использование Self type (новое в 3.11)
- [ ] **Обновить методы классов:**
  ```python
  # БЫЛО:
  from typing import TypeVar
  T = TypeVar('T', bound='ClassName')
  def method(self: T) -> T:
  
  # СТАЛО:
  from typing import Self
  def method(self) -> Self:
  ```

#### 2.2.2 Улучшенные Exception Groups (3.11+)
- [ ] **Обновить обработку ошибок в batch операциях:**
  ```python
  # services/dynamic_batch_processor.py
  # Использовать ExceptionGroup для множественных ошибок
  try:
      results = await process_batches()
  except* ValueError as eg:
      for error in eg.exceptions:
          logger.error(f"Validation error: {error}")
  ```

#### 2.2.3 Улучшенная типизация для Generic классов
- [ ] **Обновить Repository классы:**
  ```python
  # core/repositories/base.py
  from typing import Generic, TypeVar
  T = TypeVar('T')
  
  class BaseRepository(Generic[T]):
      async def create(self, obj: T) -> T: ...
  ```

### 2.3 Оптимизация производительности

#### 2.3.1 Асинхронные операции
- [ ] **Использовать улучшенный asyncio в Python 3.11:**
  ```python
  # Более эффективные TaskGroup (3.11+)
  import asyncio
  
  async def process_multiple_searches():
      async with asyncio.TaskGroup() as tg:
          task1 = tg.create_task(vector_search())
          task2 = tg.create_task(sql_search())
          task3 = tg.create_task(fuzzy_search())
      
      return task1.result(), task2.result(), task3.result()
  ```

#### 2.3.2 Оптимизация JSON операций
- [ ] **Улучшить сериализацию ответов API:**
  ```python
  # Использовать быстрый JSON в Python 3.11+
  import json
  from typing import Any
  
  # Python 3.11 имеет улучшенный json.dumps
  def serialize_response(data: dict[str, Any]) -> str:
      return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
  ```

---

## 🧪 Этап 3: Тестирование (3-4 дня)

### 3.1 Модульные тесты
- [ ] **Запустить все существующие тесты на Python 3.11:**
  ```bash
  python3.11 -m pytest tests/ -v --tb=short
  ```
- [ ] **Исправить несовместимые тесты** (если будут)
- [ ] **Добавить тесты для новых возможностей Python 3.11**

### 3.2 Интеграционные тесты
- [ ] **Протестировать все БД подключения:**
  - PostgreSQL с asyncpg
  - Qdrant/Weaviate/Pinecone
  - Redis
- [ ] **Протестировать batch операции и производительность**
- [ ] **Протестировать загрузку CSV/Excel файлов**

### 3.3 Производительность тесты
- [ ] **Замерить производительность до и после:**
  ```python
  # Создать benchmark тесты
  import time
  import asyncio
  
  async def benchmark_vector_search():
      start = time.perf_counter()
      # ... выполнить операции
      end = time.perf_counter()
      return end - start
  ```
- [ ] **Сравнить времена выполнения:**
  - Векторный поиск
  - Batch обработка
  - API ответы
  - БД операции

### 3.4 Regression тестирование  
- [ ] **Протестировать все API endpoints**
- [ ] **Проверить корректность поиска и результатов**
- [ ] **Валидация Pydantic схем**

---

## 🚀 Этап 4: Обновление инфраструктуры (2-3 дня)

### 4.1 Docker и контейнеризация
- [ ] **Обновить Dockerfile:**
  ```dockerfile
  # БЫЛО:
  FROM python:3.9-slim
  
  # СТАЛО:  
  FROM python:3.11-slim
  ```
- [ ] **Обновить docker-compose.yml**
- [ ] **Пересобрать образы и протестировать**

### 4.2 CI/CD пайплайны
- [ ] **Обновить GitHub Actions / GitLab CI:**
  ```yaml
  # .github/workflows/test.yml
  strategy:
    matrix:
      python-version: [3.11, 3.12]  # убрать 3.9
  ```
- [ ] **Обновить скрипты развертывания**
- [ ] **Проверить совместимость с prod окружением**

### 4.3 Документация
- [ ] **Обновить README.md:**
  - Изменить требования Python 3.9+ → Python 3.11+
  - Добавить инструкции по миграции
  - Обновить примеры установки
- [ ] **Обновить .cursorrules:**
  ```
  - Python 3.11+, FastAPI, async/await везде
  ```

---

## 📊 Этап 5: Мониторинг и оптимизация (1-2 дня)

### 5.1 Мониторинг производительности
- [ ] **Настроить метрики для отслеживания:**
  - Время ответа API
  - Использование памяти
  - CPU утилизация
  - Throughput операций

### 5.2 Профилирование
- [ ] **Использовать cProfile для анализа:**
  ```python
  import cProfile
  import pstats
  
  def profile_search_operations():
      profiler = cProfile.Profile()
      profiler.enable()
      # ... операции поиска
      profiler.disable()
      
      stats = pstats.Stats(profiler)
      stats.sort_stats('cumulative')
      stats.print_stats(20)
  ```

### 5.3 Оптимизация узких мест
- [ ] **Оптимизировать найденные bottlenecks**
- [ ] **Использовать новые возможности Python 3.11 для ускорения**

---

## ⚠️ Управление рисками

### Потенциальные проблемы:
1. **Несовместимость зависимостей** → Заранее протестировать все библиотеки
2. **Изменения поведения asyncio** → Тщательное тестирование async кода  
3. **Проблемы с production** → Поэтапный rollout

### Стратегия отката:
- [ ] Сохранить образы Docker с Python 3.9
- [ ] Иметь готовую ветку для быстрого отката
- [ ] Настроить monitoring для быстрого обнаружения проблем

---

## 📈 Ожидаемые результаты

### Производительность:
- **15-25% ускорение** async операций
- **10-20% ускорение** JSON операций  
- **Улучшенное** использование памяти

### Качество кода:
- **Современный синтаксис** Python 3.11+
- **Лучшие error messages** для debugging
- **Унифицированные** type hints

### Совместимость:
- **Поддержка** новых версий библиотек
- **Готовность** к Python 3.12+ в будущем

---

## ✅ Чек-лист готовности к миграции

**Перед началом:**
- [ ] Team готова к миграции
- [ ] Есть время для тестирования
- [ ] Настроен rollback план
- [ ] Production мониторинг готов

**После завершения:**
- [ ] Все тесты проходят
- [ ] Производительность не хуже (желательно лучше)
- [ ] Документация обновлена
- [ ] Team обучена новым возможностям

---

## 📞 Контакты и поддержка

**Ответственный за миграцию:** [Указать ответственного]
**Дата начала:** [Указать дату]
**Планируемое завершение:** [Указать дату]

**Важно:** Этот план является живым документом и может корректироваться в процессе миграции на основе обнаруженных особенностей проекта. 