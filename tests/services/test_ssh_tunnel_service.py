"""
Tests for SSH Tunnel Service.

This module tests the SSH tunnel service functionality including configuration,
connection management, and service lifecycle.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import os

from services.ssh_tunnel_service import SSHTunnelService, initialize_tunnel_service, shutdown_tunnel_service
from services.tunnel.tunnel_config import TunnelConfig
from services.tunnel.tunnel_manager import TunnelManager
from services.tunnel.ssh_tunnel import SSHTunnel
from services.tunnel.exceptions import (
    SSHTunnelConnectionError,
    SSHTunnelConfigError,
    SSHTunnelAuthenticationError,
    SSHTunnelKeyError
)


class TestTunnelConfig:
    """Test tunnel configuration validation and creation."""
    
    def test_tunnel_config_creation(self):
        """Test basic tunnel configuration creation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_key_path = f.name
            f.write("dummy key content")
        
        try:
            # Set restrictive permissions
            os.chmod(temp_key_path, 0o600)
            
            config = TunnelConfig(
                enabled=True,
                local_port=5435,
                remote_host="test.example.com",
                remote_user="testuser",
                remote_port=5432,
                key_path=temp_key_path,
                timeout=30
            )
            
            assert config.enabled is True
            assert config.local_port == 5435
            assert config.remote_host == "test.example.com"
            assert config.remote_user == "testuser"
            assert config.remote_port == 5432
            assert config.timeout == 30
            assert "testuser@test.example.com:5432 -> localhost:5435" in config.connection_string
        finally:
            os.unlink(temp_key_path)
    
    def test_tunnel_config_port_validation(self):
        """Test port number validation."""
        # Valid ports
        config = TunnelConfig(local_port=1234, remote_port=5432)
        assert config.local_port == 1234
        assert config.remote_port == 5432
        
        # Invalid ports
        with pytest.raises(SSHTunnelConfigError):
            TunnelConfig(local_port=0)
        
        with pytest.raises(SSHTunnelConfigError):
            TunnelConfig(remote_port=70000)
    
    def test_tunnel_config_host_validation(self):
        """Test host validation."""
        # Valid host
        config = TunnelConfig(remote_host="valid.host.com")
        assert config.remote_host == "valid.host.com"
        
        # Invalid empty host
        with pytest.raises(SSHTunnelConfigError):
            TunnelConfig(remote_host="")
        
        with pytest.raises(SSHTunnelConfigError):
            TunnelConfig(remote_host="   ")
    
    def test_tunnel_config_user_validation(self):
        """Test user validation."""
        # Valid user
        config = TunnelConfig(remote_user="validuser")
        assert config.remote_user == "validuser"
        
        # Invalid empty user
        with pytest.raises(SSHTunnelConfigError):
            TunnelConfig(remote_user="")
        
        with pytest.raises(SSHTunnelConfigError):
            TunnelConfig(remote_user="   ")
    
    def test_tunnel_config_timeout_validation(self):
        """Test timeout values validation."""
        # Valid timeouts
        config = TunnelConfig(timeout=30, retry_delay=5, heartbeat_interval=60)
        assert config.timeout == 30
        assert config.retry_delay == 5
        assert config.heartbeat_interval == 60
        
        # Invalid timeouts
        with pytest.raises(SSHTunnelConfigError):
            TunnelConfig(timeout=0)
        
        with pytest.raises(SSHTunnelConfigError):
            TunnelConfig(retry_delay=-1)
    
    def test_tunnel_config_key_path_expansion(self):
        """Test SSH key path expansion."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_key_path = f.name
            f.write("dummy key content")
        
        try:
            # Set restrictive permissions
            os.chmod(temp_key_path, 0o600)
            
            config = TunnelConfig(key_path=temp_key_path)
            assert config.key_path == temp_key_path
            assert config.expanded_key_path == Path(temp_key_path)
        finally:
            os.unlink(temp_key_path)
    
    @patch('services.tunnel.tunnel_config.Path.exists')
    def test_tunnel_config_key_path_not_exists(self, mock_exists):
        """Test SSH key path validation when file doesn't exist."""
        mock_exists.return_value = False
        
        with pytest.raises(SSHTunnelConfigError, match="SSH key file does not exist"):
            TunnelConfig(key_path="/nonexistent/key")
    
    def test_tunnel_config_dev_profile(self):
        """Test development configuration profile."""
        config = TunnelConfig.create_dev_config()
        
        assert config.enabled is True
        assert config.local_port == 5435
        assert config.remote_host == "31.130.148.200"
        assert config.remote_user == "root"
        assert config.remote_port == 5432
        assert config.auto_restart is True
    
    @patch('services.tunnel.tunnel_config.Path.exists')
    @patch('services.tunnel.tunnel_config.Path.is_file')
    @patch('services.tunnel.tunnel_config.Path.stat')
    def test_tunnel_config_prod_profile(self, mock_stat, mock_is_file, mock_exists):
        """Test production configuration profile."""
        # Mock file validation
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_stat_result = Mock()
        mock_stat_result.st_mode = 0o600  # Proper permissions
        mock_stat.return_value = mock_stat_result
        
        config = TunnelConfig.create_prod_config()
        
        assert config.enabled is False  # Usually disabled in production
        assert config.timeout == 60  # Longer timeout
        assert config.retry_attempts == 5  # More retries
        assert config.heartbeat_interval == 30  # More frequent checks


