"""
Metrics exporter implementation.

This module provides an exporter for metrics to external systems.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from core.logging.specialized.metrics.metrics_collector import MetricsCollector


class MetricsExporter:
    """Exporter for metrics to external systems."""
    
    def __init__(
        self,
        metrics_collector: Optional[MetricsCollector] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize a new metrics exporter.
        
        Args:
            metrics_collector: The metrics collector to use
            logger: The logger to use
        """
        self._metrics_collector = metrics_collector or MetricsCollector()
        self._logger = logger or logging.getLogger("metrics")
    
    def export_to_log(self) -> None:
        """Export metrics to logs."""
        metrics = self._metrics_collector.get_metrics()
        self._logger.info(f"Metrics: {json.dumps(metrics)}")
    
    def export_to_json(self) -> str:
        """
        Export metrics to JSON.
        
        Returns:
            The metrics as JSON
        """
        metrics = self._metrics_collector.get_metrics()
        return json.dumps(metrics)
    
    def export_to_prometheus(self) -> str:
        """
        Export metrics to Prometheus format.
        
        Returns:
            The metrics in Prometheus format
        """
        metrics = self._metrics_collector.get_metrics()
        prometheus_metrics = []
        
        for name, data in metrics.items():
            metric_type = data["type"]
            
            if metric_type == "counter":
                prometheus_metrics.append(f"# TYPE {name} counter")
                prometheus_metrics.append(f"{name} {data['value']}")
            
            elif metric_type == "gauge":
                prometheus_metrics.append(f"# TYPE {name} gauge")
                prometheus_metrics.append(f"{name} {data['value']}")
            
            elif metric_type == "histogram":
                prometheus_metrics.append(f"# TYPE {name} histogram")
                
                # Add sum
                prometheus_metrics.append(f"{name}_sum {data['sum']}")
                
                # Add count
                prometheus_metrics.append(f"{name}_count {data['count']}")
                
                # Add buckets
                for bucket, count in data["buckets"].items():
                    prometheus_metrics.append(f"{name}_bucket{{le=\"{bucket}\"}} {count}")
        
        return "\n".join(prometheus_metrics)


class AsyncMetricsExporter(MetricsExporter):
    """Asynchronous exporter for metrics to external systems."""
    
    async def aexport_to_log(self) -> None:
        """Export metrics to logs asynchronously."""
        metrics = await self._metrics_collector.aget_metrics()
        self._logger.info(f"Metrics: {json.dumps(metrics)}")
    
    async def aexport_to_json(self) -> str:
        """
        Export metrics to JSON asynchronously.
        
        Returns:
            The metrics as JSON
        """
        metrics = await self._metrics_collector.aget_metrics()
        return json.dumps(metrics)
    
    async def aexport_to_prometheus(self) -> str:
        """
        Export metrics to Prometheus format asynchronously.
        
        Returns:
            The metrics in Prometheus format
        """
        metrics = await self._metrics_collector.aget_metrics()
        prometheus_metrics = []
        
        for name, data in metrics.items():
            metric_type = data["type"]
            
            if metric_type == "counter":
                prometheus_metrics.append(f"# TYPE {name} counter")
                prometheus_metrics.append(f"{name} {data['value']}")
            
            elif metric_type == "gauge":
                prometheus_metrics.append(f"# TYPE {name} gauge")
                prometheus_metrics.append(f"{name} {data['value']}")
            
            elif metric_type == "histogram":
                prometheus_metrics.append(f"# TYPE {name} histogram")
                
                # Add sum
                prometheus_metrics.append(f"{name}_sum {data['sum']}")
                
                # Add count
                prometheus_metrics.append(f"{name}_count {data['count']}")
                
                # Add buckets
                for bucket, count in data["buckets"].items():
                    prometheus_metrics.append(f"{name}_bucket{{le=\"{bucket}\"}} {count}")
        
        return "\n".join(prometheus_metrics) 