#!/usr/bin/env python3
"""
📚 Базовый пример использования системы логирования

Этот пример демонстрирует основные возможности модульной системы логирования:
- Создание и использование логгера
- Различные уровни логирования
- Использование correlation ID для трассировки
- Структурированные данные в логах
- Логирование исключений
"""

import sys
import os
import time

# Добавляем путь к корню проекта для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core.logging import (
    get_logger,
    CorrelationContext,
    get_correlation_id,
    set_correlation_id
)


def basic_logging_example():
    """Демонстрация базового логирования"""
    print("🚀 БАЗОВОЕ ЛОГИРОВАНИЕ")
    print("=" * 50)
    
    # Создание логгера
    logger = get_logger("basic_example")
    
    # Различные уровни логирования
    logger.debug("Это отладочное сообщение")
    logger.info("Это информационное сообщение")
    logger.warning("Это предупреждение")
    logger.error("Это ошибка")
    logger.critical("Это критическая ошибка")
    
    # Логирование со структурированными данными
    logger.info("Пользователь выполнил действие", extra={
        "user_id": 12345,
        "action": "login",
        "timestamp": time.time(),
        "ip_address": "192.168.1.100"
    })
    
    print("✅ Базовое логирование выполнено\n")


def correlation_id_example():
    """Демонстрация использования correlation ID"""
    print("🔗 CORRELATION ID")
    print("=" * 50)
    
    logger = get_logger("correlation_example")
    
    # Автоматическое создание correlation ID
    with CorrelationContext.with_correlation_id():
        current_id = get_correlation_id()
        logger.info(f"Начало операции с correlation ID: {current_id}")
        
        # Имитация обработки запроса
        logger.info("Обработка данных пользователя", extra={
            "step": 1,
            "operation": "validate_input"
        })
        
        logger.info("Запрос к базе данных", extra={
            "step": 2,
            "operation": "fetch_user_data"
        })
        
        logger.info("Формирование ответа", extra={
            "step": 3,
            "operation": "build_response"
        })
        
        logger.info(f"Операция завершена с correlation ID: {current_id}")
    
    # Ручная установка correlation ID
    set_correlation_id("custom-request-12345")
    logger.info("Лог с пользовательским correlation ID")
    
    print("✅ Correlation ID демонстрация выполнена\n")


def exception_logging_example():
    """Демонстрация логирования исключений"""
    print("🚨 ЛОГИРОВАНИЕ ИСКЛЮЧЕНИЙ")
    print("=" * 50)
    
    logger = get_logger("exception_example")
    
    # Пример 1: Перехват и логирование исключения
    try:
        # Имитация ошибки
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.exception("Ошибка деления на ноль", extra={
            "operation": "division",
            "dividend": 10,
            "divisor": 0,
            "error_type": type(e).__name__
        })
    
    # Пример 2: Логирование с дополнительным контекстом
    try:
        user_data = {"name": "John", "age": "invalid_age"}
        age = int(user_data["age"])
    except ValueError as e:
        logger.error("Ошибка преобразования данных пользователя", extra={
            "error": str(e),
            "user_data": user_data,
            "field": "age",
            "expected_type": "int",
            "actual_value": user_data["age"]
        })
    
    # Пример 3: Критическая ошибка с дополнительными деталями
    try:
        # Имитация критической ошибки системы
        raise RuntimeError("Критическая ошибка системы: недостаточно памяти")
    except RuntimeError as e:
        logger.critical("Критическая ошибка системы", extra={
            "error_message": str(e),
            "system_state": "degraded",
            "recovery_action": "restart_required",
            "alert_level": "high"
        })
    
    print("✅ Логирование исключений выполнено\n")


def structured_data_example():
    """Демонстрация работы со структурированными данными"""
    print("📊 СТРУКТУРИРОВАННЫЕ ДАННЫЕ")
    print("=" * 50)
    
    logger = get_logger("structured_example")
    
    # Пример 1: Логирование бизнес-событий
    with CorrelationContext.with_correlation_id():
        logger.info("Создание нового заказа", extra={
            "event_type": "order_created",
            "order_id": "ORD-2024-001",
            "customer_id": 12345,
            "total_amount": 299.99,
            "currency": "USD",
            "items_count": 3,
            "payment_method": "credit_card",
            "shipping_address": {
                "city": "Moscow",
                "country": "Russia",
                "postal_code": "101000"
            }
        })
        
        # Имитация обработки заказа
        time.sleep(0.1)  # Небольшая задержка для реалистичности
        
        logger.info("Обработка платежа", extra={
            "event_type": "payment_processing",
            "order_id": "ORD-2024-001",
            "payment_status": "pending",
            "payment_gateway": "stripe",
            "amount": 299.99
        })
        
        # Успешная обработка
        logger.info("Заказ успешно обработан", extra={
            "event_type": "order_completed",
            "order_id": "ORD-2024-001",
            "processing_time_ms": 150,
            "status": "completed",
            "next_step": "shipping"
        })
    
    # Пример 2: Логирование производительности
    start_time = time.time()
    
    # Имитация долгой операции
    time.sleep(0.2)
    
    duration = (time.time() - start_time) * 1000  # в миллисекундах
    
    logger.info("Операция завершена", extra={
        "event_type": "performance_metric",
        "operation": "data_processing",
        "duration_ms": round(duration, 2),
        "records_processed": 1000,
        "success_rate": 99.5,
        "performance_grade": "excellent" if duration < 100 else "good"
    })
    
    print("✅ Структурированные данные выполнены\n")


