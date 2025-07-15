"""
Units Configuration Manager

Advanced management system for measurement units with validation,
conversion, and dynamic configuration for construction materials.
"""

import json
import time
from typing import Dict, List, Set, Optional, Any, Union, Tuple
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass, field, asdict
from enum import Enum
import re

# Core infrastructure imports
from core.config.parsers import ParserConfig, get_parser_config
from core.config.constants import ParserConstants
from core.logging.specialized.parsers import get_material_parser_logger

print("DEBUG: core/parsers/config/units_config_manager.py loaded")

class UnitType(Enum):
    WEIGHT = "weight"
    VOLUME = "volume"
    AREA = "area"
    LENGTH = "length"
    COUNT = "count"
    PACKAGING = "packaging"
    LIQUID = "liquid"

@dataclass
class UnitInfo:
    name: str
    symbol: str
    unit_type: UnitType
    base_unit: Optional[str] = None
    coefficient: float = 1.0
    aliases: List[str] = field(default_factory=list)


@dataclass
class UnitValidationRule:
    """Validation rule for unit coefficients"""
    unit: str
    min_coefficient: float
    max_coefficient: float
    typical_range: Tuple[float, float]
    description: str
    
    def validate(self, coefficient: float) -> bool:
        """Validate coefficient against rule"""
        return self.min_coefficient <= coefficient <= self.max_coefficient
    
    def is_typical(self, coefficient: float) -> bool:
        """Check if coefficient is in typical range"""
        return self.typical_range[0] <= coefficient <= self.typical_range[1]


@dataclass
class MaterialUnitMapping:
    """Mapping between material types and preferred units"""
    material_keywords: List[str]
    preferred_unit: str
    alternative_units: List[str]
    confidence_boost: float = 0.1
    description: str = ""
    
    def matches_material(self, material_name: str) -> bool:
        """Check if material name matches this mapping"""
        material_lower = material_name.lower()
        return any(keyword in material_lower for keyword in self.material_keywords)


