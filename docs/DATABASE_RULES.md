# Строгие правила работы с базой данных PostgreSQL

## 🔒 Обязательные требования

### База данных: ТОЛЬКО `stbr_rag1`

**СТРОГОЕ ПРАВИЛО:** Проект работает исключительно с базой данных `stbr_rag1`.

#### Технические причины:

1. **ICU локаль (ru-RU-x-icu)** - обеспечивает полную поддержку русского языка
2. **Корректная сортировка** - правильная обработка кириллических символов
3. **Полнотекстовый поиск** - поддержка русскоязычных запросов
4. **Уникодная нормализация** - правильная обработка диакритических знаков

#### Конфигурация базы данных:

```
Name: stbr_rag1
Owner: postgres  
Encoding: UTF8
Collate: en_US.UTF-8
Ctype: en_US.UTF-8
Locale Provider: icu
ICU Locale: ru-RU-x-icu
```

## ⚠️ Запрещенные базы данных

Следующие базы данных **ЗАПРЕЩЕНЫ** для использования:

- `materials` (libc локаль - нет поддержки русского языка)
- `postgres` (системная база данных)
- `template0`, `template1` (шаблонные базы данных)
- `stbo_1`, `stbr` (используются другими проектами)

## 🛠️ Настройка конфигурации

### Environment переменные:

```bash
# ОБЯЗАТЕЛЬНАЯ конфигурация
POSTGRESQL_DATABASE=stbr_rag1
POSTGRESQL_URL=postgresql+asyncpg://user:password@host:port/stbr_rag1
```

### Автоматическая валидация:

Система автоматически проверяет:
- ✅ Название базы данных должно быть `stbr_rag1`
- ✅ URL подключения должен содержать `/stbr_rag1`
- ❌ При нарушении правил - ошибка валидации

## 🔍 Проверка соответствия

### Команды для проверки:

```bash
# Проверка текущей базы данных
python -c "from core.config import get_settings; print(get_settings().POSTGRESQL_DATABASE)"

# Диагностика подключения
python utils/data/postgresql_diagnostic.py

# Проверка локали
SELECT datname, datcollate, datctype, datlocprovider, daticulocale 
FROM pg_database 
WHERE datname = 'stbr_rag1';
```

### Ожидаемый результат:

```
datname: stbr_rag1
datcollate: en_US.UTF-8  
datctype: en_US.UTF-8
datlocprovider: i (ICU)
daticulocale: ru-RU-x-icu
```

## 📋 Миграции и схема

### Создание таблиц в `stbr_rag1`:

```bash
# Применение миграций Alembic
alembic upgrade head
```

### Проверка таблиц:

```sql
-- Должны быть созданы в схеме public базы stbr_rag1
\dt public.*
```

Ожидаемые таблицы:
- `alembic_version` - версии миграций
- `materials` - основные материалы
- `raw_products` - сырые продукты от поставщиков

## 🚨 Безопасность

### Запрет операций:

- ❌ Создание новых баз данных
- ❌ Удаление существующих баз данных  
- ❌ Изменение конфигурации `stbr_rag1`
- ❌ Подключение к другим базам данных

### Разрешенные операции:

- ✅ CRUD операции в таблицах `stbr_rag1`
- ✅ Создание индексов в `stbr_rag1`
- ✅ Применение миграций в `stbr_rag1`
- ✅ Резервное копирование `stbr_rag1`

## 🔧 Устранение неполадок

### Проблема: "Database not found"

```bash
# Проверьте существование базы
psql -h localhost -p 5435 -U superadmin -l | grep stbr_rag1
```

### Проблема: "Validation error"

```bash
# Проверьте конфигурацию
grep POSTGRESQL_DATABASE .env.local
```

### Проблема: "Encoding issues with Russian text"

```sql
-- Проверьте локаль базы данных
SELECT datname, daticulocale FROM pg_database WHERE datname = 'stbr_rag1';
```

Должен вернуть: `ru-RU-x-icu`

---

**❗ ВАЖНО:** Нарушение этих правил может привести к некорректной работе с русскоязычным контентом и поисковыми запросами. 