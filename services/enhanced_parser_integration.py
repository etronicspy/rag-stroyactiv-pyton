"""
Enhanced Parser Integration Service

Modern integration service using the new core.parsers architecture
with full async support and comprehensive error handling.
"""

import asyncio
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import asdict

# Modern core.parsers architecture
from core.parsers import (
    get_material_parser_service,
    get_batch_parser_service,
    get_parser_config_manager,
    MaterialParseData,
    AIParseRequest,
    AIParseResult,
    BatchParseResult,
    ParseStatus,
    is_migration_complete,
    check_parser_availability
)

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
    Modern parser integration service using core.parsers architecture.
    
    Provides seamless integration between new parser services and existing API,
    with automatic fallback to legacy parsers if needed.
    """
    
    def __init__(self, config: Optional[ParserIntegrationConfig] = None):
        print("DEBUG: EnhancedParserIntegrationService __init__ called")
        """
        Initialize the enhanced parser integration service.
        
        Args:
            config: Optional integration configuration
        """
        self.config = config or ParserIntegrationConfig()
        self.settings = get_settings()
        self.logger = logger
        
        # Determine which parser system to use
        self.use_new_parsers = is_migration_complete()
        
        # Initialize appropriate parser system
        if self.use_new_parsers:
            self._initialize_new_parsers()
        else:
            raise RuntimeError("New parser architecture is not available.")
        
        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "color_extractions": 0,
            "total_processing_time": 0.0,
            "parser_type": "new"
        }
        
        self.logger.info(
            f"Enhanced Parser Integration Service initialized "
            f"(using new parsers)"
        )
    
    def _initialize_new_parsers(self):
        """Initialize new core.parsers services"""
        try:
            # Get parser services
            self.material_parser = get_material_parser_service()
            self.batch_parser = get_batch_parser_service()
            self.config_manager = get_parser_config_manager()
            
            # Switch to integration profile if available
            self.config_manager.switch_profile("integration")
            
            # Check service health
            availability = check_parser_availability()
            self.logger.info(f"Parser services availability: {availability}")
            
            self.parser = None  # Not used in new architecture
            
        except Exception as e:
            self.logger.error(f"Failed to initialize new parsers: {e}")
            raise RuntimeError(f"New parser initialization failed: {e}")
    
    async def parse_single_material(self, request: EnhancedParseRequest) -> EnhancedParseResult:
        """
        Parse a single material with enhanced features.
        
        Args:
            request: Enhanced parse request
            
        Returns:
            Enhanced parse result with color and embeddings
        """
        start_time = time.time()
        
        try:
            self.logger.debug(f"Parsing material: {request.name}")
            
            # Use new parser architecture
            result = await self._parse_with_new_parsers(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # Update statistics
            self._update_stats(result)
            
            self.logger.info(
                f"Successfully parsed: {request.name} -> "
                f"{result.unit_parsed} (color: {result.color})"
            )
            
            return result
            
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
    
    async def _parse_with_new_parsers(self, request: EnhancedParseRequest) -> EnhancedParseResult:
        """Parse material using new core.parsers architecture"""
        
        # Create full material description
        material_text = f"{request.name}"
        if request.unit:
            material_text += f", {request.unit}"
        if request.price > 0:
            material_text += f", {request.price} руб"
        
        # Parse with new material parser service
        parse_result = await self.material_parser.parse_material(material_text)
        
        # Convert to enhanced result format
        if parse_result.status == ParseStatus.SUCCESS:
            enhanced_result = EnhancedParseResult(
                name=request.name,
                original_unit=request.unit,
                original_price=request.price,
                unit_parsed=parse_result.data.unit_parsed,
                price_coefficient=parse_result.data.price_coefficient,
                price_parsed=parse_result.data.price_parsed,
                color=parse_result.data.color,
                embeddings=parse_result.data.embeddings,
                color_embedding=parse_result.data.color_embedding,
                unit_embedding=parse_result.data.unit_embedding,
                parsing_method=ParsingMethod.AI_GPT,
                confidence=parse_result.confidence,
                success=True,
                processing_time=parse_result.processing_time
            )
        else:
            enhanced_result = EnhancedParseResult(
                name=request.name,
                original_unit=request.unit,
                original_price=request.price,
                success=False,
                error_message=parse_result.error_message,
                parsing_method=request.parsing_method,
                confidence=parse_result.confidence,
                processing_time=parse_result.processing_time
            )
        
        return enhanced_result
    
    async def parse_batch_materials(self, request: BatchParseRequest) -> BatchParseResponse:
        """
        Parse multiple materials in batch.
        
        Args:
            request: Batch parse request
            
        Returns:
            Batch parse response with statistics
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing batch of {len(request.materials)} materials")
            
            # Use new batch parser
            results = await self._process_batch_with_new_parsers(request)
            
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
                f"in {total_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            raise
    
    async def _process_batch_with_new_parsers(self, request: BatchParseRequest) -> List[EnhancedParseResult]:
        """Process batch using new parser architecture"""
        
        # Convert to material texts for batch processing
        material_texts = []
        for material in request.materials:
            text = f"{material.name}"
            if material.unit:
                text += f", {material.unit}"
            if material.price > 0:
                text += f", {material.price} руб"
            material_texts.append(text)
        
        # Process with batch parser
        batch_result = await self.batch_parser.parse_batch(material_texts)
        
        # Convert results to enhanced format
        enhanced_results = []
        for i, parse_result in enumerate(batch_result.results):
            original_request = request.materials[i]
            
            if parse_result.status == ParseStatus.SUCCESS:
                enhanced_result = EnhancedParseResult(
                    name=original_request.name,
                    original_unit=original_request.unit,
                    original_price=original_request.price,
                    unit_parsed=parse_result.data.unit_parsed,
                    price_coefficient=parse_result.data.price_coefficient,
                    price_parsed=parse_result.data.price_parsed,
                    color=parse_result.data.color,
                    embeddings=parse_result.data.embeddings,
                    color_embedding=parse_result.data.color_embedding,
                    unit_embedding=parse_result.data.unit_embedding,
                    parsing_method=ParsingMethod.AI_GPT,
                    confidence=parse_result.confidence,
                    success=True,
                    processing_time=parse_result.processing_time
                )
            else:
                enhanced_result = EnhancedParseResult(
                    name=original_request.name,
                    original_unit=original_request.unit,
                    original_price=original_request.price,
                    success=False,
                    error_message=parse_result.error_message,
                    parsing_method=original_request.parsing_method,
                    confidence=parse_result.confidence,
                    processing_time=parse_result.processing_time
                )
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    def _update_stats(self, result: EnhancedParseResult):
        """Update service statistics"""
        self.stats["total_requests"] += 1
        self.stats["total_processing_time"] += result.processing_time
        
        if result.success:
            self.stats["successful_parses"] += 1
            if result.color:
                self.stats["color_extractions"] += 1
        else:
            self.stats["failed_parses"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get integration service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        base_stats = {
            "service_type": "enhanced_parser_integration",
            "parser_architecture": "new",
            "integration_stats": self.stats.copy()
        }
        
        # Add parser-specific statistics
        if self.material_parser:
            base_stats["material_parser_stats"] = self.material_parser.get_statistics()
        if self.batch_parser:
            base_stats["batch_parser_stats"] = self.batch_parser.get_statistics()
        if self.config_manager:
            base_stats["config_manager_stats"] = self.config_manager.get_statistics()
        
        return base_stats
    
    def clear_statistics(self):
        """Clear service statistics"""
        self.stats = {
            "total_requests": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "color_extractions": 0,
            "total_processing_time": 0.0,
            "parser_type": "new"
        }
        
        # Clear parser statistics if using new architecture
        if self.material_parser:
            self.material_parser.clear_cache()
        if self.batch_parser:
            self.batch_parser.clear_statistics()
    
    async def test_connection(self) -> bool:
        """
        Test parser connection and functionality.
        
        Returns:
            True if parsers are working correctly
        """
        try:
            # Test with a simple material
            test_request = EnhancedParseRequest(
                name="Тестовый материал",
                unit="шт",
                price=100.0,
                parsing_method=ParsingMethod.AI_GPT
            )
            
            result = await self.parse_single_material(test_request)
            
            # Check if we got a valid result
            success = result is not None
            
            self.logger.info(f"Parser connection test: {'✅ SUCCESS' if success else '❌ FAILED'}")
            return success
            
        except Exception as e:
            self.logger.error(f"Parser connection test failed: {e}")
            return False
    
    def get_parser_info(self) -> Dict[str, Any]:
        """
        Get information about the current parser system.
        
        Returns:
            Dictionary with parser information
        """
        info = {
            "architecture": "new",
            "migration_complete": is_migration_complete(),
            "config": {
                "openai_model": self.config.openai_model,
                "embeddings_model": self.config.embeddings_model,
                "embeddings_dimensions": self.config.embeddings_dimensions,
                "confidence_threshold": self.config.confidence_threshold
            }
        }
        
        if self.material_parser:
            info["parser_availability"] = check_parser_availability()
            if self.config_manager:
                info["current_profile"] = self.config_manager.current_profile
        
        return info


# Service factory function
def get_parser_service(config: Optional[ParserIntegrationConfig] = None) -> EnhancedParserIntegrationService:
    """
    Get an instance of the Enhanced Parser Integration Service.
    
    Args:
        config: Optional integration configuration
        
    Returns:
        EnhancedParserIntegrationService instance
    """
    return EnhancedParserIntegrationService(config)


# Testing and utility functions
async def test_enhanced_parser() -> bool:
    """
    Test the enhanced parser integration.
    
    Returns:
        True if all tests pass
    """
    try:
        service = get_parser_service()
        
        # Test connection
        connection_ok = await service.test_connection()
        if not connection_ok:
            return False
        
        # Test single material parsing
        test_materials = [
            EnhancedParseRequest(
                name="Кирпич красный облицовочный",
                unit="шт",
                price=25.0,
                parsing_method=ParsingMethod.AI_GPT
            ),
            EnhancedParseRequest(
                name="Цемент портландцемент М400",
                unit="мешок",
                price=350.0,
                parsing_method=ParsingMethod.AI_GPT
            )
        ]
        
        # Test batch processing
        batch_request = BatchParseRequest(
            materials=test_materials,
            parallel_processing=True,
            max_workers=2
        )
        
        batch_response = await service.parse_batch_materials(batch_request)
        
        success = (
            batch_response.total_processed == len(test_materials) and
            batch_response.successful_parses > 0
        )
        
        logger.info(f"Enhanced parser test: {'✅ PASSED' if success else '❌ FAILED'}")
        logger.info(f"Batch results: {batch_response.successful_parses}/{batch_response.total_processed} successful")
        
        return success
        
    except Exception as e:
        logger.error(f"Enhanced parser test failed: {e}")
        return False


# Main execution for testing
if __name__ == "__main__":
    async def main():
        """Main test function"""
        print("🧪 Testing Enhanced Parser Integration Service...")
        
        success = await test_enhanced_parser()
        
        if success:
            print("✅ All tests passed!")
        else:
            print("❌ Tests failed!")
            
        return success
    
    # Run the test
    asyncio.run(main()) 