class TestSSHTunnel:
    """Test SSH tunnel implementation."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock tunnel configuration."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_key_path = f.name
            f.write("dummy key content")
        
        os.chmod(temp_key_path, 0o600)
        
        config = TunnelConfig(
            enabled=True,
            local_port=5435,
            remote_host="test.example.com",
            remote_user="testuser",
            remote_port=5432,
            key_path=temp_key_path,
            timeout=10,
            retry_attempts=2,
            retry_delay=1
        )
        
        yield config
        
        # Cleanup
        try:
            os.unlink(temp_key_path)
        except:
            pass
    
    def test_ssh_tunnel_initialization(self, mock_config):
        """Test SSH tunnel initialization."""
        tunnel = SSHTunnel(mock_config)
        
        assert tunnel.config == mock_config
        assert tunnel.is_connected is False
        assert tunnel.ssh_client is None
        assert tunnel.connection_attempts == 0
    
    @patch('services.tunnel.ssh_tunnel.paramiko.SSHClient')
    @patch('services.tunnel.ssh_tunnel.paramiko.RSAKey.from_private_key_file')
    async def test_ssh_tunnel_connect_success(self, mock_key, mock_ssh_client, mock_config):
        """Test successful SSH tunnel connection."""
        # Setup mocks
        mock_key.return_value = Mock()
        mock_client_instance = Mock()
        mock_ssh_client.return_value = mock_client_instance
        
        tunnel = SSHTunnel(mock_config)
        
        # Mock server socket
        with patch('services.tunnel.ssh_tunnel.socket.socket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            
            # Mock successful connection
            result = await tunnel.connect()
            
            assert result is True
            assert tunnel.is_connected is True
            assert tunnel.connection_attempts == 1
            assert tunnel.successful_connections == 1
            mock_client_instance.connect.assert_called_once()
    
    @patch('services.tunnel.ssh_tunnel.paramiko.SSHClient')
    @patch('services.tunnel.ssh_tunnel.paramiko.RSAKey.from_private_key_file')
    async def test_ssh_tunnel_connect_auth_failure(self, mock_key, mock_ssh_client, mock_config):
        """Test SSH tunnel connection with authentication failure."""
        from paramiko.ssh_exception import AuthenticationException
        
        # Setup mocks
        mock_key.return_value = Mock()
        mock_client_instance = Mock()
        mock_client_instance.connect.side_effect = AuthenticationException("Auth failed")
        mock_ssh_client.return_value = mock_client_instance
        
        tunnel = SSHTunnel(mock_config)
        
        with pytest.raises(SSHTunnelAuthenticationError):
            await tunnel.connect()
        
        assert tunnel.is_connected is False
        assert tunnel.failed_connections == 1
    
    @patch('services.tunnel.ssh_tunnel.paramiko.RSAKey.from_private_key_file')
    async def test_ssh_tunnel_key_not_found(self, mock_key, mock_config):
        """Test SSH tunnel connection with missing key file."""
        mock_key.side_effect = FileNotFoundError("Key not found")
        
        tunnel = SSHTunnel(mock_config)
        
        with pytest.raises(SSHTunnelKeyError):
            await tunnel.connect()
    
    async def test_ssh_tunnel_disconnect(self, mock_config):
        """Test SSH tunnel disconnection."""
        tunnel = SSHTunnel(mock_config)
        tunnel.is_connected = True
        tunnel.ssh_client = Mock()
        tunnel.server_socket = Mock()
        tunnel.tunnel_thread = Mock()
        tunnel.tunnel_thread.is_alive.return_value = False
        
        await tunnel.disconnect()
        
        assert tunnel.is_connected is False
        assert tunnel.ssh_client is None
        assert tunnel.server_socket is None
    
    async def test_ssh_tunnel_health_check_not_connected(self, mock_config):
        """Test health check when tunnel is not connected."""
        tunnel = SSHTunnel(mock_config)
        
        result = await tunnel.health_check()
        
        assert result is False
        assert tunnel.health_check_status is False
    
    def test_ssh_tunnel_get_status(self, mock_config):
        """Test getting tunnel status."""
        tunnel = SSHTunnel(mock_config)
        tunnel.connection_attempts = 3
        tunnel.successful_connections = 2
        tunnel.failed_connections = 1
        
        status = tunnel.get_status()
        
        assert status["connected"] is False
        assert status["statistics"]["connection_attempts"] == 3
        assert status["statistics"]["successful_connections"] == 2
        assert status["statistics"]["failed_connections"] == 1


class TestTunnelManager:
    """Test tunnel manager functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock tunnel configuration."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_key_path = f.name
            f.write("dummy key content")
        
        os.chmod(temp_key_path, 0o600)
        
        config = TunnelConfig(
            enabled=True,
            local_port=5435,
            remote_host="test.example.com",
            remote_user="testuser",
            remote_port=5432,
            key_path=temp_key_path,
            timeout=10,
            retry_attempts=2,
            retry_delay=1
        )
        
        yield config
        
        try:
            os.unlink(temp_key_path)
        except:
            pass
    
    def test_tunnel_manager_initialization(self, mock_config):
        """Test tunnel manager initialization."""
        manager = TunnelManager(mock_config)
        
        assert manager.config == mock_config
        assert manager.is_active is False
        assert manager.tunnel is None
        assert manager.restart_count == 0
    
    @patch('services.tunnel.tunnel_manager.SSHTunnel')
    async def test_tunnel_manager_start_success(self, mock_tunnel_class, mock_config):
        """Test successful tunnel start."""
        # Setup mock tunnel
        mock_tunnel_instance = AsyncMock()
        mock_tunnel_instance.connect.return_value = True
        mock_tunnel_class.return_value = mock_tunnel_instance
        
        manager = TunnelManager(mock_config)
        
        result = await manager.start_tunnel()
        
        assert result is True
        assert manager.is_active is True
        assert manager.tunnel == mock_tunnel_instance
        mock_tunnel_instance.connect.assert_called_once()
    
    @patch('services.tunnel.tunnel_manager.SSHTunnel')
    async def test_tunnel_manager_start_with_retries(self, mock_tunnel_class, mock_config):
        """Test tunnel start with retries."""
        # Setup mock tunnel that fails then succeeds
        mock_tunnel_instance = AsyncMock()
        mock_tunnel_instance.connect.side_effect = [
            SSHTunnelConnectionError("Connection failed", "test.example.com", 22),
            True
        ]
        mock_tunnel_class.return_value = mock_tunnel_instance
        
        manager = TunnelManager(mock_config)
        
        result = await manager.start_tunnel()
        
        assert result is True
        assert manager.is_active is True
        assert mock_tunnel_instance.connect.call_count == 2
    
    @patch('services.tunnel.tunnel_manager.SSHTunnel')
    async def test_tunnel_manager_start_all_retries_failed(self, mock_tunnel_class, mock_config):
        """Test tunnel start when all retries fail."""
        # Setup mock tunnel that always fails
        mock_tunnel_instance = AsyncMock()
        mock_tunnel_instance.connect.side_effect = SSHTunnelConnectionError(
            "Connection failed", "test.example.com", 22
        )
        mock_tunnel_instance.disconnect = AsyncMock()
        mock_tunnel_class.return_value = mock_tunnel_instance
        
        manager = TunnelManager(mock_config)
        
        result = await manager.start_tunnel()
        
        assert result is False
        assert manager.is_active is False
        assert mock_tunnel_instance.connect.call_count == mock_config.retry_attempts
    
    async def test_tunnel_manager_stop(self, mock_config):
        """Test tunnel stop."""
        manager = TunnelManager(mock_config)
        manager.is_active = True
        manager.tunnel = AsyncMock()
        manager.last_start_time = 1000.0
        
        with patch('time.time', return_value=1060.0):  # 60 seconds later
            await manager.stop_tunnel()
        
        assert manager.is_active is False
        assert manager.total_uptime == 60.0
        manager.tunnel.disconnect.assert_called_once()
    
    @patch('services.tunnel.tunnel_manager.SSHTunnel')
    async def test_tunnel_manager_restart(self, mock_tunnel_class, mock_config):
        """Test tunnel restart."""
        mock_tunnel_instance = AsyncMock()
        mock_tunnel_instance.connect.return_value = True
        mock_tunnel_class.return_value = mock_tunnel_instance
        
        manager = TunnelManager(mock_config)
        manager.is_active = True
        manager.tunnel = AsyncMock()
        
        result = await manager.restart_tunnel()
        
        assert result is True
        assert manager.restart_count == 1
    
    async def test_tunnel_manager_health_check_no_tunnel(self, mock_config):
        """Test health check when no tunnel is active."""
        manager = TunnelManager(mock_config)
        
        result = await manager.health_check()
        
        assert result is False
        assert manager.health_check_failures == 1
        assert manager.last_health_status is False
    
    async def test_tunnel_manager_health_check_success(self, mock_config):
        """Test successful health check."""
        manager = TunnelManager(mock_config)
        manager.is_active = True
        manager.tunnel = AsyncMock()
        manager.tunnel.health_check.return_value = True
        
        result = await manager.health_check()
        
        assert result is True
        assert manager.last_health_status is True
        manager.tunnel.health_check.assert_called_once()
    
    def test_tunnel_manager_get_status(self, mock_config):
        """Test getting manager status."""
        manager = TunnelManager(mock_config)
        manager.restart_count = 2
        manager.health_check_count = 10
        manager.health_check_failures = 1
        
        status = manager.get_status()
        
        assert status["active"] is False
        assert status["restart_count"] == 2
        assert status["health_monitoring"]["total_checks"] == 10
        assert status["health_monitoring"]["total_failures"] == 1
        assert status["health_monitoring"]["success_rate"] == 0.9


