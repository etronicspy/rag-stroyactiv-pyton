"""
Unified request logging middleware using core monitoring system.
Eliminates code duplication by leveraging core/monitoring/logger.py components.

ARCHITECTURE: Integrated with core.monitoring.logger for consistency
"""

import time
import uuid
import sys
import logging
from typing import Optional, Dict, Any, List, Callable, Union
import traceback
import os
from pathlib import Path

from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

from core.config import get_settings, Settings
from core.monitoring.unified_manager import get_unified_logging_manager
from core.monitoring.context import CorrelationContext, set_correlation_id
from core.monitoring.performance_optimizer import get_performance_optimizer
from core.monitoring.logger import get_logger
from core.logging.context.correlation import get_correlation_id
from core.logging.managers.unified import UnifiedLoggingManager


def safe_log(logger, level: str, message: str, extra: Optional[Dict[str, Any]] = None, correlation_id: Optional[str] = None):
    """
    🛡️ БЕЗОПАСНОЕ ЛОГИРОВАНИЕ с fallback в stderr.
    
    Гарантирует, что сообщение будет залогировано даже при сбое основного логгера.
    
    Args:
        logger: Основной логгер
        level: Уровень логирования (INFO, ERROR, etc.)
        message: Сообщение для логирования
        extra: Дополнительные данные
        correlation_id: ID корреляции
    """
    try:
        # Попытка основного логирования
        if hasattr(logger, level.lower()):
            log_method = getattr(logger, level.lower())
            if extra:
                log_method(message, extra=extra)
            else:
                log_method(message)
        else:
            logger.log(getattr(logging, level.upper()), message, extra=extra or {})
    except Exception as primary_error:
        # 🚨 КРИТИЧЕСКИЙ FALLBACK: Вывод в stderr
        try:
            import json
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            fallback_data = {
                "timestamp": timestamp,
                "level": level,
                "message": message,
                "correlation_id": correlation_id or "unknown",
                "extra": extra or {},
                "fallback_reason": f"Primary logger failed: {str(primary_error)}"
            }
            # Структурированный вывод в stderr
            sys.stderr.write(f"[FALLBACK-LOG] {json.dumps(fallback_data, ensure_ascii=False)}\n")
            sys.stderr.flush()
        except Exception as fallback_error:
            # 🚨 ПОСЛЕДНЯЯ ЛИНИЯ ОБОРОНЫ: Простой текст в stderr
            try:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                fallback_message = f"[FALLBACK-LOG] {timestamp} [{level}] {message} (correlation_id: {correlation_id or 'unknown'})\n"
                sys.stderr.write(fallback_message)
                sys.stderr.flush()
            except Exception:
                # Если даже stderr недоступен - ничего не можем сделать
                pass


