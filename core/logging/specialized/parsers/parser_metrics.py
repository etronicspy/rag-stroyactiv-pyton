"""
Parser Metrics Implementation

Metrics collection and tracking for parser operations with integration
into the main monitoring system.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import lru_cache
import threading

from core.logging.interfaces.metrics import IMetricsCollector, IPerformanceTracker


class ParserMetrics:
    """
    Metrics collection for parser operations.
    
    Provides performance tracking, success rates, and operational metrics
    for parser operations with thread-safe collection.
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize parser metrics.
        
        Args:
            window_size: Size of rolling window for metrics calculation
        """
        self.window_size = window_size
        self._lock = threading.Lock()
        
        # Operation metrics
        self._operation_times: deque = deque(maxlen=window_size)
        self._operation_counts: Dict[str, int] = defaultdict(int)
        self._success_counts: Dict[str, int] = defaultdict(int)
        self._failure_counts: Dict[str, int] = defaultdict(int)
        
        # Performance metrics
        self._start_time = time.time()
        self._total_operations = 0
        self._total_processing_time = 0.0
        
        # Rolling metrics
        self._hourly_metrics: deque = deque(maxlen=24)  # 24 hours
        self._last_hour_reset = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Current hour metrics
        self._current_hour_metrics = {
            "operations": 0,
            "successes": 0,
            "failures": 0,
            "total_time": 0.0,
            "start_time": datetime.now()
        }
    
    def record_operation_start(self, operation_type: str, operation_id: str) -> None:
        """
        Record the start of an operation.
        
        Args:
            operation_type: Type of operation
            operation_id: Unique identifier for operation
        """
        with self._lock:
            self._operation_counts[operation_type] += 1
            self._total_operations += 1
            self._current_hour_metrics["operations"] += 1
    
    def record_operation_success(
        self,
        operation_type: str,
        operation_id: str,
        processing_time: float
    ) -> None:
        """
        Record successful operation completion.
        
        Args:
            operation_type: Type of operation
            operation_id: Unique identifier for operation
            processing_time: Time taken for operation
        """
        with self._lock:
            self._success_counts[operation_type] += 1
            self._operation_times.append(processing_time)
            self._total_processing_time += processing_time
            self._current_hour_metrics["successes"] += 1
            self._current_hour_metrics["total_time"] += processing_time
            
            self._check_hourly_reset()
    
    def record_operation_failure(
        self,
        operation_type: str,
        operation_id: str,
        processing_time: float,
        error_type: str
    ) -> None:
        """
        Record failed operation.
        
        Args:
            operation_type: Type of operation
            operation_id: Unique identifier for operation
            processing_time: Time taken for operation
            error_type: Type of error
        """
        with self._lock:
            self._failure_counts[operation_type] += 1
            self._operation_times.append(processing_time)
            self._total_processing_time += processing_time
            self._current_hour_metrics["failures"] += 1
            self._current_hour_metrics["total_time"] += processing_time
            
            self._check_hourly_reset()
    
    def get_success_rate(self, operation_type: Optional[str] = None) -> float:
        """
        Get success rate for operations.
        
        Args:
            operation_type: Specific operation type (optional)
            
        Returns:
            float: Success rate as percentage
        """
        with self._lock:
            if operation_type:
                total = self._success_counts[operation_type] + self._failure_counts[operation_type]
                if total == 0:
                    return 0.0
                return (self._success_counts[operation_type] / total) * 100
            else:
                total_success = sum(self._success_counts.values())
                total_failure = sum(self._failure_counts.values())
                total = total_success + total_failure
                if total == 0:
                    return 0.0
                return (total_success / total) * 100
    
    def get_average_processing_time(self) -> float:
        """
        Get average processing time for operations.
        
        Returns:
            float: Average processing time in seconds
        """
        with self._lock:
            if not self._operation_times:
                return 0.0
            return sum(self._operation_times) / len(self._operation_times)
    
    def get_operations_per_second(self) -> float:
        """
        Get operations per second rate.
        
        Returns:
            float: Operations per second
        """
        with self._lock:
            uptime = time.time() - self._start_time
            if uptime == 0:
                return 0.0
            return self._total_operations / uptime
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dict[str, Any]: Current metrics
        """
        with self._lock:
            return {
                "total_operations": self._total_operations,
                "operation_counts": dict(self._operation_counts),
                "success_counts": dict(self._success_counts),
                "failure_counts": dict(self._failure_counts),
                "success_rate": self.get_success_rate(),
                "average_processing_time": self.get_average_processing_time(),
                "operations_per_second": self.get_operations_per_second(),
                "total_processing_time": self._total_processing_time,
                "uptime": time.time() - self._start_time,
                "current_hour": dict(self._current_hour_metrics)
            }
    
    def get_hourly_metrics(self) -> List[Dict[str, Any]]:
        """
        Get hourly metrics for the last 24 hours.
        
        Returns:
            List[Dict[str, Any]]: Hourly metrics
        """
        with self._lock:
            return list(self._hourly_metrics)
    
    def _check_hourly_reset(self) -> None:
        """Check if we need to reset hourly metrics."""
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        if current_hour > self._last_hour_reset:
            # Save current hour metrics
            self._current_hour_metrics["end_time"] = now
            self._hourly_metrics.append(self._current_hour_metrics.copy())
            
            # Reset for new hour
            self._current_hour_metrics = {
                "operations": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "start_time": now
            }
            self._last_hour_reset = current_hour
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._operation_times.clear()
            self._operation_counts.clear()
            self._success_counts.clear()
            self._failure_counts.clear()
            self._hourly_metrics.clear()
            
            self._start_time = time.time()
            self._total_operations = 0
            self._total_processing_time = 0.0
            
            self._current_hour_metrics = {
                "operations": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "start_time": datetime.now()
            }


