# План интеграции SSH туннеля в проект

## Цель
Интегрировать SSH туннель как **отдельный сервис** в проект с гибкой конфигурацией, чтобы автоматически управлять подключением к удаленной PostgreSQL базе данных при запуске сервера.

## Архитектура решения

### 1. Структура модулей
```
services/
├── __init__.py
├── ssh_tunnel_service.py      # Основной сервис SSH туннеля
└── tunnel/
    ├── __init__.py
    ├── ssh_tunnel.py          # Класс SSH туннеля
    ├── tunnel_manager.py      # Менеджер жизненного цикла туннеля
    ├── tunnel_config.py       # Конфигурация туннеля
    └── exceptions.py          # Исключения для туннеля

core/
├── config.py                  # Добавить настройки SSH туннеля
└── dependencies/
    └── tunnel.py              # Dependency injection для туннеля
```

### 2. Конфигурация в core/config.py
```python
# === SSH TUNNEL SERVICE CONFIGURATION ===
# Автоматический запуск SSH туннеля как сервиса
ENABLE_SSH_TUNNEL: bool = Field(default=False)
SSH_TUNNEL_LOCAL_PORT: int = Field(default=5435)
SSH_TUNNEL_REMOTE_HOST: str = Field(default="31.130.148.200")
SSH_TUNNEL_REMOTE_USER: str = Field(default="root")
SSH_TUNNEL_REMOTE_PORT: int = Field(default=5432)
SSH_TUNNEL_KEY_PATH: str = Field(default="~/.ssh/postgres_key")
SSH_TUNNEL_TIMEOUT: int = Field(default=30)
SSH_TUNNEL_RETRY_ATTEMPTS: int = Field(default=3)
SSH_TUNNEL_RETRY_DELAY: int = Field(default=5)
SSH_TUNNEL_HEARTBEAT_INTERVAL: int = Field(default=60)  # Проверка каждые 60 сек
SSH_TUNNEL_AUTO_RESTART: bool = Field(default=True)
```

### 3. Основные компоненты

#### 3.1 services/ssh_tunnel_service.py
- **Главный сервис** `SSHTunnelService` для управления туннелем
- Методы: `start_service()`, `stop_service()`, `restart_service()`, `get_status()`
- Автоматический запуск при старте приложения
- Мониторинг состояния в фоновом режиме
- Heartbeat проверки и автоматическое восстановление

#### 3.2 services/tunnel/ssh_tunnel.py
- Класс `SSHTunnel` для создания и управления SSH туннелем
- Методы: `connect()`, `disconnect()`, `is_active()`, `health_check()`
- Поддержка автоматического переподключения
- Логирование всех операций

#### 3.3 services/tunnel/tunnel_manager.py
- Класс `TunnelManager` для управления жизненным циклом
- Интеграция с сервисом
- Мониторинг состояния туннеля
- Переподключение при сбоях

#### 3.4 services/tunnel/tunnel_config.py
- Класс `TunnelConfig` для конфигурации
- Валидация параметров подключения
- Поддержка разных профилей (dev, staging, prod)
- Загрузка конфигурации из переменных окружения

#### 3.5 core/dependencies/tunnel.py
- Dependency injection для FastAPI
- Функция `get_tunnel_service()`
- Интеграция с lifecycle приложения

## Этапы реализации

### Этап 1: Создание сервисной архитектуры
1. Создать `services/ssh_tunnel_service.py` - главный сервис
2. Создать директорию `services/tunnel/` для вспомогательных классов
3. Добавить настройки SSH туннеля в `core/config.py`
4. Создать базовый класс `SSHTunnel`

### Этап 2: Сервис управления туннелем
1. Реализовать класс `SSHTunnelService` как основной сервис
2. Добавить фоновые задачи для мониторинга
3. Реализовать автоматический запуск/остановку туннеля
4. Добавить heartbeat проверки состояния

### Этап 3: Интеграция с FastAPI Lifespan
1. Создать startup event для запуска сервиса туннеля
2. Создать shutdown event для корректной остановки
3. Интегрировать с FastAPI lifecycle через `@asynccontextmanager`
4. Обеспечить правильную последовательность инициализации

### Этап 4: Менеджер жизненного цикла
1. Создать класс `TunnelManager` для работы с сервисом
2. Реализовать мониторинг состояния
3. Автоматическое переподключение при сбоях
4. Логирование всех операций сервиса

### Этап 5: Конфигурация и валидация
1. Создать класс `TunnelConfig`
2. Добавить валидацию параметров SSH
3. Поддержка множественных профилей
4. Интеграция с основной конфигурацией проекта

### Этап 6: Обработка ошибок и мониторинг
1. Создать специализированные исключения
2. Добавить детальное логирование сервиса
3. Реализовать health checks
4. Метрики производительности туннеля

### Этап 7: Dependency Injection и API
1. Создать dependency provider для FastAPI
2. Добавить эндпоинты для управления туннелем (статус, перезапуск)
3. Интегрировать с существующими dependencies
4. Health check эндпоинт для туннеля