class UnitsConfigManager:
    """
    Advanced units configuration manager.
    
    Provides comprehensive unit management including validation, conversion,
    normalization, and dynamic configuration for construction materials.
    """
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize Units Config Manager.
        
        Args:
            config: Optional parser configuration
        """
        self.config = config or get_parser_config()
        self.logger = get_material_parser_logger()
        
        # Units storage
        self._units: Dict[str, UnitInfo] = {}
        self._unit_aliases: Dict[str, str] = {}
        self._validation_rules: Dict[str, UnitValidationRule] = {}
        self._material_mappings: List[MaterialUnitMapping] = []
        
        # Unit categories
        self._metric_units: Set[str] = set()
        self._non_metric_units: Set[str] = set()
        self._block_materials: Set[str] = set()
        
        # Service metadata
        self._service_name = "units_config_manager"
        self._version = "2.0.0"
        
        # Statistics
        self.stats = {
            "total_units": 0,
            "total_aliases": 0,
            "validation_requests": 0,
            "successful_validations": 0,
            "normalization_requests": 0,
            "successful_normalizations": 0,
            "material_hint_requests": 0,
            "successful_material_hints": 0
        }
        
        # Initialize units system
        self._initialize_units_system()
        
        self.logger.info(f"Units Config Manager v{self._version} initialized")
    
    def _initialize_units_system(self):
        """Initialize units system with default configuration"""
        
        self._initialize_basic_units()
        
        # Initialize validation rules
        self._initialize_validation_rules()
        
        # Initialize material mappings
        self._initialize_material_mappings()
        
        # Update statistics
        self.stats["total_units"] = len(self._units)
        self.stats["total_aliases"] = len(self._unit_aliases)
    
    def _initialize_basic_units(self):
        """Initialize basic units when legacy system is not available"""
        # Basic units
        basic_units = {
            "кг": UnitInfo("кг", "kg", UnitType.WEIGHT, aliases=["килограмм", "кило"]),
            "г": UnitInfo("г", "g", UnitType.WEIGHT, "кг", 0.001, aliases=["грамм"]),
            "т": UnitInfo("т", "t", UnitType.WEIGHT, "кг", 1000.0, aliases=["тонна"]),
            "м3": UnitInfo("м3", "m³", UnitType.VOLUME, aliases=["куб.м", "кубометр"]),
            "л": UnitInfo("л", "l", UnitType.LIQUID, aliases=["литр"]),
            "м2": UnitInfo("м2", "m²", UnitType.AREA, aliases=["кв.м"]),
            "м": UnitInfo("м", "m", UnitType.LENGTH, aliases=["метр"]),
            "шт": UnitInfo("шт", "pcs", UnitType.COUNT, aliases=["штука"]),
            "упак": UnitInfo("упак", "pack", UnitType.PACKAGING, aliases=["упаковка"])
        }
        
        for unit_key, unit_info in basic_units.items():
            self._units[unit_key] = unit_info
            
            # Create aliases
            self._unit_aliases[unit_info.name] = unit_key
            self._unit_aliases[unit_info.symbol] = unit_key
            for alias in unit_info.aliases:
                self._unit_aliases[alias.lower()] = unit_key
        
        # Basic metric units
        self._metric_units = {"кг", "г", "т", "м3", "л", "м2", "м"}
        self._non_metric_units = {"шт", "упак"}
        
        # Basic block materials
        self._block_materials = {"кирпич", "газобетон", "пеноблок", "шлакоблок", "блок"}
        
        self.logger.info("Initialized basic units system")
    
    def _initialize_validation_rules(self):
        """Initialize validation rules for units"""
        validation_rules = {
            "кг": UnitValidationRule(
                unit="кг",
                min_coefficient=0.001,
                max_coefficient=10000.0,
                typical_range=(0.1, 1000.0),
                description="Weight in kilograms"
            ),
            "м3": UnitValidationRule(
                unit="м3",
                min_coefficient=0.000001,
                max_coefficient=100.0,
                typical_range=(0.001, 10.0),
                description="Volume in cubic meters"
            ),
            "м2": UnitValidationRule(
                unit="м2",
                min_coefficient=0.0001,
                max_coefficient=1000.0,
                typical_range=(0.01, 100.0),
                description="Area in square meters"
            ),
            "л": UnitValidationRule(
                unit="л",
                min_coefficient=0.001,
                max_coefficient=1000.0,
                typical_range=(0.1, 100.0),
                description="Volume in liters"
            ),
            "м": UnitValidationRule(
                unit="м",
                min_coefficient=0.001,
                max_coefficient=1000.0,
                typical_range=(0.1, 100.0),
                description="Length in meters"
            ),
            "шт": UnitValidationRule(
                unit="шт",
                min_coefficient=0.1,
                max_coefficient=10000.0,
                typical_range=(1.0, 1000.0),
                description="Count in pieces"
            )
        }
        
        self._validation_rules = validation_rules
    
    def _initialize_material_mappings(self):
        """Initialize material-to-unit mappings"""
        material_mappings = [
            MaterialUnitMapping(
                material_keywords=["кирпич", "кирпича", "кирпичный"],
                preferred_unit="м3",
                alternative_units=["шт"],
                confidence_boost=0.2,
                description="Brick materials should be measured in volume"
            ),
            MaterialUnitMapping(
                material_keywords=["газобетон", "газобетонный", "пеноблок", "пеноблочный"],
                preferred_unit="м3",
                alternative_units=["шт"],
                confidence_boost=0.2,
                description="Foam concrete blocks measured in volume"
            ),
            MaterialUnitMapping(
                material_keywords=["цемент", "цементный"],
                preferred_unit="кг",
                alternative_units=["т", "меш"],
                confidence_boost=0.1,
                description="Cement typically measured by weight"
            ),
            MaterialUnitMapping(
                material_keywords=["краска", "лак", "грунтовка"],
                preferred_unit="л",
                alternative_units=["кг", "банка"],
                confidence_boost=0.1,
                description="Liquid materials measured in liters"
            ),
            MaterialUnitMapping(
                material_keywords=["плитка", "ламинат", "паркет", "линолеум"],
                preferred_unit="м2",
                alternative_units=["упак", "шт"],
                confidence_boost=0.1,
                description="Flooring materials measured in area"
            ),
            MaterialUnitMapping(
                material_keywords=["труба", "профиль", "арматура", "кабель"],
                preferred_unit="м",
                alternative_units=["кг", "шт"],
                confidence_boost=0.1,
                description="Linear materials measured in length"
            )
        ]
        
        self._material_mappings = material_mappings
    
    @property
    def service_name(self) -> str:
        """Get service name"""
        return self._service_name
    
    @property
    def version(self) -> str:
        """Get service version"""
        return self._version
    
    def normalize_unit(self, unit: str) -> Optional[str]:
        """
        Normalize unit string to standard format.
        
        Args:
            unit: Input unit string
            
        Returns:
            Optional[str]: Normalized unit or None if not found
        """
        self.stats["normalization_requests"] += 1
        
        if not unit:
            return None
        
        # Clean and lowercase
        unit_clean = unit.strip().lower()
        
        # Direct lookup
        if unit_clean in self._unit_aliases:
            self.stats["successful_normalizations"] += 1
            return self._unit_aliases[unit_clean]
        
        # Try partial matching for common variations
        for alias, standard in self._unit_aliases.items():
            if unit_clean in alias or alias in unit_clean:
                self.stats["successful_normalizations"] += 1
                return standard
        
        # Try regex patterns for common unit formats
        unit_patterns = [
            (r'(\d+)?\s*кг', 'кг'),
            (r'(\d+)?\s*г', 'г'),
            (r'(\d+)?\s*л', 'л'),
            (r'(\d+)?\s*м³?', 'м'),
            (r'(\d+)?\s*шт', 'шт'),
            (r'куб\.?\s*м', 'м3'),
            (r'кв\.?\s*м', 'м2'),
            (r'п\.?\s*м', 'м'),
        ]
        
        for pattern, standard_unit in unit_patterns:
            if re.search(pattern, unit_clean):
                self.stats["successful_normalizations"] += 1
                return standard_unit
        
        self.logger.debug(f"Could not normalize unit: {unit}")
        return None
    
    def is_metric_unit(self, unit: str) -> bool:
        """
        Check if unit is a metric unit requiring coefficient calculation.
        
        Args:
            unit: Unit to check
            
        Returns:
            bool: True if metric unit
        """
        normalized = self.normalize_unit(unit)
        return normalized in self._metric_units if normalized else False
    
    def is_packaging_unit(self, unit: str) -> bool:
        """
        Check if unit is a packaging unit.
        
        Args:
            unit: Unit to check
            
        Returns:
            bool: True if packaging unit
        """
        normalized = self.normalize_unit(unit)
        if not normalized:
            return False
        
        unit_info = self._units.get(normalized)
        return unit_info.unit_type == UnitType.PACKAGING if unit_info else False
    
    def get_unit_type(self, unit: str) -> Optional[UnitType]:
        """
        Get unit type for a given unit.
        
        Args:
            unit: Unit string
            
        Returns:
            Optional[UnitType]: Unit type or None if not found
        """
        normalized = self.normalize_unit(unit)
        if not normalized:
            return None
        
        unit_info = self._units.get(normalized)
        return unit_info.unit_type if unit_info else None
    
    def is_block_material(self, material_name: str) -> bool:
        """
        Check if material is a block material that should be measured in volume.
        
        Args:
            material_name: Material name to check
            
        Returns:
            bool: True if block material
        """
        if not material_name:
            return False
        
        material_lower = material_name.lower()
        return any(block_keyword in material_lower for block_keyword in self._block_materials)
    
    def get_material_hint(self, material_name: str) -> Optional[str]:
        """
        Get unit hint for a material based on its name.
        
        Args:
            material_name: Material name
            
        Returns:
            Optional[str]: Suggested unit or None
        """
        self.stats["material_hint_requests"] += 1
        
        if not material_name:
            return None
        
        # Check material mappings
        for mapping in self._material_mappings:
            if mapping.matches_material(material_name):
                self.stats["successful_material_hints"] += 1
                return mapping.preferred_unit
        
        # Check if it's a block material
        if self.is_block_material(material_name):
            self.stats["successful_material_hints"] += 1
            return "м3"
        
        # Check legacy hints if available
        # The legacy hints are removed, so this block is effectively removed.
        
        return None
    
    def validate_unit_coefficient(self, unit: str, coefficient: float) -> bool:
        """
        Validate unit coefficient against expected ranges.
        
        Args:
            unit: Unit string
            coefficient: Coefficient to validate
            
        Returns:
            bool: True if valid
        """
        self.stats["validation_requests"] += 1
        
        normalized = self.normalize_unit(unit)
        if not normalized:
            return False
        
        # Check validation rules
        validation_rule = self._validation_rules.get(normalized)
        if validation_rule:
            is_valid = validation_rule.validate(coefficient)
            if is_valid:
                self.stats["successful_validations"] += 1
            return is_valid
        
        # Use legacy validation if available
        # The legacy validation is removed, so this block is effectively removed.
        
        # Basic validation - coefficient should be positive
        is_valid = coefficient > 0
        if is_valid:
            self.stats["successful_validations"] += 1
        
        return is_valid
    
    def get_coefficient_confidence(self, unit: str, coefficient: float) -> float:
        """
        Get confidence score for unit coefficient.
        
        Args:
            unit: Unit string
            coefficient: Coefficient value
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        normalized = self.normalize_unit(unit)
        if not normalized:
            return 0.0
        
        validation_rule = self._validation_rules.get(normalized)
        if not validation_rule:
            return 0.5  # Default confidence
        
        # Check if coefficient is in typical range
        if validation_rule.is_typical(coefficient):
            return 0.9
        
        # Check if coefficient is valid but not typical
        if validation_rule.validate(coefficient):
            return 0.6
        
        # Invalid coefficient
        return 0.1
    
    def get_common_units_for_ai(self) -> List[str]:
        """
        Get list of common units for AI prompts.
        
        Returns:
            List[str]: List of common units
        """
        # The legacy hints are removed, so this block is effectively removed.
        
        # Return basic common units
        return ["кг", "г", "т", "м3", "л", "м2", "м", "шт", "упак"]
    
    def get_all_unit_aliases(self) -> List[str]:
        """
        Get all available unit aliases.
        
        Returns:
            List[str]: List of all aliases
        """
        return list(self._unit_aliases.keys())
    
    def get_units_by_type(self, unit_type: UnitType) -> List[str]:
        """
        Get units by type.
        
        Args:
            unit_type: Type of units to get
            
        Returns:
            List[str]: List of units of specified type
        """
        return [
            unit_key for unit_key, unit_info in self._units.items()
            if unit_info.unit_type == unit_type
        ]
    
    def add_unit(
        self, 
        unit_key: str, 
        unit_info: UnitInfo,
        aliases: Optional[List[str]] = None
    ) -> bool:
        """
        Add new unit to the system.
        
        Args:
            unit_key: Key for the unit
            unit_info: Unit information
            aliases: Additional aliases
            
        Returns:
            bool: True if successful
        """
        try:
            # Add unit
            self._units[unit_key] = unit_info
            
            # Add aliases
            self._unit_aliases[unit_info.name] = unit_key
            self._unit_aliases[unit_info.symbol] = unit_key
            
            for alias in unit_info.aliases:
                self._unit_aliases[alias.lower()] = unit_key
            
            if aliases:
                for alias in aliases:
                    self._unit_aliases[alias.lower()] = unit_key
            
            # Update categories
            if unit_info.unit_type in [UnitType.WEIGHT, UnitType.VOLUME, UnitType.AREA, UnitType.LENGTH]:
                self._metric_units.add(unit_key)
            else:
                self._non_metric_units.add(unit_key)
            
            # Update statistics
            self.stats["total_units"] = len(self._units)
            self.stats["total_aliases"] = len(self._unit_aliases)
            
            self.logger.info(f"Added new unit: {unit_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding unit: {e}")
            return False
    
    def remove_unit(self, unit_key: str) -> bool:
        """
        Remove unit from the system.
        
        Args:
            unit_key: Key of unit to remove
            
        Returns:
            bool: True if successful
        """
        try:
            if unit_key not in self._units:
                self.logger.error(f"Unit '{unit_key}' not found")
                return False
            
            # Get unit info
            unit_info = self._units[unit_key]
            
            # Remove unit
            del self._units[unit_key]
            
            # Remove aliases
            aliases_to_remove = []
            for alias, target_unit in self._unit_aliases.items():
                if target_unit == unit_key:
                    aliases_to_remove.append(alias)
            
            for alias in aliases_to_remove:
                del self._unit_aliases[alias]
            
            # Update categories
            self._metric_units.discard(unit_key)
            self._non_metric_units.discard(unit_key)
            
            # Update statistics
            self.stats["total_units"] = len(self._units)
            self.stats["total_aliases"] = len(self._unit_aliases)
            
            self.logger.info(f"Removed unit: {unit_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing unit: {e}")
            return False
    
    def add_material_mapping(self, mapping: MaterialUnitMapping) -> bool:
        """
        Add material-to-unit mapping.
        
        Args:
            mapping: Material unit mapping
            
        Returns:
            bool: True if successful
        """
        try:
            self._material_mappings.append(mapping)
            self.logger.info(f"Added material mapping for: {mapping.material_keywords}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding material mapping: {e}")
            return False
    
    def add_validation_rule(self, rule: UnitValidationRule) -> bool:
        """
        Add validation rule for unit.
        
        Args:
            rule: Validation rule
            
        Returns:
            bool: True if successful
        """
        try:
            self._validation_rules[rule.unit] = rule
            self.logger.info(f"Added validation rule for: {rule.unit}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding validation rule: {e}")
            return False
    
    def export_configuration(self, output_path: Union[str, Path]) -> bool:
        """
        Export units configuration to file.
        
        Args:
            output_path: Output file path
            
        Returns:
            bool: True if successful
        """
        output_path = Path(output_path)
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create export data
            export_data = {
                "metadata": {
                    "service_name": self.service_name,
                    "version": self.version,
                    "exported_at": time.time()
                },
                "units": {
                    unit_key: {
                        "name": unit_info.name,
                        "symbol": unit_info.symbol,
                        "unit_type": unit_info.unit_type.value,
                        "base_unit": unit_info.base_unit,
                        "conversion_factor": unit_info.conversion_factor,
                        "aliases": unit_info.aliases
                    }
                    for unit_key, unit_info in self._units.items()
                },
                "validation_rules": {
                    unit: {
                        "min_coefficient": rule.min_coefficient,
                        "max_coefficient": rule.max_coefficient,
                        "typical_range": rule.typical_range,
                        "description": rule.description
                    }
                    for unit, rule in self._validation_rules.items()
                },
                "material_mappings": [
                    {
                        "material_keywords": mapping.material_keywords,
                        "preferred_unit": mapping.preferred_unit,
                        "alternative_units": mapping.alternative_units,
                        "confidence_boost": mapping.confidence_boost,
                        "description": mapping.description
                    }
                    for mapping in self._material_mappings
                ],
                "categories": {
                    "metric_units": list(self._metric_units),
                    "non_metric_units": list(self._non_metric_units),
                    "block_materials": list(self._block_materials)
                }
            }
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Units configuration exported to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_configuration(self, input_path: Union[str, Path]) -> bool:
        """
        Import units configuration from file.
        
        Args:
            input_path: Input file path
            
        Returns:
            bool: True if successful
        """
        input_path = Path(input_path)
        
        try:
            # Check if file exists
            if not input_path.exists():
                self.logger.error(f"Configuration file not found: {input_path}")
                return False
            
            # Load configuration file
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data
            if "units" not in import_data:
                self.logger.error("Invalid configuration file format")
                return False
            
            # Import units
            imported_units = 0
            for unit_key, unit_data in import_data["units"].items():
                try:
                    unit_info = UnitInfo(
                        name=unit_data["name"],
                        symbol=unit_data["symbol"],
                        unit_type=UnitType(unit_data["unit_type"]),
                        base_unit=unit_data.get("base_unit"),
                        conversion_factor=unit_data.get("conversion_factor", 1.0),
                        aliases=unit_data.get("aliases", [])
                    )
                    
                    if self.add_unit(unit_key, unit_info):
                        imported_units += 1
                        
                except Exception as e:
                    self.logger.warning(f"Error importing unit {unit_key}: {e}")
            
            # Import validation rules
            if "validation_rules" in import_data:
                for unit, rule_data in import_data["validation_rules"].items():
                    try:
                        rule = UnitValidationRule(
                            unit=unit,
                            min_coefficient=rule_data["min_coefficient"],
                            max_coefficient=rule_data["max_coefficient"],
                            typical_range=tuple(rule_data["typical_range"]),
                            description=rule_data.get("description", "")
                        )
                        self.add_validation_rule(rule)
                    except Exception as e:
                        self.logger.warning(f"Error importing validation rule for {unit}: {e}")
            
            # Import material mappings
            if "material_mappings" in import_data:
                for mapping_data in import_data["material_mappings"]:
                    try:
                        mapping = MaterialUnitMapping(
                            material_keywords=mapping_data["material_keywords"],
                            preferred_unit=mapping_data["preferred_unit"],
                            alternative_units=mapping_data.get("alternative_units", []),
                            confidence_boost=mapping_data.get("confidence_boost", 0.1),
                            description=mapping_data.get("description", "")
                        )
                        self.add_material_mapping(mapping)
                    except Exception as e:
                        self.logger.warning(f"Error importing material mapping: {e}")
            
            self.logger.info(f"Imported {imported_units} units from configuration")
            return imported_units > 0
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get units manager statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return {
            "service_name": self.service_name,
            "version": self.version,
            "total_units": len(self._units),
            "total_aliases": len(self._unit_aliases),
            "metric_units": len(self._metric_units),
            "non_metric_units": len(self._non_metric_units),
            "validation_rules": len(self._validation_rules),
            "material_mappings": len(self._material_mappings),
            "block_materials": len(self._block_materials),
            "success_rates": {
                "normalization": (
                    self.stats["successful_normalizations"] / self.stats["normalization_requests"]
                    if self.stats["normalization_requests"] > 0 else 0.0
                ),
                "validation": (
                    self.stats["successful_validations"] / self.stats["validation_requests"]
                    if self.stats["validation_requests"] > 0 else 0.0
                ),
                "material_hints": (
                    self.stats["successful_material_hints"] / self.stats["material_hint_requests"]
                    if self.stats["material_hint_requests"] > 0 else 0.0
                )
            },
            "operations": self.stats.copy()
        }
    
    def get_unit_info(self, unit: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a unit.
        
        Args:
            unit: Unit string
            
        Returns:
            Optional[Dict[str, Any]]: Unit information or None if not found
        """
        normalized = self.normalize_unit(unit)
        if not normalized:
            return None
        
        unit_info = self._units.get(normalized)
        if not unit_info:
            return None
        
        return {
            "name": unit_info.name,
            "symbol": unit_info.symbol,
            "unit_type": unit_info.unit_type.value,
            "base_unit": unit_info.base_unit,
            "conversion_factor": unit_info.conversion_factor,
            "aliases": unit_info.aliases,
            "is_metric": normalized in self._metric_units,
            "validation_rule": self._validation_rules.get(normalized)
        }


# Service factory
@lru_cache(maxsize=1)
def get_units_manager() -> UnitsConfigManager:
    """
    Get Units Config Manager instance (singleton).
    
    Returns:
        UnitsConfigManager: Units manager instance
    """
    return UnitsConfigManager()


# Convenience functions
def normalize_unit(unit: str) -> Optional[str]:
    """
    Normalize unit string.
    
    Args:
        unit: Unit to normalize
        
    Returns:
        Optional[str]: Normalized unit or None
    """
    manager = get_units_manager()
    return manager.normalize_unit(unit)


def is_metric_unit(unit: str) -> bool:
    """
    Check if unit is metric.
    
    Args:
        unit: Unit to check
        
    Returns:
        bool: True if metric unit
    """
    manager = get_units_manager()
    return manager.is_metric_unit(unit)


def is_block_material(material_name: str) -> bool:
    """
    Check if material is a block material.
    
    Args:
        material_name: Material name
        
    Returns:
        bool: True if block material
    """
    manager = get_units_manager()
    return manager.is_block_material(material_name)


def get_material_hint(material_name: str) -> Optional[str]:
    """
    Get unit hint for material.
    
    Args:
        material_name: Material name
        
    Returns:
        Optional[str]: Unit hint or None
    """
    manager = get_units_manager()
    return manager.get_material_hint(material_name)


def validate_unit_coefficient(unit: str, coefficient: float) -> bool:
    """
    Validate unit coefficient.
    
    Args:
        unit: Unit string
        coefficient: Coefficient to validate
        
    Returns:
        bool: True if valid
    """
    manager = get_units_manager()
    return manager.validate_unit_coefficient(unit, coefficient)


def get_common_units_for_ai() -> List[str]:
    """
    Get common units for AI prompts.
    
    Returns:
        List[str]: List of common units
    """
    manager = get_units_manager()
    return manager.get_common_units_for_ai() 