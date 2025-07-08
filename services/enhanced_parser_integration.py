"""
Enhanced Parser Integration Service

This service provides integration between the enhanced AI parser module
and the main RAG Construction Materials API system.
"""

import asyncio
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import sys

# Add parser_module to sys.path for imports
current_dir = Path(__file__).parent.parent
parser_module_path = current_dir / "parser_module"
if str(parser_module_path) not in sys.path:
    sys.path.append(str(parser_module_path))

try:
    from parser_module.material_parser import MaterialParser
    from parser_module.parser_config import ParserConfig, get_config
    from parser_module.ai_parser import ParsedResult
except ImportError as e:
    logging.error(f"Failed to import parser_module: {e}")
    raise ImportError("Parser module not found. Ensure parser_module is properly installed.")

from core.schemas.enhanced_parsing import (
    EnhancedParseRequest,
    EnhancedParseResult,
    BatchParseRequest,
    BatchParseResponse,
    ParserIntegrationConfig,
    ParsingMethod
)
from core.config.base import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


class EnhancedParserIntegrationService:
    """
    Service for integrating enhanced AI parser with the main system
    
    This service provides a bridge between the parser_module and the main
    RAG Construction Materials API, handling configuration, caching, and
    result transformation.
    """
    
    def __init__(self, config: Optional[ParserIntegrationConfig] = None):
        """
        Initialize the parser integration service
        
        Args:
            config: Optional integration configuration
        """
        self.config = config or ParserIntegrationConfig()
        self.settings = get_settings()
        self.logger = logger
        
        # Initialize parser with integration config
        self.parser = self._initialize_parser()
        
        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "color_extractions": 0,
            "total_processing_time": 0.0
        }
        
        self.logger.info("Enhanced Parser Integration Service initialized")
    
    def _initialize_parser(self) -> MaterialParser:
        """Initialize the AI parser with proper configuration"""
        try:
            # Create parser config based on integration settings
            parser_config = ParserConfig(
                openai_api_key=self.settings.OPENAI_API_KEY,
                openai_model=self.config.openai_model,
                embeddings_model=self.config.embeddings_model,
                embeddings_dimensions=self.config.embeddings_dimensions,
                embeddings_enabled=True,
                enable_caching=self.config.embedding_cache_enabled,
                max_retries=self.config.retry_attempts,
                openai_timeout=self.config.request_timeout,
                confidence_threshold=self.config.confidence_threshold,
                enable_validation=self.config.enable_validation,
                integration_mode=True,
                use_main_project_config=True
            )
            
            parser = MaterialParser(config=parser_config, env="integration")
            self.logger.info(f"Parser initialized with model: {self.config.openai_model}")
            return parser
            
        except Exception as e:
            self.logger.error(f"Failed to initialize parser: {e}")
            raise RuntimeError(f"Parser initialization failed: {e}")
    
    async def parse_single_material(self, request: EnhancedParseRequest) -> EnhancedParseResult:
        """
        Parse a single material with enhanced features
        
        Args:
            request: Enhanced parse request
            
        Returns:
            Enhanced parse result with color and embeddings
        """
        start_time = time.time()
        
        try:
            self.logger.debug(f"Parsing material: {request.name}")
            
            # Parse material using enhanced parser
            result_dict = self.parser.parse_single(
                name=request.name,
                unit=request.unit,
                price=request.price
            )
            
            # Convert parser result to enhanced result
            enhanced_result = self._convert_to_enhanced_result(
                result_dict, 
                request,
                time.time() - start_time
            )
            
            # Update statistics
            self._update_stats(enhanced_result)
            
            self.logger.info(
                f"Successfully parsed: {request.name} -> "
                f"{enhanced_result.unit_parsed} (color: {enhanced_result.color})"
            )
            
            return enhanced_result
            
        except Exception as e:
            self.logger.error(f"Error parsing material {request.name}: {e}")
            
            # Return error result
            error_result = EnhancedParseResult(
                name=request.name,
                original_unit=request.unit,
                original_price=request.price,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
                parsing_method=request.parsing_method
            )
            
            self.stats["failed_parses"] += 1
            return error_result
    
    async def parse_batch_materials(self, request: BatchParseRequest) -> BatchParseResponse:
        """
        Parse multiple materials in batch
        
        Args:
            request: Batch parse request
            
        Returns:
            Batch parse response with statistics
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing batch of {len(request.materials)} materials")
            
            if request.parallel_processing and len(request.materials) > 1:
                # Parallel processing
                results = await self._process_batch_parallel(
                    request.materials, 
                    request.max_workers
                )
            else:
                # Sequential processing
                results = await self._process_batch_sequential(request.materials)
            
            # Calculate statistics
            total_time = time.time() - start_time
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            # Create response
            response = BatchParseResponse(
                results=results,
                total_processed=len(results),
                successful_parses=successful,
                failed_parses=failed,
                success_rate=(successful / len(results)) * 100 if results else 0,
                total_processing_time=total_time
            )
            
            self.logger.info(
                f"Batch processing completed: {successful}/{len(results)} successful "
                f"({response.success_rate:.1f}%) in {total_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            raise RuntimeError(f"Batch processing failed: {e}")
    
    async def _process_batch_parallel(
        self, 
        materials: List[EnhancedParseRequest], 
        max_workers: int
    ) -> List[EnhancedParseResult]:
        """Process materials in parallel"""
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_with_semaphore(material):
            async with semaphore:
                return await self.parse_single_material(material)
        
        # Execute all tasks concurrently
        tasks = [process_with_semaphore(material) for material in materials]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = EnhancedParseResult(
                    name=materials[i].name,
                    original_unit=materials[i].unit,
                    original_price=materials[i].price,
                    success=False,
                    error_message=str(result),
                    processing_time=0.0,
                    parsing_method=materials[i].parsing_method
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_batch_sequential(
        self, 
        materials: List[EnhancedParseRequest]
    ) -> List[EnhancedParseResult]:
        """Process materials sequentially"""
        
        results = []
        for material in materials:
            result = await self.parse_single_material(material)
            results.append(result)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return results
    
    def _convert_to_enhanced_result(
        self, 
        parser_result: Dict[str, Any], 
        request: EnhancedParseRequest,
        processing_time: float
    ) -> EnhancedParseResult:
        """
        Convert parser module result to enhanced result format
        
        Args:
            parser_result: Result from parser module
            request: Original request
            processing_time: Total processing time
            
        Returns:
            Enhanced parse result
        """
        
        return EnhancedParseResult(
            # Original data
            name=parser_result.get("name", request.name),
            original_unit=parser_result.get("original_unit", request.unit),
            original_price=parser_result.get("original_price", request.price),
            
            # Parsed results
            unit_parsed=parser_result.get("unit_parsed"),
            price_coefficient=parser_result.get("price_coefficient"),
            price_parsed=parser_result.get("price_parsed"),
            
            # Enhanced fields
            color=parser_result.get("color"),
            embeddings=parser_result.get("embeddings"),
            color_embedding=parser_result.get("color_embedding"),
            unit_embedding=parser_result.get("unit_embedding"),
            
            # Metadata
            parsing_method=ParsingMethod(parser_result.get("parsing_method", "ai_gpt")),
            confidence=parser_result.get("confidence", 0.0),
            success=parser_result.get("success", False),
            error_message=parser_result.get("error_message"),
            processing_time=processing_time
        )
    
    def _update_stats(self, result: EnhancedParseResult):
        """Update internal statistics"""
        self.stats["total_requests"] += 1
        self.stats["total_processing_time"] += result.processing_time
        
        if result.success:
            self.stats["successful_parses"] += 1
        else:
            self.stats["failed_parses"] += 1
        
        if result.color:
            self.stats["color_extractions"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get parsing statistics
        
        Returns:
            Dictionary with current statistics
        """
        total_requests = self.stats["total_requests"]
        
        return {
            "total_requests": total_requests,
            "successful_parses": self.stats["successful_parses"],
            "failed_parses": self.stats["failed_parses"],
            "color_extractions": self.stats["color_extractions"],
            "success_rate": (
                self.stats["successful_parses"] / total_requests * 100 
                if total_requests > 0 else 0
            ),
            "color_extraction_rate": (
                self.stats["color_extractions"] / total_requests * 100
                if total_requests > 0 else 0
            ),
            "average_processing_time": (
                self.stats["total_processing_time"] / total_requests
                if total_requests > 0 else 0
            ),
            "total_processing_time": self.stats["total_processing_time"]
        }
    
    def clear_statistics(self):
        """Clear all statistics"""
        self.stats = {
            "total_requests": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "color_extractions": 0,
            "total_processing_time": 0.0
        }
        self.logger.info("Statistics cleared")
    
    async def test_connection(self) -> bool:
        """
        Test parser connection and functionality
        
        Returns:
            True if parser is working correctly
        """
        try:
            test_request = EnhancedParseRequest(
                name="Тестовый материал белый",
                unit="шт",
                price=100.0
            )
            
            result = await self.parse_single_material(test_request)
            
            # Check if basic parsing worked
            success = result.success and result.unit_parsed is not None
            
            self.logger.info(f"Parser connection test: {'PASSED' if success else 'FAILED'}")
            return success
            
        except Exception as e:
            self.logger.error(f"Parser connection test failed: {e}")
            return False
    
    def get_parser_info(self) -> Dict[str, Any]:
        """
        Get information about the parser configuration
        
        Returns:
            Dictionary with parser information
        """
        return {
            "parser_type": "enhanced_ai_parser",
            "openai_model": self.config.openai_model,
            "embeddings_model": self.config.embeddings_model,
            "embeddings_dimensions": self.config.embeddings_dimensions,
            "confidence_threshold": self.config.confidence_threshold,
            "max_concurrent_requests": self.config.max_concurrent_requests,
            "request_timeout": self.config.request_timeout,
            "retry_attempts": self.config.retry_attempts,
            "embedding_cache_enabled": self.config.embedding_cache_enabled,
            "validation_enabled": self.config.enable_validation
        }


