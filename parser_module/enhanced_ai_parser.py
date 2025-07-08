"""
Enhanced AI Parser for Construction Materials with Color Extraction and Embeddings

This module extends the base AI parser with color extraction capabilities
and embedding generation for integration with RAG normalization system.
"""

import json
import time
import logging
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass
from openai import OpenAI

# Import base AI parser
try:
    from .ai_parser import AIParser, ParsedResult
    from .parser_config import ParserConfig
except ImportError:
    # Fallback to absolute imports when running as script
    from ai_parser import AIParser, ParsedResult
    from parser_config import ParserConfig

# Try to import from main project
MAIN_PROJECT_AVAILABLE = False

# For parser testing, disable main project integration
# This allows testing the parser independently
print("Enhanced AI Parser running in standalone mode (main project integration disabled for testing)")


@dataclass
class EnhancedParseResult(ParsedResult):
    """Enhanced result of AI parsing with color extraction and embeddings"""
    
    # Color extraction
    color: Optional[str] = None
    color_confidence: float = 0.0
    color_embedding: Optional[List[float]] = None
    
    # Enhanced embeddings
    parsed_unit_embedding: Optional[List[float]] = None
    material_embedding: Optional[List[float]] = None
    
    # RAG normalization (added in pipeline)
    normalized_color: Optional[str] = None
    normalized_unit: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        base_dict = super().to_dict()
        base_dict.update({
            "color": self.color,
            "color_confidence": self.color_confidence,
            "color_embedding": self.color_embedding,
            "parsed_unit_embedding": self.parsed_unit_embedding,
            "material_embedding": self.material_embedding,
            "normalized_color": self.normalized_color,
            "normalized_unit": self.normalized_unit
        })
        return base_dict


