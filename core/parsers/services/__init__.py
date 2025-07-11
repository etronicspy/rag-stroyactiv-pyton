"""
Parser Services Package

This package contains all parser service implementations including
AI-powered parsing, material-specific parsing, and batch processing.
"""

from functools import lru_cache
from typing import Optional

# Lazy import functions
def get_ai_parser_service():
    """Get AI parser service instance (lazy import)."""
    try:
        from .ai_parser_service import AIParserService, get_ai_parser_service as _get_service
        return _get_service()
    except ImportError as e:
        raise ImportError(f"AI parser service not available: {e}")

def get_material_parser_service():
    """Get material parser service instance (lazy import)."""
    try:
        from .material_parser_service import MaterialParserService, get_material_parser_service as _get_service
        return _get_service()
    except ImportError as e:
        raise ImportError(f"Material parser service not available: {e}")

def get_batch_parser_service():
    """Get batch parser service instance (lazy import)."""
    try:
        from .batch_parser_service import BatchParserService, get_batch_parser_service as _get_service
        return _get_service()
    except ImportError as e:
        raise ImportError(f"Batch parser service not available: {e}")

# Service registry for dynamic access
_SERVICE_REGISTRY = {
    "ai_parser": get_ai_parser_service,
    "material_parser": get_material_parser_service,
    "batch_parser": get_batch_parser_service
}

def get_parser_service(service_name: str):
    """
    Get parser service by name.
    
    Args:
        service_name: Name of the service to get
        
    Returns:
        Parser service instance
        
    Raises:
        ValueError: If service name is not recognized
        ImportError: If service is not available
    """
    if service_name not in _SERVICE_REGISTRY:
        available_services = list(_SERVICE_REGISTRY.keys())
        raise ValueError(f"Unknown service '{service_name}'. Available: {available_services}")
    
    return _SERVICE_REGISTRY[service_name]()

def list_available_services() -> list:
    """
    List all available parser services.
    
    Returns:
        list: List of available service names
    """
    available = []
    for service_name, factory in _SERVICE_REGISTRY.items():
        try:
            factory()
            available.append(service_name)
        except ImportError:
            pass
    return available

def check_services_health() -> dict:
    """
    Check health status of all parser services.
    
    Returns:
        dict: Health status for each service
    """
    health_status = {}
    for service_name, factory in _SERVICE_REGISTRY.items():
        try:
            service = factory()
            if hasattr(service, 'is_healthy'):
                health_status[service_name] = service.is_healthy()
            else:
                health_status[service_name] = True  # Assume healthy if no health check
        except ImportError:
            health_status[service_name] = False
        except Exception as e:
            health_status[service_name] = False
    
    return health_status

# Version information
__version__ = "2.0.0"
__author__ = "RAG Construction Materials Team"
__description__ = "Parser service implementations"

# Export service access functions
__all__ = [
    'get_ai_parser_service',
    'get_material_parser_service', 
    'get_batch_parser_service',
    'get_parser_service',
    'list_available_services',
    'check_services_health',
    '__version__',
    '__author__',
    '__description__'
] 