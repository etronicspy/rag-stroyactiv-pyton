"""
SSH Tunnel implementation for RAG Construction Materials API.

This module provides the core SSH tunnel functionality using paramiko.
"""

import asyncio
import logging
import socket
import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path

import paramiko
from paramiko import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import SSHException, AuthenticationException

from .tunnel_config import TunnelConfig
from .exceptions import (
    SSHTunnelError,
    SSHTunnelConnectionError,
    SSHTunnelTimeoutError,
    SSHTunnelAuthenticationError,
    SSHTunnelKeyError
)

logger = logging.getLogger(__name__)


class SSHTunnel:
    """SSH Tunnel implementation for secure database connections.
    
    This class creates and manages SSH tunnels for connecting to remote databases.
    It supports automatic reconnection, health checks, and monitoring.
    """
    
    def __init__(self, config: TunnelConfig):
        """Initialize SSH tunnel with configuration.
        
        Args:
            config: TunnelConfig instance with connection parameters
        """
        self.config = config
        self.ssh_client: Optional[SSHClient] = None
        self.tunnel_thread: Optional[threading.Thread] = None
        self.server_socket: Optional[socket.socket] = None
        self.is_connected: bool = False
        self.should_stop: bool = False
        self.connection_start_time: Optional[float] = None
        self.last_health_check: Optional[float] = None
        self.health_check_status: bool = False
        
        # Connection statistics
        self.connection_attempts = 0
        self.successful_connections = 0
        self.failed_connections = 0
        self.total_bytes_transferred = 0
        
        logger.info(f"SSH Tunnel initialized: {self.config.connection_string}")
    
    async def connect(self) -> bool:
        """Establish SSH tunnel connection.
        
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            SSHTunnelError: For various connection failures
        """
        try:
            logger.info(f"Attempting to establish SSH tunnel: {self.config.connection_string}")
            self.connection_attempts += 1
            
            # Create SSH client
            self.ssh_client = SSHClient()
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            
            # Load private key
            try:
                private_key = paramiko.RSAKey.from_private_key_file(self.config.key_path)
            except FileNotFoundError:
                raise SSHTunnelKeyError(
                    f"SSH private key not found: {self.config.key_path}",
                    key_path=self.config.key_path
                )
            except paramiko.PasswordRequiredException:
                raise SSHTunnelKeyError(
                    f"SSH private key requires password: {self.config.key_path}",
                    key_path=self.config.key_path
                )
            except Exception as e:
                raise SSHTunnelKeyError(
                    f"Cannot load SSH private key: {e}",
                    key_path=self.config.key_path
                )
            
            # Connect to SSH server
            try:
                self.ssh_client.connect(
                    hostname=self.config.remote_host,
                    username=self.config.remote_user,
                    pkey=private_key,
                    timeout=self.config.timeout,
                    banner_timeout=self.config.timeout
                )
            except AuthenticationException:
                raise SSHTunnelAuthenticationError(
                    f"SSH authentication failed for user {self.config.remote_user}",
                    username=self.config.remote_user
                )
            except socket.timeout:
                raise SSHTunnelTimeoutError(
                    f"SSH connection timeout after {self.config.timeout} seconds",
                    timeout=self.config.timeout
                )
            except socket.gaierror as e:
                raise SSHTunnelConnectionError(
                    f"Cannot resolve hostname {self.config.remote_host}: {e}",
                    host=self.config.remote_host,
                    port=self.config.remote_port
                )
            except Exception as e:
                raise SSHTunnelConnectionError(
                    f"SSH connection failed: {e}",
                    host=self.config.remote_host,
                    port=self.config.remote_port
                )
            
            # Start tunnel server
            await self._start_tunnel_server()
            
            self.is_connected = True
            self.connection_start_time = time.time()
            self.successful_connections += 1
            
            logger.info(f"SSH tunnel established successfully: {self.config.connection_string}")
            return True
            
        except Exception as e:
            self.failed_connections += 1
            logger.error(f"Failed to establish SSH tunnel: {e}")
            await self.disconnect()
            raise
    
    async def disconnect(self) -> None:
        """Disconnect SSH tunnel and cleanup resources."""
        logger.info("Disconnecting SSH tunnel")
        
        self.should_stop = True
        self.is_connected = False
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.warning(f"Error closing server socket: {e}")
            self.server_socket = None
        
        # Wait for tunnel thread to finish
        if self.tunnel_thread and self.tunnel_thread.is_alive():
            self.tunnel_thread.join(timeout=5)
            if self.tunnel_thread.is_alive():
                logger.warning("Tunnel thread did not stop gracefully")
        
        # Close SSH connection
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except Exception as e:
                logger.warning(f"Error closing SSH client: {e}")
            self.ssh_client = None
        
        logger.info("SSH tunnel disconnected")
    
    async def _start_tunnel_server(self) -> None:
        """Start the tunnel server in a separate thread."""
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('localhost', self.config.local_port))
            self.server_socket.listen(1)
        except socket.error as e:
            raise SSHTunnelConnectionError(
                f"Cannot bind to local port {self.config.local_port}: {e}",
                host="localhost",
                port=self.config.local_port
            )
        
        # Start tunnel thread
        self.should_stop = False
        self.tunnel_thread = threading.Thread(
            target=self._tunnel_worker,
            name=f"SSH-Tunnel-{self.config.local_port}",
            daemon=True
        )
        self.tunnel_thread.start()
        
        # Wait a bit to ensure tunnel is ready
        await asyncio.sleep(0.1)
    
    def _tunnel_worker(self) -> None:
        """Worker thread for handling tunnel connections."""
        logger.info(f"Tunnel worker started, listening on localhost:{self.config.local_port}")
        
        while not self.should_stop:
            try:
                self.server_socket.settimeout(1.0)  # Non-blocking accept
                client_socket, client_addr = self.server_socket.accept()
                
                if self.should_stop:
                    client_socket.close()
                    break
                
                logger.debug(f"New tunnel connection from {client_addr}")
                
                # Handle connection in separate thread
                connection_thread = threading.Thread(
                    target=self._handle_tunnel_connection,
                    args=(client_socket,),
                    daemon=True
                )
                connection_thread.start()
                
            except socket.timeout:
                continue  # Check should_stop flag
            except Exception as e:
                if not self.should_stop:
                    logger.error(f"Error in tunnel worker: {e}")
                break
        
        logger.info("Tunnel worker stopped")
    
    def _handle_tunnel_connection(self, client_socket: socket.socket) -> None:
        """Handle individual tunnel connection."""
        try:
            # Create SSH channel
            ssh_transport = self.ssh_client.get_transport()
            ssh_channel = ssh_transport.open_channel(
                'direct-tcpip',
                (self.config.remote_host, self.config.remote_port),
                client_socket.getpeername()
            )
            
            # Relay data between client and SSH channel
            self._relay_data(client_socket, ssh_channel)
            
        except Exception as e:
            logger.error(f"Error handling tunnel connection: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _relay_data(self, client_socket: socket.socket, ssh_channel) -> None:
        """Relay data between client socket and SSH channel."""
        import select
        
        try:
            while True:
                # Use select to handle bidirectional data flow
                ready_sockets, _, error_sockets = select.select(
                    [client_socket, ssh_channel], [], [client_socket, ssh_channel], 1.0
                )
                
                if error_sockets or self.should_stop:
                    break
                
                for sock in ready_sockets:
                    try:
                        if sock is client_socket:
                            data = client_socket.recv(4096)
                            if not data:
                                return
                            ssh_channel.send(data)
                            self.total_bytes_transferred += len(data)
                        elif sock is ssh_channel:
                            data = ssh_channel.recv(4096)
                            if not data:
                                return
                            client_socket.send(data)
                            self.total_bytes_transferred += len(data)
                    except Exception as e:
                        logger.debug(f"Data relay error: {e}")
                        return
                        
        except Exception as e:
            logger.error(f"Error in data relay: {e}")
        finally:
            try:
                ssh_channel.close()
            except:
                pass
    
    async def health_check(self) -> bool:
        """Perform health check on SSH tunnel.
        
        Returns:
            True if tunnel is healthy, False otherwise
        """
        try:
            if not self.is_connected or not self.ssh_client:
                self.health_check_status = False
                return False
            
            # Check SSH transport
            transport = self.ssh_client.get_transport()
            if not transport or not transport.is_active():
                self.health_check_status = False
                return False
            
            # Test local port connectivity
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            try:
                result = test_socket.connect_ex(('localhost', self.config.local_port))
                if result != 0:
                    self.health_check_status = False
                    return False
            finally:
                test_socket.close()
            
            self.health_check_status = True
            self.last_health_check = time.time()
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self.health_check_status = False
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current tunnel status and statistics.
        
        Returns:
            Dictionary with tunnel status information
        """
        uptime = None
        if self.connection_start_time:
            uptime = time.time() - self.connection_start_time
        
        return {
            "connected": self.is_connected,
            "config": self.config.connection_string,
            "uptime_seconds": uptime,
            "last_health_check": self.last_health_check,
            "health_status": self.health_check_status,
            "statistics": {
                "connection_attempts": self.connection_attempts,
                "successful_connections": self.successful_connections,
                "failed_connections": self.failed_connections,
                "total_bytes_transferred": self.total_bytes_transferred
            }
        }
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.is_connected:
            try:
                # Use asyncio.create_task if we're in an async context
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.disconnect())
                    else:
                        loop.run_until_complete(self.disconnect())
                except RuntimeError:
                    # Not in async context, do sync cleanup
                    self.should_stop = True
                    if self.server_socket:
                        self.server_socket.close()
                    if self.ssh_client:
                        self.ssh_client.close()
            except Exception:
                pass  # Ignore cleanup errors in destructor 