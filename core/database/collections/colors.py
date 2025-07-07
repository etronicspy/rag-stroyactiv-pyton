"""
Color collection for construction materials.

Коллекция цветов для строительных материалов.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.logging import get_logger

logger = get_logger(__name__)


class ColorCollection:
    """Collection of construction material colors.
    
    Коллекция цветов строительных материалов.
    """
    
    collection_name = "construction_colors"
    vector_size = 1536  # OpenAI embedding size
    
    # Base colors with their variations and hex codes
    BASE_COLORS = [
        {
            "name": "белый",
            "hex_code": "#FFFFFF",
            "rgb_values": [255, 255, 255],
            "aliases": ["светлый", "молочный", "снежный", "кремовый", "белоснежный", "белесый"]
        },
        {
            "name": "черный",
            "hex_code": "#000000", 
            "rgb_values": [0, 0, 0],
            "aliases": ["темный", "чёрный", "угольный", "антрацитовый", "сажевый"]
        },
        {
            "name": "серый",
            "hex_code": "#808080",
            "rgb_values": [128, 128, 128], 
            "aliases": ["пепельный", "дымчатый", "стальной", "графитовый", "сизый"]
        },
        {
            "name": "красный",
            "hex_code": "#FF0000",
            "rgb_values": [255, 0, 0],
            "aliases": ["алый", "багровый", "кирпичный", "бордовый", "рубиновый", "вишневый"]
        },
        {
            "name": "синий",
            "hex_code": "#0000FF",
            "rgb_values": [0, 0, 255],
            "aliases": ["голубой", "лазурный", "небесный", "васильковый", "ультрамариновый"]
        },
        {
            "name": "зеленый",
            "hex_code": "#008000",
            "rgb_values": [0, 128, 0],
            "aliases": ["зелёный", "изумрудный", "салатовый", "оливковый", "хаки", "малахитовый"]
        },
        {
            "name": "желтый",
            "hex_code": "#FFFF00",
            "rgb_values": [255, 255, 0],
            "aliases": ["жёлтый", "золотистый", "лимонный", "канареечный", "песочный", "янтарный"]
        },
        {
            "name": "коричневый",
            "hex_code": "#A52A2A",
            "rgb_values": [165, 42, 42],
            "aliases": ["бурый", "шоколадный", "каштановый", "кофейный", "ореховый", "терракотовый"]
        },
        {
            "name": "оранжевый",
            "hex_code": "#FFA500",
            "rgb_values": [255, 165, 0],
            "aliases": ["апельсиновый", "морковный", "персиковый", "медный", "рыжий"]
        },
        {
            "name": "фиолетовый",
            "hex_code": "#800080",
            "rgb_values": [128, 0, 128],
            "aliases": ["лиловый", "сиреневый", "пурпурный", "баклажанный", "аметистовый"]
        },
        {
            "name": "розовый",
            "hex_code": "#FFC0CB",
            "rgb_values": [255, 192, 203],
            "aliases": ["нежно-розовый", "лососевый", "пудровый", "фуксиевый"]
        },
        {
            "name": "бежевый",
            "hex_code": "#F5F5DC",
            "rgb_values": [245, 245, 220],
            "aliases": ["телесный", "песочный", "кремовый", "слоновой кости"]
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
    def generate_color_data(cls, embedding_generator=None) -> List[Dict[str, Any]]:
        """Generate color data with embeddings.
        
        Генерировать данные цветов с эмбеддингами.
        
        Args:
            embedding_generator: Function to generate embeddings
            
        Returns:
            List of color data dictionaries
        """
        colors_data = []
        current_time = datetime.utcnow()
        
        for color_info in cls.BASE_COLORS:
            color_id = str(uuid.uuid4())
            
            # Create embedding text from name and aliases
            embedding_text = f"{color_info['name']} {' '.join(color_info['aliases'])}"
            
            # Generate embedding if generator provided
            embedding = None
            if embedding_generator:
                try:
                    embedding = embedding_generator(embedding_text)
                    logger.debug(f"Generated embedding for color: {color_info['name']}")
                except Exception as e:
                    logger.error(f"Failed to generate embedding for color {color_info['name']}: {e}")
                    # Use default embedding as fallback
                    embedding = [0.0] * cls.vector_size
            else:
                # Use default embedding if no generator
                embedding = [0.0] * cls.vector_size
            
            color_data = {
                "id": color_id,
                "vector": embedding,
                "payload": {
                    "name": color_info["name"],
                    "hex_code": color_info["hex_code"],
                    "rgb_values": color_info["rgb_values"],
                    "aliases": color_info["aliases"],
                    "created_at": current_time.isoformat(),
                    "updated_at": current_time.isoformat()
                }
            }
            
            colors_data.append(color_data)
            logger.info(f"Prepared color data: {color_info['name']} with {len(color_info['aliases'])} aliases")
        
        return colors_data
    
    @classmethod
    def get_color_names(cls) -> List[str]:
        """Get list of all color names including aliases.
        
        Получить список всех названий цветов включая синонимы.
        """
        all_names = []
        for color_info in cls.BASE_COLORS:
            all_names.append(color_info["name"])
            all_names.extend(color_info["aliases"])
        return all_names
    
    @classmethod
    def get_base_color_names(cls) -> List[str]:
        """Get list of base color names only.
        
        Получить список только основных названий цветов.
        """
        return [color_info["name"] for color_info in cls.BASE_COLORS]
    
    @classmethod
    def find_color_by_alias(cls, alias: str) -> Optional[str]:
        """Find base color name by alias.
        
        Найти основное название цвета по синониму.
        
        Args:
            alias: Color alias to search for
            
        Returns:
            Base color name if found, None otherwise
        """
        alias_lower = alias.lower().strip()
        
        for color_info in cls.BASE_COLORS:
            # Check exact name match
            if color_info["name"].lower() == alias_lower:
                return color_info["name"]
            
            # Check aliases
            for color_alias in color_info["aliases"]:
                if color_alias.lower() == alias_lower:
                    return color_info["name"]
        
        return None
    
    @classmethod
    def get_color_info(cls, color_name: str) -> Optional[Dict[str, Any]]:
        """Get complete color information by name.
        
        Получить полную информацию о цвете по названию.
        
        Args:
            color_name: Color name to search for
            
        Returns:
            Color information dictionary if found, None otherwise
        """
        color_name_lower = color_name.lower().strip()
        
        for color_info in cls.BASE_COLORS:
            if color_info["name"].lower() == color_name_lower:
                return color_info.copy()
        
        return None
    
    @classmethod
    def validate_color_name(cls, color_name: str) -> bool:
        """Validate if color name exists in collection.
        
        Проверить существует ли название цвета в коллекции.
        
        Args:
            color_name: Color name to validate
            
        Returns:
            True if color exists, False otherwise
        """
        return cls.find_color_by_alias(color_name) is not None 