class AIParserMetrics(ParserMetrics):
    """
    Extended metrics for AI parser operations.
    
    Includes AI-specific metrics like token usage, model performance,
    and cost tracking.
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize AI parser metrics.
        
        Args:
            window_size: Size of rolling window for metrics calculation
        """
        super().__init__(window_size)
        
        # AI-specific metrics
        self._token_usage: Dict[str, int] = defaultdict(int)
        self._model_usage: Dict[str, int] = defaultdict(int)
        self._cost_tracking: Dict[str, float] = defaultdict(float)
        self._confidence_scores: deque = deque(maxlen=window_size)
        
        # Embedding metrics
        self._embedding_generations: int = 0
        self._embedding_processing_times: deque = deque(maxlen=window_size)
        
        # Model performance
        self._model_response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
    
    def record_ai_operation(
        self,
        operation_id: str,
        model_name: str,
        tokens_used: int,
        processing_time: float,
        confidence_score: Optional[float] = None,
        cost_estimate: Optional[float] = None
    ) -> None:
        """
        Record AI operation metrics.
        
        Args:
            operation_id: Unique identifier for operation
            model_name: Name of AI model used
            tokens_used: Number of tokens used
            processing_time: Time taken for operation
            confidence_score: Confidence score (optional)
            cost_estimate: Estimated cost (optional)
        """
        with self._lock:
            self._token_usage[model_name] += tokens_used
            self._model_usage[model_name] += 1
            self._model_response_times[model_name].append(processing_time)
            
            if confidence_score is not None:
                self._confidence_scores.append(confidence_score)
            
            if cost_estimate is not None:
                self._cost_tracking[model_name] += cost_estimate
    
    def record_embedding_generation(
        self,
        operation_id: str,
        model_name: str,
        processing_time: float,
        embedding_dimensions: int
    ) -> None:
        """
        Record embedding generation metrics.
        
        Args:
            operation_id: Unique identifier for operation
            model_name: Name of embedding model
            processing_time: Time taken for embedding generation
            embedding_dimensions: Dimensions of generated embedding
        """
        with self._lock:
            self._embedding_generations += 1
            self._embedding_processing_times.append(processing_time)
            self._model_usage[model_name] += 1
    
    def get_token_usage(self, model_name: Optional[str] = None) -> int:
        """
        Get total token usage.
        
        Args:
            model_name: Specific model name (optional)
            
        Returns:
            int: Total tokens used
        """
        with self._lock:
            if model_name:
                return self._token_usage[model_name]
            return sum(self._token_usage.values())
    
    def get_average_confidence(self) -> float:
        """
        Get average confidence score.
        
        Returns:
            float: Average confidence score
        """
        with self._lock:
            if not self._confidence_scores:
                return 0.0
            return sum(self._confidence_scores) / len(self._confidence_scores)
    
    def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """
        Get performance metrics for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dict[str, Any]: Model performance metrics
        """
        with self._lock:
            response_times = self._model_response_times[model_name]
            
            if not response_times:
                return {
                    "usage_count": 0,
                    "average_response_time": 0.0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            
            return {
                "usage_count": self._model_usage[model_name],
                "average_response_time": sum(response_times) / len(response_times),
                "total_tokens": self._token_usage[model_name],
                "total_cost": self._cost_tracking[model_name]
            }
    
    def get_ai_metrics(self) -> Dict[str, Any]:
        """
        Get AI-specific metrics.
        
        Returns:
            Dict[str, Any]: AI metrics
        """
        with self._lock:
            base_metrics = self.get_current_metrics()
            
            ai_metrics = {
                "total_tokens_used": sum(self._token_usage.values()),
                "total_cost": sum(self._cost_tracking.values()),
                "model_usage": dict(self._model_usage),
                "token_usage_by_model": dict(self._token_usage),
                "cost_by_model": dict(self._cost_tracking),
                "average_confidence": self.get_average_confidence(),
                "embedding_generations": self._embedding_generations,
                "average_embedding_time": (
                    sum(self._embedding_processing_times) / len(self._embedding_processing_times)
                    if self._embedding_processing_times else 0.0
                )
            }
            
            # Add model performance data
            model_performance = {}
            for model_name in self._model_usage:
                model_performance[model_name] = self.get_model_performance(model_name)
            ai_metrics["model_performance"] = model_performance
            
            return {**base_metrics, **ai_metrics}


# Factory function for easy access
@lru_cache(maxsize=10)
def get_parser_metrics(metrics_name: str = "default") -> ParserMetrics:
    """
    Get cached parser metrics instance.
    
    Args:
        metrics_name: Name for the metrics instance
        
    Returns:
        ParserMetrics: Cached metrics instance
    """
    return ParserMetrics()


@lru_cache(maxsize=10)
def get_ai_parser_metrics(metrics_name: str = "ai_default") -> AIParserMetrics:
    """
    Get cached AI parser metrics instance.
    
    Args:
        metrics_name: Name for the metrics instance
        
    Returns:
        AIParserMetrics: Cached metrics instance
    """
    return AIParserMetrics()


# Export all metrics types
__all__ = [
    'ParserMetrics',
    'AIParserMetrics',
    'get_parser_metrics',
    'get_ai_parser_metrics'
] 