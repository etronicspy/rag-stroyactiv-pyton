"""
Parser Configuration Package

This package contains configuration managers for parser operations including
parser settings, system prompts, and units configuration.
"""

from functools import lru_cache
from typing import Optional, Dict, Any

# Lazy import functions
def get_parser_config_manager():
    """Get parser configuration manager (lazy import)."""
    try:
        from .parser_config_manager import ParserConfigManager, get_config_manager
        return get_config_manager()
    except ImportError as e:
        raise ImportError(f"Parser config manager not available: {e}")

def get_system_prompts_manager():
    """Get system prompts manager (lazy import)."""
    try:
        from .system_prompts_manager import SystemPromptsManager, get_prompts_manager
        return get_prompts_manager()
    except ImportError as e:
        raise ImportError(f"System prompts manager not available: {e}")

def get_units_config_manager():
    """Get units configuration manager (lazy import)."""
    try:
        from .units_config_manager import UnitsConfigManager, get_units_manager
        return get_units_manager()
    except ImportError as e:
        raise ImportError(f"Units config manager not available: {e}")

# Configuration registry
_CONFIG_REGISTRY = {
    "parser_config": get_parser_config_manager,
    "system_prompts": get_system_prompts_manager,
    "units_config": get_units_config_manager
}

def get_config_manager(manager_name: str):
    """
    Get configuration manager by name.
    
    Args:
        manager_name: Name of the configuration manager
        
    Returns:
        Configuration manager instance
        
    Raises:
        ValueError: If manager name is not recognized
        ImportError: If manager is not available
    """
    if manager_name not in _CONFIG_REGISTRY:
        available_managers = list(_CONFIG_REGISTRY.keys())
        raise ValueError(f"Unknown config manager '{manager_name}'. Available: {available_managers}")
    
    return _CONFIG_REGISTRY[manager_name]()

def list_available_config_managers() -> list:
    """
    List all available configuration managers.
    
    Returns:
        list: List of available manager names
    """
    available = []
    for manager_name, factory in _CONFIG_REGISTRY.items():
        try:
            factory()
            available.append(manager_name)
        except ImportError:
            pass
    return available

def get_all_configurations() -> Dict[str, Any]:
    """
    Get all parser configurations.
    
    Returns:
        Dict[str, Any]: All configuration data
    """
    configurations = {}
    
    for manager_name, factory in _CONFIG_REGISTRY.items():
        try:
            manager = factory()
            if hasattr(manager, 'get_config'):
                configurations[manager_name] = manager.get_config()
            elif hasattr(manager, 'get_all_configs'):
                configurations[manager_name] = manager.get_all_configs()
            else:
                configurations[manager_name] = "No config accessor available"
        except ImportError:
            configurations[manager_name] = "Manager not available"
        except Exception as e:
            configurations[manager_name] = f"Error accessing config: {e}"
    
    return configurations

def validate_all_configurations() -> Dict[str, bool]:
    """
    Validate all parser configurations.
    
    Returns:
        Dict[str, bool]: Validation status for each configuration
    """
    validation_results = {}
    
    for manager_name, factory in _CONFIG_REGISTRY.items():
        try:
            manager = factory()
            if hasattr(manager, 'validate_config'):
                validation_results[manager_name] = manager.validate_config()
            else:
                validation_results[manager_name] = True  # Assume valid if no validation
        except ImportError:
            validation_results[manager_name] = False
        except Exception:
            validation_results[manager_name] = False
    
    return validation_results

def reload_all_configurations() -> Dict[str, bool]:
    """
    Reload all parser configurations.
    
    Returns:
        Dict[str, bool]: Reload status for each configuration
    """
    reload_results = {}
    
    for manager_name, factory in _CONFIG_REGISTRY.items():
        try:
            manager = factory()
            if hasattr(manager, 'reload_config'):
                reload_results[manager_name] = manager.reload_config()
            else:
                reload_results[manager_name] = True  # Assume successful if no reload method
        except ImportError:
            reload_results[manager_name] = False
        except Exception:
            reload_results[manager_name] = False
    
    return reload_results

# Version information
__version__ = "2.0.0"
__author__ = "RAG Construction Materials Team"
__description__ = "Parser configuration managers"

# Export configuration access functions
__all__ = [
    'get_parser_config_manager',
    'get_system_prompts_manager',
    'get_units_config_manager',
    'get_config_manager',
    'list_available_config_managers',
    'get_all_configurations',
    'validate_all_configurations',
    'reload_all_configurations',
    '__version__',
    '__author__',
    '__description__'
] 