"""
🎯 Correlation ID Context Management System

Provides thread-safe, async-safe correlation ID propagation through the entire application.
ЭТАП 3: Полное покрытие correlation ID для 100% трассировки.

Correlation context management for request tracing with enhanced error handling.
Provides safe correlation ID handling with multiple fallback mechanisms.
"""

import uuid
import sys
from contextvars import ContextVar
from typing import Optional, Callable, Any, Dict
from functools import wraps
import asyncio
import logging

# Context variable for correlation ID with safe default
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# Context variable for request metadata with safe default  
_request_metadata: ContextVar[Dict[str, Any]] = ContextVar('request_metadata', default={})

# Emergency fallback storage for critical cases
_emergency_correlation_storage: Dict[str, str] = {}

# 🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Добавляем недостающие ContextVar для совместимости
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_metadata: ContextVar[Dict[str, Any]] = ContextVar('request_metadata', default={})


def safe_generate_correlation_id() -> str:
    """
    🛡️ БЕЗОПАСНАЯ ГЕНЕРАЦИЯ correlation ID с fallback механизмами.
    
    Гарантирует получение correlation ID даже в критических ситуациях.
    """
    try:
        # Основной способ - UUID4
        return str(uuid.uuid4())
    except Exception as uuid_error:
        try:
            # Fallback 1: Простая генерация на основе времени
            import time
            import random
            timestamp = int(time.time() * 1000000)  # микросекунды
            random_part = random.randint(1000, 9999)
            fallback_id = f"fallback-{timestamp}-{random_part}"
            
            # Логируем проблему в stderr
            sys.stderr.write(f"[CORRELATION-WARNING] UUID generation failed: {uuid_error}. Using fallback: {fallback_id}\n")
            sys.stderr.flush()
            
            return fallback_id
            
        except Exception as fallback_error:
            # Fallback 2: Простейший статический ID с счетчиком
            try:
                import time
                static_id = f"emergency-{int(time.time())}"
                
                sys.stderr.write(f"[CORRELATION-CRITICAL] All ID generation failed. Using static: {static_id}\n")
                sys.stderr.flush()
                
                return static_id
                
            except Exception:
                # Последняя линия обороны - константный ID
                return "critical-fallback-id"


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    🛡️ БЕЗОПАСНАЯ УСТАНОВКА correlation ID с множественными fallback.
    
    Args:
        correlation_id: ID для установки (если None - генерируется новый)
        
    Returns:
        str: Установленный correlation ID
    """
    try:
        # Генерируем ID если не передан
        if correlation_id is None:
            correlation_id = safe_generate_correlation_id()
        
        # Валидируем ID
        if not correlation_id or not isinstance(correlation_id, str):
            correlation_id = safe_generate_correlation_id()
            sys.stderr.write(f"[CORRELATION-WARNING] Invalid correlation_id provided, generated new: {correlation_id}\n")
            sys.stderr.flush()
        
        # Основная попытка установки через ContextVar
        try:
            _correlation_id.set(correlation_id)
            return correlation_id
            
        except Exception as context_error:
            # Fallback 1: Аварийное хранилище
            try:
                import threading
                thread_id = str(threading.get_ident())
                _emergency_correlation_storage[thread_id] = correlation_id
                
                sys.stderr.write(f"[CORRELATION-FALLBACK] ContextVar failed: {context_error}. Using emergency storage.\n")
                sys.stderr.flush()
                
                return correlation_id
                
            except Exception as emergency_error:
                # Fallback 2: Хотя бы вернем ID для использования
                sys.stderr.write(f"[CORRELATION-CRITICAL] All storage failed: {emergency_error}. ID available but not stored.\n")
                sys.stderr.flush()
                
                return correlation_id
                
    except Exception as general_error:
        # Критический fallback - генерируем и возвращаем простой ID
        try:
            emergency_id = safe_generate_correlation_id()
            sys.stderr.write(f"[CORRELATION-EMERGENCY] Complete failure: {general_error}. Using emergency ID: {emergency_id}\n")
            sys.stderr.flush()
            return emergency_id
            
        except Exception:
            # Последняя линия обороны
            return "total-failure-id"


def get_correlation_id() -> Optional[str]:
    """
    🛡️ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ correlation ID с fallback поиском.
    
    Returns:
        Optional[str]: Correlation ID или None если не найден
    """
    try:
        # Основная попытка - из ContextVar
        correlation_id = _correlation_id.get()
        if correlation_id:
            return correlation_id
            
        # Fallback 1: Аварийное хранилище
        try:
            import threading
            thread_id = str(threading.get_ident())
            emergency_id = _emergency_correlation_storage.get(thread_id)
            if emergency_id:
                return emergency_id
                
        except Exception as emergency_error:
            sys.stderr.write(f"[CORRELATION-FALLBACK] Emergency storage access failed: {emergency_error}\n")
            sys.stderr.flush()
        
        # Fallback 2: Возвращаем None - ID не найден
        return None
        
    except Exception as general_error:
        # Критический fallback
        sys.stderr.write(f"[CORRELATION-CRITICAL] Get correlation ID failed: {general_error}\n")
        sys.stderr.flush()
        return None


def set_request_metadata(metadata: Dict[str, Any]) -> bool:
    """
    🛡️ БЕЗОПАСНАЯ УСТАНОВКА метаданных запроса.
    
    Args:
        metadata: Словарь метаданных
        
    Returns:
        bool: True если успешно установлено
    """
    try:
        # Валидируем метаданные
        if not isinstance(metadata, dict):
            sys.stderr.write(f"[METADATA-WARNING] Invalid metadata type: {type(metadata)}. Using empty dict.\n")
            sys.stderr.flush()
            metadata = {}
        
        # Основная попытка установки
        try:
            _request_metadata.set(metadata)
            return True
            
        except Exception as context_error:
            # Fallback: Аварийное хранилище для метаданных
            try:
                import threading
                thread_id = str(threading.get_ident())
                storage_key = f"metadata_{thread_id}"
                _emergency_correlation_storage[storage_key] = str(metadata)  # Сериализуем в строку
                
                sys.stderr.write(f"[METADATA-FALLBACK] ContextVar failed: {context_error}. Using emergency storage.\n")
                sys.stderr.flush()
                
                return True
                
            except Exception as emergency_error:
                sys.stderr.write(f"[METADATA-CRITICAL] All metadata storage failed: {emergency_error}\n")
                sys.stderr.flush()
                return False
                
    except Exception as general_error:
        sys.stderr.write(f"[METADATA-EMERGENCY] Complete metadata failure: {general_error}\n")
        sys.stderr.flush()
        return False


def get_request_metadata() -> Dict[str, Any]:
    """
    🛡️ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ метаданных запроса.
    
    Returns:
        Dict[str, Any]: Метаданные запроса или пустой словарь
    """
    try:
        # Основная попытка - из ContextVar
        metadata = _request_metadata.get()
        if metadata and isinstance(metadata, dict):
            return metadata
            
        # Fallback 1: Аварийное хранилище
        try:
            import threading
            thread_id = str(threading.get_ident())
            storage_key = f"metadata_{thread_id}"
            emergency_metadata = _emergency_correlation_storage.get(storage_key)
            
            if emergency_metadata:
                # Пытаемся десериализовать из строки
                try:
                    import ast
                    return ast.literal_eval(emergency_metadata)
                except Exception:
                    # Если не получается - возвращаем базовую информацию
                    return {"emergency_metadata": emergency_metadata}
                    
        except Exception as emergency_error:
            sys.stderr.write(f"[METADATA-FALLBACK] Emergency metadata access failed: {emergency_error}\n")
            sys.stderr.flush()
        
        # Fallback 2: Пустой словарь
        return {}
        
    except Exception as general_error:
        sys.stderr.write(f"[METADATA-CRITICAL] Get metadata failed: {general_error}\n")
        sys.stderr.flush()
        return {}


def clear_correlation_context() -> bool:
    """
    🛡️ БЕЗОПАСНАЯ ОЧИСТКА correlation context.
    
    Returns:
        bool: True если успешно очищено
    """
    success = True
    
    try:
        # Очищаем ContextVar
        try:
            _correlation_id.set(None)
        except Exception as context_error:
            sys.stderr.write(f"[CONTEXT-CLEAR] ContextVar correlation clear failed: {context_error}\n")
            sys.stderr.flush()
            success = False
            
        try:
            _request_metadata.set({})
        except Exception as metadata_error:
            sys.stderr.write(f"[CONTEXT-CLEAR] ContextVar metadata clear failed: {metadata_error}\n")
            sys.stderr.flush()
            success = False
        
        # Очищаем аварийное хранилище для текущего потока
        try:
            import threading
            thread_id = str(threading.get_ident())
            
            # Удаляем записи для текущего потока
            keys_to_remove = [key for key in _emergency_correlation_storage.keys() 
                            if key == thread_id or key == f"metadata_{thread_id}"]
            
            for key in keys_to_remove:
                _emergency_correlation_storage.pop(key, None)
                
        except Exception as emergency_error:
            sys.stderr.write(f"[CONTEXT-CLEAR] Emergency storage clear failed: {emergency_error}\n")
            sys.stderr.flush()
            success = False
        
        return success
        
    except Exception as general_error:
        sys.stderr.write(f"[CONTEXT-CLEAR] Complete clear failure: {general_error}\n")
        sys.stderr.flush()
        return False


def get_correlation_context_info() -> Dict[str, Any]:
    """
    🔍 ДИАГНОСТИЧЕСКАЯ ФУНКЦИЯ: Получение полной информации о состоянии context.
    
    Полезно для отладки проблем с correlation context.
    
    Returns:
        Dict[str, Any]: Полная диагностическая информация
    """
    try:
        info = {
            "correlation_id": None,
            "metadata": {},
            "context_var_status": "unknown",
            "emergency_storage_status": "unknown",
            "thread_id": None,
            "emergency_keys": []
        }
        
        # Получаем correlation ID
        try:
            info["correlation_id"] = get_correlation_id()
            info["context_var_status"] = "accessible"
        except Exception as corr_error:
            info["context_var_status"] = f"error: {corr_error}"
        
        # Получаем метаданные
        try:
            info["metadata"] = get_request_metadata()
        except Exception as meta_error:
            info["metadata"] = {"error": str(meta_error)}
        
        # Информация о потоке
        try:
            import threading
            info["thread_id"] = str(threading.get_ident())
        except Exception:
            info["thread_id"] = "unknown"
        
        # Состояние аварийного хранилища
        try:
            info["emergency_keys"] = list(_emergency_correlation_storage.keys())
            info["emergency_storage_status"] = "accessible"
        except Exception as emergency_error:
            info["emergency_storage_status"] = f"error: {emergency_error}"
        
        return info
        
    except Exception as general_error:
        return {
            "error": f"Complete diagnostic failure: {general_error}",
            "correlation_id": None,
            "metadata": {},
            "status": "critical_failure"
        }


# Класс для удобной работы с контекстом
class CorrelationContext:
    """
    🛡️ БЕЗОПАСНЫЙ КЛАСС для работы с correlation context.
    
    Предоставляет удобный интерфейс с гарантированной безопасностью.
    """
    
    @staticmethod
    def create(correlation_id: Optional[str] = None) -> str:
        """Создать новый correlation context."""
        return set_correlation_id(correlation_id)
    
    @staticmethod
    def get() -> Optional[str]:
        """Получить текущий correlation ID."""
        return get_correlation_id()
    
    @staticmethod
    def set_metadata(metadata: Dict[str, Any]) -> bool:
        """Установить метаданные запроса."""
        return set_request_metadata(metadata)
    
    @staticmethod
    def get_metadata() -> Dict[str, Any]:
        """Получить метаданные запроса."""
        return get_request_metadata()
    
    @staticmethod
    def clear() -> bool:
        """Очистить correlation context."""
        return clear_correlation_context()
    
    @staticmethod
    def diagnose() -> Dict[str, Any]:
        """Получить диагностическую информацию."""
        return get_correlation_context_info()


class CorrelationContext:
    """
    🎯 Correlation ID context manager and utilities.
    
    Provides:
    - Automatic correlation ID generation
    - Context propagation through async/sync calls
    - Integration with logging system
    - Request metadata management
    """
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """
        Get current correlation ID from context.
        
        Returns:
            Current correlation ID or None if not set
        """
        try:
            return correlation_id.get()
        except Exception as e:
            sys.stderr.write(f"[CONTEXT-ERROR] Failed to get correlation ID: {e}\n")
            sys.stderr.flush()
            return None
    
    @staticmethod
    def set_correlation_id(corr_id: str) -> None:
        """
        Set correlation ID in current context.
        
        Args:
            corr_id: Correlation ID to set
        """
        try:
            correlation_id.set(corr_id)
        except Exception as e:
            sys.stderr.write(f"[CONTEXT-ERROR] Failed to set correlation ID: {e}\n")
            sys.stderr.flush()
    
    @staticmethod
    def generate_correlation_id() -> str:
        """
        Generate new correlation ID and set it in context.
        
        Returns:
            Generated correlation ID
        """
        try:
            new_id = str(uuid.uuid4())
            correlation_id.set(new_id)
            return new_id
        except Exception as e:
            sys.stderr.write(f"[CONTEXT-ERROR] Failed to generate correlation ID: {e}\n")
            sys.stderr.flush()
            return safe_generate_correlation_id()
    
    @staticmethod
    def get_or_generate_correlation_id() -> str:
        """
        Get current correlation ID or generate new one if not exists.
        
        Returns:
            Correlation ID (existing or newly generated)
        """
        try:
            current_id = correlation_id.get()
            if current_id is None:
                current_id = CorrelationContext.generate_correlation_id()
            return current_id
        except Exception as e:
            sys.stderr.write(f"[CONTEXT-ERROR] Failed to get or generate correlation ID: {e}\n")
            sys.stderr.flush()
            return safe_generate_correlation_id()
    
    @staticmethod
    def get_request_metadata() -> Dict[str, Any]:
        """
        Get current request metadata.
        
        Returns:
            Current request metadata dictionary
        """
        try:
            metadata = request_metadata.get()
            return metadata if metadata else {}
        except Exception as e:
            sys.stderr.write(f"[CONTEXT-ERROR] Failed to get request metadata: {e}\n")
            sys.stderr.flush()
            return {}
    
    @staticmethod
    def set_request_metadata(metadata: Dict[str, Any]) -> None:
        """
        Set request metadata in current context.
        
        Args:
            metadata: Metadata dictionary to set
        """
        try:
            request_metadata.set(metadata.copy())
        except Exception as e:
            sys.stderr.write(f"[CONTEXT-ERROR] Failed to set request metadata: {e}\n")
            sys.stderr.flush()
    
    @staticmethod
    def update_request_metadata(key: str, value: Any) -> None:
        """
        Update single key in request metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        try:
            current_metadata = request_metadata.get({})
            current_metadata[key] = value
            request_metadata.set(current_metadata)
        except Exception as e:
            sys.stderr.write(f"[CONTEXT-ERROR] Failed to update request metadata: {e}\n")
            sys.stderr.flush()
    
    @classmethod
    def with_correlation_id(cls, corr_id: Optional[str] = None):
        """
        Context manager to set correlation ID for a block of operations.
        
        Args:
            corr_id: Correlation ID to use (generates new if None)
            
        Usage:
            with CorrelationContext.with_correlation_id():
                # All operations here will have the same correlation ID
                logger.info("This log will have correlation ID")
        """
        class CorrelationContextManager:
            def __init__(self, correlation_id_value: Optional[str]):
                self.correlation_id_value = correlation_id_value or str(uuid.uuid4())
                self.token = None
            
            def __enter__(self):
                try:
                    self.token = correlation_id.set(self.correlation_id_value)
                    return self.correlation_id_value
                except Exception as e:
                    sys.stderr.write(f"[CONTEXT-MANAGER-ERROR] Failed to enter correlation context: {e}\n")
                    sys.stderr.flush()
                    return self.correlation_id_value
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    if self.token is not None:
                        correlation_id.reset(self.token)
                except Exception as e:
                    sys.stderr.write(f"[CONTEXT-MANAGER-ERROR] Failed to exit correlation context: {e}\n")
                    sys.stderr.flush()
        
        return CorrelationContextManager(corr_id)
    
    @classmethod
    def with_request_context(cls, corr_id: Optional[str] = None, 
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager to set full request context.
        
        Args:
            corr_id: Correlation ID to use
            metadata: Request metadata to set
            
        Usage:
            with CorrelationContext.with_request_context(
                corr_id="12345", 
                metadata={"user_id": "user123", "ip": "1.2.3.4"}
            ):
                # All operations here will have correlation ID and metadata
                pass
        """
        class RequestContextManager:
            def __init__(self, correlation_id_value: Optional[str], 
                        metadata_value: Optional[Dict[str, Any]]):
                self.correlation_id_value = correlation_id_value or str(uuid.uuid4())
                self.metadata_value = metadata_value or {}
                self.corr_token = None
                self.meta_token = None
            
            def __enter__(self):
                try:
                    self.corr_token = correlation_id.set(self.correlation_id_value)
                    self.meta_token = request_metadata.set(self.metadata_value.copy())
                    return self.correlation_id_value
                except Exception as e:
                    sys.stderr.write(f"[REQUEST-CONTEXT-ERROR] Failed to enter request context: {e}\n")
                    sys.stderr.flush()
                    return self.correlation_id_value
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    if self.corr_token is not None:
                        correlation_id.reset(self.corr_token)
                    if self.meta_token is not None:
                        request_metadata.reset(self.meta_token)
                except Exception as e:
                    sys.stderr.write(f"[REQUEST-CONTEXT-ERROR] Failed to exit request context: {e}\n")
                    sys.stderr.flush()
        
        return RequestContextManager(corr_id, metadata)


def with_correlation_context(func: Callable) -> Callable:
    """
    Decorator to ensure function runs with correlation ID context.
    
    If correlation ID doesn't exist, generates new one.
    Preserves existing correlation ID if present.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with correlation context
        
    Usage:
        @with_correlation_context
        async def my_function():
            # This function will always have correlation ID available
            corr_id = CorrelationContext.get_correlation_id()
            logger.info(f"Processing with correlation ID: {corr_id}")
    """
    try:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    # 🛡️ БЕЗОПАСНОЕ обеспечение correlation ID
                    correlation_id = CorrelationContext.get_or_generate_correlation_id()
                    return await func(*args, **kwargs)
                    
                except Exception as func_error:
                    # Логируем ошибку с correlation ID
                    try:
                        correlation_id = CorrelationContext.get_correlation_id() or "unknown"
                        sys.stderr.write(f"[DECORATOR-ERROR] Async function {func.__name__} failed (correlation_id: {correlation_id}): {func_error}\n")
                        sys.stderr.flush()
                    except Exception:
                        sys.stderr.write(f"[DECORATOR-CRITICAL] Async function {func.__name__} failed and logging failed: {func_error}\n")
                        sys.stderr.flush()
                    raise
                    
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    # 🛡️ БЕЗОПАСНОЕ обеспечение correlation ID
                    correlation_id = CorrelationContext.get_or_generate_correlation_id()
                    return func(*args, **kwargs)
                    
                except Exception as func_error:
                    # Логируем ошибку с correlation ID
                    try:
                        correlation_id = CorrelationContext.get_correlation_id() or "unknown"
                        sys.stderr.write(f"[DECORATOR-ERROR] Sync function {func.__name__} failed (correlation_id: {correlation_id}): {func_error}\n")
                        sys.stderr.flush()
                    except Exception:
                        sys.stderr.write(f"[DECORATOR-CRITICAL] Sync function {func.__name__} failed and logging failed: {func_error}\n")
                        sys.stderr.flush()
                    raise
                    
            return sync_wrapper
            
    except Exception as decorator_error:
        # 🚨 КРИТИЧЕСКИЙ FALLBACK - возвращаем оригинальную функцию
        try:
            sys.stderr.write(f"[DECORATOR-CRITICAL] Decorator setup failed for {func.__name__}: {decorator_error}. Using original function.\n")
            sys.stderr.flush()
        except Exception:
            pass
        return func


def log_with_correlation(logger_func: Callable) -> Callable:
    """
    Decorator to automatically add correlation ID to log messages.
    
    Args:
        logger_func: Logger function (logger.info, logger.error, etc.)
        
    Returns:
        Enhanced logger function with correlation ID
        
    Usage:
        @log_with_correlation
        def enhanced_info(message, *args, **kwargs):
            return logger.info(message, *args, **kwargs)
    """
    @wraps(logger_func)
    def wrapper(message: str, *args, **kwargs):
        corr_id = CorrelationContext.get_correlation_id()
        if corr_id:
            # Add correlation ID to extra fields
            extra = kwargs.get('extra', {})
            extra['correlation_id'] = corr_id
            kwargs['extra'] = extra
            
            # Prefix message with correlation ID for easy reading
            if not message.startswith('['):
                message = f"[{corr_id}] {message}"
        
        return logger_func(message, *args, **kwargs)
    return wrapper


class CorrelationLoggingAdapter(logging.LoggerAdapter):
    """
    Logging adapter that automatically adds correlation ID to all log records.
    
    Usage:
        logger = logging.getLogger(__name__)
        corr_logger = CorrelationLoggingAdapter(logger)
        corr_logger.info("This message will have correlation ID")
    """
    
    def process(self, msg, kwargs):
        """🛡️ БЕЗОПАСНОЕ добавление correlation ID к log record."""
        try:
            # Безопасно получаем correlation ID
            try:
                corr_id = CorrelationContext.get_correlation_id()
            except Exception as corr_error:
                sys.stderr.write(f"[ADAPTER-WARNING] Failed to get correlation ID: {corr_error}\n")
                sys.stderr.flush()
                corr_id = None
            
            # Безопасно получаем метаданные
            try:
                metadata = CorrelationContext.get_request_metadata()
            except Exception as meta_error:
                sys.stderr.write(f"[ADAPTER-WARNING] Failed to get metadata: {meta_error}\n")
                sys.stderr.flush()
                metadata = {}
            
            # Безопасно обрабатываем extra поля
            try:
                extra = kwargs.get('extra', {})
                if not isinstance(extra, dict):
                    extra = {}
                
                # Добавляем correlation ID
                if corr_id:
                    extra['correlation_id'] = corr_id
                
                # Добавляем метаданные
                for key, value in metadata.items():
                    if key not in extra:  # Не переписываем существующие поля
                        try:
                            extra[key] = value
                        except Exception as field_error:
                            # Если не можем добавить поле - пропускаем
                            sys.stderr.write(f"[ADAPTER-WARNING] Failed to add metadata field {key}: {field_error}\n")
                            sys.stderr.flush()
                
                if extra:
                    kwargs['extra'] = extra
                    
            except Exception as extra_error:
                sys.stderr.write(f"[ADAPTER-ERROR] Failed to process extra fields: {extra_error}\n")
                sys.stderr.flush()
            
            # Безопасно добавляем префикс к сообщению
            try:
                if corr_id and not str(msg).startswith('['):
                    msg = f"[{corr_id}] {msg}"
            except Exception as prefix_error:
                sys.stderr.write(f"[ADAPTER-WARNING] Failed to add correlation prefix: {prefix_error}\n")
                sys.stderr.flush()
            
            return msg, kwargs
            
        except Exception as general_error:
            # 🚨 КРИТИЧЕСКИЙ FALLBACK - возвращаем как есть
            try:
                sys.stderr.write(f"[ADAPTER-CRITICAL] Complete process failure: {general_error}\n")
                sys.stderr.flush()
            except Exception:
                pass
            return msg, kwargs


# 🔧 ИСПРАВЛЕННЫЕ Convenience functions для совместимости
# Используем безопасные функции вместо дублированных методов класса

def get_correlation_id_safe() -> Optional[str]:
    """Безопасное получение correlation ID."""
    return get_correlation_id()

def set_correlation_id_safe(corr_id: Optional[str] = None) -> str:
    """Безопасная установка correlation ID."""
    return set_correlation_id(corr_id)

def generate_correlation_id_safe() -> str:
    """Безопасная генерация correlation ID."""
    return safe_generate_correlation_id()

def get_or_generate_correlation_id_safe() -> str:
    """Безопасное получение или генерация correlation ID."""
    current_id = get_correlation_id()
    if current_id is None:
        current_id = set_correlation_id()
    return current_id

# 🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Добавляем недостающие функции для обратной совместимости
def get_or_generate_correlation_id() -> str:
    """
    🛡️ ОБРАТНАЯ СОВМЕСТИМОСТЬ: Получение или генерация correlation ID.
    
    Эта функция нужна для импорта в performance_optimizer.py
    """
    try:
        return CorrelationContext.get_or_generate_correlation_id()
    except Exception as e:
        sys.stderr.write(f"[COMPATIBILITY-ERROR] get_or_generate_correlation_id failed: {e}\n")
        sys.stderr.flush()
        return safe_generate_correlation_id()

def generate_correlation_id() -> str:
    """
    🛡️ ОБРАТНАЯ СОВМЕСТИМОСТЬ: Генерация correlation ID.
    
    Эта функция нужна для импорта в других модулях
    """
    try:
        return CorrelationContext.generate_correlation_id()
    except Exception as e:
        sys.stderr.write(f"[COMPATIBILITY-ERROR] generate_correlation_id failed: {e}\n")
        sys.stderr.flush()
        return safe_generate_correlation_id()

# Алиасы для полной совместимости
set_correlation_id_compat = set_correlation_id
get_correlation_id_compat = get_correlation_id

# 🔧 ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ СОВМЕСТИМОСТИ для всех возможных импортов
def get_request_metadata_compat() -> Dict[str, Any]:
    """Совместимость для get_request_metadata."""
    try:
        return CorrelationContext.get_request_metadata()
    except Exception as e:
        sys.stderr.write(f"[COMPATIBILITY-ERROR] get_request_metadata_compat failed: {e}\n")
        sys.stderr.flush()
        return {}

def set_request_metadata_compat(metadata: Dict[str, Any]) -> None:
    """Совместимость для set_request_metadata."""
    try:
        CorrelationContext.set_request_metadata(metadata)
    except Exception as e:
        sys.stderr.write(f"[COMPATIBILITY-ERROR] set_request_metadata_compat failed: {e}\n")
        sys.stderr.flush()

def clear_correlation_context_compat() -> bool:
    """Совместимость для clear_correlation_context."""
    try:
        return clear_correlation_context()
    except Exception as e:
        sys.stderr.write(f"[COMPATIBILITY-ERROR] clear_correlation_context_compat failed: {e}\n")
        sys.stderr.flush()
        return False

# Экспортируем все функции для максимальной совместимости
__all__ = [
    # Основные функции
    'get_correlation_id',
    'set_correlation_id', 
    'generate_correlation_id',
    'get_or_generate_correlation_id',
    'get_request_metadata',
    'set_request_metadata',
    'clear_correlation_context',
    # Безопасные функции
    'safe_generate_correlation_id',
    'get_correlation_context_info',
    # Классы
    'CorrelationContext',
    'CorrelationLoggingAdapter',
    # Декораторы
    'with_correlation_context',
    'log_with_correlation',
    # Совместимость
    'get_correlation_id_compat',
    'set_correlation_id_compat',
    'get_request_metadata_compat',
    'set_request_metadata_compat',
    'clear_correlation_context_compat'
] 