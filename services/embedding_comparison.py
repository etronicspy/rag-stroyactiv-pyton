"""
Embedding Comparison Service for RAG normalization.

Сервис сравнения эмбеддингов для RAG нормализации.
"""

import asyncio
from typing import Optional, List, Dict, Any, Tuple
from core.logging import get_logger
from core.database.interfaces import IVectorDatabase
from core.database.collections.colors import ColorCollection
from core.config.base import get_settings

logger = get_logger(__name__)


class EmbeddingComparisonService:
    """Service for RAG-based normalization using vector similarity search (через fallback manager)."""
    def __init__(self):
        self.settings = get_settings()
        self.logger = logger
        self.color_similarity_threshold = 0.8
        self.unit_similarity_threshold = 0.8
        self.default_similarity_threshold = 0.7
        self.colors_collection = "construction_colors"
        self.units_collection = "construction_units"

    async def normalize_color(self, color_text: str, similarity_threshold: Optional[float] = None) -> Dict[str, Any]:
        from core.database.factories import get_fallback_manager, AllDatabasesUnavailableError
        fallback_manager = get_fallback_manager()
        if not color_text or not color_text.strip():
            return {
                "original_text": color_text,
                "normalized_color": None,
                "similarity_score": 0.0,
                "suggestions": [],
                "success": False,
                "method": "empty_input"
            }
        threshold = similarity_threshold or self.color_similarity_threshold
        color_text_clean = color_text.strip().lower()
        self.logger.debug(f"Normalizing color: '{color_text}' with threshold {threshold}")
        # First try: exact match in ColorCollection
        exact_match = ColorCollection.find_color_by_alias(color_text_clean)
        if exact_match:
            self.logger.debug(f"Found exact match for color: {color_text} -> {exact_match}")
            return {
                "original_text": color_text,
                "normalized_color": exact_match,
                "similarity_score": 1.0,
                "suggestions": [exact_match],
                "success": True,
                "method": "exact_match"
            }
        # Second try: centralized vector search
        try:
            vector_result = await fallback_manager.embedding_search(
                text=color_text,
                collection=self.colors_collection,
                threshold=threshold,
                mode="color"
            )
            if vector_result["success"]:
                return vector_result
        except AllDatabasesUnavailableError:
            raise
        except Exception as e:
            self.logger.error(f"Vector search failed for color '{color_text}': {e}")
        # Third try: centralized fuzzy search
        fuzzy_result = fallback_manager.fuzzy_search(
            text=color_text_clean,
            collection=self.colors_collection,
            threshold=threshold,
            mode="color"
        )
        if fuzzy_result["success"]:
            return fuzzy_result
        # No match found
        suggestions = fallback_manager.suggestion_search(
            text=color_text_clean,
            collection=self.colors_collection,
            mode="color"
        )
        return {
            "original_text": color_text,
            "normalized_color": None,
            "similarity_score": 0.0,
            "suggestions": suggestions[:5],
            "success": False,
            "method": "no_match"
        }

    async def normalize_unit(self, unit_text: str, similarity_threshold: Optional[float] = None) -> Dict[str, Any]:
        from core.database.factories import get_fallback_manager, AllDatabasesUnavailableError
        fallback_manager = get_fallback_manager()
        if not unit_text or not unit_text.strip():
            return {
                "original_text": unit_text,
                "normalized_unit": None,
                "similarity_score": 0.0,
                "suggestions": [],
                "success": False,
                "method": "empty_input"
            }
        threshold = similarity_threshold or self.unit_similarity_threshold
        unit_text_clean = unit_text.strip().lower()
        self.logger.debug(f"Normalizing unit: '{unit_text}' with threshold {threshold}")
        # First try: exact match
        exact_match = self._exact_match_unit(unit_text_clean)
        if exact_match:
            self.logger.debug(f"Found exact match for unit: {unit_text} -> {exact_match}")
            return {
                "original_text": unit_text,
                "normalized_unit": exact_match,
                "similarity_score": 1.0,
                "suggestions": [exact_match],
                "success": True,
                "method": "exact_match"
            }
        # Second try: centralized vector search
        try:
            vector_result = await fallback_manager.embedding_search(
                text=unit_text,
                collection=self.units_collection,
                threshold=threshold,
                mode="unit"
            )
            if vector_result["success"]:
                return vector_result
        except AllDatabasesUnavailableError:
            raise
        except Exception as e:
            self.logger.error(f"Vector search failed for unit '{unit_text}': {e}")
        # Third try: centralized fuzzy search
        fuzzy_result = fallback_manager.fuzzy_search(
            text=unit_text_clean,
            collection=self.units_collection,
            threshold=threshold,
            mode="unit"
        )
        if fuzzy_result["success"]:
            return fuzzy_result
        # No match found
        suggestions = fallback_manager.suggestion_search(
            text=unit_text_clean,
            collection=self.units_collection,
            mode="unit"
        )
        return {
            "original_text": unit_text,
            "normalized_unit": None,
            "similarity_score": 0.0,
            "suggestions": suggestions[:5],
            "success": False,
            "method": "no_match"
        }

    def _fuzzy_match_color(self, color_text: str, threshold: float) -> Dict[str, Any]:
        """Perform fuzzy matching for color normalization.
        
        Выполнить нечеткое сопоставление для нормализации цвета.
        """
        try:
            from difflib import SequenceMatcher
            
            best_match = None
            best_score = 0.0
            all_matches = []
            
            # Check against all colors and aliases
            for color_info in ColorCollection.BASE_COLORS:
                color_name = color_info["name"]
                
                # Check main name
                score = SequenceMatcher(None, color_text, color_name.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = color_name
                
                all_matches.append((color_name, score))
                
                # Check aliases
                for alias in color_info["aliases"]:
                    score = SequenceMatcher(None, color_text, alias.lower()).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = color_name
                    
                    all_matches.append((color_name, score))
            
            # Sort by score and get top suggestions
            all_matches.sort(key=lambda x: x[1], reverse=True)
            suggestions = []
            seen = set()
            for name, score in all_matches:
                if name not in seen and len(suggestions) < 5:
                    suggestions.append(name)
                    seen.add(name)
            
            if best_score >= threshold:
                return {
                    "original_text": color_text,
                    "normalized_color": best_match,
                    "similarity_score": best_score,
                    "suggestions": suggestions,
                    "success": True,
                    "method": "fuzzy_match"
                }
            
            return {
                "original_text": color_text,
                "normalized_color": None,
                "similarity_score": best_score,
                "suggestions": suggestions,
                "success": False,
                "method": "fuzzy_below_threshold"
            }
            
        except Exception as e:
            self.logger.error(f"Fuzzy matching error for color: {e}")
            return {"success": False, "method": "fuzzy_error"}
    
    def _fuzzy_match_unit(self, unit_text: str, threshold: float) -> Dict[str, Any]:
        """Perform fuzzy matching for unit normalization.
        
        Выполнить нечеткое сопоставление для нормализации единицы.
        """
        try:
            from difflib import SequenceMatcher
            
            # Get unit mappings from existing logic
            unit_mappings = self._get_unit_mappings()
            
            best_match = None
            best_score = 0.0
            all_matches = []
            
            # Check against all units and aliases
            for standard_unit, aliases in unit_mappings.items():
                
                # Check standard unit name
                score = SequenceMatcher(None, unit_text, standard_unit.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = standard_unit
                
                all_matches.append((standard_unit, score))
                
                # Check aliases
                for alias in aliases:
                    score = SequenceMatcher(None, unit_text, alias.lower()).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = standard_unit
                    
                    all_matches.append((standard_unit, score))
            
            # Sort by score and get top suggestions
            all_matches.sort(key=lambda x: x[1], reverse=True)
            suggestions = []
            seen = set()
            for name, score in all_matches:
                if name not in seen and len(suggestions) < 5:
                    suggestions.append(name)
                    seen.add(name)
            
            if best_score >= threshold:
                return {
                    "original_text": unit_text,
                    "normalized_unit": best_match,
                    "similarity_score": best_score,
                    "suggestions": suggestions,
                    "success": True,
                    "method": "fuzzy_match"
                }
            
            return {
                "original_text": unit_text,
                "normalized_unit": None,
                "similarity_score": best_score,
                "suggestions": suggestions,
                "success": False,
                "method": "fuzzy_below_threshold"
            }
            
        except Exception as e:
            self.logger.error(f"Fuzzy matching error for unit: {e}")
            return {"success": False, "method": "fuzzy_error"}
    
    def _exact_match_unit(self, unit_text: str) -> Optional[str]:
        """Find exact match for unit text.
        
        Найти точное совпадение для текста единицы.
        """
        unit_mappings = self._get_unit_mappings()
        
        # Check standard names
        for standard_unit in unit_mappings.keys():
            if unit_text == standard_unit.lower():
                return standard_unit
        
        # Check aliases
        for standard_unit, aliases in unit_mappings.items():
            for alias in aliases:
                if unit_text == alias.lower():
                    return standard_unit
        
        return None
    
    def _get_unit_mappings(self) -> Dict[str, List[str]]:
        """Get unit mappings with aliases.
        
        Получить сопоставления единиц с синонимами.
        """
        return {
            "кг": ["килограмм", "кило", "kg", "килограммы"],
            "м³": ["куб", "кубометр", "м3", "куб.м", "кубический метр", "кубометры"],
            "м²": ["квадрат", "кв.м", "м2", "квадратный метр", "квадратные метры"],
            "шт": ["штука", "штук", "штуки", "pcs", "piece"],
            "м": ["метр", "метры", "погонный", "пог.м", "п.м"],
            "л": ["литр", "литры", "литров", "liter"],
            "т": ["тонна", "тонны", "тонн", "ton"],
            "мешок": ["меш", "мешки", "мешков", "bag"],
            "упак": ["упаковка", "упаковки", "упаковок", "package", "pack"],
            "рулон": ["рулоны", "рулонов", "roll"],
            "лист": ["листы", "листов", "sheet"],
            "пачка": ["пачки", "пачек", "bundle"],
            "ведро": ["ведра", "ведер", "bucket"],
            "банка": ["банки", "банок", "jar", "can"],
            "тюбик": ["тюбики", "тюбиков", "tube"]
        }
    
    def _get_color_suggestions(self, color_text: str) -> List[str]:
        """Get color suggestions based on partial matches.
        
        Получить предложения цветов на основе частичных совпадений.
        """
        suggestions = []
        color_text_lower = color_text.lower()
        
        for color_info in ColorCollection.BASE_COLORS:
            color_name = color_info["name"]
            
            # Check if color text is substring of any color/alias
            if color_text_lower in color_name.lower():
                suggestions.append(color_name)
                continue
            
            for alias in color_info["aliases"]:
                if color_text_lower in alias.lower():
                    suggestions.append(color_name)
                    break
        
        return list(set(suggestions))  # Remove duplicates
    
    def _get_unit_suggestions(self, unit_text: str) -> List[str]:
        """Get unit suggestions based on partial matches.
        
        Получить предложения единиц на основе частичных совпадений.
        """
        suggestions = []
        unit_text_lower = unit_text.lower()
        unit_mappings = self._get_unit_mappings()
        
        for standard_unit, aliases in unit_mappings.items():
            # Check if unit text is substring of standard unit
            if unit_text_lower in standard_unit.lower():
                suggestions.append(standard_unit)
                continue
            
            # Check aliases
            for alias in aliases:
                if unit_text_lower in alias.lower():
                    suggestions.append(standard_unit)
                    break
        
        return list(set(suggestions))  # Remove duplicates
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text.
        
        Сгенерировать эмбеддинг для текста.
        """
        try:
            # This would use OpenAI or other embedding service
            # For now, return None to indicate embedding generation failed
            # In real implementation, this would call OpenAI API
            
            # Example:
            # from openai import OpenAI
            # client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
            # response = await client.embeddings.create(
            #     model="text-embedding-3-small",
            #     input=text
            # )
            # return response.data[0].embedding
            
            self.logger.warning("Embedding generation not implemented yet")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def batch_normalize_colors(self, color_texts: List[str]) -> List[Dict[str, Any]]:
        """Normalize multiple colors in batch.
        
        Нормализовать несколько цветов в пакете.
        """
        tasks = [self.normalize_color(color_text) for color_text in color_texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error normalizing color '{color_texts[i]}': {result}")
                processed_results.append({
                    "original_text": color_texts[i],
                    "normalized_color": None,
                    "similarity_score": 0.0,
                    "suggestions": [],
                    "success": False,
                    "method": "batch_error"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def batch_normalize_units(self, unit_texts: List[str]) -> List[Dict[str, Any]]:
        """Normalize multiple units in batch.
        
        Нормализовать несколько единиц в пакете.
        """
        tasks = [self.normalize_unit(unit_text) for unit_text in unit_texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error normalizing unit '{unit_texts[i]}': {result}")
                processed_results.append({
                    "original_text": unit_texts[i],
                    "normalized_unit": None,
                    "similarity_score": 0.0,
                    "suggestions": [],
                    "success": False,
                    "method": "batch_error"
                })
            else:
                processed_results.append(result)
        
        return processed_results 