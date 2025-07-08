"""
AI Parser Engine for Construction Materials

This module provides intelligent parsing of construction material names 
using OpenAI GPT to extract metric units and calculate price coefficients.
"""

import json
import time
import logging
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass
from openai import OpenAI
try:
    # Try relative imports (when imported as module)
    from .parser_config import ParserConfig
    from .units_config import (
        normalize_unit, 
        is_metric_unit, 
        validate_unit_coefficient,
        get_common_units_for_ai,
        get_material_hint,
        is_block_material
    )
    from .system_prompts import (
        get_material_parsing_system_prompt,
        get_material_parsing_user_prompt
    )
except ImportError:
    # Fall back to absolute imports (when run as script)
    from parser_config import ParserConfig
    from units_config import (
        normalize_unit, 
        is_metric_unit, 
        validate_unit_coefficient,
        get_common_units_for_ai,
        get_material_hint,
        is_block_material
    )
    from system_prompts import (
        get_material_parsing_system_prompt,
        get_material_parsing_user_prompt
    )


@dataclass
class ParsedResult:
    """Result of AI parsing with enhanced color and embeddings support"""
    name: str
    original_unit: str
    original_price: float
    unit_parsed: Optional[str] = None
    price_coefficient: Optional[float] = None
    price_parsed: Optional[float] = None
    parsing_method: str = "ai_gpt"
    confidence: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    processing_time: float = 0.0
    # Enhanced fields for RAG integration
    color: Optional[str] = None  # Extracted color from material name
    embeddings: Optional[List[float]] = None  # Material name embedding (1536dim)
    color_embedding: Optional[List[float]] = None  # Color embedding (1536dim)
    unit_embedding: Optional[List[float]] = None  # Unit embedding (1536dim)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "original_unit": self.original_unit,
            "original_price": self.original_price,
            "unit_parsed": self.unit_parsed,
            "price_coefficient": self.price_coefficient,
            "price_parsed": self.price_parsed,
            "parsing_method": self.parsing_method,
            "confidence": self.confidence,
            "success": self.success,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            # Enhanced fields for RAG integration
            "color": self.color,
            "embeddings": self.embeddings,
            "color_embedding": self.color_embedding,
            "unit_embedding": self.unit_embedding
        }


