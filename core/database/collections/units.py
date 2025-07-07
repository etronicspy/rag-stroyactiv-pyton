"""
Units collection for construction materials.

Коллекция единиц измерения для строительных материалов.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.logging import get_logger

logger = get_logger(__name__)


class UnitsCollection:
    """Collection of construction material units.
    
    Коллекция единиц измерения строительных материалов.
    """
    
    collection_name = "construction_units"
    vector_size = 1536  # OpenAI embedding size
    
    # Base units with their variations and descriptions
    BASE_UNITS = [
        {
            "name": "кг",
            "full_name": "килограмм",
            "type": "weight",
            "description": "Единица измерения массы",
            "aliases": ["килограмм", "кило", "kg", "килограммы", "килограммов"]
        },
        {
            "name": "м³",
            "full_name": "кубический метр",
            "type": "volume",
            "description": "Единица измерения объема",
            "aliases": ["куб", "кубометр", "м3", "куб.м", "кубический метр", "кубометры", "кубометров"]
        },
        {
            "name": "м²",
            "full_name": "квадратный метр",
            "type": "area",
            "description": "Единица измерения площади",
            "aliases": ["квадрат", "кв.м", "м2", "квадратный метр", "квадратные метры", "квадратных метров"]
        },
        {
            "name": "шт",
            "full_name": "штука",
            "type": "count",
            "description": "Единица штучного счета",
            "aliases": ["штука", "штук", "штуки", "pcs", "piece", "pieces"]
        },
        {
            "name": "м",
            "full_name": "метр",
            "type": "length",
            "description": "Единица измерения длины",
            "aliases": ["метр", "метры", "метров", "погонный", "пог.м", "п.м", "meter"]
        },
        {
            "name": "л",
            "full_name": "литр",
            "type": "volume",
            "description": "Единица измерения объема жидкости",
            "aliases": ["литр", "литры", "литров", "liter", "litre"]
        },
        {
            "name": "т",
            "full_name": "тонна",
            "type": "weight",
            "description": "Единица измерения большой массы",
            "aliases": ["тонна", "тонны", "тонн", "ton", "tons"]
        },
        {
            "name": "мешок",
            "full_name": "мешок",
            "type": "package",
            "description": "Упаковочная единица",
            "aliases": ["меш", "мешки", "мешков", "bag", "bags"]
        },
        {
            "name": "упак",
            "full_name": "упаковка",
            "type": "package",
            "description": "Единица упаковки",
            "aliases": ["упаковка", "упаковки", "упаковок", "package", "pack", "пакет"]
        },
        {
            "name": "рулон",
            "full_name": "рулон",
            "type": "package",
            "description": "Рулонная упаковка",
            "aliases": ["рулоны", "рулонов", "roll", "rolls"]
        },
        {
            "name": "лист",
            "full_name": "лист",
            "type": "count",
            "description": "Листовая единица",
            "aliases": ["листы", "листов", "sheet", "sheets"]
        },
        {
            "name": "пачка",
            "full_name": "пачка",
            "type": "package",
            "description": "Пачечная упаковка",
            "aliases": ["пачки", "пачек", "bundle", "bundles"]
        },
        {
            "name": "ведро",
            "full_name": "ведро",
            "type": "package",
            "description": "Ведерная упаковка",
            "aliases": ["ведра", "ведер", "bucket", "buckets"]
        },
        {
            "name": "банка",
            "full_name": "банка",
            "type": "package",
            "description": "Банковая упаковка",
            "aliases": ["банки", "банок", "jar", "jars", "can", "cans"]
        },
        {
            "name": "тюбик",
            "full_name": "тюбик",
            "type": "package",
            "description": "Тюбиковая упаковка",
            "aliases": ["тюбики", "тюбиков", "tube", "tubes"]
        },
        {
            "name": "палета",
            "full_name": "палета",
            "type": "package",
            "description": "Паллетная упаковка",
            "aliases": ["палет", "паллета", "паллет", "pallet", "pallets"]
        },
        {
            "name": "коробка",
            "full_name": "коробка",
            "type": "package",
            "description": "Коробочная упаковка",
            "aliases": ["коробки", "коробок", "box", "boxes"]
        }
    ]
    
    @classmethod
    def get_collection_config(cls) -> Dict[str, Any]:
        """Get Qdrant collection configuration.
        
        Получить конфигурацию коллекции Qdrant.
        """
        return {
            "collection_name": cls.collection_name,
            "vector_size": cls.vector_size,
            "distance": "Cosine",
            "on_disk_payload": True
        }
    
    @classmethod
    def generate_units_data(cls, embedding_generator=None) -> List[Dict[str, Any]]:
        """Generate units data with embeddings.
        
        Генерировать данные единиц с эмбеддингами.
        
        Args:
            embedding_generator: Function to generate embeddings
            
        Returns:
            List of units data dictionaries
        """
        units_data = []
        current_time = datetime.utcnow()
        
        for unit_info in cls.BASE_UNITS:
            unit_id = str(uuid.uuid4())
            
            # Create embedding text from name, full_name, and aliases
            embedding_text = f"{unit_info['name']} {unit_info['full_name']} {unit_info['description']} {' '.join(unit_info['aliases'])}"
            
            # Generate embedding if generator provided
            embedding = None
            if embedding_generator:
                try:
                    embedding = embedding_generator(embedding_text)
                    logger.debug(f"Generated embedding for unit: {unit_info['name']}")
                except Exception as e:
                    logger.error(f"Failed to generate embedding for unit {unit_info['name']}: {e}")
                    # Use default embedding as fallback
                    embedding = [0.0] * cls.vector_size
            else:
                # Use default embedding if no generator
                embedding = [0.0] * cls.vector_size
            
            unit_data = {
                "id": unit_id,
                "vector": embedding,
                "payload": {
                    "name": unit_info["name"],
                    "full_name": unit_info["full_name"],
                    "type": unit_info["type"],
                    "description": unit_info["description"],
                    "aliases": unit_info["aliases"],
                    "created_at": current_time.isoformat(),
                    "updated_at": current_time.isoformat()
                }
            }
            
            units_data.append(unit_data)
            logger.info(f"Prepared unit data: {unit_info['name']} ({unit_info['full_name']}) with {len(unit_info['aliases'])} aliases")
        
        return units_data
    
    @classmethod
    def get_unit_names(cls) -> List[str]:
        """Get list of all unit names including aliases.
        
        Получить список всех названий единиц включая синонимы.
        """
        all_names = []
        for unit_info in cls.BASE_UNITS:
            all_names.append(unit_info["name"])
            all_names.append(unit_info["full_name"])
            all_names.extend(unit_info["aliases"])
        return all_names
    
    @classmethod
    def get_base_unit_names(cls) -> List[str]:
        """Get list of base unit names only.
        
        Получить список только основных названий единиц.
        """
        return [unit_info["name"] for unit_info in cls.BASE_UNITS]
    
    @classmethod
    def find_unit_by_alias(cls, alias: str) -> Optional[str]:
        """Find base unit name by alias.
        
        Найти основное название единицы по синониму.
        
        Args:
            alias: Unit alias to search for
            
        Returns:
            Base unit name if found, None otherwise
        """
        alias_lower = alias.lower().strip()
        
        for unit_info in cls.BASE_UNITS:
            # Check exact name match
            if unit_info["name"].lower() == alias_lower:
                return unit_info["name"]
            
            # Check full name match
            if unit_info["full_name"].lower() == alias_lower:
                return unit_info["name"]
            
            # Check aliases
            for unit_alias in unit_info["aliases"]:
                if unit_alias.lower() == alias_lower:
                    return unit_info["name"]
        
        return None
    
    @classmethod
    def get_unit_info(cls, unit_name: str) -> Optional[Dict[str, Any]]:
        """Get complete unit information by name.
        
        Получить полную информацию о единице по названию.
        
        Args:
            unit_name: Unit name to search for
            
        Returns:
            Unit information dictionary if found, None otherwise
        """
        unit_name_lower = unit_name.lower().strip()
        
        for unit_info in cls.BASE_UNITS:
            if unit_info["name"].lower() == unit_name_lower:
                return unit_info.copy()
        
        return None
    
    @classmethod
    def get_units_by_type(cls, unit_type: str) -> List[Dict[str, Any]]:
        """Get units by type.
        
        Получить единицы по типу.
        
        Args:
            unit_type: Type of units (weight, volume, area, count, length, package)
            
        Returns:
            List of units of specified type
        """
        return [unit_info for unit_info in cls.BASE_UNITS if unit_info["type"] == unit_type]
    
    @classmethod
    def validate_unit_name(cls, unit_name: str) -> bool:
        """Validate if unit name exists in collection.
        
        Проверить существует ли название единицы в коллекции.
        
        Args:
            unit_name: Unit name to validate
            
        Returns:
            True if unit exists, False otherwise
        """
        return cls.find_unit_by_alias(unit_name) is not None
    
    @classmethod
    def get_unit_mappings(cls) -> Dict[str, List[str]]:
        """Get unit mappings for compatibility with existing code.
        
        Получить сопоставления единиц для совместимости с существующим кодом.
        
        Returns:
            Dictionary mapping standard unit names to their aliases
        """
        mappings = {}
        for unit_info in cls.BASE_UNITS:
            mappings[unit_info["name"]] = unit_info["aliases"]
        return mappings
    
    @classmethod
    def normalize_unit_simple(cls, unit_text: str) -> Optional[str]:
        """Simple unit normalization without embeddings.
        
        Простая нормализация единицы без эмбеддингов.
        
        Args:
            unit_text: Unit text to normalize
            
        Returns:
            Normalized unit name if found, None otherwise
        """
        if not unit_text:
            return None
        
        unit_text_clean = unit_text.strip().lower()
        
        # Direct alias lookup
        normalized = cls.find_unit_by_alias(unit_text_clean)
        if normalized:
            return normalized
        
        # Fuzzy matching for common variations
        for unit_info in cls.BASE_UNITS:
            unit_name = unit_info["name"].lower()
            unit_full = unit_info["full_name"].lower()
            
            # Check if input contains unit name
            if unit_name in unit_text_clean or unit_text_clean in unit_name:
                return unit_info["name"]
            
            # Check if input contains full name
            if unit_full in unit_text_clean or unit_text_clean in unit_full:
                return unit_info["name"]
            
            # Check aliases
            for alias in unit_info["aliases"]:
                alias_lower = alias.lower()
                if alias_lower in unit_text_clean or unit_text_clean in alias_lower:
                    return unit_info["name"]
        
        return None 