"""
AI-Only Material Parser Module for Construction Materials

This module provides intelligent parsing of construction material names 
to extract metric units and calculate price coefficients using OpenAI GPT.

Features:
- Pure AI-based parsing (no regex)
- Automatic unit extraction from product names
- Price coefficient calculation
- Support for complex material descriptions
- Integration with main RAG project

Usage:
    from parser_module import MaterialParser
    
    parser = MaterialParser()
    result = parser.parse_material("Цемент 50кг", "меш", 300.0)
    print(result.unit_parsed)  # "кг"
    print(result.price_coefficient)  # 50.0
"""

try:
    # Try relative imports (when imported as module)
    from .material_parser import MaterialParser
    from .ai_parser import AIParser
    from .units_config import STANDARD_UNITS, UNIT_ALIASES
    from .parser_config import ParserConfig
except ImportError:
    # Fall back to absolute imports (when run as script)
    from material_parser import MaterialParser
    from ai_parser import AIParser
    from units_config import STANDARD_UNITS, UNIT_ALIASES
    from parser_config import ParserConfig

__version__ = "1.0.0"
__author__ = "RAG Construction Materials Team"

# Main exports
__all__ = [
    "MaterialParser",
    "AIParser", 
    "ParserConfig",
    "STANDARD_UNITS",
    "UNIT_ALIASES"
] 