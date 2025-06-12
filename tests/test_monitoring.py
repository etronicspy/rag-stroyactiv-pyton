"""
Tests for monitoring and health check system.

Tests comprehensive health checking, metrics collection, and performance tracking.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from core.monitoring.metrics import (
    MetricsCollector, 
    DatabaseMetrics, 
    PerformanceTracker,
    get_metrics_collector
)
from core.monitoring.logger import (
    DatabaseLogger,
    setup_structured_logging,
    get_logger,
    RequestLogger
)
from api.routes.health import HealthChecker


class TestDatabaseMetrics:
    """Test database metrics collection."""
    
    def test_database_metrics_initialization(self):
        """Test DatabaseMetrics initialization."""
        metrics = DatabaseMetrics()
        
        assert metrics.operation_count == 0
        assert metrics.total_duration_ms == 0.0
        assert metrics.error_count == 0
        assert metrics.success_count == 0
        assert metrics.avg_duration_ms == 0.0
        assert metrics.max_duration_ms == 0.0
        assert metrics.min_duration_ms == float('inf')
        assert metrics.records_processed == 0
        assert metrics.last_operation_time is None
        assert len(metrics.operation_history) == 0
    
    def test_database_metrics_update(self):
        """Test metrics update functionality."""
        metrics = DatabaseMetrics()
        
        # Test successful operation
        metrics.update(duration_ms=100.0, success=True, record_count=5)
        
        assert metrics.operation_count == 1
        assert metrics.total_duration_ms == 100.0
        assert metrics.success_count == 1
        assert metrics.error_count == 0
        assert metrics.avg_duration_ms == 100.0
        assert metrics.max_duration_ms == 100.0
        assert metrics.min_duration_ms == 100.0
        assert metrics.records_processed == 5
        assert metrics.last_operation_time is not None
        assert len(metrics.operation_history) == 1
        assert metrics.success_rate == 100.0
        assert metrics.error_rate == 0.0
        
        # Test failed operation
        metrics.update(duration_ms=50.0, success=False, record_count=0)
        
        assert metrics.operation_count == 2
        assert metrics.total_duration_ms == 150.0
        assert metrics.success_count == 1
        assert metrics.error_count == 1
        assert metrics.avg_duration_ms == 75.0
        assert metrics.max_duration_ms == 100.0
        assert metrics.min_duration_ms == 50.0
        assert metrics.records_processed == 5
        assert len(metrics.operation_history) == 2
        assert metrics.success_rate == 50.0
        assert metrics.error_rate == 50.0
    
    def test_database_metrics_get_stats_dict(self):
        """Test metrics stats dictionary conversion."""
        metrics = DatabaseMetrics()
        metrics.update(duration_ms=100.0, success=True, record_count=5)
        
        stats = metrics.get_stats_dict()
        
        assert isinstance(stats, dict)
        assert 'operation_count' in stats
        assert 'total_duration_ms' in stats
        assert 'avg_duration_ms' in stats
        assert 'success_rate' in stats
        assert 'error_rate' in stats
        assert stats['operation_count'] == 1
        assert stats['success_rate'] == 100.0


class TestPerformanceTracker:
    """Test performance tracking functionality."""
    
    def test_performance_tracker_initialization(self):
        """Test PerformanceTracker initialization."""
        tracker = PerformanceTracker()
        
        assert len(tracker._metrics) == 0
    
    def test_track_operation(self):
        """Test operation tracking."""
        tracker = PerformanceTracker()
        
        # Track operations
        tracker.track_operation("postgresql", "search", 100.0, True, 10)
        tracker.track_operation("qdrant", "insert", 50.0, True, 5)
        tracker.track_operation("postgresql", "search", 200.0, False, 0)
        
        # Check metrics
        metrics = tracker.get_metrics()
        
        assert "postgresql.search" in metrics
        assert "qdrant.insert" in metrics
        assert metrics["postgresql.search"]["operation_count"] == 2
        assert metrics["qdrant.insert"]["operation_count"] == 1
        assert metrics["postgresql.search"]["success_rate"] == 50.0
        assert metrics["qdrant.insert"]["success_rate"] == 100.0
    
    def test_get_database_summary(self):
        """Test database summary generation."""
        tracker = PerformanceTracker()
        
        # Track operations for multiple databases
        tracker.track_operation("postgresql", "search", 100.0, True, 10)
        tracker.track_operation("postgresql", "insert", 50.0, True, 5)
        tracker.track_operation("qdrant", "search", 75.0, True, 3)
        
        summary = tracker.get_database_summary()
        
        assert "postgresql" in summary
        assert "qdrant" in summary
        assert summary["postgresql"]["total_operations"] == 2
        assert summary["qdrant"]["total_operations"] == 1
        assert "operations" in summary["postgresql"]
        assert "search" in summary["postgresql"]["operations"]
        assert "insert" in summary["postgresql"]["operations"]
    
    def test_time_operation_context_manager(self):
        """Test operation timing context manager."""
        tracker = PerformanceTracker()
        
        with tracker.time_operation("test_db", "test_op", 5):
            time.sleep(0.01)  # 10ms
        
        metrics = tracker.get_metrics("test_db")
        assert "test_db.test_op" in metrics
        assert metrics["test_db.test_op"]["operation_count"] == 1
        assert metrics["test_db.test_op"]["records_processed"] == 5
        # Duration should be around 10ms, allow some variance
        assert 5 <= metrics["test_db.test_op"]["avg_duration_ms"] <= 50


class TestMetricsCollector:
    """Test metrics collection system."""
    
    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()
        
        assert len(collector._metrics) == 0
        assert len(collector._counters) == 0
        assert len(collector._gauges) == 0
        assert len(collector._histograms) == 0
        assert collector._performance_tracker is not None
    
    def test_increment_counter(self):
        """Test counter metrics."""
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter", 1)
        collector.increment_counter("test_counter", 5)
        collector.increment_counter("labeled_counter", 2, {"env": "test"})
        
        summary = collector.get_metrics_summary()
        
        assert "test_counter" in summary["counters"]
        assert summary["counters"]["test_counter"] == 6
        assert "labeled_counter{env=test}" in summary["counters"]
        assert summary["counters"]["labeled_counter{env=test}"] == 2
    
    def test_set_gauge(self):
        """Test gauge metrics."""
        collector = MetricsCollector()
        
        collector.set_gauge("test_gauge", 42.5)
        collector.set_gauge("test_gauge", 100.0)  # Should overwrite
        
        summary = collector.get_metrics_summary()
        
        assert "test_gauge" in summary["gauges"]
        assert summary["gauges"]["test_gauge"] == 100.0
    
    def test_record_histogram(self):
        """Test histogram metrics."""
        collector = MetricsCollector()
        
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            collector.record_histogram("test_histogram", value)
        
        summary = collector.get_metrics_summary()
        
        assert "test_histogram" in summary["histograms"]
        hist_data = summary["histograms"]["test_histogram"]
        assert hist_data["count"] == 5
        assert hist_data["min"] == 10.0
        assert hist_data["max"] == 50.0
        assert hist_data["avg"] == 30.0
    
    def test_get_health_metrics(self):
        """Test health metrics generation."""
        collector = MetricsCollector()
        
        # Add some test data
        collector.increment_counter("http_requests_total", 100)
        tracker = collector.get_performance_tracker()
        tracker.track_operation("postgresql", "search", 100.0, True, 10)
        tracker.track_operation("postgresql", "search", 200.0, False, 0)
        
        health_metrics = collector.get_health_metrics()
        
        assert "uptime_seconds" in health_metrics
        assert "total_requests" in health_metrics
        assert "error_rate" in health_metrics
        assert "database_health" in health_metrics
        assert health_metrics["total_requests"] == 100
        assert "postgresql" in health_metrics["database_health"]


class TestDatabaseLogger:
    """Test database logging functionality."""
    
    def test_database_logger_initialization(self):
        """Test DatabaseLogger initialization."""
        logger = DatabaseLogger("test_db")
        
        assert logger.db_type == "test_db"
        assert logger.logger is not None
    
    def test_log_operation(self):
        """Test operation logging."""
        with patch('core.monitoring.logger.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            db_logger = DatabaseLogger("test_db")
            
            # Test successful operation
            db_logger.log_operation(
                operation="search",
                duration_ms=100.5,
                record_count=5,
                success=True,
                correlation_id="test-123"
            )
            
            # Verify logging was called
            assert mock_logger.info.called or mock_logger.error.called
    
    def test_operation_timer_context_manager(self):
        """Test operation timer context manager."""
        with patch('core.monitoring.logger.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            db_logger = DatabaseLogger("test_db")
            
            # Test successful operation
            with db_logger.operation_timer("test_operation", record_count=3):
                time.sleep(0.01)
            
            # Test failed operation
            with pytest.raises(ValueError):
                with db_logger.operation_timer("failed_operation"):
                    raise ValueError("Test error")


class TestHealthChecker:
    """Test health checking functionality."""
    
    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker instance for testing."""
        with patch('core.monitoring.get_metrics_collector'):
            return HealthChecker()
    
    @pytest.mark.asyncio
    async def test_check_basic_health(self, health_checker):
        """Test basic health check."""
        result = await health_checker.check_basic_health()
        
        assert result["status"] == "healthy"
        assert "service" in result
        assert "version" in result
        assert "environment" in result
        assert "timestamp" in result
        assert "uptime_seconds" in result
    
    @pytest.mark.asyncio
    async def test_check_qdrant_health(self, health_checker):
        """Test Qdrant health check."""
        mock_client = Mock()
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        mock_client.get_cluster_info.return_value = Mock(status="green")
        
        with patch('core.database.factories.get_vector_db_client', return_value=mock_client):
            with patch('core.config.get_settings') as mock_settings:
                mock_settings.return_value.DATABASE_TYPE.value = "qdrant_cloud"
                mock_settings.return_value.QDRANT_URL = "https://test.qdrant.io"
                mock_settings.return_value.QDRANT_COLLECTION_NAME = "test_materials"
                
                result = await health_checker._check_qdrant()
                
                assert result["status"] == "healthy"
                assert "details" in result
                assert "collections_count" in result["details"]
    
    @pytest.mark.asyncio
    async def test_check_postgresql_health(self, health_checker):
        """Test PostgreSQL health check."""
        # Mock successful database connection
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        
        mock_db_client = AsyncMock()
        mock_db_client.return_value.__aenter__.return_value = mock_session
        
        with patch('core.database.factories.get_postgresql_client', return_value=mock_db_client):
            with patch('core.config.get_settings') as mock_settings:
                mock_settings.return_value.POSTGRESQL_URL = "postgresql://test"
                
                result = await health_checker.check_postgresql()
                
                assert result["type"] == "postgresql"
                assert "status" in result
                assert "response_time_ms" in result
    
    @pytest.mark.asyncio 
    async def test_check_redis_health(self, health_checker):
        """Test Redis health check."""
        mock_redis_client = AsyncMock()
        mock_redis_client.ping.return_value = True
        mock_redis_client.info.return_value = {
            'redis_version': '6.2.0',
            'used_memory_human': '1.2M',
            'connected_clients': 5
        }
        mock_redis_client.get.return_value = "test_value"
        
        with patch('core.database.factories.get_redis_client', return_value=mock_redis_client):
            with patch('core.config.get_settings') as mock_settings:
                mock_settings.return_value.REDIS_URL = "redis://localhost:6379"
                
                result = await health_checker.check_redis()
                
                assert result["type"] == "redis"
                assert "status" in result
                assert "response_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_check_openai_health(self, health_checker):
        """Test OpenAI health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "text-embedding-3-small"},
                {"id": "gpt-3.5-turbo"}
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            with patch('core.config.get_settings') as mock_settings:
                mock_settings.return_value.get_ai_config.return_value = {
                    'api_key': 'test-key',
                    'model': 'text-embedding-3-small'
                }
                
                result = await health_checker._check_openai()
                
                assert result["status"] == "healthy"
                assert "details" in result
                assert result["details"]["model_exists"] is True


class TestStructuredLogging:
    """Test structured logging setup."""
    
    def test_setup_structured_logging(self):
        """Test structured logging setup."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            setup_structured_logging(
                log_level="INFO",
                enable_structured=True
            )
            
            # Verify logger configuration was called
            assert mock_logger.setLevel.called
            assert mock_logger.addHandler.called
    
    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test_logger")
        
        assert logger is not None
        assert logger.name == "test_logger"


class TestRequestLogger:
    """Test request logging functionality."""
    
    def test_request_logger_initialization(self):
        """Test RequestLogger initialization."""
        request_logger = RequestLogger()
        
        assert request_logger.logger is not None
    
    def test_log_request(self):
        """Test request logging."""
        with patch('core.monitoring.logger.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            request_logger = RequestLogger()
            
            request_logger.log_request(
                method="GET",
                path="/api/v1/health",
                status_code=200,
                duration_ms=45.2,
                user_id="user123",
                request_id="req-456"
            )
            
            # Verify logging was called
            assert mock_logger.log.called or mock_logger.info.called


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_basic_health_endpoint(self):
        """Test basic health endpoint integration."""
        from api.routes.health import basic_health_check
        
        result = await basic_health_check()
        
        assert result["status"] == "healthy"
        assert "service" in result
        assert "version" in result
    
    @pytest.mark.asyncio 
    async def test_config_status_endpoint(self):
        """Test config status endpoint."""
        from api.routes.health import config_status
        
        result = await config_status()
        
        assert "service" in result
        assert "configuration" in result
        assert "timestamp" in result
        assert "database_type" in result["configuration"]
        assert "ai_provider" in result["configuration"] 