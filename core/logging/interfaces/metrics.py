"""
Metrics interfaces for the logging system.

This module defines interfaces for metrics collection and performance tracking:
- IMetricsCollector: Interface for metrics collection
- IPerformanceTracker: Interface for performance tracking
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, ContextManager


class IMetricsCollector(ABC):
    """Interface for metrics collection."""
    
    @abstractmethod
    def increment_counter(
        self, 
        name: str, 
        value: float = 1.0, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: The metric name
            value: The increment value
            labels: The metric labels
        """
    
    @abstractmethod
    def set_gauge(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric.
        
        Args:
            name: The metric name
            value: The gauge value
            labels: The metric labels
        """
    
    @abstractmethod
    def record_histogram(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram metric.
        
        Args:
            name: The metric name
            value: The histogram value
            labels: The metric labels
        """
    
    @abstractmethod
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics.
        
        Returns:
            A dictionary of all metrics
        """


class IPerformanceTracker(ABC):
    """Interface for performance tracking."""
    
    @abstractmethod
    def start_timer(self, name: str) -> None:
        """
        Start a timer.
        
        Args:
            name: The timer name
        """
    
    @abstractmethod
    def stop_timer(self, name: str) -> float:
        """
        Stop a timer.
        
        Args:
            name: The timer name
            
        Returns:
            The elapsed time in milliseconds
        """
    
    @abstractmethod
    def track_operation(
        self, 
        operation_type: str, 
        name: str, 
        duration_ms: float, 
        success: bool, 
        **kwargs
    ) -> None:
        """
        Track an operation.
        
        Args:
            operation_type: The operation type
            name: The operation name
            duration_ms: The operation duration in milliseconds
            success: Whether the operation was successful
            **kwargs: Additional context for the operation
        """
    
    @abstractmethod
    def operation_context(
        self, 
        operation_type: str, 
        name: str, 
        **kwargs
    ) -> ContextManager[Dict[str, Any]]:
        """
        Context manager for tracking operations.
        
        Args:
            operation_type: The operation type
            name: The operation name
            **kwargs: Additional context for the operation
            
        Returns:
            A context manager that tracks the operation
        """
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            A dictionary of performance statistics
        """
