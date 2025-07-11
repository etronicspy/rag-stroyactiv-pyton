"""
Core Parsers Module

Comprehensive AI-powered parsing system for construction materials and text processing.
Provides type-safe, configurable parsers with advanced AI capabilities.
"""

# Import interfaces
from .interfaces import (
    # Base types
    InputType,
    OutputType,
    ConfigType,
    ParseStatus,
    ParseResult,
    ParseRequest,
    BatchParseRequest,
    BatchParseResult,
    
    # Base interfaces
    IBaseParser,
    IParserHealthCheck,
    IParserConfig,
    IParserMetrics,
    
    # AI interfaces
    IAIParser,
    IMaterialParser,
    ITextParser,
    
    # AI types
    AIModelType,
    AIParseMode,
    AIParseRequest,
    AIParseResult,
    MaterialParseData,
    TextParseData,
    
    # Metadata
    __version__ as interfaces_version,
    INTERFACE_HIERARCHY,
    get_interface_info,
    list_available_interfaces,
    validate_interface_implementation
)

# Lazy imports for services (will be available after migration)
def get_ai_parser_service():
    """Get AI parser service instance (lazy import)."""
    try:
        from .services.ai_parser_service import AIParserService, get_ai_parser_service as _get_service
        return _get_service()
    except ImportError:
        raise ImportError("AI parser service not yet available. Run parser migration first.")

def get_material_parser_service():
    """Get material parser service instance (lazy import)."""
    try:
        from .services.material_parser_service import MaterialParserService, get_material_parser_service as _get_service
        return _get_service()
    except ImportError:
        raise ImportError("Material parser service not yet available. Run parser migration first.")

def get_batch_parser_service():
    """Get batch parser service instance (lazy import)."""
    try:
        from .services.batch_parser_service import BatchParserService, get_batch_parser_service as _get_service
        return _get_service()
    except ImportError:
        raise ImportError("Batch parser service not yet available. Run parser migration first.")

# Lazy imports for configuration
def get_parser_config_manager():
    """Get parser configuration manager (lazy import)."""
    try:
        from .config.parser_config_manager import ParserConfigManager, get_config_manager
        return get_config_manager()
    except ImportError:
        raise ImportError("Parser config manager not yet available. Run parser migration first.")

def get_system_prompts_manager():
    """Get system prompts manager (lazy import)."""
    try:
        from .config.system_prompts_manager import SystemPromptsManager, get_prompts_manager
        return get_prompts_manager()
    except ImportError:
        raise ImportError("System prompts manager not yet available. Run parser migration first.")

def get_units_config_manager():
    """Get units configuration manager (lazy import)."""
    try:
        from .config.units_config_manager import UnitsConfigManager, get_units_manager
        return get_units_manager()
    except ImportError:
        raise ImportError("Units config manager not yet available. Run parser migration first.")

# Module metadata
__version__ = "2.0.0"
__author__ = "RAG Construction Materials Team"
__description__ = "AI-powered parser system for construction materials"

# Migration status
_MIGRATION_STATUS = {
    "interfaces": True,
    "services": True,   # ✅ Completed: ai_parser_service, material_parser_service, batch_parser_service
    "config": True,     # ✅ Completed: parser_config_manager, system_prompts_manager, units_config_manager
    "logging": True,
    "complete": True    # ✅ All components migrated successfully
}

def get_migration_status() -> dict:
    """
    Get current migration status.
    
    Returns:
        dict: Migration status for each component
    """
    return _MIGRATION_STATUS.copy()

def is_migration_complete() -> bool:
    """
    Check if parser migration is complete.
    
    Returns:
        bool: True if migration is complete, False otherwise
    """
    return _MIGRATION_STATUS["complete"]

def check_parser_availability() -> dict:
    """
    Check availability of parser components.
    
    Returns:
        dict: Component availability status
    """
    availability = {}
    
    # Check services
    try:
        get_ai_parser_service()
        availability["ai_parser_service"] = True
    except ImportError:
        availability["ai_parser_service"] = False
    
    try:
        get_material_parser_service()
        availability["material_parser_service"] = True
    except ImportError:
        availability["material_parser_service"] = False
    
    try:
        get_batch_parser_service()
        availability["batch_parser_service"] = True
    except ImportError:
        availability["batch_parser_service"] = False
    
    # Check configuration
    try:
        get_parser_config_manager()
        availability["config_manager"] = True
    except ImportError:
        availability["config_manager"] = False
    
    try:
        get_system_prompts_manager()
        availability["prompts_manager"] = True
    except ImportError:
        availability["prompts_manager"] = False
    
    try:
        get_units_config_manager()
        availability["units_manager"] = True
    except ImportError:
        availability["units_manager"] = False
    
    return availability

# Export core interface types for immediate use
__all__ = [
    # Interface types (available immediately)
    'InputType',
    'OutputType',
    'ConfigType',
    'ParseStatus',
    'ParseResult',
    'ParseRequest',
    'BatchParseRequest',
    'BatchParseResult',
    'IBaseParser',
    'IParserHealthCheck',
    'IParserConfig',
    'IParserMetrics',
    'IAIParser',
    'IMaterialParser',
    'ITextParser',
    'AIModelType',
    'AIParseMode',
    'AIParseRequest',
    'AIParseResult',
    'MaterialParseData',
    'TextParseData',
    
    # Interface utilities
    'INTERFACE_HIERARCHY',
    'get_interface_info',
    'list_available_interfaces',
    'validate_interface_implementation',
    
    # Service factories (lazy imports)
    'get_ai_parser_service',
    'get_material_parser_service',
    'get_batch_parser_service',
    
    # Configuration factories (lazy imports)
    'get_parser_config_manager',
    'get_system_prompts_manager',
    'get_units_config_manager',
    
    # Migration utilities
    'get_migration_status',
    'is_migration_complete',
    'check_parser_availability',
    
    # Metadata
    '__version__',
    '__author__',
    '__description__'
]

# Compatibility note for legacy imports
def _legacy_import_warning():
    """Issue warning for legacy imports from parser_module."""
    import warnings
    warnings.warn(
        "Direct imports from 'parser_module' are deprecated. "
        "Use 'core.parsers' instead. "
        "Legacy imports will be removed in version 3.0.0.",
        DeprecationWarning,
        stacklevel=3
    )

# Parser module ready status
print(f"🔧 Core Parsers Module v{__version__} loaded")
print(f"📊 Migration Status: {get_migration_status()}")
if not is_migration_complete():
    print("⚠️  Migration in progress. Some components may not be available yet.")
else:
    print("✅ All parser components available") 