class TestSSHTunnelService:
    """Test SSH tunnel service."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock tunnel configuration."""
        return TunnelConfig(
            enabled=True,
            local_port=5435,
            remote_host="test.example.com",
            remote_user="testuser",
            remote_port=5432,
            key_path="/tmp/test_key",
            timeout=10,
            heartbeat_interval=5,
            auto_restart=True
        )
    
    def test_ssh_tunnel_service_initialization(self, mock_config):
        """Test service initialization."""
        service = SSHTunnelService(mock_config)
        
        assert service.config == mock_config
        assert service.is_running is False
        assert service.tunnel_manager is None
        assert service.monitoring_task is None
    
    def test_ssh_tunnel_service_disabled(self):
        """Test service with disabled configuration."""
        config = TunnelConfig(enabled=False)
        service = SSHTunnelService(config)
        
        assert service.config.enabled is False
    
    @patch('services.ssh_tunnel_service.TunnelManager')
    async def test_ssh_tunnel_service_start_success(self, mock_manager_class, mock_config):
        """Test successful service start."""
        # Setup mock manager
        mock_manager_instance = AsyncMock()
        mock_manager_instance.start_tunnel.return_value = True
        mock_manager_class.return_value = mock_manager_instance
        
        service = SSHTunnelService(mock_config)
        
        result = await service.start_service()
        
        assert result is True
        assert service.is_running is True
        assert service.tunnel_manager == mock_manager_instance
        assert service.monitoring_task is not None
        mock_manager_instance.start_tunnel.assert_called_once()
    
    @patch('services.ssh_tunnel_service.TunnelManager')
    async def test_ssh_tunnel_service_start_failure(self, mock_manager_class, mock_config):
        """Test service start failure."""
        # Setup mock manager that fails to start
        mock_manager_instance = AsyncMock()
        mock_manager_instance.start_tunnel.return_value = False
        mock_manager_class.return_value = mock_manager_instance
        
        service = SSHTunnelService(mock_config)
        
        result = await service.start_service()
        
        assert result is False
        assert service.is_running is False
    
    async def test_ssh_tunnel_service_start_disabled(self):
        """Test service start when disabled."""
        config = TunnelConfig(enabled=False)
        service = SSHTunnelService(config)
        
        result = await service.start_service()
        
        assert result is False
        assert service.is_running is False
    
    async def test_ssh_tunnel_service_stop(self, mock_config):
        """Test service stop."""
        service = SSHTunnelService(mock_config)
        service.is_running = True
        service.monitoring_task = AsyncMock()
        service.tunnel_manager = AsyncMock()
        
        await service.stop_service()
        
        assert service.is_running is False
        assert service.monitoring_task is None
        assert service.tunnel_manager is None
    
    @patch('services.ssh_tunnel_service.TunnelManager')
    async def test_ssh_tunnel_service_restart(self, mock_manager_class, mock_config):
        """Test service restart."""
        mock_manager_instance = AsyncMock()
        mock_manager_instance.start_tunnel.return_value = True
        mock_manager_class.return_value = mock_manager_instance
        
        service = SSHTunnelService(mock_config)
        service.is_running = True
        service.tunnel_manager = AsyncMock()
        
        result = await service.restart_service()
        
        assert result is True
    
    def test_ssh_tunnel_service_get_status(self, mock_config):
        """Test getting service status."""
        service = SSHTunnelService(mock_config)
        service.is_running = True
        service.tunnel_manager = Mock()
        service.tunnel_manager.get_status.return_value = {"active": True}
        
        status = service.get_status()
        
        assert status["service_running"] is True
        assert status["config_enabled"] is True
        assert status["tunnel_manager"]["active"] is True
    
    def test_ssh_tunnel_service_is_tunnel_active_no_manager(self, mock_config):
        """Test tunnel active check when no manager."""
        service = SSHTunnelService(mock_config)
        
        result = service.is_tunnel_active()
        
        assert result is False
    
    def test_ssh_tunnel_service_is_tunnel_active_with_manager(self, mock_config):
        """Test tunnel active check with manager."""
        service = SSHTunnelService(mock_config)
        service.is_running = True
        service.tunnel_manager = Mock()
        service.tunnel_manager.is_tunnel_active.return_value = True
        
        result = service.is_tunnel_active()
        
        assert result is True


