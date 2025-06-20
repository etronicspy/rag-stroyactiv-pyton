# 📚 Примеры использования системы логирования

Эта директория содержит практические примеры использования модульной системы логирования.

## 📁 Структура примеров

- `basic_usage.py` - Базовое использование логирования
- `advanced_features.py` - Продвинутые возможности (метрики, оптимизация)
- `api_integration.py` - Интеграция с FastAPI endpoints
- `service_integration.py` - Использование в сервисах
- `middleware_example.py` - Создание middleware с логированием
- `migration_example.py` - Миграция от старой системы
- `performance_tuning.py` - Настройка производительности
- `troubleshooting.py` - Диагностика и отладка

## 🚀 Быстрый запуск

```bash
# Перейти в директорию примеров
cd examples/logging

# Запустить базовый пример
python basic_usage.py

# Запустить продвинутый пример
python advanced_features.py
```

## 📋 Требования

Все примеры используют модули из `core.logging` и требуют:
- Python 3.9+
- Настроенные переменные окружения (см. `.env.example`)
- Установленные зависимости из `requirements.txt`

## 🔧 Конфигурация для примеров

Создайте `.env` файл с необходимыми настройками:

```bash
LOG_LEVEL=DEBUG
ENABLE_STRUCTURED_LOGGING=false
LOG_COLORS=true
LOG_CORRELATION_ID=true
LOG_DATABASE_OPERATIONS=true
LOG_PERFORMANCE_METRICS=true
```

## 📖 Описание примеров

### `basic_usage.py`
- Создание логгера
- Базовые уровни логирования  
- Использование correlation ID
- Структурированные данные

### `advanced_features.py`
- Производительные оптимизации
- Сбор метрик
- Асинхронное логирование
- Батчинг операций

### `api_integration.py`
- Логирование FastAPI endpoint'ов
- Middleware для автоматического логирования
- Обработка ошибок с логированием
- HTTP метрики

### `service_integration.py`
- Логирование в сервисных классах
- Database операции с логированием
- Business logic логирование
- Error handling

### `migration_example.py`
- Постепенная миграция от `core.monitoring`
- Обратная совместимость
- Новые возможности
- Best practices

## 🎯 Рекомендации

1. **Начните с `basic_usage.py`** для понимания основ
2. **Изучите `advanced_features.py`** для production use cases
3. **Используйте `api_integration.py`** для веб-приложений
4. **Следуйте `migration_example.py`** при переходе от старой системы

## 🔗 Дополнительные ресурсы

- [Полное руководство](../../docs/LOGGING_SYSTEM_GUIDE.md)
- [Troubleshooting](../../docs/TROUBLESHOOTING_LOGGING.md)
- [Конфигурация](../../core/config/logging.py)
- [Исходный код](../../core/logging/) 