"""
SSH Tunnel exceptions for RAG Construction Materials API.

This module defines custom exceptions for SSH tunnel operations.
"""

from typing import Optional


class SSHTunnelError(Exception):
    """Base exception for SSH tunnel operations."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SSHTunnelConnectionError(SSHTunnelError):
    """Exception raised when SSH tunnel connection fails."""
    
    def __init__(self, message: str, host: str, port: int, details: Optional[dict] = None):
        super().__init__(message, details)
        self.host = host
        self.port = port


class SSHTunnelConfigError(SSHTunnelError):
    """Exception raised for SSH tunnel configuration errors."""
    
    def __init__(self, message: str, config_field: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message, details)
        self.config_field = config_field


class SSHTunnelTimeoutError(SSHTunnelError):
    """Exception raised when SSH tunnel operations timeout."""
    
    def __init__(self, message: str, timeout: int, details: Optional[dict] = None):
        super().__init__(message, details)
        self.timeout = timeout


class SSHTunnelAuthenticationError(SSHTunnelError):
    """Exception raised for SSH authentication failures."""
    
    def __init__(self, message: str, username: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.username = username


class SSHTunnelKeyError(SSHTunnelError):
    """Exception raised for SSH key related errors."""
    
    def __init__(self, message: str, key_path: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.key_path = key_path 