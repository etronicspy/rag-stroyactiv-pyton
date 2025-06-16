# План интеграции SSH туннеля в проект

## Цель
Интегрировать SSH туннель в проект как отдельный модуль с гибкой конфигурацией, чтобы автоматически управлять подключением к удаленной PostgreSQL базе данных.

## Архитектура решения

### 1. Структура модулей
```
core/
├── tunnel/
│   ├── __init__.py
│   ├── ssh_tunnel.py          # Основной класс SSH туннеля
│   ├── tunnel_manager.py      # Менеджер жизненного цикла туннеля
│   ├── tunnel_config.py       # Конфигурация туннеля
│   └── exceptions.py          # Исключения для туннеля
├── config.py                  # Добавить настройки SSH туннеля
└── dependencies/
    └── tunnel.py              # Dependency injection для туннеля
```

### 2. Конфигурация в core/config.py
```python
# === SSH TUNNEL CONFIGURATION ===
# Автоматический запуск SSH туннеля
ENABLE_SSH_TUNNEL: bool = Field(default=False)
SSH_TUNNEL_LOCAL_PORT: int = Field(default=5435)
SSH_TUNNEL_REMOTE_HOST: str = Field(default="31.130.148.200")
SSH_TUNNEL_REMOTE_USER: str = Field(default="root")
SSH_TUNNEL_REMOTE_PORT: int = Field(default=5432)
SSH_TUNNEL_KEY_PATH: str = Field(default="~/.ssh/postgres_key")
SSH_TUNNEL_TIMEOUT: int = Field(default=30)
SSH_TUNNEL_RETRY_ATTEMPTS: int = Field(default=3)
SSH_TUNNEL_RETRY_DELAY: int = Field(default=5)
```

### 3. Основные компоненты

#### 3.1 core/tunnel/ssh_tunnel.py
- Класс `SSHTunnel` для создания и управления SSH туннелем
- Методы: `connect()`, `disconnect()`, `is_active()`, `health_check()`
- Поддержка автоматического переподключения
- Логирование всех операций

#### 3.2 core/tunnel/tunnel_manager.py
- Класс `TunnelManager` для управления жизненным циклом
- Автоматический запуск при старте приложения
- Автоматическое закрытие при завершении приложения
- Мониторинг состояния туннеля
- Переподключение при сбоях

#### 3.3 core/tunnel/tunnel_config.py
- Класс `TunnelConfig` для конфигурации
- Валидация параметров подключения
- Поддержка разных профилей (dev, staging, prod)
- Загрузка конфигурации из переменных окружения

#### 3.4 core/dependencies/tunnel.py
- Dependency injection для FastAPI
- Функция `get_tunnel_manager()`
- Интеграция с lifecycle приложения

## Этапы реализации

### Этап 1: Базовая структура модуля
1. Создать директорию `core/tunnel/`
2. Создать базовые файлы модуля
3. Добавить настройки SSH туннеля в `core/config.py`
4. Создать базовый класс `SSHTunnel`

### Этап 2: Менеджер жизненного цикла
1. Создать класс `TunnelManager`
2. Интегрировать с FastAPI lifecycle events
3. Добавить автоматический запуск/остановку туннеля
4. Реализовать мониторинг состояния

### Этап 3: Конфигурация и валидация
1. Создать класс `TunnelConfig`
2. Добавить валидацию параметров SSH
3. Поддержка множественных профилей
4. Интеграция с основной конфигурацией проекта

### Этап 4: Обработка ошибок и мониторинг
1. Создать специализированные исключения
2. Добавить детальное логирование
3. Реализовать health checks
4. Автоматическое переподключение при сбоях

### Этап 5: Dependency Injection
1. Создать dependency provider для FastAPI
2. Интегрировать с существующими dependencies
3. Обеспечить правильный порядок инициализации

### Этап 6: Тестирование и документация
1. Unit тесты для всех компонентов
2. Integration тесты с реальным SSH
3. Обновить документацию проекта
4. Создать примеры использования

## Особенности реализации

### Автоматический запуск
- Туннель запускается автоматически при `ENABLE_SSH_TUNNEL=true`
- Проверка доступности SSH ключа при старте
- Graceful shutdown при завершении приложения

### Конфигурационные профили
```python
# Разработка
ENABLE_SSH_TUNNEL=true
SSH_TUNNEL_REMOTE_HOST=31.130.148.200

# Продакшн (прямое подключение)
ENABLE_SSH_TUNNEL=false
POSTGRESQL_HOST=production-db.example.com
```

### Мониторинг и логирование
- Детальное логирование всех операций туннеля
- Health checks для проверки состояния
- Метрики для мониторинга производительности
- Alerts при сбоях подключения

### Fallback стратегия
- При недоступности SSH туннеля - попытка прямого подключения
- Переключение на mock базу данных в крайнем случае
- Уведомления об изменении режима подключения

## Конфигурация в env файлах

### env.example обновления
```bash
# === SSH TUNNEL CONFIGURATION ===
# Автоматический запуск SSH туннеля для PostgreSQL
ENABLE_SSH_TUNNEL=true
SSH_TUNNEL_LOCAL_PORT=5435
SSH_TUNNEL_REMOTE_HOST=31.130.148.200
SSH_TUNNEL_REMOTE_USER=root
SSH_TUNNEL_REMOTE_PORT=5432
SSH_TUNNEL_KEY_PATH=~/.ssh/postgres_key
SSH_TUNNEL_TIMEOUT=30
SSH_TUNNEL_RETRY_ATTEMPTS=3
SSH_TUNNEL_RETRY_DELAY=5

# PostgreSQL настройки для туннеля
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5435  # Локальный порт туннеля
```

## Интеграция с FastAPI

### main.py обновления
```python
from core.tunnel.tunnel_manager import TunnelManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    tunnel_manager = TunnelManager()
    if settings.ENABLE_SSH_TUNNEL:
        await tunnel_manager.start()
    
    yield
    
    # Shutdown
    if settings.ENABLE_SSH_TUNNEL:
        await tunnel_manager.stop()
```

## Преимущества решения

1. **Прозрачность**: Туннель работает автоматически, не требуя ручного вмешательства
2. **Гибкость**: Легко переключаться между режимами подключения
3. **Надежность**: Автоматическое переподключение при сбоях
4. **Мониторинг**: Полное логирование и health checks
5. **Конфигурируемость**: Все параметры настраиваются через переменные окружения

## Результат

После реализации:
- SSH туннель запускается автоматически при старте приложения
- Не нужно помнить о запуске туннеля вручную
- Конфигурация легко меняется через .env файлы
- Полная интеграция с остальными компонентами проекта
- Автоматическое управление жизненным циклом туннеля

## Файлы для создания/изменения

1. `core/tunnel/__init__.py`
2. `core/tunnel/ssh_tunnel.py`
3. `core/tunnel/tunnel_manager.py`
4. `core/tunnel/tunnel_config.py`
5. `core/tunnel/exceptions.py`
6. `core/dependencies/tunnel.py`
7. `core/config.py` (обновления)
8. `main.py` (обновления)
9. `env.example` (обновления)
10. Тесты в `tests/tunnel/` 