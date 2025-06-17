# 🗄️ PostgreSQL Database Rules

## 🔒 Основные требования

### База данных: `stbr_rag1`
Проект работает исключительно с базой данных `stbr_rag1` по техническим причинам:

- **ICU локаль (ru-RU-x-icu)** - полная поддержка русского языка
- **Корректная сортировка** кириллических символов
- **Полнотекстовый поиск** на русском языке

### Конфигурация базы данных
```
Name: stbr_rag1
Encoding: UTF8
ICU Locale: ru-RU-x-icu
```

## ⚙️ Настройка

### Environment переменные
```env
# ОБЯЗАТЕЛЬНАЯ конфигурация
POSTGRESQL_DATABASE=stbr_rag1
POSTGRESQL_URL=postgresql+asyncpg://user:password@host:port/stbr_rag1
```

### Автоматическая валидация
Система проверяет:
- ✅ Название базы данных = `stbr_rag1`
- ✅ URL содержит `/stbr_rag1`
- ❌ При нарушении - ошибка валидации

## 🔧 Проверка соответствия

```bash
# Проверка текущей базы данных
python -c "from core.config import get_settings; print(get_settings().POSTGRESQL_DATABASE)"

# Проверка локали
SELECT datname, daticulocale FROM pg_database WHERE datname = 'stbr_rag1';
# Ожидаемый результат: ru-RU-x-icu
```

## 📋 Миграции

```bash
# Применение миграций Alembic
alembic upgrade head

# Проверка таблиц
\dt public.*
```

**Ожидаемые таблицы**:
- `materials` - основные материалы
- `raw_products` - сырые продукты от поставщиков
- `categories` - категории материалов
- `units` - единицы измерения

## 🚨 Безопасность

### ❌ Запрещено
- Создание/удаление баз данных
- Подключение к другим БД (`materials`, `postgres`, `template0/1`)
- Изменение конфигурации `stbr_rag1`

### ✅ Разрешено
- CRUD операции в таблицах `stbr_rag1`
- Создание индексов
- Применение миграций
- Резервное копирование

---

**❗ ВАЖНО**: Нарушение правил может привести к некорректной работе с русскоязычным контентом. 