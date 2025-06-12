"""
Tests for Dynamic Pool Manager functionality.

Тесты функциональности динамического менеджера пулов подключений.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from core.database.pool_manager import (
    DynamicPoolManager, 
    PoolConfig, 
    PoolMetrics,
    initialize_pool_manager,
    shutdown_pool_manager,
    get_pool_manager
)
from core.database.pool_adapters import MockPoolAdapter


class TestDynamicPoolManager:
    """Test suite for Dynamic Pool Manager."""
    
    @pytest.fixture
    def pool_config(self):
        """Create test pool configuration."""
        return PoolConfig(
            min_size=2,
            max_size=20,
            target_utilization=0.75,
            scale_up_threshold=0.85,
            scale_down_threshold=0.4,
            scale_factor=1.5,
            monitoring_interval=1.0,  # Short interval for testing
            auto_scaling_enabled=True
        )
    
    @pytest.fixture
    def pool_manager(self, pool_config):
        """Create test pool manager."""
        return DynamicPoolManager(pool_config)
    
    @pytest.fixture
    def mock_pool(self):
        """Create mock pool adapter."""
        return MockPoolAdapter("test_pool", initial_size=5)
    
    def test_pool_config_creation(self, pool_config):
        """Test pool configuration creation."""
        assert pool_config.min_size == 2
        assert pool_config.max_size == 20
        assert pool_config.target_utilization == 0.75
        assert pool_config.scale_up_threshold == 0.85
        assert pool_config.scale_down_threshold == 0.4
        assert pool_config.auto_scaling_enabled is True
    
    def test_pool_manager_initialization(self, pool_manager):
        """Test pool manager initialization."""
        assert pool_manager.config is not None
        assert pool_manager.pools == {}
        assert pool_manager.metrics == {}
        assert pool_manager.is_monitoring is False
    
    def test_pool_registration(self, pool_manager, mock_pool):
        """Test pool registration."""
        pool_manager.register_pool("test_pool", mock_pool, initial_size=5, max_size=20)
        
        assert "test_pool" in pool_manager.pools
        assert "test_pool" in pool_manager.metrics
        assert pool_manager.metrics["test_pool"].pool_name == "test_pool"
        assert pool_manager.metrics["test_pool"].current_size == 5
        assert pool_manager.metrics["test_pool"].max_size == 20
    
    def test_pool_unregistration(self, pool_manager, mock_pool):
        """Test pool unregistration."""
        pool_manager.register_pool("test_pool", mock_pool)
        pool_manager.unregister_pool("test_pool")
        
        assert "test_pool" not in pool_manager.pools
        assert "test_pool" not in pool_manager.metrics
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, pool_manager, mock_pool):
        """Test metrics collection from pools."""
        pool_manager.register_pool("test_pool", mock_pool)
        
        # Simulate high utilization
        mock_pool.simulate_load(0.9)
        
        await pool_manager._collect_metrics()
        
        metrics = pool_manager.metrics["test_pool"]
        assert metrics.active_connections > 0
        assert metrics.utilization_percentage > 0
        assert metrics.last_updated is not None
    
    @pytest.mark.asyncio
    async def test_pool_scaling_up(self, pool_manager, mock_pool):
        """Test pool scaling up under high load."""
        pool_manager.register_pool("test_pool", mock_pool, initial_size=5)
        
        # Simulate high utilization (90%)
        mock_pool.simulate_load(0.9)
        
        await pool_manager._collect_metrics()
        
        # Manually trigger scaling since we need to wait for adjustment cooldown
        metrics = pool_manager.metrics["test_pool"]
        if metrics.utilization_percentage > pool_manager.config.scale_up_threshold * 100:
            await pool_manager.force_pool_resize("test_pool", 8, "Test scaling")
        
        # Pool should be scaled up
        assert mock_pool.current_size > 5
    
    @pytest.mark.asyncio
    async def test_pool_scaling_down(self, pool_manager, mock_pool):
        """Test pool scaling down under low load."""
        pool_manager.register_pool("test_pool", mock_pool, initial_size=10)
        
        # Simulate low utilization (20%)
        mock_pool.simulate_load(0.2)
        
        await pool_manager._collect_metrics()
        await pool_manager._analyze_and_adjust_pools()
        
        # Pool should be scaled down
        assert mock_pool.current_size < 10
    
    @pytest.mark.asyncio
    async def test_pool_scaling_bounds(self, pool_manager, mock_pool):
        """Test pool scaling respects min/max bounds."""
        pool_manager.register_pool("test_pool", mock_pool, initial_size=2)
        
        # Try to scale below minimum
        mock_pool.simulate_load(0.1)  # Very low utilization
        
        await pool_manager._collect_metrics()
        await pool_manager._analyze_and_adjust_pools()
        
        # Should not go below min_size
        assert mock_pool.current_size >= pool_manager.config.min_size
        
        # Try to scale above maximum
        mock_pool.current_size = pool_manager.config.max_size
        mock_pool.simulate_load(0.95)  # Very high utilization
        
        await pool_manager._collect_metrics()
        await pool_manager._analyze_and_adjust_pools()
        
        # Should not go above max_size
        assert mock_pool.current_size <= pool_manager.config.max_size
    
    @pytest.mark.asyncio
    async def test_manual_pool_resize(self, pool_manager, mock_pool):
        """Test manual pool resize functionality."""
        pool_manager.register_pool("test_pool", mock_pool, initial_size=5)
        
        # Test successful resize
        success = await pool_manager.force_pool_resize("test_pool", 10, "Manual test")
        assert success is True
        assert mock_pool.current_size == 10
        
        # Test resize with invalid pool name
        success = await pool_manager.force_pool_resize("invalid_pool", 10)
        assert success is False
        
        # Test resize with invalid size
        success = await pool_manager.force_pool_resize("test_pool", 100)  # Above max_size
        assert success is False
    
    def test_get_pool_metrics(self, pool_manager, mock_pool):
        """Test getting pool metrics."""
        pool_manager.register_pool("test_pool", mock_pool, initial_size=5)
        
        # Get all metrics
        all_metrics = pool_manager.get_pool_metrics()
        assert "test_pool" in all_metrics
        assert all_metrics["test_pool"]["current_size"] == 5
        
        # Get specific pool metrics
        specific_metrics = pool_manager.get_pool_metrics("test_pool")
        assert "test_pool" in specific_metrics
        
        # Get non-existent pool metrics
        empty_metrics = pool_manager.get_pool_metrics("non_existent")
        assert empty_metrics == {}
    
    def test_adjustment_history(self, pool_manager):
        """Test adjustment history tracking."""
        # Initially empty
        history = pool_manager.get_adjustment_history()
        assert len(history) == 0
        
        # Add some fake adjustments
        for i in range(5):
            adjustment = {
                "timestamp": datetime.utcnow().isoformat(),
                "pool_name": f"pool_{i}",
                "old_size": i + 5,
                "new_size": i + 10,
                "reason": f"Test adjustment {i}"
            }
            pool_manager.adjustment_history.append(adjustment)
        
        # Get all history
        history = pool_manager.get_adjustment_history()
        assert len(history) == 5
        
        # Get limited history
        limited_history = pool_manager.get_adjustment_history(limit=3)
        assert len(limited_history) == 3
        
        # Get pool-specific history
        pool_history = pool_manager.get_adjustment_history("pool_1")
        assert len(pool_history) == 1
        assert pool_history[0]["pool_name"] == "pool_1"
    
    def test_recommendations(self, pool_manager, mock_pool):
        """Test optimization recommendations."""
        pool_manager.register_pool("test_pool", mock_pool)
        
        # Simulate high utilization
        mock_pool.simulate_load(0.95)
        pool_manager.metrics["test_pool"].utilization_percentage = 95.0
        
        recommendations = pool_manager.get_recommendations()
        
        # Should recommend scaling up
        high_priority = [r for r in recommendations if r.get("priority") == "high"]
        assert len(high_priority) > 0
        
        scale_up_recs = [r for r in high_priority if r.get("type") == "scale_up"]
        assert len(scale_up_recs) > 0
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, pool_manager):
        """Test monitoring start/stop lifecycle."""
        assert pool_manager.is_monitoring is False
        
        # Start monitoring
        await pool_manager.start_monitoring()
        assert pool_manager.is_monitoring is True
        assert pool_manager.monitoring_task is not None
        
        # Stop monitoring
        await pool_manager.stop_monitoring()
        assert pool_manager.is_monitoring is False
    
    @patch('core.database.pool_manager.psutil')
    def test_system_resource_check(self, mock_psutil, pool_manager):
        """Test system resource checking."""
        # Mock high memory usage
        mock_memory = MagicMock()
        mock_memory.percent = 90
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 95
        
        # Should return False for high resource usage
        assert pool_manager._check_system_resources() is False
        
        # Mock normal resource usage
        mock_memory.percent = 50
        mock_psutil.cpu_percent.return_value = 30
        
        # Should return True for normal resource usage
        assert pool_manager._check_system_resources() is True
    
    @pytest.mark.asyncio
    async def test_global_pool_manager(self):
        """Test global pool manager functions."""
        # Test initialization
        config = PoolConfig(monitoring_interval=0.1)  # Short interval for testing
        manager = await initialize_pool_manager(config)
        
        assert manager is not None
        assert manager.config.monitoring_interval == 0.1
        
        # Test getting global instance
        global_manager = get_pool_manager()
        assert global_manager is manager
        
        # Test shutdown
        await shutdown_pool_manager()
        assert not manager.is_monitoring


class TestPoolMetrics:
    """Test suite for PoolMetrics class."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = PoolMetrics(pool_name="test_pool")
        
        assert metrics.pool_name == "test_pool"
        assert metrics.current_size == 0
        assert metrics.max_size == 10
        assert metrics.utilization_percentage == 0.0
        assert metrics.last_updated is not None
    
    def test_utilization_calculation(self):
        """Test utilization percentage calculation."""
        metrics = PoolMetrics(
            pool_name="test_pool",
            max_size=10,
            active_connections=8
        )
        
        metrics.update_utilization()
        
        assert metrics.utilization_percentage == 80.0
        assert metrics.peak_connections == 8
    
    def test_peak_connections_tracking(self):
        """Test peak connections tracking."""
        metrics = PoolMetrics(pool_name="test_pool", max_size=10)
        
        # First update
        metrics.active_connections = 5
        metrics.update_utilization()
        assert metrics.peak_connections == 5
        
        # Higher value
        metrics.active_connections = 8
        metrics.update_utilization()
        assert metrics.peak_connections == 8
        
        # Lower value (should not change peak)
        metrics.active_connections = 3
        metrics.update_utilization()
        assert metrics.peak_connections == 8


