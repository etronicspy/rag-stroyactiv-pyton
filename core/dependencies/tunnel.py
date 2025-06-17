"""
SSH Tunnel Dependencies for FastAPI.

This module provides dependency injection for SSH tunnel service in FastAPI endpoints.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status

from services.ssh_tunnel_service import get_tunnel_service, SSHTunnelService


async def get_tunnel_dependency() -> Optional[SSHTunnelService]:
    """Dependency to get SSH tunnel service.
    
    Returns:
        SSHTunnelService instance or None if not available
    """
    return get_tunnel_service()


async def require_tunnel_service() -> SSHTunnelService:
    """Dependency that requires SSH tunnel service to be available.
    
    Returns:
        SSHTunnelService instance
        
    Raises:
        HTTPException: If tunnel service is not available
    """
    service = get_tunnel_service()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SSH tunnel service is not available"
        )
    return service


async def get_active_tunnel() -> SSHTunnelService:
    """Dependency that requires an active SSH tunnel.
    
    Returns:
        SSHTunnelService instance with active tunnel
        
    Raises:
        HTTPException: If tunnel is not active
    """
    service = await require_tunnel_service()
    
    if not service.is_tunnel_active():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SSH tunnel is not currently active"
        )
    
    return service


# Type aliases for cleaner FastAPI route definitions
TunnelService = Annotated[Optional[SSHTunnelService], Depends(get_tunnel_dependency)]
RequiredTunnelService = Annotated[SSHTunnelService, Depends(require_tunnel_service)]  
ActiveTunnelService = Annotated[SSHTunnelService, Depends(get_active_tunnel)] 