### Этап 8: Тестирование и документация
1. Unit тесты для сервиса и всех компонентов
2. Integration тесты с реальным SSH
3. Обновить документацию проекта
4. Создать примеры использования

## Особенности реализации

### Сервисная архитектура
- **Автономный сервис**: SSH туннель работает как независимый сервис
- **Автоматический запуск**: Сервис запускается при старте FastAPI приложения
- **Фоновый мониторинг**: Постоянная проверка состояния туннеля
- **Graceful shutdown**: Корректная остановка при завершении приложения

### Конфигурационные профили
```python
# Разработка с SSH туннелем
ENABLE_SSH_TUNNEL=true
SSH_TUNNEL_REMOTE_HOST=31.130.148.200
SSH_TUNNEL_AUTO_RESTART=true

# Продакшн (прямое подключение)
ENABLE_SSH_TUNNEL=false
POSTGRESQL_HOST=production-db.example.com
```

### Мониторинг и управление
- Детальное логирование всех операций сервиса
- Health checks для проверки состояния туннеля
- API эндпоинты для управления туннелем
- Метрики для мониторинга производительности
- Alerts при сбоях подключения

### Fallback стратегия
- При недоступности SSH туннеля - попытка прямого подключения
- Переключение на mock базу данных в крайнем случае
- Уведомления об изменении режима подключения

## Конфигурация в env файлах

### env.example обновления
```bash
# === SSH TUNNEL SERVICE CONFIGURATION ===
# Автоматический запуск SSH туннеля как сервиса
ENABLE_SSH_TUNNEL=true
SSH_TUNNEL_LOCAL_PORT=5435
SSH_TUNNEL_REMOTE_HOST=31.130.148.200
SSH_TUNNEL_REMOTE_USER=root
SSH_TUNNEL_REMOTE_PORT=5432
SSH_TUNNEL_KEY_PATH=~/.ssh/postgres_key
SSH_TUNNEL_TIMEOUT=30
SSH_TUNNEL_RETRY_ATTEMPTS=3
SSH_TUNNEL_RETRY_DELAY=5
SSH_TUNNEL_HEARTBEAT_INTERVAL=60
SSH_TUNNEL_AUTO_RESTART=true

# PostgreSQL настройки для туннеля
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5435  # Локальный порт туннеля
```

## Интеграция с FastAPI

### main.py обновления
```python
from contextlib import asynccontextmanager
from services.ssh_tunnel_service import SSHTunnelService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - запуск сервиса туннеля
    tunnel_service = None
    if settings.ENABLE_SSH_TUNNEL:
        tunnel_service = SSHTunnelService()
        await tunnel_service.start_service()
        app.state.tunnel_service = tunnel_service
    
    yield
    
    # Shutdown - остановка сервиса туннеля
    if settings.ENABLE_SSH_TUNNEL and tunnel_service:
        await tunnel_service.stop_service()

app = FastAPI(lifespan=lifespan)
```

### Добавление API эндпоинтов для управления
```python
# api/routes/tunnel.py
@router.get("/tunnel/status")
async def get_tunnel_status():
    """Получить статус SSH туннеля"""
    
@router.post("/tunnel/restart")
async def restart_tunnel():
    """Перезапустить SSH туннель"""
```

## Преимущества сервисного подхода

1. **Автономность**: Туннель работает как независимый сервис
2. **Управляемость**: API для управления состоянием туннеля
3. **Мониторинг**: Постоянный контроль состояния
4. **Надежность**: Автоматическое восстановление при сбоях
5. **Интеграция**: Seamless интеграция с FastAPI lifecycle
6. **Конфигурируемость**: Все параметры настраиваются через переменные окружения
7. **Масштабируемость**: Легко расширить для поддержки множественных туннелей

## Результат

После реализации:
- SSH туннель запускается как автономный сервис при старте сервера
- Не нужно помнить о запуске туннеля вручную
- Полное управление через API эндпоинты
- Мониторинг состояния в реальном времени
- Автоматическое восстановление при сбоях
- Конфигурация легко меняется через .env файлы
- Полная интеграция с остальными компонентами проекта

## Файлы для создания/изменения

### Новые файлы:
1. `services/ssh_tunnel_service.py` - **Основной сервис**
2. `services/tunnel/__init__.py`
3. `services/tunnel/ssh_tunnel.py`
4. `services/tunnel/tunnel_manager.py`
5. `services/tunnel/tunnel_config.py`
6. `services/tunnel/exceptions.py`
7. `api/routes/tunnel.py` - API для управления туннелем
8. `tests/services/test_ssh_tunnel_service.py`

### Обновляемые файлы:
1. `core/config.py` - настройки SSH туннеля
2. `core/dependencies/tunnel.py` - dependency injection
3. `main.py` - интеграция с FastAPI lifecycle
4. `env.example` - конфигурация туннеля
5. Тесты в `tests/tunnel/` 