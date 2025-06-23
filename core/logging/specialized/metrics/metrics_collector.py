"""
Metrics collector implementation.

This module provides a collector for metrics.
"""

from typing import Any, Dict, List, Optional

from core.logging.interfaces import IMetricsCollector


class Counter:
    """Counter metric."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a new counter.
        
        Args:
            name: The counter name
            description: The counter description
        """
        self._name = name
        self._description = description
        self._value = 0
    
    def increment(self, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment the counter.
        
        Args:
            value: The value to increment by
            labels: The labels for the counter
        """
        self._value += value
    
    def get_value(self) -> int:
        """
        Get the counter value.
        
        Returns:
            The counter value
        """
        return self._value
    
    def reset(self) -> None:
        """Reset the counter."""
        self._value = 0


class Gauge:
    """Gauge metric."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a new gauge.
        
        Args:
            name: The gauge name
            description: The gauge description
        """
        self._name = name
        self._description = description
        self._value = 0.0
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Set the gauge value.
        
        Args:
            value: The value to set
            labels: The labels for the gauge
        """
        self._value = value
    
    def increment(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment the gauge.
        
        Args:
            value: The value to increment by
            labels: The labels for the gauge
        """
        self._value += value
    
    def decrement(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Decrement the gauge.
        
        Args:
            value: The value to decrement by
            labels: The labels for the gauge
        """
        self._value -= value
    
    def get_value(self) -> float:
        """
        Get the gauge value.
        
        Returns:
            The gauge value
        """
        return self._value
    
    def reset(self) -> None:
        """Reset the gauge."""
        self._value = 0.0


class Histogram:
    """Histogram metric."""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: Optional[List[float]] = None
    ):
        """
        Initialize a new histogram.
        
        Args:
            name: The histogram name
            description: The histogram description
            buckets: The histogram buckets
        """
        self._name = name
        self._description = description
        self._buckets = buckets or [
            0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10
        ]
        self._values: List[float] = []
    
    def record(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a value.
        
        Args:
            value: The value to record
            labels: The labels for the histogram
        """
        self._values.append(value)
    
    def get_values(self) -> List[float]:
        """
        Get the histogram values.
        
        Returns:
            The histogram values
        """
        return self._values.copy()
    
    def get_count(self) -> int:
        """
        Get the number of recorded values.
        
        Returns:
            The number of recorded values
        """
        return len(self._values)
    
    def get_sum(self) -> float:
        """
        Get the sum of recorded values.
        
        Returns:
            The sum of recorded values
        """
        return sum(self._values)
    
    def get_average(self) -> float:
        """
        Get the average of recorded values.
        
        Returns:
            The average of recorded values
        """
        if not self._values:
            return 0.0
        return self.get_sum() / self.get_count()
    
    def get_bucket_counts(self) -> Dict[float, int]:
        """
        Get the bucket counts.
        
        Returns:
            The bucket counts
        """
        bucket_counts = {bucket: 0 for bucket in self._buckets}
        
        for value in self._values:
            for bucket in self._buckets:
                if value <= bucket:
                    bucket_counts[bucket] += 1
        
        return bucket_counts
    
    def reset(self) -> None:
        """Reset the histogram."""
        self._values = []


class MetricsCollector(IMetricsCollector):
    """Collector for metrics."""
    
    def __init__(self):
        """Initialize a new metrics collector."""
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
    
    def counter(self, name: str, description: str = "") -> Counter:
        """
        Get a counter.
        
        Args:
            name: The counter name
            description: The counter description
            
        Returns:
            The counter
        """
        if name not in self._counters:
            self._counters[name] = Counter(name, description)
        return self._counters[name]
    
    def gauge(self, name: str, description: str = "") -> Gauge:
        """
        Get a gauge.
        
        Args:
            name: The gauge name
            description: The gauge description
            
        Returns:
            The gauge
        """
        if name not in self._gauges:
            self._gauges[name] = Gauge(name, description)
        return self._gauges[name]
    
    def histogram(self, name: str, description: str = "", buckets: Optional[List[float]] = None) -> Histogram:
        """
        Get a histogram.
        
        Args:
            name: The histogram name
            description: The histogram description
            buckets: The histogram buckets
            
        Returns:
            The histogram
        """
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, description, buckets)
        return self._histograms[name]
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter.
        
        Args:
            name: The counter name
            value: The value to increment by
            labels: The labels for the counter
        """
        self.counter(name).increment(value, labels)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge value.
        
        Args:
            name: The gauge name
            value: The value to set
            labels: The labels for the gauge
        """
        self.gauge(name).set(value, labels)
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a histogram value.
        
        Args:
            name: The histogram name
            value: The value to record
            labels: The labels for the histogram
        """
        self.histogram(name).record(value, labels)
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all metrics.
        
        Returns:
            All metrics
        """
        metrics = {}
        
        # Add counters
        for name, counter in self._counters.items():
            metrics[name] = {
                "type": "counter",
                "value": counter.get_value(),
            }
        
        # Add gauges
        for name, gauge in self._gauges.items():
            metrics[name] = {
                "type": "gauge",
                "value": gauge.get_value(),
            }
        
        # Add histograms
        for name, histogram in self._histograms.items():
            metrics[name] = {
                "type": "histogram",
                "count": histogram.get_count(),
                "sum": histogram.get_sum(),
                "average": histogram.get_average(),
                "buckets": histogram.get_bucket_counts(),
            }
        
        return metrics
    
    def reset(self) -> None:
        """Reset all metrics."""
        for counter in self._counters.values():
            counter.reset()
        
        for gauge in self._gauges.values():
            gauge.reset()
        
        for histogram in self._histograms.values():
            histogram.reset()


class AsyncMetricsCollector(MetricsCollector):
    """Asynchronous collector for metrics."""
    
    async def aincrement_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter asynchronously.
        
        Args:
            name: The counter name
            value: The value to increment by
            labels: The labels for the counter
        """
        self.increment_counter(name, value, labels)
    
    async def aset_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge value asynchronously.
        
        Args:
            name: The gauge name
            value: The value to set
            labels: The labels for the gauge
        """
        self.set_gauge(name, value, labels)
    
    async def arecord_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a histogram value asynchronously.
        
        Args:
            name: The histogram name
            value: The value to record
            labels: The labels for the histogram
        """
        self.record_histogram(name, value, labels)
    
    async def aget_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all metrics asynchronously.
        
        Returns:
            All metrics
        """
        return self.get_metrics()
    
    async def areset(self) -> None:
        """Reset all metrics asynchronously."""
        self.reset() 