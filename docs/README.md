# 📚 Документация проекта

Центральная точка доступа к документации RAG Construction Materials API.

## 🗂 Структура документации

### 📋 Основная документация
- **[API Documentation](API_DOCUMENTATION.md)** - Полное описание API эндпоинтов
- **[API Endpoints Complete](API_ENDPOINTS_COMPLETE.md)** - Исчерпывающая документация всех 30+ эндпоинтов
- **[API Quick Reference](API_ENDPOINTS_QUICK_REFERENCE.md)** - Краткий справочник по эндпоинтам
- **[Configuration Guide](CONFIGURATION.md)** - Настройка и конфигурация системы
- **[Database Architecture](DATABASE_ARCHITECTURE.md)** - Архитектура баз данных

### 🔧 Техническая документация
- **[Material Object Structure](MATERIAL_OBJECT_STRUCTURE.md)** - Структура объектов материалов
- **[Batch Materials Loading](BATCH_MATERIALS_LOADING.md)** - Пакетная загрузка данных
- **[Database Rules](DATABASE_RULES.md)** - Правила работы с PostgreSQL
- **[SSH Tunnel Solution](SSH_TUNNEL_CONNECTION_RESET_SOLUTION.md)** - Решение проблем SSH туннелей

### 📖 Руководства и справочники
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Диагностика и устранение проблем
- **[Project History](HISTORY.md)** - История изменений проекта

### 🏗 Архитектурные решения (ADR)
- **[ADR Directory](adr/)** - Architecture Decision Records
  - `20250616-fastapi-asgi-middleware-fix.md` - Решение проблем ASGI middleware
  - `20250616-ssh-tunnel-service-integration.md` - Интеграция SSH туннелей
  - `20250617-ssh-tunnel-connection-reset-fix.md` - Исправление SSH туннелей

## 🚀 Быстрый старт

### Для разработчиков
1. **[Configuration Guide](CONFIGURATION.md)** - настройка окружения
2. **[API Documentation](API_DOCUMENTATION.md)** - изучение API
3. **[Troubleshooting Guide](TROUBLESHOOTING.md)** - решение проблем

### Для системных администраторов
1. **[Database Architecture](DATABASE_ARCHITECTURE.md)** - понимание архитектуры
2. **[Database Rules](DATABASE_RULES.md)** - правила работы с БД
3. **[SSH Tunnel Solution](SSH_TUNNEL_CONNECTION_RESET_SOLUTION.md)** - настройка туннелей

### Для пользователей API
1. **[API Documentation](API_DOCUMENTATION.md)** - описание эндпоинтов
2. **[Material Object Structure](MATERIAL_OBJECT_STRUCTURE.md)** - структура данных
3. **[Batch Materials Loading](BATCH_MATERIALS_LOADING.md)** - массовая загрузка

## 📊 Статистика документации

- **Общее количество документов**: 13
- **Основная документация**: 5 документов
- **Техническая документация**: 4 документа
- **Руководства**: 2 документа
- **ADR записи**: 3 документа

## 🔄 Обновления

**Последняя оптимизация**: 2025-01
- Удалены устаревшие документы (10 файлов)
- Сокращена детализация решенных проблем
- Интегрированы дублирующиеся разделы
- Улучшена навигация и структура

## 📚 Документация по системе

### 📝 Общие документы
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Документация по API
- [API_ENDPOINTS_COMPLETE.md](API_ENDPOINTS_COMPLETE.md) - Полная документация эндпоинтов
- [API_ENDPOINTS_QUICK_REFERENCE.md](API_ENDPOINTS_QUICK_REFERENCE.md) - Краткий справочник API
- [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) - Архитектура баз данных
- [CONFIGURATION.md](CONFIGURATION.md) - Конфигурация системы
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Устранение неполадок

### 📊 Система логирования
- [LOGGING_SYSTEM_GUIDE.md](LOGGING_SYSTEM_GUIDE.md) - Полное руководство по системе логирования
- [TROUBLESHOOTING_LOGGING.md](TROUBLESHOOTING_LOGGING.md) - Устранение неполадок логирования

### 🔍 Материалы и данные
- [MATERIAL_OBJECT_STRUCTURE.md](MATERIAL_OBJECT_STRUCTURE.md) - Структура объектов материалов
- [BATCH_MATERIALS_LOADING.md](BATCH_MATERIALS_LOADING.md) - Пакетная загрузка материалов

### 🔧 Решения проблем
- [SSH_TUNNEL_CONNECTION_RESET_SOLUTION.md](SSH_TUNNEL_CONNECTION_RESET_SOLUTION.md) - Решение проблемы сброса соединения SSH туннеля

### 📜 Архитектурные решения
- [adr/](adr/) - Архитектурные решения (ADR)

## 🚀 Новая система логирования

Система логирования была полностью модернизирована и теперь включает:

### 🏗️ Архитектура
- Модульная структура с четким разделением ответственности
- Интерфейс-ориентированный дизайн с соблюдением принципов SOLID
- Поддержка асинхронного логирования для высокой производительности

### 🔌 Интеграции
- Интеграция с FastAPI через middleware
- Интеграция с SQLAlchemy для логирования SQL запросов
- Интеграция с векторными БД (Qdrant, Weaviate, Pinecone)

### 🎛️ Конфигурация
- Гибкая конфигурация через переменные окружения
- Валидация конфигурации с подробными сообщениями об ошибках
- Программный доступ к настройкам через ConfigurationProvider

### 📊 Метрики и производительность
- Сбор метрик производительности
- Оптимизации для высоконагруженных сценариев
- Кеширование и пулинг для эффективного использования ресурсов

### 🔍 Трассировка запросов
- Поддержка Correlation ID для трассировки запросов
- Контекстные менеджеры для удобного использования
- Автоматическое распространение контекста

Подробное руководство по использованию системы логирования доступно в [LOGGING_SYSTEM_GUIDE.md](LOGGING_SYSTEM_GUIDE.md).

---

**Поддержка документации**: Документация регулярно обновляется в соответствии с изменениями в проекте.