"""Common utilities for the RAG Construction Materials API.

Общие утилиты для RAG API строительных материалов.
"""

import hashlib
import logging
import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from difflib import SequenceMatcher
import numpy as np

logger = logging.getLogger(__name__)


# === Text Processing Utilities ===

def truncate_text(text: str, max_length: int = 30) -> str:
    """Truncate text with ellipsis if it exceeds max_length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length-3] + "..."


def clean_text(text: str) -> str:
    """Clean and normalize text for processing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters but keep Russian and English letters, numbers, and basic punctuation
    text = re.sub(r'[^\w\s\-.,()№]', '', text)
    
    return text


def normalize_unit(unit: str) -> str:
    """Normalize unit of measurement to standard format.
    
    Args:
        unit: Unit to normalize
        
    Returns:
        Normalized unit
    """
    if not unit:
        return "шт"
    
    unit_mapping = {
        "штука": "шт",
        "штук": "шт",
        "piece": "шт",
        "pieces": "шт",
        "кг": "кг",
        "килограмм": "кг",
        "kg": "кг",
        "тонна": "т",
        "тонн": "т",
        "ton": "т",
        "tons": "т",
        "м": "м",
        "метр": "м",
        "метров": "м",
        "meter": "м",
        "meters": "м",
        "м²": "м²",
        "м2": "м²",
        "кв.м": "м²",
        "квадратный метр": "м²",
        "м³": "м³",
        "м3": "м³",
        "куб.м": "м³",
        "кубический метр": "м³",
        "литр": "л",
        "литров": "л",
        "l": "л",
        "liters": "л"
    }
    
    unit_lower = unit.lower().strip()
    return unit_mapping.get(unit_lower, unit)


# === Price and Number Formatting ===

def format_price(price: Union[int, float], currency: str = "₽") -> str:
    """Format price with currency symbol.
    
    Args:
        price: Price value
        currency: Currency symbol
        
    Returns:
        Formatted price string
    """
    if price is None:
        return "N/A"
    
    try:
        price_float = float(price)
        if price_float >= 1000000:
            return f"{price_float/1000000:.1f}M {currency}"
        elif price_float >= 1000:
            return f"{price_float/1000:.1f}K {currency}"
        else:
            return f"{price_float:.2f} {currency}"
    except (ValueError, TypeError):
        return str(price)


def parse_price(price_str: str) -> Optional[float]:
    """Parse price string to float value.
    
    Args:
        price_str: Price string to parse
        
    Returns:
        Parsed price or None if invalid
    """
    if not price_str:
        return None
    
    # Remove currency symbols and spaces
    cleaned = re.sub(r'[₽$€£\s,]', '', str(price_str))
    
    try:
        return float(cleaned)
    except ValueError:
        return None


# === Vector and Similarity Utilities ===

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    try:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # Handle zero vectors
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(v1, v2) / (norm1 * norm2))
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0


def calculate_cosine_similarity_batch(vectors1: List[List[float]], 
                                    vectors2: List[List[float]]) -> List[List[float]]:
    """Calculate cosine similarity for batches of vectors efficiently.
    
    Args:
        vectors1: First batch of vectors
        vectors2: Second batch of vectors
        
    Returns:
        Matrix of similarity scores
    """
    try:
        v1_array = np.array(vectors1)
        v2_array = np.array(vectors2)
        
        # Normalize vectors
        v1_norm = v1_array / np.linalg.norm(v1_array, axis=1, keepdims=True)
        v2_norm = v2_array / np.linalg.norm(v2_array, axis=1, keepdims=True)
        
        # Calculate cosine similarity matrix
        similarities = np.dot(v1_norm, v2_norm.T)
        
        return similarities.tolist()
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity batch: {e}")
        return [[0.0] * len(vectors2) for _ in vectors1]


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using SequenceMatcher.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


# === Confidence and Quality Scoring ===

def format_confidence(score: float, 
                     high_threshold: float = 0.85, 
                     medium_threshold: float = 0.70) -> str:
    """Determine confidence level based on score.
    
    Args:
        score: Similarity or confidence score
        high_threshold: Threshold for high confidence
        medium_threshold: Threshold for medium confidence
        
    Returns:
        Confidence level string
    """
    if score >= high_threshold:
        return "high"
    elif score >= medium_threshold:
        return "medium"
    else:
        return "low"


def calculate_combined_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """Calculate weighted combined score from multiple metrics.
    
    Args:
        scores: Dictionary of metric scores
        weights: Dictionary of metric weights
        
    Returns:
        Combined weighted score
    """
    total_score = 0.0
    total_weight = 0.0
    
    for metric, score in scores.items():
        weight = weights.get(metric, 1.0)
        total_score += score * weight
        total_weight += weight
    
    return total_score / total_weight if total_weight > 0 else 0.0


