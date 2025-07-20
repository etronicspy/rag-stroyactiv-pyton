"""
SSH Tunnel Configuration Module

This module provides configuration management for SSH tunnel connections,
including connection settings, retry logic, and security parameters.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


def get_env_int(key: str, default: int) -> int:
    """Get integer value from environment variable."""
    return int(os.getenv(key, str(default)))


def get_env_str(key: str, default: str) -> str:
    """Get string value from environment variable."""
    return os.getenv(key, default)


class SSHDefaults:
    """SSH tunnel default configuration."""
    REMOTE_HOST = get_env_str("SSH_DEFAULT_REMOTE_HOST", "31.130.148.200")
    REMOTE_USER = get_env_str("SSH_DEFAULT_REMOTE_USER", "root")
    KEY_PATH = get_env_str("SSH_DEFAULT_KEY_PATH", "~/.ssh/postgres_key")
    RETRY_ATTEMPTS = get_env_int("SSH_DEFAULT_RETRY_ATTEMPTS", 3)
    RETRY_DELAY = get_env_int("SSH_DEFAULT_RETRY_DELAY", 5)
    KEEP_ALIVE = get_env_int("SSH_DEFAULT_KEEP_ALIVE", 60)


class DefaultPorts:
    """Default port numbers for various services."""
    POSTGRESQL = get_env_int("DEFAULT_PORT_POSTGRESQL", 5432)
    REDIS = get_env_int("DEFAULT_PORT_REDIS", 6379)
    SSH_TUNNEL_LOCAL = get_env_int("DEFAULT_PORT_SSH_TUNNEL_LOCAL", 5435)


class DefaultTimeouts:
    """Default timeout values for various operations."""
    DATABASE = get_env_int("DEFAULT_TIMEOUT_DATABASE", 30)
    AI_CLIENT = get_env_int("DEFAULT_TIMEOUT_AI_CLIENT", 30)
    CONNECTION_POOL = get_env_int("DEFAULT_TIMEOUT_CONNECTION_POOL", 30)
    REDIS = get_env_int("DEFAULT_TIMEOUT_REDIS", 10)
    SSH_TUNNEL = get_env_int("DEFAULT_TIMEOUT_SSH_TUNNEL", 30)


class TunnelConfig(BaseModel):
    """Configuration for SSH tunnel connection.
    
    This class handles configuration validation and provides 
    configuration for different environments (dev, staging, prod).
    """
    
    # Connection settings
    local_port: int = Field(default=DefaultPorts.SSH_TUNNEL_LOCAL, description="Local port for SSH tunnel")
    remote_host: str = Field(default=SSHDefaults.REMOTE_HOST, description="Remote host for SSH tunnel")
    remote_user: str = Field(default=SSHDefaults.REMOTE_USER, description="Remote user for SSH tunnel")
    remote_port: int = Field(default=DefaultPorts.POSTGRESQL, description="Remote port for SSH tunnel")
    
    # SSH settings
    key_path: str = Field(default=SSHDefaults.KEY_PATH, description="SSH private key path")
    key_passphrase: Optional[str] = Field(default=None, description="SSH private key passphrase")
    
    # Connection timeouts and retries
    timeout: int = Field(default=DefaultTimeouts.SSH_TUNNEL, description="SSH tunnel connection timeout")
    retry_attempts: int = Field(default=SSHDefaults.RETRY_ATTEMPTS, description="SSH tunnel retry attempts")
    retry_delay: int = Field(default=SSHDefaults.RETRY_DELAY, description="SSH tunnel retry delay in seconds")
    
    # Monitoring settings
    heartbeat_interval: int = Field(default=SSHDefaults.KEEP_ALIVE, description="SSH tunnel heartbeat check interval")
    auto_restart: bool = Field(default=True, description="Auto restart SSH tunnel on failure")
    
    # Service settings
    enabled: bool = Field(default=False, description="Enable SSH tunnel service")
    
    class Config:
        """Pydantic model configuration."""
        str_strip_whitespace = True
        validate_assignment = True
        extra = "forbid"
    
    @field_validator('local_port', 'remote_port')
    @classmethod
    def validate_ports(cls, v):
        """Validate port numbers are in valid range."""
        if not (1 <= v <= 65535):
            raise SSHTunnelConfigError(
                f"Port number must be between 1 and 65535, got {v}",
                config_field="port"
            )
        return v
    
    @field_validator('key_path')
    @classmethod
    def validate_key_path(cls, v):
        """Validate SSH key path exists and is readable."""
        if not v:
            raise SSHTunnelConfigError(
                "SSH key path cannot be empty",
                config_field="key_path"
            )
        
        # Expand user path (~)
        expanded_path = Path(os.path.expanduser(v))
        
        if not expanded_path.exists():
            raise SSHTunnelConfigError(
                f"SSH key file does not exist: {expanded_path}",
                config_field="key_path"
            )
        
        if not expanded_path.is_file():
            raise SSHTunnelConfigError(
                f"SSH key path is not a file: {expanded_path}",
                config_field="key_path"
            )
        
        # Check file permissions (should not be world readable)
        try:
            stat = expanded_path.stat()
            if stat.st_mode & 0o077:  # Check for group/other permissions
                raise SSHTunnelConfigError(
                    f"SSH key file has too open permissions: {oct(stat.st_mode & 0o777)}. "
                    f"Should be 600 or similar.",
                    config_field="key_path"
                )
        except OSError as e:
            raise SSHTunnelConfigError(
                f"Cannot check SSH key file permissions: {e}",
                config_field="key_path"
            )
        
        return str(expanded_path)
    
    @field_validator('remote_host')
    @classmethod
    def validate_remote_host(cls, v):
        """Validate remote host is not empty."""
        if not v.strip():
            raise SSHTunnelConfigError(
                "Remote host cannot be empty",
                config_field="remote_host"
            )
        return v.strip()
    
    @field_validator('remote_user')
    @classmethod
    def validate_remote_user(cls, v):
        """Validate remote user is not empty."""
        if not v.strip():
            raise SSHTunnelConfigError(
                "Remote user cannot be empty",
                config_field="remote_user"
            )
        return v.strip()
    
    @field_validator('timeout', 'retry_attempts', 'retry_delay', 'heartbeat_interval')
    @classmethod
    def validate_positive_integers(cls, v):
        """Validate timeout values are positive."""
        if v <= 0:
            raise SSHTunnelConfigError(
                f"Value must be positive, got {v}",
                config_field="timeout_value"
            )
        return v
    
    @property
    def expanded_key_path(self) -> Path:
        """Get expanded SSH key path as Path object."""
        return Path(os.path.expanduser(self.key_path))
    
    @property
    def connection_string(self) -> str:
        """Get connection string for logging purposes."""
        return f"{self.remote_user}@{self.remote_host}:{self.remote_port} -> localhost:{self.local_port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict()
    
    @classmethod
    def from_settings(cls, settings) -> "TunnelConfig":
        """Create TunnelConfig from application settings.
        
        Args:
            settings: Application settings object
            
        Returns:
            TunnelConfig instance
        """
        return cls(
            enabled=settings.ENABLE_SSH_TUNNEL,
            local_port=settings.SSH_TUNNEL_LOCAL_PORT,
            remote_host=settings.SSH_TUNNEL_REMOTE_HOST,
            remote_user=settings.SSH_TUNNEL_REMOTE_USER,
            remote_port=settings.SSH_TUNNEL_REMOTE_PORT,
            key_path=settings.SSH_TUNNEL_KEY_PATH,
            key_passphrase=getattr(settings, 'SSH_TUNNEL_KEY_PASSPHRASE', None),
            timeout=settings.SSH_TUNNEL_TIMEOUT,
            retry_attempts=settings.SSH_TUNNEL_RETRY_ATTEMPTS,
            retry_delay=settings.SSH_TUNNEL_RETRY_DELAY,
            heartbeat_interval=settings.SSH_TUNNEL_HEARTBEAT_INTERVAL,
            auto_restart=settings.SSH_TUNNEL_AUTO_RESTART
        )
    
    @classmethod
    def create_dev_config(cls) -> "TunnelConfig":
        """Create development configuration.
        
        Returns:
            TunnelConfig for development environment
        """
        return cls(
            enabled=True,
            local_port=5435,
            remote_host="31.130.148.200",
            remote_user="root",
            remote_port=5432,
            key_path="~/.ssh/postgres_key",
            timeout=30,
            retry_attempts=3,
            retry_delay=5,
            heartbeat_interval=60,
            auto_restart=True
        )
    
    @classmethod 
    def create_prod_config(cls) -> "TunnelConfig":
        """Create production configuration.
        
        Returns:
            TunnelConfig for production environment
        """
        return cls(
            enabled=False,  # Usually disabled in production
            local_port=5435,
            remote_host="production-db.example.com",
            remote_user="postgres",
            remote_port=5432,
            key_path="~/.ssh/prod_postgres_key",
            timeout=60,  # Longer timeout for production
            retry_attempts=5,  # More retries for production
            retry_delay=10,
            heartbeat_interval=30,  # More frequent checks
            auto_restart=True
        ) 