"""
Performance tests for monitoring and health check system
Тесты производительности для системы мониторинга и health проверок

Объединяет тесты из:
- test_monitoring.py
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


class TestDatabaseMetricsPerformance:
    """Test database metrics collection performance."""
    
    @pytest.mark.performance
    def test_metrics_update_performance(self):
        """Test metrics update performance under load."""
        metrics = DatabaseMetrics()
        
        start_time = time.time()
        
        # Simulate many metric updates
        for i in range(1000):
            metrics.update(
                duration_ms=float(i % 100),
                success=i % 10 != 0,  # 10% failure rate
                record_count=i % 50
            )
        
        update_time = time.time() - start_time
        
        # Should handle many updates efficiently
        assert update_time < 0.5  # Less than 500ms for 1000 updates
        
        # Verify metrics are correct
        assert metrics.operation_count == 1000
        assert 0 < metrics.avg_duration_ms < 100
        assert metrics.success_rate == 90.0  # 10% failure rate
    
    @pytest.mark.performance
    def test_metrics_stats_generation_performance(self):
        """Test metrics stats generation performance."""
        metrics = DatabaseMetrics()
        
        # Pre-populate with data
        for i in range(100):
            metrics.update(duration_ms=float(i), success=True, record_count=i)
        
        start_time = time.time()
        
        # Generate stats many times
        for _ in range(100):
            stats = metrics.get_stats_dict()
        
        stats_time = time.time() - start_time
        
        # Should generate stats quickly
        assert stats_time < 0.1  # Less than 100ms for 100 generations
        
        # Verify stats are correct
        stats = metrics.get_stats_dict()
        assert stats['operation_count'] == 100
        assert stats['success_rate'] == 100.0


class TestPerformanceTrackerPerformance:
    """Test performance tracking performance."""
    
    @pytest.mark.performance
    def test_track_operation_performance(self):
        """Test operation tracking performance."""
        tracker = PerformanceTracker()
        
        start_time = time.time()
        
        # Track many operations across different databases
        for i in range(500):
            db_name = f"db_{i % 5}"  # 5 different databases
            operation = f"op_{i % 3}"  # 3 different operations
            tracker.track_operation(
                db_name, operation, 
                duration_ms=float(i % 100),
                success=i % 10 != 0,
                record_count=i % 20
            )
        
        tracking_time = time.time() - start_time
        
        # Should track operations efficiently
        assert tracking_time < 1.0  # Less than 1 second for 500 operations
        
        # Verify tracking worked
        metrics = tracker.get_metrics()
        assert len(metrics) == 15  # 5 databases * 3 operations
    
    @pytest.mark.performance
    def test_time_operation_context_manager_performance(self):
        """Test operation timing context manager performance."""
        tracker = PerformanceTracker()
        
        start_time = time.time()
        
        # Use context manager many times
        for i in range(100):
            with tracker.time_operation("perf_db", "perf_op", i):
                # Simulate very short operation
                pass
        
        context_time = time.time() - start_time
        
        # Should be efficient even with many context managers
        assert context_time < 0.5  # Less than 500ms for 100 context uses
        
        # Verify operations were tracked
        metrics = tracker.get_metrics("perf_db")
        assert "perf_db.perf_op" in metrics
        assert metrics["perf_db.perf_op"]["operation_count"] == 100
    
    @pytest.mark.performance
    def test_get_database_summary_performance(self):
        """Test database summary generation performance."""
        tracker = PerformanceTracker()
        
        # Pre-populate with significant data
        for i in range(200):
            db_name = f"db_{i % 10}"  # 10 databases
            operation = f"op_{i % 5}"  # 5 operations each
            tracker.track_operation(db_name, operation, float(i), True, i)
        
        start_time = time.time()
        
        # Generate summaries multiple times
        for _ in range(50):
            summary = tracker.get_database_summary()
        
        summary_time = time.time() - start_time
        
        # Should generate summaries efficiently
        assert summary_time < 0.5  # Less than 500ms for 50 summaries
        
        # Verify summary structure
        summary = tracker.get_database_summary()
        assert len(summary) == 10  # 10 databases
        for db_summary in summary.values():
            assert "total_operations" in db_summary
            assert "operations" in db_summary


class TestMetricsCollectorPerformance:
    """Test metrics collection system performance."""
    
    @pytest.mark.performance
    def test_counter_increment_performance(self):
        """Test counter increment performance."""
        collector = MetricsCollector()
        
        start_time = time.time()
        
        # Increment counters many times
        for i in range(1000):
            collector.increment_counter(f"counter_{i % 10}", 1)
            if i % 2 == 0:
                collector.increment_counter(f"labeled_counter_{i % 5}", 1, {"env": "test"})
        
        increment_time = time.time() - start_time
        
        # Should increment efficiently
        assert increment_time < 0.5  # Less than 500ms for 1500 increments
        
        # Verify counters
        summary = collector.get_metrics_summary()
        assert len(summary["counters"]) >= 10  # At least 10 basic counters
    
    @pytest.mark.performance
    def test_gauge_set_performance(self):
        """Test gauge set performance."""
        collector = MetricsCollector()
        
        start_time = time.time()
        
        # Set gauges many times
        for i in range(1000):
            collector.set_gauge(f"gauge_{i % 20}", float(i))
        
        gauge_time = time.time() - start_time
        
        # Should set gauges efficiently
        assert gauge_time < 0.3  # Less than 300ms for 1000 sets
        
        # Verify gauges
        summary = collector.get_metrics_summary()
        assert len(summary["gauges"]) == 20  # 20 unique gauges
    
    @pytest.mark.performance
    def test_histogram_record_performance(self):
        """Test histogram recording performance."""
        collector = MetricsCollector()
        
        start_time = time.time()
        
        # Record histogram values many times
        for i in range(500):
            collector.record_histogram(f"histogram_{i % 5}", float(i % 100))
        
        histogram_time = time.time() - start_time
        
        # Should record efficiently
        assert histogram_time < 0.5  # Less than 500ms for 500 recordings
        
        # Verify histograms
        summary = collector.get_metrics_summary()
        assert len(summary["histograms"]) == 5  # 5 unique histograms
    
    @pytest.mark.performance
    def test_metrics_summary_generation_performance(self):
        """Test metrics summary generation performance."""
        collector = MetricsCollector()
        
        # Pre-populate with significant data
        for i in range(100):
            collector.increment_counter(f"counter_{i}", 1)
            collector.set_gauge(f"gauge_{i}", float(i))
            collector.record_histogram(f"histogram_{i % 10}", float(i))
        
        start_time = time.time()
        
        # Generate summaries multiple times
        for _ in range(100):
            summary = collector.get_metrics_summary()
        
        summary_time = time.time() - start_time
        
        # Should generate summaries efficiently
        assert summary_time < 0.5  # Less than 500ms for 100 summaries
        
        # Verify summary structure
        summary = collector.get_metrics_summary()
        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary
        assert len(summary["counters"]) == 100
        assert len(summary["gauges"]) == 100
        assert len(summary["histograms"]) == 10


class TestDatabaseLoggerPerformance:
    """Test database logger performance."""
    
    @pytest.mark.performance
    def test_log_operation_performance(self):
        """Test database operation logging performance."""
        logger = DatabaseLogger("test_db")
        
        start_time = time.time()
        
        # Log many operations
        for i in range(200):
            logger.log_operation(
                operation=f"op_{i % 5}",
                duration_ms=float(i % 100),
                success=i % 10 != 0,
                record_count=i % 50,
                details={"test": f"value_{i}"}
            )
        
        logging_time = time.time() - start_time
        
        # Should log efficiently
        assert logging_time < 1.0  # Less than 1 second for 200 logs
    
    @pytest.mark.performance
    def test_operation_timer_performance(self):
        """Test operation timer context manager performance."""
        logger = DatabaseLogger("test_db")
        
        start_time = time.time()
        
        # Use timer context manager many times
        for i in range(100):
            with logger.operation_timer(f"timed_op_{i % 10}", i):
                # Simulate very short operation
                pass
        
        timer_time = time.time() - start_time
        
        # Should time operations efficiently
        assert timer_time < 0.5  # Less than 500ms for 100 timed operations


class TestHealthCheckerPerformance:
    """Test health checker performance."""
    
    @pytest.fixture
    def health_checker(self):
        """Create health checker instance."""
        return HealthChecker()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_basic_health_check_performance(self, health_checker):
        """Test basic health check performance."""
        start_time = time.time()
        
        # Run health checks multiple times
        for _ in range(20):
            health_status = await health_checker.check_basic_health()
        
        health_check_time = time.time() - start_time
        
        # Should check health efficiently
        assert health_check_time < 2.0  # Less than 2 seconds for 20 checks
        
        # Verify health check structure
        health_status = await health_checker.check_basic_health()
        assert "status" in health_status
        assert "timestamp" in health_status
        assert "uptime_seconds" in health_status
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_health_check_performance(self, health_checker):
        """Test database health check performance."""
        # Mock database adapters for performance testing
        mock_postgresql = AsyncMock()
        mock_postgresql.health_check.return_value = {
            "status": "healthy",
            "response_time_ms": 50,
            "materials_count": 1000
        }
        
        mock_redis = AsyncMock()
        mock_redis.health_check.return_value = {
            "status": "healthy",
            "response_time_ms": 10,
            "total_keys": 500
        }
        
        with patch('core.database.factories.DatabaseFactory.create_relational_database', return_value=mock_postgresql):
            with patch('core.database.factories.DatabaseFactory.create_cache_database', return_value=mock_redis):
                
                start_time = time.time()
                
                # Check database health multiple times
                for _ in range(10):
                    await health_checker.check_postgresql_health()
                    await health_checker.check_redis_health()
                
                db_health_time = time.time() - start_time
                
                # Should check database health efficiently
                assert db_health_time < 1.0  # Less than 1 second for 20 DB checks
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_comprehensive_health_check_performance(self, health_checker):
        """Test comprehensive health check performance."""
        # Mock all external dependencies
        with patch.object(health_checker, 'check_qdrant_health', return_value={"status": "healthy"}):
            with patch.object(health_checker, 'check_postgresql_health', return_value={"status": "healthy"}):
                with patch.object(health_checker, 'check_redis_health', return_value={"status": "healthy"}):
                    with patch.object(health_checker, 'check_openai_health', return_value={"status": "healthy"}):
                        
                        start_time = time.time()
                        
                        # Run comprehensive health checks
                        for _ in range(5):
                            basic_health = await health_checker.check_basic_health()
                            qdrant_health = await health_checker.check_qdrant_health()
                            pg_health = await health_checker.check_postgresql_health()
                            redis_health = await health_checker.check_redis_health()
                            openai_health = await health_checker.check_openai_health()
                        
                        comprehensive_time = time.time() - start_time
                        
                        # Should complete comprehensive checks efficiently
                        assert comprehensive_time < 3.0  # Less than 3 seconds for 5 full checks


class TestMonitoringIntegrationPerformance:
    """Integration performance tests for monitoring system."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_monitoring_system_under_load(self):
        """Test entire monitoring system under load."""
        # Create all monitoring components
        metrics_collector = MetricsCollector()
        performance_tracker = PerformanceTracker()
        db_logger = DatabaseLogger("load_test_db")
        
        start_time = time.time()
        
        # Simulate high load scenario
        for i in range(100):
            # Metrics collection
            metrics_collector.increment_counter("requests", 1)
            metrics_collector.set_gauge("active_connections", i % 50)
            metrics_collector.record_histogram("response_time", float(i % 200))
            
            # Performance tracking
            performance_tracker.track_operation(
                "test_db", "query", float(i % 100), i % 20 != 0, i % 10
            )
            
            # Database logging
            db_logger.log_operation(
                operation="load_test",
                duration_ms=float(i % 50),
                success=i % 15 != 0,
                record_count=i % 25
            )
        
        load_test_time = time.time() - start_time
        
        # Should handle load efficiently
        assert load_test_time < 2.0  # Less than 2 seconds for 300 operations
        
        # Verify all systems captured data
        metrics_summary = metrics_collector.get_metrics_summary()
        assert metrics_summary["counters"]["requests"] == 100
        assert len(metrics_summary["gauges"]) > 0
        assert len(metrics_summary["histograms"]) > 0
        
        perf_metrics = performance_tracker.get_metrics()
        assert "test_db.query" in perf_metrics
        assert perf_metrics["test_db.query"]["operation_count"] == 100 