def should_exclude_path(path: str) -> bool:
    """
    🛡️ СУПЕР-БЕЗОПАСНАЯ фильтрация путей с множественными fallback механизмами.
    
    Поддерживает:
    - Exact matches: /health
    - Prefix patterns: /docs*  
    - Suffix patterns: */health
    - Wildcard patterns: /api/*/health/*
    - Path segments: health (matches any path containing 'health')
    - Regex patterns: ^/api/v\d+/health$
    
    ГАРАНТИЯ: Функция НИКОГДА не падает и не ломает логирование.
    """
    import sys
    
    # 🚨 ВХОДНАЯ ВАЛИДАЦИЯ: Проверяем корректность пути
    try:
        if not path or not isinstance(path, str):
            sys.stderr.write(f"[PATH-FILTER-WARNING] Invalid path type: {type(path)}. Allowing logging.\n")
            sys.stderr.flush()
            return False
        
        # Нормализуем путь для безопасности
        normalized_path = path.strip()
        if not normalized_path:
            sys.stderr.write(f"[PATH-FILTER-WARNING] Empty path after normalization. Allowing logging.\n")
            sys.stderr.flush()
            return False
            
    except Exception as validation_error:
        sys.stderr.write(f"[PATH-FILTER-CRITICAL] Path validation failed: {validation_error}. Allowing logging.\n")
        sys.stderr.flush()
        return False
    
    # 🔧 ПОЛУЧЕНИЕ НАСТРОЕК: С множественными fallback
    try:
        from core.config import get_settings
        settings = get_settings()
    except Exception as settings_error:
        sys.stderr.write(f"[PATH-FILTER-ERROR] Settings access failed: {settings_error}. Allowing logging.\n")
        sys.stderr.flush()
        return False
    
    try:
        exclude_paths = getattr(settings, 'LOG_EXCLUDE_PATHS', [])
        
        # Валидируем exclude_paths
        if not isinstance(exclude_paths, (list, tuple)):
            sys.stderr.write(f"[PATH-FILTER-WARNING] Invalid exclude_paths type: {type(exclude_paths)}. Using empty list.\n")
            sys.stderr.flush()
            exclude_paths = []
            
    except Exception as exclude_error:
        sys.stderr.write(f"[PATH-FILTER-ERROR] Exclude paths extraction failed: {exclude_error}. Using empty list.\n")
        sys.stderr.flush()
        exclude_paths = []
    
    # 🔍 ПРОВЕРКА ПАТТЕРНОВ: С индивидуальной защитой каждого типа
    for i, exclude_pattern in enumerate(exclude_paths):
        try:
            # Валидируем паттерн
            if not exclude_pattern or not isinstance(exclude_pattern, str):
                sys.stderr.write(f"[PATH-FILTER-WARNING] Invalid pattern #{i}: {exclude_pattern}. Skipping.\n")
                sys.stderr.flush()
                continue
            
            exclude_pattern = exclude_pattern.strip()
            if not exclude_pattern:
                continue
            
            # 1. 🎯 EXACT MATCH: Самый быстрый и безопасный
            try:
                if normalized_path == exclude_pattern:
                    return True
            except Exception as exact_error:
                sys.stderr.write(f"[PATH-FILTER-WARNING] Exact match failed for pattern '{exclude_pattern}': {exact_error}\n")
                sys.stderr.flush()
            
            # 2. 🔍 PREFIX MATCH: С защитой от некорректных паттернов
            try:
                if exclude_pattern.endswith('*'):
                    prefix = exclude_pattern[:-1]
                    if prefix and normalized_path.startswith(prefix):
                        return True
                elif normalized_path.startswith(exclude_pattern):
                    return True
            except Exception as prefix_error:
                sys.stderr.write(f"[PATH-FILTER-WARNING] Prefix match failed for pattern '{exclude_pattern}': {prefix_error}\n")
                sys.stderr.flush()
            
            # 3. 🔍 SUFFIX MATCH: С защитой от некорректных паттернов
            try:
                if exclude_pattern.startswith('*'):
                    suffix = exclude_pattern[1:]
                    if suffix and normalized_path.endswith(suffix):
                        return True
            except Exception as suffix_error:
                sys.stderr.write(f"[PATH-FILTER-WARNING] Suffix match failed for pattern '{exclude_pattern}': {suffix_error}\n")
                sys.stderr.flush()
            
            # 4. 🌟 WILDCARD PATTERN: С защитой от regex ошибок
            try:
                if '*' in exclude_pattern:
                    import fnmatch
                    if fnmatch.fnmatch(normalized_path, exclude_pattern):
                        return True
            except Exception as wildcard_error:
                sys.stderr.write(f"[PATH-FILTER-WARNING] Wildcard match failed for pattern '{exclude_pattern}': {wildcard_error}\n")
                sys.stderr.flush()
            
            # 5. 🔍 SEGMENT MATCH: Проверка вхождения подстроки
            try:
                if '/' not in exclude_pattern and exclude_pattern in normalized_path:
                    return True
            except Exception as segment_error:
                sys.stderr.write(f"[PATH-FILTER-WARNING] Segment match failed for pattern '{exclude_pattern}': {segment_error}\n")
                sys.stderr.flush()
            
            # 6. 🚀 REGEX PATTERN: Дополнительная поддержка для сложных случаев
            try:
                if exclude_pattern.startswith('^') or exclude_pattern.endswith('$'):
                    import re
                    if re.match(exclude_pattern, normalized_path):
                        return True
            except Exception as regex_error:
                sys.stderr.write(f"[PATH-FILTER-WARNING] Regex match failed for pattern '{exclude_pattern}': {regex_error}\n")
                sys.stderr.flush()
            
        except Exception as pattern_error:
            # 🛡️ БЕЗОПАСНОСТЬ: Некорректный паттерн не должен ломать логирование
            sys.stderr.write(f"[PATH-FILTER-ERROR] Pattern processing failed for '{exclude_pattern}': {pattern_error}\n")
            sys.stderr.flush()
            continue
    
    # 🎯 DEFAULT: Если ничего не исключено - разрешаем логирование
    return False


