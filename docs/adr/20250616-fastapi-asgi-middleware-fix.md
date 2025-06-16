# ADR-001: Переход с BaseHTTPMiddleware на чистый ASGI middleware для предотвращения зависаний

**Дата**: 2025-06-16  
**Статус**: ✅ Принято и реализовано  
**Автор**: AI Assistant  

## Context

FastAPI сервер испытывал критические проблемы со стабильностью:

1. **Зависания POST запросов**: Все POST/PUT/PATCH запросы зависали с timeout
2. **Проблемы middleware**: BaseHTTPMiddleware вызывал anyio.WouldBlock и asyncio.CancelledError
3. **Производительность**: Невозможность обработки параллельных запросов с body
4. **Ошибки ASGI**: "ASGI callable returned without completing response"

### Техническая проблема
- **BaseHTTPMiddleware** имеет известные ограничения производительности
- **Двойное чтение body** между SecurityMiddleware и LoggingMiddleware
- **Отсутствие greenlet** для SQLAlchemy async операций
- **Двойной процесс** при запуске с --reload

## Decision

Принято решение о полном переходе на **правильную архитектуру middleware**:

### 1. Замена BaseHTTPMiddleware на ASGI middleware
```python
# БЫЛО (проблематично)
class BodyCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Проблемы с anyio/asyncio

# СТАЛО (правильно)
class BodyCacheMiddleware:
    async def __call__(self, scope, receive, send):
        # Правильный ASGI паттерн
```

### 2. Использование "wrapping receive callable" паттерна
Согласно официальной документации Starlette для инспекции request body.

### 3. Добавление greenlet зависимости
```python
# requirements.txt
greenlet==3.0.1  # Для SQLAlchemy async
```

### 4. Оптимизация deployment
- Запуск без --reload для production (один процесс)
- Сохранение --reload для development

## Consequences

### ✅ Положительные

1. **Производительность**:
   - POST запросы: timeout → ~0.2s response time
   - Параллельные запросы работают корректно
   - Нет зависаний под нагрузкой

2. **Стабильность**:
   - Устранены anyio.WouldBlock ошибки
   - Нет "ASGI callable returned without completing response"
   - Корректная обработка request/response chain

3. **Функциональность**:
   - SecurityMiddleware валидация восстановлена
   - LoggingMiddleware с полным логированием body
   - Все защиты (XSS, SQL injection) работают

4. **Архитектура**:
   - Соответствие best practices Starlette
   - Правильный ASGI middleware pattern
   - Эффективное кеширование body

### ⚠️ Возможные негативные

1. **Сложность**:
   - ASGI middleware сложнее в разработке чем BaseHTTPMiddleware
   - Требует глубокое понимание ASGI protocol

2. **Maintenance**:
   - Более низкоуровневый код требует больше внимания
   - Необходимо следить за обновлениями Starlette/FastAPI

### 🔄 Нейтральные

1. **Миграция**:
   - Один раз переписать middleware
   - Обновить документацию
   - Добавить тесты для нового поведения

## Implementation Details

### Файлы изменены
- `core/middleware/body_cache.py` - полная переработка
- `main.py` - порядок middleware подтвержден
- `requirements.txt` - добавлен greenlet==3.0.1
- `README.md` - обновлены инструкции запуска

### Тестирование
```bash
# ✅ Подтверждено работает
curl -X POST "http://localhost:8000/api/v1/reference/units/" \
     -H "Content-Type: application/json" \
     -d '{"name":"test","description":"test"}'
# Status: 200, Time: ~0.2s
```

### Мониторинг
- Логи показывают "Body cached, size: X bytes"
- Нет ошибок в middleware chain
- Metrics показывают стабильные времена отклика

## References

- [Starlette Middleware Documentation](https://www.starlette.io/middleware/#inspecting-or-modifying-the-request)
- [FastAPI BaseHTTPMiddleware Issues](https://github.com/fastapi/fastapi/issues/5386)
- [ASGI Specification](https://asgi.readthedocs.io/)

## Review Date

**Следующий review**: 2025-09-16 (через 3 месяца)  
**Критерии успеха**: Стабильность POST запросов, отсутствие middleware ошибок в логах 