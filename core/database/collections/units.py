"""
Units collection for construction materials reference data.

Коллекция единиц измерения для справочных данных строительных материалов.
"""

import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from core.logging import get_logger

logger = get_logger(__name__)


class UnitsCollection:
    """Collection configuration and data generation for construction units."""
    
    collection_name = "construction_units"
    
    # Base units data for construction materials
    BASE_UNITS = [
        {
            "name": "кг",
            "aliases": ["кг", "kg", "килограмм", "kilogram"],
            "symbol": "kg",
            "description": "Килограмм"
        },
        {
            "name": "шт",
            "aliases": ["шт", "pcs", "штука", "piece"],
            "symbol": "pcs",
            "description": "Штука"
        },
        {
            "name": "м",
            "aliases": ["м", "m", "метр", "meter"],
            "symbol": "m",
            "description": "Метр"
        },
        {
            "name": "м²",
            "aliases": ["м²", "m²", "квадратный метр", "square meter"],
            "symbol": "m²",
            "description": "Квадратный метр"
        },
        {
            "name": "м³",
            "aliases": ["м³", "m³", "кубический метр", "cubic meter"],
            "symbol": "m³",
            "description": "Кубический метр"
        },
        {
            "name": "л",
            "aliases": ["л", "l", "литр", "liter"],
            "symbol": "l",
            "description": "Литр"
        },
        {
            "name": "т",
            "aliases": ["т", "t", "тонна", "ton"],
            "symbol": "t",
            "description": "Тонна"
        },
        {
            "name": "пачка",
            "aliases": ["пачка", "pack", "упаковка"],
            "symbol": "pack",
            "description": "Пачка/упаковка"
        },
        {
            "name": "мешок",
            "aliases": ["мешок", "bag", "мешок цемента"],
            "symbol": "bag",
            "description": "Мешок"
        },
        {
            "name": "рулон",
            "aliases": ["рулон", "roll", "катушка"],
            "symbol": "roll",
            "description": "Рулон"
        },
        {
            "name": "лист",
            "aliases": ["лист", "sheet", "плита"],
            "symbol": "sheet",
            "description": "Лист"
        },
        {
            "name": "блок",
            "aliases": ["блок", "block", "кирпич"],
            "symbol": "block",
            "description": "Блок"
        },
        {
            "name": "пог.м",
            "aliases": ["пог.м", "lm", "погонный метр", "linear meter"],
            "symbol": "lm",
            "description": "Погонный метр"
        },
        {
            "name": "компл",
            "aliases": ["компл", "set", "комплект"],
            "symbol": "set",
            "description": "Комплект"
        },
        {
            "name": "упак",
            "aliases": ["упак", "pack", "упаковка"],
            "symbol": "pack",
            "description": "Упаковка"
        }
    ]
    
    @classmethod
    def get_collection_config(cls) -> Dict[str, Any]:
        """Get collection configuration for Qdrant."""
        return {
            "collection_name": cls.collection_name,
            "vector_size": 1536,  # OpenAI text-embedding-3-small
            "distance": "cosine",
            "on_disk_payload": True
        }
    
    @classmethod
    def generate_units_data(cls, embedding_generator: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Generate units data with embeddings for population."""
        current_time = datetime.utcnow().isoformat()
        units_data = []
        
        for unit_info in cls.BASE_UNITS:
            # Generate embedding if generator provided, otherwise use zeros
            if embedding_generator:
                embedding_text = f"{unit_info['name']} {' '.join(unit_info['aliases'])}"
                embedding = embedding_generator(embedding_text)
            else:
                embedding = [0.0] * 1536  # Default zero embedding
            
            units_data.append({
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "name": unit_info["name"],
                    "aliases": unit_info["aliases"],
                    "symbol": unit_info.get("symbol"),
                    "description": unit_info.get("description"),
                    "type": "unit",
                    "created_at": current_time,
                    "updated_at": current_time
                }
            })
        
        logger.info(f"Generated {len(units_data)} unit records")
        return units_data 