class InterceptHandler(logging.Handler):
    """
    Перехватчик для uvicorn логов - перенаправляет их в нашу систему логирования
    """
    def emit(self, record):
        try:
            # Получаем соответствующий уровень Loguru/нашей системы
            level = record.levelname
            
            # Находим правильного вызывающего
            frame = sys._getframe(6)
            depth = 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            # Логируем через нашу систему
            safe_log(level, record.getMessage(), 
                    logger_name=record.name, 
                    extra={'depth': depth})
                    
        except Exception as e:
            # Fallback - логируем в stderr
            print(f"[INTERCEPT-ERROR] Failed to intercept log: {e}", file=sys.stderr)
            print(f"[INTERCEPT-FALLBACK] {record.levelname}: {record.getMessage()}", file=sys.stderr)


class LoggingMiddleware:
    """Enhanced ASGI logging middleware with performance optimization."""
    
    def __init__(self, app: ASGIApp):
        """Initialize logging middleware with FastAPI-compatible signature."""
        self.app = app
        self.settings = get_settings()
        
        # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Принудительная инициализация логирования
        # Гарантируем, что логирование настроено в процессе uvicorn
        self._ensure_logging_initialized()
        
        # 🚀 ЭТАП 4.4: Performance Optimization Integration
        self.enable_performance_optimization = getattr(self.settings, 'ENABLE_PERFORMANCE_OPTIMIZATION', True)
        if self.enable_performance_optimization:
            self.performance_optimizer = get_performance_optimizer()
        
        # Use optimized manager
        self.unified_manager = get_unified_logging_manager()
        self.request_logger = self.unified_manager.get_request_logger()
        
        # Get optimized logger
        if self.enable_performance_optimization:
            self.app_logger = self.unified_manager.get_optimized_logger("middleware.asgi")
        else:
            self.app_logger = get_logger("middleware.asgi")
        
        # Performance settings
        self.enable_batching = getattr(self.settings, 'ENABLE_LOG_BATCHING', True)
        self.log_requests = getattr(self.settings, 'ENABLE_REQUEST_LOGGING', True)
        self.log_request_body = getattr(self.settings, 'LOG_REQUEST_BODY', False)
        self.log_request_headers = getattr(self.settings, 'LOG_REQUEST_HEADERS', True)
        self.log_performance_metrics = getattr(self.settings, 'LOG_PERFORMANCE_METRICS', True)
        
        # 🛡️ БЕЗОПАСНАЯ ИНИЦИАЛИЗАЦИЯ: Даже если основной логгер падает
        try:
            self.app_logger.info(
                f"✅ LoggingMiddleware initialized with performance optimization: "
                f"optimization={self.enable_performance_optimization}, "
                f"batching={self.enable_batching}"
            )
        except Exception as init_error:
            safe_log(None, "ERROR", f"LoggingMiddleware initialization logging failed: {init_error}", 
                    correlation_id="init-error")
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # RAW DEBUG: This should always print if middleware is hit
        print(f"RAW DEBUG: LoggingMiddleware.__call__ entered for path: {scope.get('path', 'N/A')}")

        if scope["type"] != "http":
            print(f"RAW DEBUG: Not an HTTP request, skipping. Type: {scope['type']}")
            await self.app(scope, receive, send)
            return

        # 🔧 DEBUG: Log entry point for __call__
        print(f"RAW DEBUG: Processing HTTP request in LoggingMiddleware")
        safe_log(self.app_logger, "DEBUG", f"🔥 LoggingMiddleware.__call__ entered for scope type: {scope['type']}")
        
        # 🛡️ СУПЕР-БЕЗОПАСНОЕ извлечение данных запроса с множественными fallback
        method = "UNKNOWN"
        path = "/unknown" 
        query_params = ""
        client_ip = "unknown"
        user_agent = ""
        
        try:
            # Попытка создания Request объекта
            try:
                print(f"RAW DEBUG: Attempting to create Request object")
                request = Request(scope, receive)
                print(f"RAW DEBUG: Request object created successfully")
            except Exception as request_error:
                print(f"RAW DEBUG: Failed to create Request object: {request_error}")
                safe_log(self.app_logger, "ERROR", f"Failed to create Request object: {request_error}", {"scope_type": scope["type"]})
                await self.app(scope, receive, send)
                return

            print(f"RAW DEBUG: Extracting request details")
            method = request.method
            path = request.url.path
            query_params = str(request.query_params)
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "Unknown")
            print(f"RAW DEBUG: Request details: {method} {path}")

            # Проверяем, нужно ли исключать путь из логирования
            is_excluded_path = should_exclude_path(path)
            request_excluded_by_config = not self.log_requests or is_excluded_path
            
            print(f"DEBUG: Logging check -> log_requests: {self.log_requests}, is_excluded_path: {is_excluded_path}, request_excluded_by_config: {request_excluded_by_config}")
            
            if not request_excluded_by_config:
                print(f"RAW DEBUG: Request will be logged")
                try:
                    # Безопасный доступ к атрибутам логгера
                    logger_name = getattr(self.app_logger, 'name', 'unknown')
                    logger_propagate = getattr(self.app_logger, 'propagate', 'unknown')
                    print(f"RAW DEBUG: Logger state - Name: {logger_name}, Propagate: {logger_propagate}")
                except Exception as logger_attr_error:
                    print(f"RAW DEBUG: Error accessing logger attributes: {logger_attr_error}")

                request_id = set_correlation_id(str(uuid.uuid4()))
                print(f"RAW DEBUG: Set correlation ID: {request_id}")
                
                # Ensure Correlation ID is always available in logs
                # 🔧 DEBUG: Log entry point for request started
                try:
                    print(f"RAW DEBUG: Attempting to log request start")
                    # Прямое логирование в файл для отладки
                    with open('logs/http_debug.log', 'a') as f:
                        f.write(f"HTTP Request: {method} {path} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
                    # 🔧 ВРЕМЕННО ОТКЛЮЧЕНО: Прямая запись в app.log для тестирования safe_log
                    # with open('logs/app.log', 'a') as f:
                    #     timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    #     f.write(f"{timestamp} - middleware.http - INFO     - HTTP Request started: {method} {path} (request_id: {request_id})\n")
                    
                    safe_log(
                        self.app_logger,
                        "INFO",
                        "HTTP Request started",
                        extra={
                            "request_id": request_id,
                            "method": method,
                            "path": path,
                            "query_params": query_params,
                            "client_ip": client_ip,
                            "user_agent": user_agent,
                            "log_category": "http_request",
                        },
                    )
                    print(f"RAW DEBUG: Request start logged successfully")
                except Exception as log_error:
                    print(f"RAW DEBUG: Error logging request start: {log_error}")

                start_time = time.time()

                async def send_wrapper(message):
                    print(f"RAW DEBUG: send_wrapper called with message type: {message.get('type', 'unknown')}")
                    if message["type"] == "http.response.start":
                        status_code = message["status"]
                        headers = message["headers"]
                        print(f"RAW DEBUG: Response status: {status_code}")
                        
                        # 🔧 DEBUG: Log entry point for response completed
                        try:
                            print(f"RAW DEBUG: Attempting to log request completion")
                            
                            # Вычисляем продолжительность запроса (используем time.time() вместо time.perf_counter())
                            duration_ms = (time.time() - start_time) * 1000
                            
                            # Используем RequestLogger для логирования HTTP-запросов
                            self.request_logger.log_request(
                                method=method,
                                path=path,
                                status_code=status_code,
                                duration_ms=duration_ms,
                                request_id=CorrelationContext.get_correlation_id(),
                                ip_address=client_ip,
                                user_agent=user_agent
                            )
                            
                            # 🔧 ВРЕМЕННО ОТКЛЮЧЕНО: Прямая запись в app.log для тестирования safe_log
                            # with open('logs/app.log', 'a') as f:
                            #     timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                            #     f.write(f"{timestamp} - middleware.http - INFO     - {method} {path} - {status_code} ({duration_ms:.2f}ms)\n")
                            
                            # Стандартное логирование через safe_log
                            safe_log(
                                self.app_logger,
                                "INFO",
                                "HTTP Request completed",
                                extra={
                                    "request_id": CorrelationContext.get_correlation_id(),
                                    "method": method,
                                    "path": path,
                                    "status_code": status_code,
                                    "duration_ms": duration_ms,
                                    "response_headers": {header.decode(): value.decode() for header, value in headers} if self.log_request_headers else "********"
                                },
                            )
                            print(f"RAW DEBUG: Request completion logged successfully")
                        except Exception as log_error:
                            print(f"RAW DEBUG: Error logging request completion: {log_error}")
                    await send(message)
                
                print(f"RAW DEBUG: Calling next middleware with send_wrapper")
                await self.app(scope, receive, send_wrapper)
            else:
                print(f"RAW DEBUG: Request excluded from logging, passing through")
                await self.app(scope, receive, send)

        except Exception as e:
            print(f"RAW DEBUG: Unhandled error in LoggingMiddleware: {e}")
            import traceback
            print(f"RAW DEBUG: Traceback: {traceback.format_exc()}")
            safe_log(self.app_logger, "ERROR", f"Unhandled error in LoggingMiddleware: {e}",
                     {"method": method, "path": path, "traceback": traceback.format_exc()})
            # Re-raise the exception to ensure it's propagated
            raise

    async def _handle_request_fallback(self, scope: Scope, receive: Receive, send: Send, method: str, path: str) -> None:
        """
        🚨 КРИТИЧЕСКИЙ FALLBACK: Обработка запроса когда Request объект не может быть создан.
        
        Используется в экстремальных случаях когда основное извлечение данных полностью падает.
        """
        import sys
        
        try:
            # Генерируем correlation ID для отслеживания
            correlation_id = str(uuid.uuid4())
            
            # Логируем критическую ситуацию
            sys.stderr.write(f"[MIDDLEWARE-FALLBACK] Using emergency request handling: {method} {path} (correlation_id: {correlation_id})\n")
            sys.stderr.flush()
            
            # Проверяем исключение пути даже в fallback режиме
            try:
                if should_exclude_path(path):
                    sys.stderr.write(f"[MIDDLEWARE-FALLBACK] Path excluded: {path}\n")
                    sys.stderr.flush()
                    await self.app(scope, receive, send)
                    return
            except Exception as exclude_error:
                sys.stderr.write(f"[MIDDLEWARE-FALLBACK] Path exclusion check failed: {exclude_error}\n")
                sys.stderr.flush()
            
            # Простейшая обработка запроса
            start_time = time.time()
            
            try:
                await self.app(scope, receive, send)
                duration_ms = (time.time() - start_time) * 1000
                
                sys.stderr.write(f"[MIDDLEWARE-FALLBACK] Request completed: {method} {path} ({duration_ms:.2f}ms)\n")
                sys.stderr.flush()
                
            except Exception as app_error:
                duration_ms = (time.time() - start_time) * 1000
                
                sys.stderr.write(f"[MIDDLEWARE-FALLBACK] Request failed: {method} {path} - {str(app_error)} ({duration_ms:.2f}ms)\n")
                sys.stderr.flush()
                raise
                
        except Exception as fallback_error:
            # Последняя линия обороны - просто передаем запрос дальше
            sys.stderr.write(f"[MIDDLEWARE-EMERGENCY] Fallback handler failed: {fallback_error}. Passing request through.\n")
            sys.stderr.flush()
            await self.app(scope, receive, send)

    def _get_client_ip(self, request: Request) -> str:
        """🛡️ СУПЕР-БЕЗОПАСНОЕ извлечение client IP с множественными fallback."""
        try:
            # Основная попытка извлечения headers
            try:
                headers = dict(request.scope.get("headers", []))
            except Exception as headers_error:
                safe_log(None, "WARNING", f"Headers extraction failed: {headers_error}")
                return "unknown"
            
            # Проверяем X-Forwarded-For header
            try:
                forwarded_for = headers.get(b"x-forwarded-for")
                if forwarded_for:
                    decoded = forwarded_for.decode('utf-8', errors='ignore')
                    first_ip = decoded.split(",")[0].strip()
                    if first_ip:
                        return first_ip
            except Exception as forwarded_error:
                safe_log(None, "WARNING", f"X-Forwarded-For processing failed: {forwarded_error}")
            
            # Проверяем X-Real-IP header
            try:
                real_ip = headers.get(b"x-real-ip")
                if real_ip:
                    decoded = real_ip.decode('utf-8', errors='ignore')
                    if decoded.strip():
                        return decoded.strip()
            except Exception as real_ip_error:
                safe_log(None, "WARNING", f"X-Real-IP processing failed: {real_ip_error}")
            
            # Fallback на client info из scope
            try:
                client = request.scope.get("client")
                if client and len(client) > 0:
                    return str(client[0])
            except Exception as client_error:
                safe_log(None, "WARNING", f"Client scope extraction failed: {client_error}")
            
            # Последний fallback - прямо из scope
            try:
                scope_client = request.scope.get("client")
                if scope_client:
                    return str(scope_client[0]) if scope_client[0] else "unknown"
            except Exception as scope_error:
                safe_log(None, "WARNING", f"Scope client extraction failed: {scope_error}")
            
            return "unknown"
            
        except Exception as ip_error:
            # 🛡️ КРИТИЧЕСКИЙ FALLBACK: При любой ошибке возвращаем unknown
            import sys
            sys.stderr.write(f"[IP-EXTRACTION-CRITICAL] Complete IP extraction failed: {ip_error}\n")
            sys.stderr.flush()
            return "unknown"

    def _ensure_logging_initialized(self):
        """
        🔧 КРИТИЧЕСКАЯ ФУНКЦИЯ: Принудительная инициализация логирования.
        
        Гарантирует, что логирование настроено в процессе uvicorn,
        даже если main.py инициализация не сработала.
        """
        import logging
        import sys
        import os
        
        try:
            # 🚨 АГРЕССИВНАЯ ПРОВЕРКА: Всегда инициализируем заново
            print(f"[MIDDLEWARE-INIT] 🔧 Starting aggressive logging initialization...", file=sys.stderr)
            
            # Проверяем текущее состояние
            root_logger = logging.getLogger()
            print(f"[MIDDLEWARE-INIT] Current root level: {root_logger.level}, handlers: {len(root_logger.handlers)}", file=sys.stderr)
            
            # 🚀 ПРИНУДИТЕЛЬНАЯ НАСТРОЙКА ЛОГИРОВАНИЯ (всегда)
            
            # 1. Очистим ВСЕ существующие handlers
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
                handler.close()
            
            # Очистим handlers у всех логгеров
            for name in ['middleware', 'middleware.asgi', 'middleware.http', 'services', 'api', 'database']:
                logger = logging.getLogger(name)
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                    handler.close()
            
            print(f"[MIDDLEWARE-INIT] ✅ Cleared all existing handlers", file=sys.stderr)
            
            # 2. Установим правильный уровень для root
            root_logger.setLevel(logging.DEBUG)
            print(f"[MIDDLEWARE-INIT] ✅ Set root level to DEBUG", file=sys.stderr)
            
            # 3. Создадим console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                '%(levelname)s     - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
            print(f"[MIDDLEWARE-INIT] ✅ Added console handler", file=sys.stderr)
            
            # 4. Создадим file handler для app.log
            log_file = getattr(self.settings, 'LOG_FILE', 'logs/app.log')
            if log_file:
                try:
                    # Создаем директорию если не существует
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
                    
                    file_handler = logging.FileHandler(log_file)
                    file_handler.setLevel(logging.DEBUG)
                    file_formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)-8s - %(message)s'
                    )
                    file_handler.setFormatter(file_formatter)
                    root_logger.addHandler(file_handler)
                    
                    print(f"[MIDDLEWARE-INIT] ✅ File handler added: {log_file}", file=sys.stderr)
                    
                except Exception as file_error:
                    print(f"[MIDDLEWARE-INIT] ❌ Could not create file handler: {file_error}", file=sys.stderr)
            
            # 5. Настроим специфичные логгеры для приложения
            app_loggers = ['middleware', 'services', 'api', 'database', 'middleware.asgi', 'middleware.http']
            for logger_name in app_loggers:
                logger = logging.getLogger(logger_name)
                logger.setLevel(logging.DEBUG)
                logger.propagate = True
                print(f"[MIDDLEWARE-INIT] ✅ Configured logger: {logger_name}", file=sys.stderr)
            
            # 6. Принудительно обновим self.app_logger
            if hasattr(self, 'app_logger') and hasattr(self.app_logger, 'logger'):
                self.app_logger.logger.setLevel(logging.DEBUG)
                print(f"[MIDDLEWARE-INIT] ✅ Updated self.app_logger level", file=sys.stderr)
            
            print(f"[MIDDLEWARE-INIT] ✅ Aggressive logging initialization completed", file=sys.stderr)
            
            # 7. Тестовое сообщение для проверки
            test_logger = logging.getLogger('middleware.test')
            test_logger.info("🧪 Test message: Aggressive logging initialization completed")
            
            # 8. Проверим финальное состояние
            final_root = logging.getLogger()
            print(f"[MIDDLEWARE-INIT] Final state - Level: {final_root.level}, Handlers: {len(final_root.handlers)}", file=sys.stderr)
                
            # 9. Настраиваем uvicorn логгеры для перехвата
            intercept_handler = InterceptHandler()
            for logger_name in ['uvicorn', 'uvicorn.access', 'uvicorn.error']:
                logger = logging.getLogger(logger_name)
                logger.handlers = [intercept_handler]
                logger.propagate = False
                print(f"[MIDDLEWARE-INIT] ✅ Added intercept handler to: {logger_name}", file=sys.stderr)
                
        except Exception as init_error:
            # Критический fallback
            print(f"[MIDDLEWARE-INIT] ❌ Failed to initialize logging: {init_error}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


# 🔧 ELIMINATED: LoggingMiddlewareAdapter removed - single unified LoggingMiddleware only
# FastAPI can use ASGI middleware directly without adapter pattern 