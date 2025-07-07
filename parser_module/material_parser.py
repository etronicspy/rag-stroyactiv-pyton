"""
Main Material Parser Interface

This module provides a simplified interface for parsing construction materials
using AI-powered extraction of units and price coefficients.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
try:
    # Try relative imports (when imported as module)
    from .ai_parser import AIParser, ParsedResult
    from .parser_config import ParserConfig, get_config, validate_config
    from .units_config import normalize_unit, get_common_units_for_ai
except ImportError:
    # Fall back to absolute imports (when run as script)
    from ai_parser import AIParser, ParsedResult
    from parser_config import ParserConfig, get_config, validate_config
    from units_config import normalize_unit, get_common_units_for_ai


class MaterialParser:
    """
    Main interface for AI-powered material parsing
    
    This class provides a simple API for parsing construction materials
    and extracting metric units with price coefficients.
    """
    
    def __init__(self, config: Optional[ParserConfig] = None, env: str = "default"):
        """
        Initialize Material Parser
        
        Args:
            config: Parser configuration (optional)
            env: Environment for default config ("default", "development", "production", "integration")
        """
        self.config = config or get_config(env)
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if not validate_config(self.config):
            raise ValueError("Invalid parser configuration")
        
        # Initialize AI parser
        self.ai_parser = AIParser(self.config)
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "cache_hits": 0
        }
        
        self.logger.info("MaterialParser initialized successfully")
    
    def parse_single(self, name: str, unit: str, price: float) -> Dict[str, Any]:
        """
        Parse a single material
        
        Args:
            name: Material name
            unit: Original unit
            price: Original price
            
        Returns:
            Dictionary with parsing results
        """
        self.logger.debug(f"Parsing single material: {name}")
        
        try:
            # Parse with AI
            result = self.ai_parser.parse_material(name, unit, price)
            
            # Update statistics
            self.stats["total_processed"] += 1
            if result.success:
                self.stats["successful_parses"] += 1
            else:
                self.stats["failed_parses"] += 1
            
            return result.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error parsing material {name}: {e}")
            self.stats["failed_parses"] += 1
            return self._create_error_result(name, unit, price, str(e))
    
    def parse_batch(self, materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse multiple materials
        
        Args:
            materials: List of materials with 'name', 'unit', 'price' keys
            
        Returns:
            List of parsing results
        """
        self.logger.info(f"Parsing batch of {len(materials)} materials")
        
        try:
            # Parse with AI
            results = self.ai_parser.parse_batch(materials)
            
            # Update statistics
            self.stats["total_processed"] += len(materials)
            for result in results:
                if result.success:
                    self.stats["successful_parses"] += 1
                else:
                    self.stats["failed_parses"] += 1
            
            return [result.to_dict() for result in results]
            
        except Exception as e:
            self.logger.error(f"Error parsing batch: {e}")
            # Return error results for all materials
            return [
                self._create_error_result(
                    mat.get("name", "Unknown"),
                    mat.get("unit", "Unknown"),
                    mat.get("price", 0.0),
                    str(e)
                )
                for mat in materials
            ]
    
    def parse_from_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Parse materials from JSON file
        
        Args:
            file_path: Path to JSON file with materials
            
        Returns:
            List of parsing results
        """
        file_path = Path(file_path)
        self.logger.info(f"Parsing materials from file: {file_path}")
        
        try:
            # Load materials from file
            with open(file_path, 'r', encoding='utf-8') as f:
                materials = json.load(f)
            
            # Validate file format
            if not isinstance(materials, list):
                raise ValueError("File must contain a list of materials")
            
            # Parse materials
            return self.parse_batch(materials)
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing file {file_path}: {e}")
            raise
    
    def save_results(self, results: List[Dict[str, Any]], output_path: Union[str, Path]):
        """
        Save parsing results to JSON file
        
        Args:
            results: List of parsing results
            output_path: Path for output file
        """
        output_path = Path(output_path)
        self.logger.info(f"Saving {len(results)} results to: {output_path}")
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save results
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Results saved successfully to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get parsing statistics
        
        Returns:
            Dictionary with statistics
        """
        # Get AI parser statistics
        ai_stats = self.ai_parser.get_statistics()
        
        # Combine with main statistics
        total_processed = self.stats["total_processed"]
        success_rate = (self.stats["successful_parses"] / total_processed) if total_processed > 0 else 0
        
        return {
            "total_processed": total_processed,
            "successful_parses": self.stats["successful_parses"],
            "failed_parses": self.stats["failed_parses"],
            "success_rate": round(success_rate, 3),
            "cache_size": ai_stats.get("cache_size", 0),
            "ai_success_rate": ai_stats.get("success_rate", 0)
        }
    
    def clear_cache(self):
        """Clear parsing cache"""
        self.ai_parser.clear_cache()
        self.logger.info("Parser cache cleared")
    
    def get_supported_units(self) -> List[str]:
        """
        Get list of supported units
        
        Returns:
            List of supported unit strings
        """
        return get_common_units_for_ai()
    
    def validate_unit(self, unit: str) -> Optional[str]:
        """
        Validate and normalize unit
        
        Args:
            unit: Unit string to validate
            
        Returns:
            Normalized unit or None if invalid
        """
        return normalize_unit(unit)
    
    def _create_error_result(self, name: str, unit: str, price: float, error_message: str) -> Dict[str, Any]:
        """
        Create error result dictionary
        
        Args:
            name: Material name
            unit: Original unit
            price: Original price
            error_message: Error message
            
        Returns:
            Error result dictionary
        """
        return {
            "name": name,
            "original_unit": unit,
            "original_price": price,
            "unit_parsed": None,
            "price_coefficient": None,
            "price_parsed": None,
            "parsing_method": "ai_gpt",
            "confidence": 0.0,
            "success": False,
            "error_message": error_message,
            "processing_time": 0.0
        }
    
    def export_config(self, output_path: Union[str, Path]):
        """
        Export current configuration to file
        
        Args:
            output_path: Path for config file
        """
        output_path = Path(output_path)
        
        try:
            config_dict = self.config.to_dict()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
            
            self.logger.info(f"Configuration exported to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting config: {e}")
            raise
    
    def create_example_data(self, output_path: Union[str, Path]):
        """
        Create example data file for testing
        
        Args:
            output_path: Path for example file
        """
        output_path = Path(output_path)
        
        example_materials = [
            {"name": "Цемент М400 50кг", "unit": "меш", "price": 350.0},
            {"name": "Кирпич керамический полнотелый (250x120x65)", "unit": "шт", "price": 15.0},
            {"name": "Газобетон D500 600x300x200", "unit": "шт", "price": 95.0},
            {"name": "OSB-3 плита 2500x1250x12 мм", "unit": "шт", "price": 850.0},
            {"name": "Утеплитель минеральный 100мм (1.2x0.6м) 0.72м²", "unit": "шт", "price": 280.0},
            {"name": "Рубероид РКП-350 1x15м", "unit": "шт", "price": 380.0},
            {"name": "Мастика битумная 20кг", "unit": "шт", "price": 1200.0},
            {"name": "Пена монтажная 750мл", "unit": "шт", "price": 290.0},
            {"name": "Проволока вязальная 5кг", "unit": "кг", "price": 65.0},
            {"name": "Арматура А500С диаметр 12мм", "unit": "м", "price": 45.0}
        ]
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(example_materials, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Example data created at: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating example data: {e}")
            raise


def create_parser(env: str = "default") -> MaterialParser:
    """
    Factory function to create MaterialParser instance
    
    Args:
        env: Environment configuration ("default", "development", "production", "integration")
        
    Returns:
        MaterialParser instance
    """
    return MaterialParser(env=env)


def quick_parse(name: str, unit: str, price: float, env: str = "default") -> Dict[str, Any]:
    """
    Quick parse function for single material
    
    Args:
        name: Material name
        unit: Original unit
        price: Original price
        env: Environment configuration
        
    Returns:
        Parsing result dictionary
    """
    parser = create_parser(env)
    return parser.parse_single(name, unit, price)


def parse_file(file_path: Union[str, Path], env: str = "default") -> List[Dict[str, Any]]:
    """
    Quick parse function for file
    
    Args:
        file_path: Path to JSON file
        env: Environment configuration
        
    Returns:
        List of parsing results
    """
    parser = create_parser(env)
    return parser.parse_from_file(file_path) 