class AIParser:
    """AI-powered material parser using OpenAI GPT"""
    
    def __init__(self, config: ParserConfig):
        """
        Initialize AI parser
        
        Args:
            config: Parser configuration
        """
        self.config = config
        self.client = None
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        self._setup_openai_client()
        
        # Cache for parsed results
        self.cache: Dict[str, ParsedResult] = {}
        
    def _setup_logging(self):
        """Setup logging configuration"""
        if self.config.enable_debug_logging:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=getattr(logging, self.config.log_level))
    
    def _setup_openai_client(self):
        """Setup OpenAI client"""
        try:
            if self.config.use_main_project_config:
                # Try to use main project's OpenAI configuration
                try:
                    from core.config.ai import AIConfig
                    ai_config = AIConfig()
                    self.client = OpenAI(api_key=ai_config.openai_api_key)
                    self.logger.info("Using main project OpenAI configuration")
                except ImportError:
                    self.logger.warning("Main project AI config not found, using parser config")
                    self.client = OpenAI(api_key=self.config.openai_api_key)
            else:
                self.client = OpenAI(api_key=self.config.openai_api_key)
                
            self.logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def parse_material(self, name: str, unit: str, price: float) -> ParsedResult:
        """
        Parse material using AI
        
        Args:
            name: Material name
            unit: Original unit
            price: Original price
            
        Returns:
            ParsedResult with extracted information
        """
        start_time = time.time()
        
        # Create cache key
        cache_key = f"{name}|{unit}|{price}"
        
        # Check cache first
        if self.config.enable_caching and cache_key in self.cache:
            self.logger.debug(f"Cache hit for: {name}")
            cached_result = self.cache[cache_key]
            cached_result.processing_time = time.time() - start_time
            return cached_result
        
        # Parse with AI
        result = self._parse_with_ai(name, unit, price)
        result.processing_time = time.time() - start_time
        
        # Cache result
        if self.config.enable_caching:
            self.cache[cache_key] = result
        
        return result
    
    def _parse_with_ai(self, name: str, unit: str, price: float) -> ParsedResult:
        """
        Internal method to parse material with AI
        
        Args:
            name: Material name
            unit: Original unit
            price: Original price
            
        Returns:
            ParsedResult
        """
        result = ParsedResult(
            name=name,
            original_unit=unit,
            original_price=price
        )
        
        try:
            # Get AI response
            ai_response = self._get_ai_response(name, unit)
            
            if ai_response:
                # Parse AI response
                parsed_data = self._parse_ai_response(ai_response)
                
                if parsed_data:
                    # Validate and normalize
                    unit_parsed = normalize_unit(parsed_data.get("unit_parsed", ""))
                    price_coefficient = parsed_data.get("price_coefficient", 1.0)
                    color = parsed_data.get("color", None)
                    
                    if unit_parsed and self._validate_parsing_result(unit_parsed, price_coefficient):
                        result.unit_parsed = unit_parsed
                        result.price_coefficient = price_coefficient
                        result.color = color
                        # Fix: price_parsed should be original price divided by coefficient
                        # If 1 unit contains X metric units, then price per metric unit = price / X
                        result.price_parsed = price / price_coefficient if price_coefficient != 0 else price
                        result.confidence = parsed_data.get("confidence", 0.8)
                        result.success = True
                        
                        # Generate multiple embeddings for RAG integration
                        result.embeddings = self._generate_embeddings(name)  # Material name embedding
                        if color:
                            result.color_embedding = self._generate_embeddings(color)  # Color embedding
                        if unit_parsed:
                            result.unit_embedding = self._generate_embeddings(unit_parsed)  # Unit embedding
                        
                        self.logger.info(f"Successfully parsed: {name} -> {unit_parsed} (x{price_coefficient}) color: {color}")
                    else:
                        result.error_message = "Invalid parsing result after validation"
                        self.logger.warning(f"Validation failed for: {name}")
                else:
                    result.error_message = "Failed to parse AI response"
                    self.logger.warning(f"AI response parsing failed for: {name}")
            else:
                result.error_message = "No AI response received"
                self.logger.warning(f"No AI response for: {name}")
                
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"Error parsing {name}: {e}")
        
        # Generate embeddings even if parsing failed (for search purposes)
        if result.embeddings is None:
            result.embeddings = self._generate_embeddings(name)
        
        return result
    
    def _generate_embeddings(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings for text using OpenAI
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            List of embeddings or None if failed
        """
        if not self.config.embeddings_enabled:
            return None
            
        try:
            self.logger.debug(f"Generating embeddings for: {text[:50]}...")
            
            response = self.client.embeddings.create(
                model=self.config.embeddings_model,
                input=text,
                dimensions=self.config.embeddings_dimensions
            )
            
            embeddings = response.data[0].embedding
            self.logger.debug(f"Generated embeddings with {len(embeddings)} dimensions")
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            return None
    
    def _get_ai_response(self, name: str, unit: str) -> Optional[Dict[str, Any]]:
        """
        Get response from OpenAI API
        
        Args:
            name: Material name
            unit: Original unit
            
        Returns:
            AI response as dictionary or None
        """
        try:
            # Build prompt
            prompt = self._build_prompt(name, unit)
            
            # Make API call with retries
            for attempt in range(self.config.max_retries):
                try:
                    if self.config.log_ai_requests:
                        self.logger.debug(f"AI request attempt {attempt + 1} for: {name}")
                    
                    response = self.client.chat.completions.create(
                        model=self.config.openai_model,
                        messages=[
                            {"role": "system", "content": self._get_system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=self.config.openai_temperature,
                        max_tokens=self.config.openai_max_tokens,
                        timeout=self.config.openai_timeout
                    )
                    
                    # Extract content
                    content = response.choices[0].message.content
                    
                    if self.config.log_ai_requests:
                        self.logger.debug(f"AI response: {content}")
                    
                    # Parse JSON response
                    return json.loads(content)
                    
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON decode error (attempt {attempt + 1}): {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.warning(f"AI request error (attempt {attempt + 1}): {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                    time.sleep(2)
                    
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI"""
        common_units = get_common_units_for_ai()
        return get_material_parsing_system_prompt(common_units)
    
    def _build_prompt(self, name: str, unit: str) -> str:
        """Build prompt for specific material"""
        material_hint = get_material_hint(name)
        is_block = is_block_material(name)
        
        return get_material_parsing_user_prompt(
            name=name,
            unit=unit,
            material_hint=material_hint,
            is_block=is_block
        )
    
    def _parse_ai_response(self, ai_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse AI response and extract relevant data
        
        Args:
            ai_response: Raw AI response
            
        Returns:
            Parsed data or None
        """
        try:
            # Extract required fields
            unit_parsed = ai_response.get("unit_parsed", "")
            price_coefficient = ai_response.get("price_coefficient", 1.0)
            confidence = ai_response.get("confidence", 0.5)
            # Extract color field (new for RAG integration)
            color = ai_response.get("color", None)
            
            # Validate types
            if not isinstance(unit_parsed, str):
                return None
                
            try:
                price_coefficient = float(price_coefficient)
                confidence = float(confidence)
            except (ValueError, TypeError):
                return None
            
            # Validate color field
            if color is not None and not isinstance(color, str):
                color = None
            
            return {
                "unit_parsed": unit_parsed,
                "price_coefficient": price_coefficient,
                "confidence": confidence,
                "color": color
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _validate_parsing_result(self, unit_parsed: str, price_coefficient: float) -> bool:
        """
        Validate parsing result
        
        Args:
            unit_parsed: Parsed unit
            price_coefficient: Calculated coefficient
            
        Returns:
            True if valid, False otherwise
        """
        # Check if unit is supported
        if not unit_parsed:
            return False
        
        # Check coefficient range
        if not (self.config.min_price_coefficient <= price_coefficient <= self.config.max_price_coefficient):
            return False
        
        # Check unit-specific validation
        if not validate_unit_coefficient(unit_parsed, price_coefficient):
            return False
        
        return True
    
    def parse_batch(self, materials: List[Dict[str, Any]]) -> List[ParsedResult]:
        """
        Parse multiple materials
        
        Args:
            materials: List of materials with 'name', 'unit', 'price' keys
            
        Returns:
            List of ParsedResult objects
        """
        results = []
        
        for i, material in enumerate(materials):
            self.logger.info(f"Processing material {i+1}/{len(materials)}: {material.get('name', 'Unknown')}")
            
            result = self.parse_material(
                name=material.get("name", ""),
                unit=material.get("unit", ""),
                price=material.get("price", 0.0)
            )
            
            results.append(result)
            
            # Small delay to avoid rate limiting
            if i < len(materials) - 1:
                time.sleep(0.1)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        total_cached = len(self.cache)
        successful = sum(1 for result in self.cache.values() if result.success)
        
        return {
            "total_cached": total_cached,
            "successful_parses": successful,
            "success_rate": successful / total_cached if total_cached > 0 else 0,
            "cache_size": total_cached
        }
    
    def clear_cache(self):
        """Clear parsing cache"""
        self.cache.clear()
        self.logger.info("Parser cache cleared") 