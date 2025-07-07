"""
System Prompts for AI Material Parser

This module contains system prompts and prompt templates for the AI material parser.
All prompts are centralized here for easy maintenance and updates.
"""

from typing import List


def get_material_parsing_system_prompt(common_units: List[str]) -> str:
    """
    Get the main system prompt for material parsing
    
    Args:
        common_units: List of supported units
        
    Returns:
        System prompt string
    """
    units_text = ', '.join(common_units)
    
    return f"""
Ты эксперт по строительным материалам. Анализируй названия товаров и извлекай метрические единицы измерения.

ВОЗВРАЩАЙ ТОЛЬКО ВАЛИДНЫЙ JSON в формате:
{{
    "unit_parsed": "единица_измерения",
    "price_coefficient": число,
    "confidence": число_от_0_до_1
}}

ПОДДЕРЖИВАЕМЫЕ ЕДИНИЦЫ: {units_text}

ВАЖНО! ЛОГИКА КОЭФФИЦИЕНТА:
price_coefficient = количество метрических единиц в 1 исходной единице
Примеры:
- "Цемент 50кг" (продается за мешок) → коэффициент 50 (в 1 мешке = 50 кг)
- "Кирпич объемом 0.00195 м³" (продается за штуку) → коэффициент 0.00195 (в 1 шт = 0.00195 м³)

ПРАВИЛА ИЗВЛЕЧЕНИЯ:
1. Явные единицы: "50кг" → кг, коэффициент 50
2. БЛОЧНЫЕ МАТЕРИАЛЫ → ВСЕГДА м3 (объем):
   - Кирпич, газобетон, пеноблок, шлакоблок, керамзитобетон
   - Блоки, камни, бруски, плиты, панели, элементы, модули
   - Если есть размеры → рассчитать объем в м³
   - Если нет размеров → стандартный объем (например, кирпич = 0.00195 м³)
3. Размеры для объема: "600x300x200" → м3, рассчитать объем в м³
4. Размеры для площади: листы/плиты ≤50мм → м2, рассчитать площадь в м²
5. Жидкости: "850мл" → л, перевести в литры
6. Рулоны: "1x15м" → м2, рассчитать площадь
7. Если единица не извлекается → "шт", коэффициент 1.0

РАСЧЕТЫ:
- Объем (м³): длина×ширина×высота ÷ 1,000,000,000 (если размеры в мм)
- Площадь (м²): длина×ширина ÷ 1,000,000 (если размеры в мм)
- Стандартный кирпич: 250×120×65мм = 0.00195 м³
- Стандартный газобетонный блок: 600×300×200мм = 0.036 м³

ПРИМЕРЫ БЛОЧНЫХ МАТЕРИАЛОВ:
- "Кирпич керамический" → м3, коэффициент 0.00195
- "Газобетон 600x300x200" → м3, коэффициент 0.036
- "Пеноблок строительный" → м3, коэффициент 0.036
- "Шлакоблок полнотелый" → м3, коэффициент 0.014

CONFIDENCE:
- 0.9+ : явные единицы в названии
- 0.7-0.9 : размеры с явным контекстом или известный блочный материал
- 0.5-0.7 : размеры без четкого контекста
- 0.3-0.5 : предположения по типу материала
- <0.3 : сложные случаи

Отвечай ТОЛЬКО JSON без дополнительного текста.
"""


def get_material_parsing_user_prompt(name: str, unit: str, material_hint: str = None, is_block: bool = False) -> str:
    """
    Get user prompt for specific material parsing
    
    Args:
        name: Material name
        unit: Original unit
        material_hint: Unit hint for the material
        is_block: Whether material is a block material
        
    Returns:
        User prompt string
    """
    hint_text = f"\nПодсказка по материалу: {material_hint}" if material_hint else ""
    block_text = f"\nВНИМАНИЕ: Это блочный материал - используй м3 (объем)!" if is_block else ""
    
    return f"""
Товар: "{name}"
Единица в прайсе: "{unit}"
Цена: Указана за единицу "{unit}"{hint_text}{block_text}

Извлеки метрическую единицу измерения и рассчитай коэффициент для пересчета цены.
"""


