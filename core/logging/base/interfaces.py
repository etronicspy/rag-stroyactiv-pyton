"""
Abstract interfaces for the logging system.

Defines contracts that all logging components must follow.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
import logging


class LoggerInterface(ABC):
    """
    Abstract interface for all logger types.
    
    Defines the contract that all loggers must implement.
    """
    
    @abstractmethod
    def log(self, level: str, message: str, **kwargs) -> None:
        """
        Log a message at the specified level.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Message to log
            **kwargs: Additional logging context
        """
        pass
    
    @abstractmethod
    def get_logger_name(self) -> str:
        """
        Get the name of this logger.
        
        Returns:
            Logger name
        """
        pass


class ContextManagerInterface(ABC):
    """
    Abstract interface for context managers.
    
    Defines the contract for correlation ID and request context management.
    """
    
    @abstractmethod
    def get_correlation_id(self) -> Optional[str]:
        """
        Get current correlation ID.
        
        Returns:
            Current correlation ID or None
        """
        pass
    
    @abstractmethod
    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set correlation ID in current context.
        
        Args:
            correlation_id: ID to set
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get current request metadata.
        
        Returns:
            Request metadata dictionary
        """
        pass


class MetricsCollectorInterface(ABC):
    """
    Abstract interface for metrics collectors.
    
    Defines the contract for metrics collection and reporting.
    """
    
    @abstractmethod
    def record_operation(
        self, 
        operation: str, 
        duration_ms: float, 
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an operation metric.
        
        Args:
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
            metadata: Additional operation metadata
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.
        
        Returns:
            Statistics dictionary
        """
        pass


class FormatterInterface(ABC):
    """
    Abstract interface for log formatters.
    
    Defines the contract for formatting log records.
    """
    
    @abstractmethod
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message
        """
        pass


class DatabaseLoggerInterface(ABC):
    """
    Abstract interface for database loggers.
    
    Defines the contract for database operation logging.
    """
    
    @abstractmethod
    def log_operation(
        self,
        operation: str,
        duration_ms: Optional[float] = None,
        record_count: Optional[int] = None,
        success: bool = True,
        error: Optional[Exception] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log a database operation.
        
        Args:
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            record_count: Number of records affected
            success: Whether operation was successful
            error: Exception if operation failed
            extra_data: Additional operation data
            correlation_id: Request correlation ID
        """
        pass


# Type aliases for better code readability
LogLevel = Union[str, int]
LogContext = Dict[str, Any] 