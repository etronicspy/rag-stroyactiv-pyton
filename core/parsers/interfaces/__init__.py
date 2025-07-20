"""
Parser Interfaces Package

This package contains all abstract base classes and interfaces for parser implementations.
Provides type-safe contracts for parsing operations with support for generics and protocols.
"""

from .ai_parser_interface import (
    # AI enums
    AIModelType,
    AIParseMode,
    # AI models
    AIParseRequest,
    AIParseResult,
    # AI-specific types
    EmbeddingType,
    # AI interfaces
    IAIParser,
    IMaterialParser,
    ITextParser,
    MaterialParseData,
    PromptType,
    TextParseData,
)
from .parser_interface import (
    BatchParseRequest,
    BatchParseResult,
    ConfigType,
    # Base interface
    IBaseParser,
    # Generic types
    InputType,
    IParserConfig,
    # Protocols
    IParserHealthCheck,
    IParserMetrics,
    OutputType,
    ParseRequest,
    # Base models
    ParseResult,
    # Enums
    ParseStatus,
)

# Version information
__version__ = "1.0.0"
__author__ = "RAG Construction Materials Team"
__description__ = "Parser interfaces for AI-powered parsing operations"

# Export all interface types
__all__ = [
    # Base interface types
    'InputType',
    'OutputType',
    'ConfigType',
    'ParseStatus',
    'ParseResult',
    'ParseRequest',
    'BatchParseRequest',
    'BatchParseResult',
    'IParserHealthCheck',
    'IParserConfig',
    'IParserMetrics',
    'IBaseParser',
    
    # AI interface types
    'EmbeddingType',
    'PromptType',
    'AIModelType',
    'AIParseMode',
    'AIParseRequest',
    'AIParseResult',
    'MaterialParseData',
    'TextParseData',
    'IAIParser',
    'IMaterialParser',
    'ITextParser',
    
    # Version info
    '__version__',
    '__author__',
    '__description__'
]

# Interface hierarchy documentation
INTERFACE_HIERARCHY = {
    'IBaseParser': {
        'description': 'Base interface for all parsers',
        'generic_params': ['InputType', 'OutputType', 'ConfigType'],
        'required_methods': [
            'parse',
            'parse_batch',
            'get_supported_input_types',
            'get_parser_info',
            'validate_input',
            'cleanup'
        ],
        'optional_methods': [
            'configure',
            'pre_parse_hook',
            'post_parse_hook',
            'get_version',
            'get_name'
        ]
    },
    'IAIParser': {
        'description': 'AI-enhanced parser interface',
        'extends': 'IBaseParser',
        'additional_methods': [
            'parse_with_ai',
            'generate_embeddings',
            'validate_confidence',
            'get_supported_models',
            'get_model_info',
            'estimate_cost'
        ],
        'optional_methods': [
            'optimize_prompt',
            'post_process_ai_result',
            'supports_streaming',
            'supports_batch_optimization'
        ]
    },
    'IMaterialParser': {
        'description': 'Material-specific parser interface',
        'extends': 'IAIParser',
        'specialized_for': 'MaterialParseData',
        'additional_methods': [
            'parse_material',
            'extract_unit',
            'extract_color',
            'calculate_coefficient'
        ]
    },
    'ITextParser': {
        'description': 'Text analysis parser interface',
        'extends': 'IAIParser',
        'specialized_for': 'TextParseData',
        'additional_methods': [
            'extract_entities',
            'analyze_sentiment',
            'summarize_text',
            'extract_keywords'
        ]
    }
}

def get_interface_info(interface_name: str) -> dict:
    """
    Get information about a specific interface.
    
    Args:
        interface_name: Name of the interface
        
    Returns:
        dict: Interface information
    """
    return INTERFACE_HIERARCHY.get(interface_name, {})

def list_available_interfaces() -> list:
    """
    List all available interfaces.
    
    Returns:
        list: List of interface names
    """
    return list(INTERFACE_HIERARCHY.keys())

def validate_interface_implementation(cls, interface_name: str) -> bool:
    """
    Validate if a class properly implements an interface.
    
    Args:
        cls: Class to validate
        interface_name: Name of the interface to check against
        
    Returns:
        bool: True if implementation is valid, False otherwise
    """
    interface_info = get_interface_info(interface_name)
    if not interface_info:
        return False
    
    # Check required methods
    required_methods = interface_info.get('required_methods', [])
    for method in required_methods:
        if not hasattr(cls, method):
            return False
    
    return True 