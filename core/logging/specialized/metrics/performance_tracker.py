"""
Performance tracker implementation.

This module provides a tracker for performance metrics.
"""

import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from core.logging.interfaces import IPerformanceTracker
from core.logging.specialized.metrics.metrics_collector import MetricsCollector


class PerformanceTracker(IPerformanceTracker):
    """Tracker for performance metrics."""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize a new performance tracker.
        
        Args:
            metrics_collector: The metrics collector to use
        """
        self._metrics_collector = metrics_collector or MetricsCollector()
        self._slow_operation_threshold_ms = 100.0
    
    def set_slow_operation_threshold_ms(self, threshold_ms: float) -> None:
        """
        Set the slow operation threshold.
        
        Args:
            threshold_ms: The threshold in milliseconds
        """
        self._slow_operation_threshold_ms = threshold_ms
    
    def track_time(self, operation: str, duration_ms: float, **kwargs) -> None:
        """
        Track the time for an operation.
        
        Args:
            operation: The operation name
            duration_ms: The duration in milliseconds
            **kwargs: Additional context
        """
        # Record the duration in a histogram
        self._metrics_collector.record_histogram(
            f"{operation}_duration_ms",
            duration_ms,
            labels=kwargs
        )
        
        # Increment the operation counter
        self._metrics_collector.increment_counter(
            f"{operation}_count",
            1,
            labels=kwargs
        )
        
        # Track slow operations
        if duration_ms > self._slow_operation_threshold_ms:
            self._metrics_collector.increment_counter(
                f"{operation}_slow_count",
                1,
                labels=kwargs
            )
    
    @contextmanager
    def track_operation(self, operation: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        Context manager for tracking an operation.
        
        Args:
            operation: The operation name
            **kwargs: Additional context
            
        Yields:
            A context dictionary
        """
        # Create a context dictionary
        context = {
            "operation": operation,
            "start_time": time.time(),
            "additional_context": {},
        }
        
        try:
            # Yield the context
            yield context["additional_context"]
            
            # Calculate the duration
            duration_ms = (time.time() - context["start_time"]) * 1000
            
            # Track the time
            self.track_time(
                operation=operation,
                duration_ms=duration_ms,
                **kwargs,
                **context["additional_context"]
            )
        except Exception as e:
            # Calculate the duration
            duration_ms = (time.time() - context["start_time"]) * 1000
            
            # Track the time with error
            self.track_time(
                operation=operation,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                **kwargs,
                **context["additional_context"]
            )
            
            # Re-raise the exception
            raise


class AsyncPerformanceTracker(PerformanceTracker):
    """Asynchronous tracker for performance metrics."""
    
    async def atrack_time(self, operation: str, duration_ms: float, **kwargs) -> None:
        """
        Track the time for an operation asynchronously.
        
        Args:
            operation: The operation name
            duration_ms: The duration in milliseconds
            **kwargs: Additional context
        """
        # Record the duration in a histogram
        await self._metrics_collector.arecord_histogram(
            f"{operation}_duration_ms",
            duration_ms,
            labels=kwargs
        )
        
        # Increment the operation counter
        await self._metrics_collector.aincrement_counter(
            f"{operation}_count",
            1,
            labels=kwargs
        )
        
        # Track slow operations
        if duration_ms > self._slow_operation_threshold_ms:
            await self._metrics_collector.aincrement_counter(
                f"{operation}_slow_count",
                1,
                labels=kwargs
            )
    
    @contextmanager
    async def atrack_operation(self, operation: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """
        Async context manager for tracking an operation.
        
        Args:
            operation: The operation name
            **kwargs: Additional context
            
        Yields:
            A context dictionary
        """
        # Create a context dictionary
        context = {
            "operation": operation,
            "start_time": time.time(),
            "additional_context": {},
        }
        
        try:
            # Yield the context
            yield context["additional_context"]
            
            # Calculate the duration
            duration_ms = (time.time() - context["start_time"]) * 1000
            
            # Track the time
            await self.atrack_time(
                operation=operation,
                duration_ms=duration_ms,
                **kwargs,
                **context["additional_context"]
            )
        except Exception as e:
            # Calculate the duration
            duration_ms = (time.time() - context["start_time"]) * 1000
            
            # Track the time with error
            await self.atrack_time(
                operation=operation,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                **kwargs,
                **context["additional_context"]
            )
            
            # Re-raise the exception
            raise 