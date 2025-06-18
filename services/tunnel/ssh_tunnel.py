"""
SSH Tunnel implementation for secure database connections.

Updated to use proven sshtunnel library based on internet research.
"""

from core.monitoring.logger import get_logger
import time
import threading
from typing import Optional, Dict, Any
from pathlib import Path

from sshtunnel import SSHTunnelForwarder
import paramiko

from .tunnel_config import TunnelConfig
from .exceptions import SSHTunnelError, SSHTunnelKeyError, SSHTunnelConnectionError

logger = get_logger(__name__)


class SSHTunnel:
    """
    SSH Tunnel implementation using sshtunnel library.
    
    This implementation uses the battle-tested sshtunnel library
    instead of custom paramiko code for better reliability.
    """
    
    def __init__(self, config: TunnelConfig):
        """Initialize SSH tunnel with sshtunnel library."""
        self.config = config
        self.tunnel_forwarder: Optional[SSHTunnelForwarder] = None
        self.is_connected = False
        self._connection_start_time = None
        self._statistics = {
            "connection_attempts": 0,
            "successful_connections": 0,
            "failed_connections": 0,
            "total_bytes_transferred": 0
        }
        
        logger.info(f"SSH Tunnel (sshtunnel) initialized: {self.config.connection_string}")
    
    def _load_ssh_key(self) -> paramiko.PKey:
        """Load SSH private key with support for multiple formats (OpenSSH, RSA, Ed25519, etc.)."""
        key_path = Path(self.config.key_path).expanduser()
        
        if not key_path.exists():
            raise SSHTunnelKeyError(
                f"SSH private key not found: {key_path}",
                key_path=str(key_path)
            )
        
        # Try different key formats
        key_loaders = [
            paramiko.RSAKey.from_private_key_file,
            paramiko.Ed25519Key.from_private_key_file,  # OpenSSH support
            paramiko.ECDSAKey.from_private_key_file,
            paramiko.DSSKey.from_private_key_file,
        ]
        
        last_error = None
        for loader in key_loaders:
            try:
                if self.config.key_passphrase:
                    return loader(str(key_path), password=self.config.key_passphrase)
                else:
                    return loader(str(key_path))
            except paramiko.PasswordRequiredException:
                if not self.config.key_passphrase:
                    raise SSHTunnelKeyError(
                        f"SSH private key requires password but no passphrase configured: {key_path}",
                        key_path=str(key_path)
                    )
                try:
                    return loader(str(key_path), password=self.config.key_passphrase)
                except Exception as passphrase_error:
                    last_error = passphrase_error
                    continue
            except Exception as e:
                last_error = e
                continue
        
        raise SSHTunnelKeyError(
            f"Cannot load SSH private key with any supported format: {last_error}",
            key_path=str(key_path)
        )
    
    async def connect(self) -> bool:
        """Establish SSH tunnel connection using sshtunnel library."""
        if self.is_connected:
            logger.warning("SSH tunnel already connected")
            return True
        
        self._statistics["connection_attempts"] += 1
        
        try:
            logger.info(f"Attempting to establish SSH tunnel: {self.config.connection_string}")
            
            # Load SSH private key
            ssh_key = self._load_ssh_key()
            logger.info("SSH private key loaded successfully")
            
            # Create SSHTunnelForwarder
            self.tunnel_forwarder = SSHTunnelForwarder(
                (self.config.remote_host, 22),
                ssh_username=self.config.remote_user,
                ssh_pkey=ssh_key,
                remote_bind_address=("localhost", self.config.remote_port),
                local_bind_address=("localhost", self.config.local_port)
            )
            
            # Start the tunnel
            self.tunnel_forwarder.start()
            
            self.is_connected = True
            self._connection_start_time = time.time()
            self._statistics["successful_connections"] += 1
            
            logger.info(f"SSH tunnel established successfully: {self.config.connection_string}")
            return True
            
        except Exception as e:
            self._statistics["failed_connections"] += 1
            self.is_connected = False
            
            # Clean up on failure
            if self.tunnel_forwarder:
                try:
                    self.tunnel_forwarder.stop()
                except:
                    pass
                self.tunnel_forwarder = None
            
            logger.error(f"Failed to establish SSH tunnel: {e}")
            raise SSHTunnelConnectionError(f"SSH tunnel connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect SSH tunnel."""
        if not self.is_connected:
            return
        
        try:
            if self.tunnel_forwarder:
                self.tunnel_forwarder.stop()
                self.tunnel_forwarder = None
            
            self.is_connected = False
            self._connection_start_time = None
            
            logger.info("SSH tunnel disconnected successfully")
            
        except Exception as e:
            logger.error(f"Error during SSH tunnel disconnect: {e}")
            raise SSHTunnelError(f"Failed to disconnect SSH tunnel: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get tunnel status and statistics."""
        uptime = 0
        if self.is_connected and self._connection_start_time:
            uptime = time.time() - self._connection_start_time
        
        return {
            "connected": self.is_connected,
            "config": self.config.connection_string,
            "uptime_seconds": uptime,
            "last_health_check": None,
            "health_status": self.is_connected,
            "statistics": self._statistics.copy()
        }
    
    async def health_check(self) -> bool:
        """Perform health check of SSH tunnel."""
        if not self.is_connected or not self.tunnel_forwarder:
            return False
        
        try:
            return self.tunnel_forwarder.is_alive
        except Exception as e:
            logger.warning(f"SSH tunnel health check failed: {e}")
            return False 