def get_embeddings_system_prompt() -> str:
    """
    Get system prompt for embeddings generation
    
    Returns:
        System prompt for embeddings
    """
    return """
Ты создаешь эмбеддинги для строительных материалов. 
Фокусируйся на ключевых характеристиках материала:
- Тип материала (цемент, кирпич, утеплитель и т.д.)
- Назначение (строительство, отделка, изоляция)
- Основные свойства (прочность, теплоизоляция, водостойкость)
- Размеры и форма
- Материал изготовления
"""


# Prompt templates for different material types
MATERIAL_TYPE_PROMPTS = {
    "block_materials": """
    БЛОЧНЫЕ МАТЕРИАЛЫ - СПЕЦИАЛЬНЫЕ ПРАВИЛА:
    - Всегда переводить в м³ (объем)
    - Рассчитывать объем по размерам если указаны
    - Использовать стандартные объемы для типовых изделий
    - Примеры: кирпич, газобетон, пеноблок, шлакоблок
    """,
    
    "liquid_materials": """
    ЖИДКИЕ МАТЕРИАЛЫ - СПЕЦИАЛЬНЫЕ ПРАВИЛА:
    - Переводить в литры (л)
    - Учитывать плотность для расчета объема
    - Примеры: краски, лаки, грунтовки, растворители
    """,
    
    "sheet_materials": """
    ЛИСТОВЫЕ МАТЕРИАЛЫ - СПЕЦИАЛЬНЫЕ ПРАВИЛА:
    - Переводить в м² (площадь)
    - Рассчитывать площадь по размерам листа
    - Примеры: фанера, OSB, гипсокартон, профлист
    """,
    
    "bulk_materials": """
    СЫПУЧИЕ МАТЕРИАЛЫ - СПЕЦИАЛЬНЫЕ ПРАВИЛА:
    - Переводить в кг (вес) или м³ (объем)
    - Учитывать насыпную плотность
    - Примеры: песок, щебень, цемент, сухие смеси
    """
}


def get_specialized_prompt(material_type: str) -> str:
    """
    Get specialized prompt for specific material type
    
    Args:
        material_type: Type of material
        
    Returns:
        Specialized prompt or empty string if not found
    """
    return MATERIAL_TYPE_PROMPTS.get(material_type, "")


# Common parsing patterns for different units
UNIT_PARSING_PATTERNS = {
    "weight_patterns": [
        r"(\d+(?:\.\d+)?)\s*кг",
        r"(\d+(?:\.\d+)?)\s*г",
        r"(\d+(?:\.\d+)?)\s*т",
        r"(\d+(?:\.\d+)?)\s*килограмм",
        r"(\d+(?:\.\d+)?)\s*грамм",
        r"(\d+(?:\.\d+)?)\s*тонн"
    ],
    
    "volume_patterns": [
        r"(\d+(?:\.\d+)?)\s*л",
        r"(\d+(?:\.\d+)?)\s*мл",
        r"(\d+(?:\.\d+)?)\s*литр",
        r"(\d+(?:\.\d+)?)\s*м3",
        r"(\d+(?:\.\d+)?)\s*м³"
    ],
    
    "area_patterns": [
        r"(\d+(?:\.\d+)?)\s*м2",
        r"(\d+(?:\.\d+)?)\s*м²",
        r"(\d+(?:\.\d+)?)\s*кв\.?м"
    ],
    
    "dimension_patterns": [
        r"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)",  # 3D dimensions
        r"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)",  # 2D dimensions
        r"(\d+(?:\.\d+)?)\s*х\s*(\d+(?:\.\d+)?)\s*х\s*(\d+(?:\.\d+)?)",  # Russian x
        r"(\d+(?:\.\d+)?)\s*х\s*(\d+(?:\.\d+)?)"  # Russian x 2D
    ]
}


def get_parsing_patterns() -> dict:
    """
    Get all parsing patterns for unit extraction
    
    Returns:
        Dictionary of parsing patterns
    """
    return UNIT_PARSING_PATTERNS 