class EnhancedAIParser(AIParser):
    """Enhanced AI parser with color extraction and embeddings generation"""
    
    def __init__(self, config: ParserConfig):
        """Initialize enhanced AI parser"""
        super().__init__(config)
        
        # Initialize embedding service if main project is available
        self.embedding_service = None
        if MAIN_PROJECT_AVAILABLE:
            try:
                self.embedding_service = EmbeddingComparisonService()
                self.logger.info("EmbeddingComparisonService initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize EmbeddingComparisonService: {e}")
        
        # Color patterns for extraction
        self.color_patterns = self._get_color_patterns()
        
    def _get_color_patterns(self) -> List[str]:
        """Get color extraction patterns from ColorCollection"""
        patterns = []
        
        if MAIN_PROJECT_AVAILABLE:
            try:
                color_collection = ColorCollection()
                # Get all color names and aliases
                for color_data in color_collection.colors:
                    patterns.append(color_data["name"])
                    patterns.extend(color_data["aliases"])
            except Exception as e:
                self.logger.warning(f"Could not load color patterns: {e}")
        
        # Default color patterns if main project not available
        if not patterns:
            patterns = [
                "белый", "белая", "белое", "черный", "черная", "черное",
                "серый", "серая", "серое", "красный", "красная", "красное",
                "синий", "синяя", "синее", "зеленый", "зеленая", "зеленое",
                "желтый", "желтая", "желтое", "коричневый", "коричневая", "коричневое",
                "розовый", "розовая", "розовое", "оранжевый", "оранжевая", "оранжевое"
            ]
        
        return patterns
    
    def parse_material_enhanced(self, name: str, unit: str, price: float = 0.0) -> EnhancedParseResult:
        """
        Enhanced parsing with color extraction and embeddings generation
        
        Args:
            name: Material name
            unit: Original unit
            price: Original price (optional)
            
        Returns:
            EnhancedParseResult with color and embeddings
        """
        start_time = time.time()
        
        # Get base parsing result
        base_result = self.parse_material(name, unit, price)
        
        # Create enhanced result
        enhanced_result = EnhancedParseResult(
            name=base_result.name,
            original_unit=base_result.original_unit,
            original_price=base_result.original_price,
            unit_parsed=base_result.unit_parsed,
            price_coefficient=base_result.price_coefficient,
            price_parsed=base_result.price_parsed,
            parsing_method=base_result.parsing_method,
            confidence=base_result.confidence,
            success=base_result.success,
            error_message=base_result.error_message,
            embeddings=base_result.embeddings
        )
        
        # Extract color
        color_result = self._extract_color(name)
        enhanced_result.color = color_result.get("color")
        enhanced_result.color_confidence = color_result.get("confidence", 0.0)
        
        # Generate embeddings
        self._generate_enhanced_embeddings(enhanced_result)
        
        enhanced_result.processing_time = time.time() - start_time
        
        return enhanced_result
    
    def _extract_color(self, name: str) -> Dict[str, Any]:
        """
        Extract color from material name
        
        Args:
            name: Material name
            
        Returns:
            Dictionary with color and confidence
        """
        name_lower = name.lower()
        
        # Check for color patterns
        for color in self.color_patterns:
            if color.lower() in name_lower:
                return {
                    "color": color,
                    "confidence": 0.8
                }
        
        # Use AI for complex color extraction
        if self.config.openai_api_key and self.client:
            try:
                ai_color = self._extract_color_with_ai(name)
                if ai_color:
                    return ai_color
            except Exception as e:
                self.logger.warning(f"AI color extraction failed: {e}")
        
        return {"color": None, "confidence": 0.0}
    
    def _extract_color_with_ai(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Extract color using AI when pattern matching fails
        
        Args:
            name: Material name
            
        Returns:
            Dictionary with color and confidence or None
        """
        try:
            system_prompt = self._get_color_extraction_system_prompt()
            user_prompt = f"Материал: '{name}'\nИзвлеки цвет если он есть в названии."
            
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.openai_temperature,
                max_tokens=100,
                timeout=self.config.openai_timeout
            )
            
            if response.choices:
                content = response.choices[0].message.content.strip()
                try:
                    color_data = json.loads(content)
                    return {
                        "color": color_data.get("color"),
                        "confidence": color_data.get("confidence", 0.7)
                    }
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in color extraction: {content}")
            
        except Exception as e:
            self.logger.error(f"AI color extraction error: {e}")
        
        return None
    
    def _get_color_extraction_system_prompt(self) -> str:
        """Get system prompt for color extraction"""
        available_colors = ", ".join(self.color_patterns[:20])  # First 20 colors
        
        return f"""
Ты эксперт по извлечению цветов из названий строительных материалов.

ВОЗВРАЩАЙ ТОЛЬКО ВАЛИДНЫЙ JSON:
{{
    "color": "название_цвета_или_null",
    "confidence": число_от_0_до_1
}}

ДОСТУПНЫЕ ЦВЕТА: {available_colors}

ПРАВИЛА:
1. Извлекай только явно указанные цвета в названии
2. Используй базовые цвета: белый, черный, серый, красный, синий, зеленый, желтый, коричневый
3. Если цвет не найден → "color": null, "confidence": 0.0
4. Если цвет найден → "color": "название_цвета", "confidence": 0.8-0.9

ПРИМЕРЫ:
- "Цемент белый М500" → "color": "белый", "confidence": 0.9
- "Кирпич красный керамический" → "color": "красный", "confidence": 0.9
- "Утеплитель минеральный" → "color": null, "confidence": 0.0

Отвечай ТОЛЬКО JSON без дополнительного текста.
"""
    
    def _generate_enhanced_embeddings(self, result: EnhancedParseResult) -> None:
        """
        Generate embeddings for color, parsed_unit, and material
        
        Args:
            result: Enhanced parsing result to update with embeddings
        """
        if not self.config.embeddings_enabled or not self.client:
            return
        
        try:
            # Generate color embedding
            if result.color:
                result.color_embedding = self._generate_single_embedding(result.color)
            
            # Generate parsed unit embedding
            if result.unit_parsed:
                result.parsed_unit_embedding = self._generate_single_embedding(result.unit_parsed)
            
            # Generate material embedding (name + parsed_unit + color)
            material_text = self._prepare_material_text_for_embedding(
                result.name, result.unit_parsed, result.color
            )
            result.material_embedding = self._generate_single_embedding(material_text)
            
        except Exception as e:
            self.logger.error(f"Enhanced embeddings generation failed: {e}")
    
    def _generate_single_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate single embedding using OpenAI API
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of embedding values or None if failed
        """
        if not text or not text.strip():
            return None
        
        try:
            response = self.client.embeddings.create(
                model=self.config.embeddings_model,
                input=text.strip(),
                dimensions=self.config.embeddings_dimensions
            )
            
            if response.data:
                return response.data[0].embedding
                
        except Exception as e:
            self.logger.error(f"Embedding generation failed for text '{text}': {e}")
        
        return None
    
    def _prepare_material_text_for_embedding(self, name: str, unit: str, color: str) -> str:
        """
        Prepare material text for embedding generation
        
        Args:
            name: Material name
            unit: Parsed unit
            color: Extracted color
            
        Returns:
            Combined text for embedding
        """
        components = [name]
        
        if unit:
            components.append(unit)
        
        if color:
            components.append(color)
        
        return " ".join(components)
    
    def parse_batch_enhanced(self, materials: List[Dict[str, Any]]) -> List[EnhancedParseResult]:
        """
        Parse multiple materials with enhanced features
        
        Args:
            materials: List of material dictionaries with 'name', 'unit', 'price' keys
            
        Returns:
            List of EnhancedParseResult objects
        """
        results = []
        
        for material in materials:
            try:
                result = self.parse_material_enhanced(
                    name=material.get("name", ""),
                    unit=material.get("unit", ""),
                    price=material.get("price", 0.0)
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Batch parsing failed for material {material}: {e}")
                # Create error result
                error_result = EnhancedParseResult(
                    name=material.get("name", ""),
                    original_unit=material.get("unit", ""),
                    original_price=material.get("price", 0.0),
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
        
        return results
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics including color extraction metrics"""
        base_stats = self.get_statistics()
        
        # Add color extraction statistics
        color_stats = {
            "color_extraction_enabled": True,
            "color_patterns_count": len(self.color_patterns),
            "embedding_service_available": self.embedding_service is not None,
            "embeddings_enabled": self.config.embeddings_enabled
        }
        
        base_stats.update(color_stats)
        return base_stats


# Factory function for easy instantiation
def create_enhanced_ai_parser(config: ParserConfig = None) -> EnhancedAIParser:
    """
    Create enhanced AI parser instance
    
    Args:
        config: Parser configuration (optional)
        
    Returns:
        EnhancedAIParser instance
    """
    if config is None:
        config = ParserConfig()
    
    return EnhancedAIParser(config)


# Integration function for main project
def integrate_with_main_project() -> Optional[EnhancedAIParser]:
    """
    Create enhanced AI parser integrated with main project
    
    Returns:
        EnhancedAIParser instance or None if integration failed
    """
    if not MAIN_PROJECT_AVAILABLE:
        return None
    
    try:
        # Use main project configuration
        config = ParserConfig()
        config.use_main_project_config = True
        config.integration_mode = True
        
        parser = EnhancedAIParser(config)
        return parser
        
    except Exception as e:
        logging.error(f"Main project integration failed: {e}")
        return None 