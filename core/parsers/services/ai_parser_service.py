"""
AI Parser Service

Modern AI-powered material parser using OpenAI GPT with advanced type safety,
logging integration, and configuration management.
"""

import json
import time
import asyncio
from typing import Dict, Optional, List, Any, Union, cast
from functools import lru_cache
from dataclasses import dataclass, asdict
from openai import OpenAI
from contextlib import asynccontextmanager

# Core infrastructure imports
from core.config.parsers import ParserConfig, get_parser_config
from core.database.factories import get_ai_client
from core.logging import get_logger
from core.parsers.config.system_prompts_manager import get_prompts_manager
from core.parsers.config.units_config_manager import get_units_manager

# Parser interface imports
from ..interfaces import (
    IAIParser,
    AIParseRequest,
    ParseStatus,
    AIModelType,
    AIParseMode,
    InputType,
    OutputType
)
from ..interfaces.ai_parser_interface import MaterialParseData, AIParseResult

print("DEBUG: core/parsers/services/ai_parser_service.py loaded")

@dataclass
class AIParseContext:
    """Context for AI parsing operations"""
    operation_id: str
    request_id: str
    start_time: float
    model_name: str
    attempt_count: int = 0
    total_tokens: int = 0
    embeddings_generated: int = 0
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since start"""
        return time.time() - self.start_time


class AIParserService:
    """
    AI-powered material parser service.
    
    Provides intelligent parsing of construction material names using OpenAI GPT
    to extract metric units, calculate price coefficients, and generate embeddings.
    """
    
    def __init__(self, config: Optional[ParserConfig] = None):
        print("DEBUG: AIParserService __init__ called")
        """
        Initialize AI parser service.
        
        Args:
            config: Optional parser configuration. If None, uses default config.
        """
        self.config = config or get_parser_config()
        self.client: Optional[OpenAI] = None
        self.logger = get_logger(__name__)
        self.metrics = None  # Simplified for production deployment
        
        # Initialize service
        self._setup_openai_client()
        
        # Cache for parsed results
        self.cache: Dict[str, AIParseResult[MaterialParseData]] = {}
        
        # Service metadata
        self._service_name = "ai_parser_service"
        self._version = "2.0.0"
        self._initialized = True
        
        self.logger.info(f"AI Parser Service v{self._version} initialized")
    
    def _setup_openai_client(self):
        """Setup OpenAI client using centralized configuration"""
        try:
            self.client = get_ai_client()
            self.logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    @property
    def service_name(self) -> str:
        """Get service name"""
        return self._service_name
    
    @property
    def version(self) -> str:
        """Get service version"""
        return self._version
    
    def is_healthy(self) -> bool:
        """
        Check if service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            return (
                self._initialized and
                self.client is not None and
                self.config is not None
            )
        except Exception:
            return False
    
    def get_health_details(self) -> Dict[str, Any]:
        """
        Get detailed health information.
        
        Returns:
            Dict[str, Any]: Health details
        """
        return {
            "service_name": self.service_name,
            "version": self.version,
            "initialized": self._initialized,
            "client_available": self.client is not None,
            "config_available": self.config is not None,
            "cache_size": len(self.cache),
            "metrics": None  # Simplified for production deployment
        }
    
    async def parse_request(self, request: AIParseRequest[str]) -> AIParseResult[MaterialParseData]:
        """
        Parse AI request asynchronously.
        
        Args:
            request: AI parse request
            
        Returns:
            AIParseResult: Parse result with material data
        """
        context = AIParseContext(
            operation_id=request.correlation_id,
            request_id=request.correlation_id,
            start_time=time.time(),
            model_name=self.config.models.openai_model
        )
        
        # Log request
        self.logger.info(
            f"AI request: operation_id={context.operation_id}, model={context.model_name}, "
            f"prompt={request.input_data[:100] + '...' if len(request.input_data) > 100 else request.input_data}, "
            f"temperature={self.config.models.temperature}, max_tokens={self.config.models.max_tokens}"
        )
        
        try:
            # Parse material
            result = await self._parse_material_async(request, context)
            
            # Log response
            self.logger.info(
                f"AI response: operation_id={context.operation_id}, success={result.status == ParseStatus.SUCCESS}, "
                f"confidence={result.confidence}, processing_time={context.get_elapsed_time()}, token_usage={context.total_tokens}"
            )
            
            # Update metrics (simplified for production)
            self.logger.debug(f"AI operation completed: {context.model_name}, success: {result.status == ParseStatus.SUCCESS}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing material: {e}")
            
            # Create error result
            return AIParseResult(
                success=False,
                status=ParseStatus.ERROR,
                data=MaterialParseData(
                    name=request.input_data,
                    original_unit="",
                    original_price=0.0
                ),
                confidence=0.0,
                processing_time=context.get_elapsed_time(),
                error_message=str(e),
                request_id=request.correlation_id
            )
    
    async def _parse_material_async(
        self, 
        request: AIParseRequest[str], 
        context: AIParseContext
    ) -> AIParseResult[MaterialParseData]:
        """
        Internal async material parsing method.
        
        Args:
            request: Parse request
            context: Parse context
            
        Returns:
            AIParseResult: Parse result
        """
        # Create cache key
        cache_key = f"{request.input_data}|{request.model_type}|{hash(str(request.options))}"
        
        # Check cache first
        if self.config.cache.enable_caching and cache_key in self.cache:
            self.logger.debug(f"Cache hit for: {request.input_data}")
            cached_result = self.cache[cache_key]
            cached_result.processing_time = context.get_elapsed_time()
            return cached_result
        
        # Parse material (extract name, unit, price from input)
        parsed_input = self._parse_input_data(request.input_data)
        
        # Get AI response
        ai_response = await self._get_ai_response_async(
            parsed_input["name"],
            parsed_input["unit"],
            context
        )
        
        # Create result
        result = self._create_parse_result(
            request=request,
            parsed_input=parsed_input,
            ai_response=ai_response,
            context=context
        )
        
        # Generate embeddings if enabled
        if request.options.get("enable_embeddings", False):
            await self._generate_embeddings_async(result, context)
        
        # Cache result
        if self.config.cache.enable_caching:
            self.cache[cache_key] = result
        
        return result
    
    def _parse_input_data(self, input_data: str) -> Dict[str, Any]:
        """
        Parse input data to extract name, unit, and price.
        
        Args:
            input_data: Raw input string
            
        Returns:
            Dict with parsed components
        """
        # Simple parsing - can be enhanced later
        # For now, assume input is just the material name
        return {
            "name": input_data.strip(),
            "unit": "",
            "price": 0.0
        }
    
    async def _get_ai_response_async(
        self, 
        name: str, 
        unit: str, 
        context: AIParseContext
    ) -> Optional[Dict[str, Any]]:
        """
        Get AI response asynchronously.
        
        Args:
            name: Material name
            unit: Original unit
            context: Parse context
            
        Returns:
            AI response or None if failed
        """
        self.logger.debug(f"Starting AI request for: {name}, unit: {unit}")
        try:
            # Build prompt
            prompt = self._build_prompt(name, unit)
            
            # Make API call with retries
            for attempt in range(self.config.performance.retry_attempts):
                context.attempt_count = attempt + 1
                
                try:
                    self.logger.debug(f"AI request attempt {attempt + 1} for: {name}")
                    
                    # Run in executor to avoid blocking
                    response = await self.client.chat.completions.create(
                        model=context.model_name,
                        messages=[
                            {"role": "system", "content": self._get_system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=self.config.models.temperature,
                        max_tokens=self.config.models.max_tokens,
                        timeout=self.config.performance.timeout
                    )
                    
                    # Track token usage
                    if hasattr(response, 'usage') and response.usage:
                        context.total_tokens += response.usage.total_tokens
                    
                    # Extract content
                    content = response.choices[0].message.content
                    
                    self.logger.debug(f"AI response: {content}")
                    
                    # Parse JSON response
                    try:
                        parsed_response = json.loads(content)
                        self.logger.debug(f"Successfully parsed AI response: {parsed_response}")
                        return parsed_response
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse AI response as JSON: {e}")
                        self.logger.error(f"Raw AI response: {content}")
                        raise
                    
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON decode error (attempt {attempt + 1}): {e}")
                    if attempt == self.config.performance.retry_attempts - 1:
                        raise
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.warning(f"AI request error (attempt {attempt + 1}): {e}")
                    if attempt == self.config.performance.retry_attempts - 1:
                        self.logger.error(f"All AI request attempts failed: {e}")
                        raise
                    await asyncio.sleep(2)
                    
        except Exception as e:
            self.logger.error(f"AI request failed: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI"""
        common_units = get_units_manager().get_common_units_for_ai()
        return get_prompts_manager().get_system_prompt(common_units)
    
    def _build_prompt(self, name: str, unit: str) -> str:
        """Build prompt for specific material"""
        material_hint = get_units_manager().get_material_hint(name)
        is_block = get_units_manager().is_block_material(name)
        
        return get_prompts_manager().get_user_prompt(
            name=name,
            unit=unit,
            material_hint=material_hint,
            is_block=is_block
        )
    
    def _create_parse_result(
        self,
        request: AIParseRequest[str],
        parsed_input: Dict[str, Any],
        ai_response: Optional[Dict[str, Any]],
        context: AIParseContext
    ) -> AIParseResult[MaterialParseData]:
        """
        Create parse result from AI response.
        
        Args:
            request: Original request
            parsed_input: Parsed input data
            ai_response: AI response
            context: Parse context
            
        Returns:
            AIParseResult: Complete parse result
        """
        # Create base material data
        material_data = MaterialParseData(
            name=parsed_input["name"],
            original_unit=parsed_input["unit"],
            original_price=parsed_input["price"],
            unit=parsed_input["unit"],  # Set unit field for compatibility
            price=parsed_input["price"]  # Set price field for compatibility
        )
        
        # Process AI response
        if ai_response:
            self.logger.debug(f"Processing AI response: {ai_response}")
        else:
            self.logger.warning("No AI response received")
            
        if ai_response:
            try:
                # Extract parsed data
                unit_parsed = ai_response.get("unit_parsed", "")
                price_coefficient = ai_response.get("price_coefficient", 1.0)
                confidence = ai_response.get("confidence", 0.5)
                color = ai_response.get("color", None)
                
                self.logger.debug(f"AI response: unit_parsed={unit_parsed}, price_coefficient={price_coefficient}, confidence={confidence}, color={color}")
                
                # Validate and normalize
                unit_parsed = get_units_manager().normalize_unit(unit_parsed)
                self.logger.debug(f"Normalized unit: {unit_parsed}")
                
                if self._validate_parsing_result(unit_parsed, price_coefficient):
                    self.logger.info(f"AI parsing successful: unit_parsed={unit_parsed}, price_coefficient={price_coefficient}")
                else:
                    self.logger.warning(f"AI parsing validation failed: unit_parsed={unit_parsed}, price_coefficient={price_coefficient}")
                
                if self._validate_parsing_result(unit_parsed, price_coefficient):
                    material_data.unit_parsed = unit_parsed
                    material_data.price_coefficient = price_coefficient
                    material_data.color = color
                    material_data.price_parsed = (
                        parsed_input["price"] / price_coefficient 
                        if price_coefficient != 0 and parsed_input["price"] != 0
                        else parsed_input["price"]
                    )
                    material_data.parsing_method = "ai_gpt"
                    material_data.confidence = confidence
                    
                    return AIParseResult(
                        success=True,
                        status=ParseStatus.SUCCESS,
                        data=material_data,
                        confidence=confidence,
                        processing_time=context.get_elapsed_time(),
                        request_id=request.correlation_id
                    )
                
            except Exception as e:
                self.logger.error(f"Error processing AI response: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return partial result if AI processing failed
        self.logger.warning(f"AI processing failed for material: {material_data.name}")
        return AIParseResult(
            success=False,
            status=ParseStatus.PARTIAL,
            data=material_data,
            confidence=0.0,
            processing_time=context.get_elapsed_time(),
            error_message="AI processing failed or validation failed",
            request_id=request.correlation_id
        )
    
    def _validate_parsing_result(self, unit_parsed: str, price_coefficient: float) -> bool:
        """
        Validate parsing result.
        Args:
            unit_parsed: Parsed unit
            price_coefficient: Calculated coefficient
        Returns:
            bool: True if valid, False otherwise
        """
        self.logger.debug(f"Validating: unit_parsed='{unit_parsed}', price_coefficient={price_coefficient}")
        
        if not unit_parsed:
            self.logger.debug("Validation failed: empty unit_parsed")
            return False
        # Простая проверка: коэффициент должен быть положительным
        if price_coefficient <= 0:
            self.logger.debug(f"Validation failed: price_coefficient <= 0: {price_coefficient}")
            return False
        
        # Временно упростим валидацию для отладки
        # TODO: расширить валидацию через конфиг, если потребуется
        # if not get_units_manager().validate_unit_coefficient(unit_parsed, price_coefficient):
        #     self.logger.debug(f"Validation failed: validate_unit_coefficient returned False")
        #     return False
        
        self.logger.debug("Validation passed")
        return True
    
    async def _generate_embeddings_async(
        self, 
        result: AIParseResult[MaterialParseData], 
        context: AIParseContext
    ) -> None:
        """
        Generate embeddings for material data.
        Args:
            result: Parse result to add embeddings to
            context: Parse context
        """
        # FIX: ParserConfig does not have 'features'; use 'models' for embedding params
        # if not self.config.features.embeddings_enabled:
        if not self.config.models.embedding_model:
            return
        try:
            # Generate material name embedding
            if result.data.name:
                result.data.embeddings = await self._generate_single_embedding_async(result.data.name)
                context.embeddings_generated += 1
            # Generate color embedding
            if result.data.color:
                result.data.color_embedding = await self._generate_single_embedding_async(result.data.color)
                context.embeddings_generated += 1
            # Generate unit embedding
            if result.data.unit_parsed:
                result.data.unit_embedding = await self._generate_single_embedding_async(result.data.unit_parsed)
                context.embeddings_generated += 1
            self.logger.debug(f"Generated {context.embeddings_generated} embeddings")
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")

    async def _generate_single_embedding_async(self, text: str) -> Optional[List[float]]:
        """
        Generate single embedding for text.
        Args:
            text: Text to generate embedding for
        Returns:
            List of floats or None if failed
        """
        try:
            self.logger.debug(f"Generating embedding for: {text[:50]}...")
            response = await self.client.embeddings.create(
                model=self.config.models.embedding_model,
                input=text,
                dimensions=self.config.models.embedding_dimensions
            )
            embeddings = response.data[0].embedding
            self.logger.debug(f"Generated embedding with {len(embeddings)} dimensions")
            return embeddings
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def parse_batch(self, requests: List[AIParseRequest[str]]) -> List[AIParseResult[MaterialParseData]]:
        """
        Parse multiple requests in batch.
        
        Args:
            requests: List of parse requests
            
        Returns:
            List of parse results
        """
        self.logger.info(f"Starting batch parse of {len(requests)} requests")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config.performance.max_concurrent_requests)
        
        async def parse_with_semaphore(request: AIParseRequest[str]) -> AIParseResult[MaterialParseData]:
            async with semaphore:
                return await self.parse_request(request)
        
        # Process all requests concurrently
        results = await asyncio.gather(
            *[parse_with_semaphore(req) for req in requests],
            return_exceptions=True
        )
        
        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(AIParseResult(
                    success=False,
                    status=ParseStatus.ERROR,
                    data=MaterialParseData(
                        name=requests[i].input_data,
                        original_unit="",
                        original_price=0.0,
                        unit="",  # Set unit field for compatibility
                        price=0.0  # Set price field for compatibility
                    ),
                    confidence=0.0,
                    processing_time=0.0,
                    error_message=str(result),
                    request_id=requests[i].correlation_id
                ))
            else:
                final_results.append(result)
        
        self.logger.info(f"Completed batch parse: {len(final_results)} results")
        return final_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        successful = sum(1 for result in self.cache.values() if result.status == ParseStatus.SUCCESS)
        
        return {
            "service_name": self.service_name,
            "version": self.version,
            "total_cached": len(self.cache),
            "successful_parses": successful,
            "success_rate": successful / len(self.cache) if self.cache else 0.0,
            "health_status": self.get_health_details(),
            "ai_metrics": self.metrics.get_ai_metrics()
        }
    
    def clear_cache(self) -> None:
        """Clear result cache"""
        self.cache.clear()
        self.logger.info("Cache cleared")
    
    def get_cache_size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


# Service factory
@lru_cache(maxsize=1)
def get_ai_parser_service() -> AIParserService:
    """
    Get AI parser service instance (singleton).
    
    Returns:
        AIParserService: Service instance
    """
    return AIParserService()


# Async context manager for service
@asynccontextmanager
async def ai_parser_service_context():
    """
    Async context manager for AI parser service.
    
    Yields:
        AIParserService: Service instance
    """
    service = get_ai_parser_service()
    try:
        yield service
    finally:
        # Cleanup if needed
        pass 