def multiple_logger_example():
    """Демонстрация использования нескольких логгеров"""
    print("🔧 НЕСКОЛЬКО ЛОГГЕРОВ")
    print("=" * 50)
    
    # Создание логгеров для разных компонентов
    auth_logger = get_logger("auth_service")
    db_logger = get_logger("database")
    api_logger = get_logger("api_handler")
    
    with CorrelationContext.with_correlation_id():
        # Логирование в различных компонентах
        api_logger.info("Получен HTTP запрос", extra={
            "method": "POST",
            "endpoint": "/api/v1/login",
            "client_ip": "192.168.1.100"
        })
        
        auth_logger.info("Начало аутентификации", extra={
            "username": "john_doe",
            "auth_method": "password"
        })
        
        db_logger.info("Запрос к базе данных", extra={
            "query_type": "SELECT",
            "table": "users",
            "duration_ms": 25.5
        })
        
        auth_logger.info("Аутентификация успешна", extra={
            "user_id": 12345,
            "role": "user",
            "session_id": "sess_abc123"
        })
        
        api_logger.info("HTTP ответ отправлен", extra={
            "status_code": 200,
            "response_time_ms": 150,
            "content_type": "application/json"
        })
    
    print("✅ Несколько логгеров выполнено\n")


def configuration_example():
    """Демонстрация работы с конфигурацией"""
    print("⚙️ КОНФИГУРАЦИЯ")
    print("=" * 50)
    
    from core.config.logging import LoggingConfig
    
    # Получение текущей конфигурации
    config = LoggingConfig()
    
    logger = get_logger("config_example")
    
    logger.info("Текущая конфигурация логирования", extra={
        "log_level": config.LOG_LEVEL,
        "structured_logging": config.ENABLE_STRUCTURED_LOGGING,
        "correlation_id": config.LOG_CORRELATION_ID,
        "database_operations": config.LOG_DATABASE_OPERATIONS,
        "performance_metrics": config.LOG_PERFORMANCE_METRICS,
        "colors_enabled": config.LOG_COLORS
    })
    
    # Демонстрация различных настроек
    if config.LOG_CORRELATION_ID:
        logger.info("✅ Correlation ID включен")
    else:
        logger.info("❌ Correlation ID отключен")
    
    if config.ENABLE_STRUCTURED_LOGGING:
        logger.info("✅ Структурированное логирование включено (JSON формат)")
    else:
        logger.info("✅ Обычное логирование включено (текстовый формат)")
    
    print("✅ Конфигурация выполнена\n")


def main():
    """Главная функция - запуск всех примеров"""
    print("🎯 ПРИМЕРЫ БАЗОВОГО ИСПОЛЬЗОВАНИЯ СИСТЕМЫ ЛОГИРОВАНИЯ")
    print("=" * 70)
    print("Этот пример демонстрирует основные возможности модульной системы логирования\n")
    
    # Проверка переменных окружения
    import os
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    print(f"📊 Текущий уровень логирования: {log_level}")
    print(f"📊 Structured logging: {os.environ.get('ENABLE_STRUCTURED_LOGGING', 'false')}")
    print(f"📊 Correlation ID: {os.environ.get('LOG_CORRELATION_ID', 'false')}")
    print()
    
    # Запуск всех примеров
    try:
        basic_logging_example()
        correlation_id_example()
        exception_logging_example()
        structured_data_example()
        multiple_logger_example()
        configuration_example()
        
        print("🎉 ВСЕ ПРИМЕРЫ УСПЕШНО ВЫПОЛНЕНЫ!")
        print("=" * 70)
        print("Следующие шаги:")
        print("1. Изучите advanced_features.py для продвинутых возможностей")
        print("2. Посмотрите api_integration.py для интеграции с FastAPI")
        print("3. Прочитайте полное руководство в docs/LOGGING_SYSTEM_GUIDE.md")
        
    except Exception as e:
        error_logger = get_logger("example_error")
        error_logger.exception("Ошибка выполнения примера", extra={
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        print(f"❌ Ошибка выполнения примера: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 