# === ID and Hash Generation ===

def generate_unique_id(text: str, prefix: str = "") -> str:
    """Generate unique ID from text using MD5 hash.
    
    Args:
        text: Text to hash
        prefix: Optional prefix for ID
        
    Returns:
        Generated unique ID
    """
    hash_obj = hashlib.md5(text.encode('utf-8'))
    return f"{prefix}{hash_obj.hexdigest()[:8].upper()}"


def generate_material_id(name: str, category: str, sku: Optional[str] = None) -> str:
    """Generate material ID from name, category, and SKU.
    
    Args:
        name: Material name
        category: Material category
        sku: Optional SKU
        
    Returns:
        Generated material ID
    """
    text = f"{name}_{category}_{sku or ''}"
    return generate_unique_id(text, "MAT_")


# === Validation Utilities ===

def validate_email(email: str) -> bool:
    """Validate email address format.
    
    Args:
        email: Email to validate
        
    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid phone format
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits) <= 15


def validate_sku(sku: str) -> bool:
    """Validate SKU format.
    
    Args:
        sku: SKU to validate
        
    Returns:
        True if valid SKU format
    """
    if not sku:
        return False
    
    # SKU should be alphanumeric with optional hyphens and underscores
    pattern = r'^[A-Za-z0-9\-_]+$'
    return bool(re.match(pattern, sku)) and 3 <= len(sku) <= 50


# === Date and Time Utilities ===

def format_datetime(dt: datetime, format_type: str = "default") -> str:
    """Format datetime to string.
    
    Args:
        dt: Datetime to format
        format_type: Format type ('default', 'short', 'long')
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return ""
    
    formats = {
        "default": "%Y-%m-%d %H:%M:%S",
        "short": "%Y-%m-%d",
        "long": "%d.%m.%Y %H:%M:%S",
        "iso": "%Y-%m-%dT%H:%M:%S"
    }
    
    return dt.strftime(formats.get(format_type, formats["default"]))


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime string to datetime object.
    
    Args:
        dt_str: Datetime string to parse
        
    Returns:
        Parsed datetime or None if invalid
    """
    if not dt_str:
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    return None


# === Data Structure Utilities ===

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List[Any], key_func: Optional[callable] = None) -> List[Any]:
    """Remove duplicates from list while preserving order.
    
    Args:
        lst: List to deduplicate
        key_func: Optional function to extract comparison key
        
    Returns:
        List without duplicates
    """
    seen = set()
    result = []
    
    for item in lst:
        key = key_func(item) if key_func else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


# === Error Handling Utilities ===

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safely divide two numbers with default for division by zero.
    
    Args:
        a: Numerator
        b: Denominator
        default: Default value if division by zero
        
    Returns:
        Division result or default
    """
    try:
        return a / b if b != 0 else default
    except (TypeError, ValueError):
        return default


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with default.
    
    Args:
        dictionary: Dictionary to get value from
        key: Key to look up
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


# === Performance Utilities ===

def measure_time(func):
    """Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Decorated function
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    
    return wrapper


async def measure_time_async(func):
    """Decorator to measure async function execution time.
    
    Args:
        func: Async function to measure
        
    Returns:
        Decorated async function
    """
    import time
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    
    return wrapper


# === Constants ===

DEFAULT_CATEGORIES = [
    "Цемент", "Бетон", "Кирпич", "Блоки", "Газобетон", "Пеноблоки",
    "Арматура", "Металлопрокат", "Трубы", "Профили", "Листовые материалы",
    "Утеплители", "Изоляционные материалы", "Кровельные материалы",
    "Черепица", "Профнастил", "Сайдинг", "Гипсокартон", "Фанера",
    "Пиломатериалы", "Лакокрасочные материалы", "Грунтовки", "Клеи",
    "Герметики", "Сухие смеси", "Растворы", "Штукатурки", "Шпатлевки",
    "Плитка", "Керамогранит", "Ламинат", "Линолеум", "Паркет"
]

DEFAULT_UNITS = [
    "шт", "кг", "т", "м", "м²", "м³", "л", "упак", "пачка", "рулон",
    "лист", "пог.м", "ведро", "банка", "тюбик", "мешок"
]

SIMILARITY_THRESHOLDS = {
    "high": 0.85,
    "medium": 0.70,
    "low": 0.50
}

SEARCH_WEIGHTS = {
    "name": 0.4,
    "description": 0.3,
    "category": 0.2,
    "sku": 0.1
} 