# Singleton instance for the application
_parser_service: Optional[EnhancedParserIntegrationService] = None


def get_parser_service(config: Optional[ParserIntegrationConfig] = None) -> EnhancedParserIntegrationService:
    """
    Get or create the parser integration service instance
    
    Args:
        config: Optional configuration (used only on first call)
        
    Returns:
        Parser integration service instance
    """
    global _parser_service
    
    if _parser_service is None:
        _parser_service = EnhancedParserIntegrationService(config)
    
    return _parser_service


async def test_enhanced_parser() -> bool:
    """
    Test the enhanced parser integration
    
    Returns:
        True if all tests pass
    """
    try:
        service = get_parser_service()
        
        # Test connection
        connection_ok = await service.test_connection()
        if not connection_ok:
            return False
        
        # Test single parse
        test_request = EnhancedParseRequest(
            name="Кирпич керамический белый одинарный",
            unit="шт",
            price=15.50
        )
        
        result = await service.parse_single_material(test_request)
        
        # Verify enhanced features
        has_color = result.color is not None
        has_embeddings = result.embeddings is not None
        has_unit_parsed = result.unit_parsed is not None
        
        logger.info(f"Enhanced parser test results:")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Color extracted: {has_color} ('{result.color}')")
        logger.info(f"  Unit parsed: {has_unit_parsed} ('{result.unit_parsed}')")
        logger.info(f"  Embeddings generated: {has_embeddings}")
        logger.info(f"  Processing time: {result.processing_time:.2f}s")
        
        return result.success and has_embeddings
        
    except Exception as e:
        logger.error(f"Enhanced parser test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the service when run directly
    async def main():
        success = await test_enhanced_parser()
        print(f"Enhanced Parser Integration Test: {'PASSED' if success else 'FAILED'}")
    
    asyncio.run(main()) 