@pytest.mark.asyncio
class TestServiceGlobalFunctions:
    """Test global service functions."""
    
    @patch('services.ssh_tunnel_service.get_settings')
    async def test_initialize_tunnel_service_disabled(self, mock_get_settings):
        """Test initialize when service is disabled."""
        mock_settings = Mock()
        mock_settings.ENABLE_SSH_TUNNEL = False
        mock_get_settings.return_value = mock_settings
        
        result = await initialize_tunnel_service()
        
        assert result is None
    
    @patch('services.ssh_tunnel_service.get_settings')
    @patch('services.ssh_tunnel_service.SSHTunnelService')
    async def test_initialize_tunnel_service_success(self, mock_service_class, mock_get_settings):
        """Test successful service initialization."""
        mock_settings = Mock()
        mock_settings.ENABLE_SSH_TUNNEL = True
        mock_get_settings.return_value = mock_settings
        
        mock_service_instance = AsyncMock()
        mock_service_instance.start_service.return_value = True
        mock_service_class.return_value = mock_service_instance
        
        result = await initialize_tunnel_service()
        
        assert result == mock_service_instance
        mock_service_instance.start_service.assert_called_once()
    
    @patch('services.ssh_tunnel_service._tunnel_service', None)
    async def test_shutdown_tunnel_service_no_service(self):
        """Test shutdown when no service is running."""
        # Should not raise any exceptions
        await shutdown_tunnel_service()
    
    @patch('services.ssh_tunnel_service._tunnel_service')
    async def test_shutdown_tunnel_service_with_service(self, mock_service):
        """Test shutdown with active service."""
        mock_service.stop_service = AsyncMock()
        
        await shutdown_tunnel_service()
        
        mock_service.stop_service.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 