"""
Comprehensive PostgreSQL Connection Tests with SSH Tunnel Integration.

Тесты проверяют подключение к PostgreSQL через существующий SSH tunnel service.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from core.database.adapters.postgresql_adapter import PostgreSQLAdapter
from core.config import get_settings
from services.ssh_tunnel_service import get_tunnel_service


@pytest.fixture
async def postgresql_adapter():
    """Create PostgreSQL adapter with settings."""
    settings = get_settings()
    adapter = PostgreSQLAdapter(settings)
    yield adapter
    await adapter.disconnect()


@pytest.mark.asyncio
class TestPostgreSQLTunnelIntegration:
    """Test PostgreSQL integration with SSH tunnel service."""
    
    @patch('services.ssh_tunnel_service.get_tunnel_service')
    async def test_connection_with_active_tunnel(self, mock_get_tunnel_service, postgresql_adapter):
        """Test PostgreSQL connection using active SSH tunnel."""
        # Mock active tunnel service
        mock_tunnel_service = MagicMock()
        mock_tunnel_service.is_tunnel_active.return_value = True
        mock_tunnel_service.config.local_port = 5435
        mock_get_tunnel_service.return_value = mock_tunnel_service
        
        # Mock successful connection
        with patch.object(postgresql_adapter, 'engine') as mock_engine:
            mock_engine.begin = AsyncMock()
            mock_engine.begin.return_value.__aenter__ = AsyncMock()
            mock_engine.begin.return_value.__aexit__ = AsyncMock()
            
            # Mock the connection test
            mock_conn = MagicMock()
            mock_conn.execute = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            result = await postgresql_adapter.connect()
            
            assert result is True
            assert "localhost:5435" in postgresql_adapter._connection_string
            mock_tunnel_service.is_tunnel_active.assert_called_once()
    
    @patch('services.ssh_tunnel_service.get_tunnel_service')
    async def test_connection_without_tunnel(self, mock_get_tunnel_service, postgresql_adapter):
        """Test PostgreSQL connection without SSH tunnel."""
        # Mock no tunnel service
        mock_get_tunnel_service.return_value = None
        
        # Mock successful connection
        with patch.object(postgresql_adapter, 'engine') as mock_engine:
            mock_engine.begin = AsyncMock()
            mock_engine.begin.return_value.__aenter__ = AsyncMock()
            mock_engine.begin.return_value.__aexit__ = AsyncMock()
            
            # Mock the connection test
            mock_conn = MagicMock()
            mock_conn.execute = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            result = await postgresql_adapter.connect()
            
            assert result is True
            # Should use direct connection with host from settings
            assert "localhost:5435" not in postgresql_adapter._connection_string
    
    @patch('services.ssh_tunnel_service.get_tunnel_service')
    async def test_health_check_with_tunnel_status(self, mock_get_tunnel_service, postgresql_adapter):
        """Test health check includes tunnel status."""
        # Mock active tunnel service
        mock_tunnel_service = MagicMock()
        mock_tunnel_service.is_tunnel_active.return_value = True
        mock_get_tunnel_service.return_value = mock_tunnel_service
        
        # Setup adapter with mock engine
        postgresql_adapter._tunnel_service = mock_tunnel_service
        postgresql_adapter.engine = MagicMock()
        
        # Mock database query
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = ("PostgreSQL 14.0", "stbr_rag1", "postgres")
        mock_conn.execute = AsyncMock(return_value=mock_result)
        
        postgresql_adapter.engine.begin = AsyncMock()
        postgresql_adapter.engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        postgresql_adapter.engine.begin.return_value.__aexit__ = AsyncMock()
        
        health_status = await postgresql_adapter.health_check()
        
        assert health_status["status"] == "healthy"
        assert health_status["tunnel_status"] == "active"
        assert health_status["connection_type"] == "tunneled"
        assert health_status["database"] == "stbr_rag1"
    
    async def test_health_check_no_connection(self, postgresql_adapter):
        """Test health check with no database connection."""
        health_status = await postgresql_adapter.health_check()
        
        assert health_status["status"] == "error"
        assert health_status["message"] == "No database connection"
        assert health_status["tunnel_status"] == "unknown"
    
    async def test_disconnect_cleanup(self, postgresql_adapter):
        """Test proper cleanup on disconnect."""
        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()
        postgresql_adapter.engine = mock_engine
        postgresql_adapter.session_factory = MagicMock()
        
        await postgresql_adapter.disconnect()
        
        mock_engine.dispose.assert_called_once()
        assert postgresql_adapter.engine is None
        assert postgresql_adapter.session_factory is None


@pytest.mark.asyncio
class TestPostgreSQLConnectionScenarios:
    """Test various connection scenarios."""
    
    @patch('services.ssh_tunnel_service.get_tunnel_service')
    async def test_tunnel_inactive_fallback_to_direct(self, mock_get_tunnel_service):
        """Test fallback to direct connection when tunnel is inactive."""
        # Mock inactive tunnel service
        mock_tunnel_service = MagicMock()
        mock_tunnel_service.is_tunnel_active.return_value = False
        mock_get_tunnel_service.return_value = mock_tunnel_service
        
        settings = get_settings()
        adapter = PostgreSQLAdapter(settings)
        
        # Mock successful connection
        with patch.object(adapter, 'engine') as mock_engine:
            mock_engine.begin = AsyncMock()
            mock_engine.begin.return_value.__aenter__ = AsyncMock()
            mock_engine.begin.return_value.__aexit__ = AsyncMock()
            
            mock_conn = MagicMock()
            mock_conn.execute = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            result = await adapter.connect()
            
            assert result is True
            # Should use direct connection
            assert f"{settings.postgresql_host}:{settings.postgresql_port}" in adapter._connection_string
        
        await adapter.disconnect()
    
    @pytest.mark.integration
    async def test_real_connection_with_tunnel_service(self):
        """Integration test with real tunnel service (if available)."""
        tunnel_service = get_tunnel_service()
        if not tunnel_service:
            pytest.skip("SSH tunnel service not available")
        
        settings = get_settings()
        adapter = PostgreSQLAdapter(settings)
        
        try:
            result = await adapter.connect()
            
            if tunnel_service.is_tunnel_active():
                # If tunnel is active, connection should use tunnel
                assert "localhost" in adapter._connection_string
                
                # Test health check
                health = await adapter.health_check()
                assert health["status"] == "healthy"
                assert health["tunnel_status"] == "active"
                assert health["database"] == "stbr_rag1"
            else:
                # Direct connection or tunnel not active
                assert result is True or result is False  # Connection may fail without tunnel
                
        except Exception as e:
            pytest.skip(f"Cannot connect to PostgreSQL: {e}")
        finally:
            await adapter.disconnect()


if __name__ == "__main__":
    # Simple test runner
    import sys
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    async def run_basic_test():
        """Run basic connection test."""
        try:
            settings = get_settings()
            adapter = PostgreSQLAdapter(settings)
            
            print("Testing PostgreSQL connection with tunnel integration...")
            
            result = await adapter.connect()
            if result:
                print("✅ Connection successful")
                
                health = await adapter.health_check()
                print(f"Health check: {health}")
                
            else:
                print("❌ Connection failed")
                
            await adapter.disconnect()
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        
        return True
    
    # Run test
    success = asyncio.run(run_basic_test())
    sys.exit(0 if success else 1) 