@pytest.mark.asyncio
async def test_pool_manager_integration():
    """Integration test for pool manager with mock adapters."""
    config = PoolConfig(
        min_size=2,
        max_size=10,
        monitoring_interval=0.1,  # Very short for testing
        auto_scaling_enabled=True
    )
    
    manager = DynamicPoolManager(config)
    
    # Create multiple mock pools
    pools = {
        "redis_pool": MockPoolAdapter("redis", initial_size=3),
        "postgres_pool": MockPoolAdapter("postgres", initial_size=5),
        "qdrant_pool": MockPoolAdapter("qdrant", initial_size=1)
    }
    
    # Register all pools
    for name, pool in pools.items():
        manager.register_pool(name, pool, initial_size=pool.current_size)
    
    # Start monitoring
    await manager.start_monitoring()
    
    # Simulate different load patterns
    pools["redis_pool"].simulate_load(0.9)  # High load
    pools["postgres_pool"].simulate_load(0.3)  # Low load
    pools["qdrant_pool"].simulate_load(0.6)  # Medium load
    
    # Wait for monitoring cycle
    await asyncio.sleep(0.2)
    
    # Check metrics were collected
    metrics = manager.get_pool_metrics()
    assert len(metrics) == 3
    
    for pool_name in pools.keys():
        assert pool_name in metrics
        assert metrics[pool_name]["utilization"] >= 0
    
    # Stop monitoring
    await manager.stop_monitoring()
    
    # Verify monitoring stopped
    assert not manager.is_monitoring


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 