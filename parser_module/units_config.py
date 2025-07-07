"""
Units Configuration for AI Material Parser

This module contains comprehensive unit standards, aliases, and conversion factors
for construction materials. Used for validation and normalization of parsed units.
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class UnitType(Enum):
    """Categories of measurement units"""
    WEIGHT = "weight"
    VOLUME = "volume"
    AREA = "area"
    LENGTH = "length"
    COUNT = "count"
    PACKAGING = "packaging"
    LIQUID = "liquid"


@dataclass
class UnitInfo:
    """Information about a measurement unit"""
    name: str
    symbol: str
    unit_type: UnitType
    base_unit: Optional[str] = None
    conversion_factor: float = 1.0
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


# Standard units with detailed information
STANDARD_UNITS: Dict[str, UnitInfo] = {
    # Weight units
    "кг": UnitInfo("кг", "kg", UnitType.WEIGHT, aliases=["килограмм", "кило"]),
    "г": UnitInfo("г", "g", UnitType.WEIGHT, "кг", 0.001, aliases=["грамм"]),
    "т": UnitInfo("т", "t", UnitType.WEIGHT, "кг", 1000.0, aliases=["тонна", "тонн"]),
    
    # Volume units
    "м3": UnitInfo("м3", "m³", UnitType.VOLUME, aliases=["куб.м", "кубометр", "куб", "м³"]),
    "л": UnitInfo("л", "l", UnitType.LIQUID, aliases=["литр", "литра", "литров"]),
    "мл": UnitInfo("мл", "ml", UnitType.LIQUID, "л", 0.001, aliases=["миллилитр"]),
    
    # Area units
    "м2": UnitInfo("м2", "m²", UnitType.AREA, aliases=["кв.м", "квадрат", "м²"]),
    "см2": UnitInfo("см2", "cm²", UnitType.AREA, "м2", 0.0001, aliases=["кв.см"]),
    
    # Length units
    "м": UnitInfo("м", "m", UnitType.LENGTH, aliases=["метр", "метра", "метров"]),
    "см": UnitInfo("см", "cm", UnitType.LENGTH, "м", 0.01, aliases=["сантиметр"]),
    "мм": UnitInfo("мм", "mm", UnitType.LENGTH, "м", 0.001, aliases=["миллиметр"]),
    "пог.м": UnitInfo("пог.м", "m.p.", UnitType.LENGTH, aliases=["п.м", "погонный метр"]),
    
    # Count units
    "шт": UnitInfo("шт", "pcs", UnitType.COUNT, aliases=["штука", "штук", "штуки", "шт."]),
    
    # Packaging units
    "упак": UnitInfo("упак", "pack", UnitType.PACKAGING, aliases=["упаковка", "упаковки"]),
    "меш": UnitInfo("меш", "bag", UnitType.PACKAGING, aliases=["мешок", "мешка", "мешков"]),
    "рулон": UnitInfo("рулон", "roll", UnitType.PACKAGING, aliases=["рулона", "рулонов"]),
    "лист": UnitInfo("лист", "sheet", UnitType.PACKAGING, aliases=["листа", "листов"]),
    "банка": UnitInfo("банка", "can", UnitType.PACKAGING, aliases=["банки", "банок"]),
    "тюбик": UnitInfo("тюбик", "tube", UnitType.PACKAGING, aliases=["тюбика", "тюбиков"]),
    "ведро": UnitInfo("ведро", "bucket", UnitType.PACKAGING, aliases=["ведра", "ведер"]),
    "коробка": UnitInfo("коробка", "box", UnitType.PACKAGING, aliases=["коробки", "коробок"]),
    "пачка": UnitInfo("пачка", "pack", UnitType.PACKAGING, aliases=["пачки", "пачек"]),
    "палета": UnitInfo("палета", "pallet", UnitType.PACKAGING, aliases=["палеты", "поддон"]),
}

# Unit aliases for quick lookup
UNIT_ALIASES: Dict[str, str] = {}
for unit_key, unit_info in STANDARD_UNITS.items():
    # Add main name
    UNIT_ALIASES[unit_info.name] = unit_key
    UNIT_ALIASES[unit_info.symbol] = unit_key
    
    # Add aliases
    for alias in unit_info.aliases:
        UNIT_ALIASES[alias.lower()] = unit_key

# Metric units that require coefficient calculation
METRIC_UNITS: Set[str] = {
    "кг", "г", "т",      # Weight
    "м3", "л", "мл",     # Volume/Liquid
    "м2", "см2",         # Area
    "м", "см", "мм", "пог.м"  # Length
}

# Non-metric units (packaging, count)
NON_METRIC_UNITS: Set[str] = {
    "шт", "упак", "меш", "рулон", "лист", "банка", 
    "тюбик", "ведро", "коробка", "пачка", "палета"
}

# Units that typically indicate quantity in product names
QUANTITY_INDICATORS: Dict[str, str] = {
    "кг": "кг",
    "л": "л",
    "мл": "мл",
    "г": "г",
    "т": "т",
    "м3": "м3",
    "м³": "м3",
    "м2": "м2",
    "м²": "м2",
    "куб": "м3",
    "литр": "л",
    "грамм": "г",
    "тонна": "т",
    "килограмм": "кг"
}

# Block materials that should be measured in volume (м³)
BLOCK_MATERIALS: Set[str] = {
    "кирпич", "кирпича", "кирпичный", "кирпичная", "кирпичное",
    "газобетон", "газобетонный", "газобетонная", "газобетонное",
    "пеноблок", "пеноблока", "пеноблочный", "пеноблочная",
    "шлакоблок", "шлакоблока", "шлакоблочный", "шлакоблочная",
    "керамзитобетон", "керамзитобетонный", "керамзитобетонная", "керамзитобетонное",
    "блок", "блока", "блоков", "блочный", "блочная", "блочное",
    "камень", "камня", "каменный", "каменная", "каменное",
    "брусок", "бруска", "брусков", "брусковый", "брусковая",
    "плита", "плиты", "плитный", "плитная", "плитное",
    "панель", "панели", "панельный", "панельная", "панельное",
    "элемент", "элемента", "элементов", "элементный", "элементная",
    "модуль", "модуля", "модулей", "модульный", "модульная",
    "сегмент", "сегмента", "сегментов", "сегментный", "сегментная"
}

# Material-specific unit hints
MATERIAL_UNIT_HINTS: Dict[str, str] = {
    "цемент": "кг",
    "кирпич": "м3",  # Updated for volume
    "газобетон": "м3",  # Updated for volume
    "пеноблок": "м3",  # Updated for volume
    "шлакоблок": "м3",  # Updated for volume
    "утеплитель": "м2",
    "рубероид": "м2",
    "мастика": "кг",
    "пена": "шт",
    "клей": "кг",
    "краска": "л",
    "лак": "л",
    "грунтовка": "л",
    "шпаклевка": "кг",
    "плитка": "м2",
    "ламинат": "м2",
    "паркет": "м2",
    "линолеум": "м2",
    "обои": "м2",
    "профиль": "м",
    "труба": "м",
    "кабель": "м",
    "провод": "м",
    "арматура": "кг",
    "сетка": "м2",
    "пленка": "м2",
    "геотекстиль": "м2"
}


def normalize_unit(unit: str) -> Optional[str]:
    """
    Normalize unit string to standard format
    
    Args:
        unit: Input unit string
        
    Returns:
        Normalized unit or None if not found
    """
    if not unit:
        return None
    
    # Clean and lowercase
    unit_clean = unit.strip().lower()
    
    # Direct lookup
    if unit_clean in UNIT_ALIASES:
        return UNIT_ALIASES[unit_clean]
    
    # Try partial matching for common variations
    for alias, standard in UNIT_ALIASES.items():
        if unit_clean in alias or alias in unit_clean:
            return standard
    
    return None


def is_metric_unit(unit: str) -> bool:
    """Check if unit is a metric unit requiring coefficient calculation"""
    normalized = normalize_unit(unit)
    return normalized in METRIC_UNITS if normalized else False


def is_packaging_unit(unit: str) -> bool:
    """Check if unit is a packaging/count unit"""
    normalized = normalize_unit(unit)
    return normalized in NON_METRIC_UNITS if normalized else False


def get_unit_type(unit: str) -> Optional[UnitType]:
    """Get the type of a unit"""
    normalized = normalize_unit(unit)
    if normalized and normalized in STANDARD_UNITS:
        return STANDARD_UNITS[normalized].unit_type
    return None


def is_block_material(material_name: str) -> bool:
    """
    Check if material is a block material that should be measured in volume (м³)
    
    Args:
        material_name: Name of the material
        
    Returns:
        True if material is a block material, False otherwise
    """
    material_lower = material_name.lower()
    
    # Check for block material keywords
    for block_keyword in BLOCK_MATERIALS:
        if block_keyword in material_lower:
            return True
    
    return False


def get_material_hint(material_name: str) -> Optional[str]:
    """Get unit hint based on material name"""
    material_lower = material_name.lower()
    
    # First check if it's a block material
    if is_block_material(material_name):
        return "м3"
    
    # Then check regular material hints
    for keyword, unit in MATERIAL_UNIT_HINTS.items():
        if keyword in material_lower:
            return unit
    
    return None


def validate_unit_coefficient(unit: str, coefficient: float) -> bool:
    """
    Validate if coefficient makes sense for the unit
    
    Args:
        unit: Unit string
        coefficient: Coefficient value
        
    Returns:
        True if valid, False otherwise
    """
    if coefficient <= 0:
        return False
    
    normalized = normalize_unit(unit)
    if not normalized:
        return False
    
    # Reasonable ranges for different unit types
    unit_type = get_unit_type(unit)
    if unit_type == UnitType.WEIGHT:
        return 0.001 <= coefficient <= 10000  # 1g to 10 tons
    elif unit_type == UnitType.VOLUME:
        return 0.001 <= coefficient <= 1000   # 1ml to 1000L
    elif unit_type == UnitType.AREA:
        return 0.0001 <= coefficient <= 10000 # 1cm² to 1 hectare
    elif unit_type == UnitType.LENGTH:
        return 0.001 <= coefficient <= 1000   # 1mm to 1km
    else:
        return 0.1 <= coefficient <= 10000    # General range
    

def get_common_units_for_ai() -> List[str]:
    """Get list of common units for AI parsing instructions"""
    return [
        "кг", "г", "т",           # Weight
        "м3", "л", "мл",          # Volume/Liquid
        "м2", "см2",              # Area
        "м", "см", "мм", "пог.м", # Length
        "шт", "упак", "меш"       # Count/Packaging
    ]


def get_all_unit_aliases() -> List[str]:
    """Get all unit aliases for AI context"""
    return list(UNIT_ALIASES.keys()) 