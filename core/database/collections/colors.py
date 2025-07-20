"""
Color collection for construction materials reference data.

Коллекция цветов для справочных данных строительных материалов.
"""

import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from core.logging import get_logger

logger = get_logger(__name__)


class ColorCollection:
    """Collection configuration and data generation for construction colors."""
    
    collection_name = "construction_colors"
    
    # Base colors data for construction materials
    BASE_COLORS = [
        {
            "name": "белый",
            "aliases": ["белый", "white", "снежный", "молочный"],
            "hex_code": "#FFFFFF",
            "rgb_values": [255, 255, 255]
        },
        {
            "name": "серый",
            "aliases": ["серый", "gray", "grey", "пепельный"],
            "hex_code": "#808080",
            "rgb_values": [128, 128, 128]
        },
        {
            "name": "черный",
            "aliases": ["черный", "black", "темный"],
            "hex_code": "#000000",
            "rgb_values": [0, 0, 0]
        },
        {
            "name": "красный",
            "aliases": ["красный", "red", "алый"],
            "hex_code": "#FF0000",
            "rgb_values": [255, 0, 0]
        },
        {
            "name": "синий",
            "aliases": ["синий", "blue", "голубой"],
            "hex_code": "#0000FF",
            "rgb_values": [0, 0, 255]
        },
        {
            "name": "зеленый",
            "aliases": ["зеленый", "green", "изумрудный"],
            "hex_code": "#008000",
            "rgb_values": [0, 128, 0]
        },
        {
            "name": "желтый",
            "aliases": ["желтый", "yellow", "золотистый"],
            "hex_code": "#FFFF00",
            "rgb_values": [255, 255, 0]
        },
        {
            "name": "оранжевый",
            "aliases": ["оранжевый", "orange", "морковный"],
            "hex_code": "#FFA500",
            "rgb_values": [255, 165, 0]
        },
        {
            "name": "коричневый",
            "aliases": ["коричневый", "brown", "бурый"],
            "hex_code": "#A52A2A",
            "rgb_values": [165, 42, 42]
        },
        {
            "name": "розовый",
            "aliases": ["розовый", "pink", "малиновый"],
            "hex_code": "#FFC0CB",
            "rgb_values": [255, 192, 203]
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
    def generate_color_data(cls, embedding_generator: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Generate color data with embeddings for population."""
        current_time = datetime.utcnow().isoformat()
        color_data = []
        
        for color_info in cls.BASE_COLORS:
            # Generate embedding if generator provided, otherwise use zeros
            if embedding_generator:
                embedding_text = f"{color_info['name']} {' '.join(color_info['aliases'])}"
                embedding = embedding_generator(embedding_text)
            else:
                embedding = [0.0] * 1536  # Default zero embedding
            
            color_data.append({
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "name": color_info["name"],
                    "aliases": color_info["aliases"],
                    "hex_code": color_info.get("hex_code"),
                    "rgb_values": color_info.get("rgb_values"),
                    "type": "color",
                    "created_at": current_time,
                    "updated_at": current_time
                }
            })
        
        logger.info(f"Generated {len(color_data)} color records")
        return color_data
    
    @classmethod
    def generate_colors_data(cls, embedding_generator: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Alias for generate_color_data for backward compatibility."""
        return cls.generate_color_data(embedding_generator) 