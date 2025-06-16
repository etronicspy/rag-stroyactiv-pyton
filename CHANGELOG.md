# Changelog

Все важные изменения в этом проекте будут задокументированы в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
и этот проект следует [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-06-16

### Fixed
- **КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ**: Полностью решена проблема зависания FastAPI при POST запросах
- **Middleware**: Переписан BodyCacheMiddleware с BaseHTTPMiddleware на правильный ASGI middleware согласно документации Starlette
- **Dependencies**: Добавлен greenlet==3.0.1 для корректной работы SQLAlchemy async операций
- **Performance**: Устранено зависание при двойном чтении request.body() в middleware chain
- **Stability**: Исправлена ошибка "ASGI callable returned without completing response"

### Changed
- **BodyCacheMiddleware**: Использует правильный паттерн "wrapping receive callable" вместо BaseHTTPMiddleware
- **Server startup**: Рекомендуется запуск без `--reload` флага для избежания проблем с двумя процессами
- **Middleware order**: Подтвержден правильный LIFO порядок добавления middleware в main.py

### Performance
- **Response time**: POST запросы теперь выполняются за ~0.2s вместо timeout
- **No more hanging**: Устранены зависания при параллельных POST запросах
- **Memory efficiency**: Оптимизировано использование памяти при кешировании request body

## [1.2.0] - 2025-06-15

### Added
- Qdrant-Only режим для упрощенной разработки
- Mock адаптеры для PostgreSQL и Redis
- Comprehensive health checks для всех БД
- Advanced search с фильтрацией по категориям и единицам измерения

### Changed
- Переход на мульти-БД архитектуру с repository pattern
- Унификация векторных операций через абстрактные интерфейсы

## [1.1.0] - 2025-06-10

### Added
- Reference API для управления категориями и единицами измерения
- Batch operations для массовой загрузки материалов
- CSV/Excel импорт прайс-листов

### Fixed
- Улучшена обработка ошибок валидации
- Исправлена кодировка при работе с русскими текстами

## [1.0.0] - 2025-06-01

### Added
- Базовый Materials API
- Векторный поиск через Qdrant
- OpenAI эмбеддинги для семантического поиска
- Basic middleware для безопасности и логирования
- Health check endpoints 