"""
Material Parser Service

High-level service for parsing construction materials with AI-powered analysis,
batch processing, and comprehensive result management.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Core infrastructure imports
from core.config.parsers import ParserConfig, get_parser_config
from core.logging.specialized.parsers import (
    get_material_parser_logger,
    get_material_parser_metrics
)

# Parser interface imports
from ..interfaces import (
    IMaterialParser,
    MaterialParseData,
    AIParseRequest,
    AIParseResult,
    ParseStatus,
    BatchParseRequest,
    BatchParseResult,
    InputType,
    OutputType
)

# Service imports
from .ai_parser_service import AIParserService, get_ai_parser_service

# Legacy compatibility imports
try:
    from parser_module.units_config import normalize_unit, get_common_units_for_ai
    LEGACY_IMPORTS_AVAILABLE = True
except ImportError:
    LEGACY_IMPORTS_AVAILABLE = False


@dataclass
class MaterialParseContext:
    """Context for material parsing operations"""
    operation_id: str
    start_time: float
    total_materials: int
    processed_materials: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    cache_hits: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.processed_materials == 0:
            return 0.0
        return self.successful_parses / self.processed_materials
    
    @property
    def progress(self) -> float:
        """Calculate progress percentage"""
        if self.total_materials == 0:
            return 100.0
        return (self.processed_materials / self.total_materials) * 100.0


class MaterialParserService(IMaterialParser[str, MaterialParseData]):
    """
    High-level service for parsing construction materials.
    
    Provides a comprehensive interface for material parsing operations including
    single item parsing, batch processing, file operations, and result management.
    """
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize Material Parser Service.
        
        Args:
            config: Optional parser configuration. If None, uses default config.
        """
        self.config = config or get_parser_config()
        self.logger = get_material_parser_logger()
        self.metrics = get_material_parser_metrics()
        
        # Initialize AI parser service
        self.ai_parser_service = get_ai_parser_service()
        
        # Service metadata
        self._service_name = "material_parser_service"
        self._version = "2.0.0"
        self._initialized = True
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "cache_hits": 0,
            "batch_operations": 0,
            "file_operations": 0
        }
        
        self.logger.info(f"Material Parser Service v{self._version} initialized")
    
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
                self.ai_parser_service.is_healthy() and
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
            "ai_parser_healthy": self.ai_parser_service.is_healthy(),
            "config_available": self.config is not None,
            "legacy_imports": LEGACY_IMPORTS_AVAILABLE,
            "statistics": self.stats,
            "ai_parser_details": self.ai_parser_service.get_health_details()
        }
    
    async def parse_material(self, material_text: str) -> AIParseResult[MaterialParseData]:
        """
        Parse single material text.
        
        Args:
            material_text: Material description text
            
        Returns:
            AIParseResult: Parse result with material data
        """
        self.logger.debug(f"Parsing single material: {material_text}")
        
        try:
            # Create AI parse request
            request = AIParseRequest(
                input_data=material_text,
                request_id=f"material_parse_{id(material_text)}",
                options={"enable_embeddings": True}
            )
            
            # Parse with AI service
            result = await self.ai_parser_service.parse_request(request)
            
            # Update statistics
            self.stats["total_processed"] += 1
            if result.status == ParseStatus.SUCCESS:
                self.stats["successful_parses"] += 1
            else:
                self.stats["failed_parses"] += 1
            
            # Log metrics
            self.metrics.record_material_parse(
                material_name=material_text,
                success=result.status == ParseStatus.SUCCESS,
                processing_time=result.processing_time,
                confidence=result.confidence
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing material {material_text}: {e}")
            self.stats["failed_parses"] += 1
            
            # Return error result
            return AIParseResult(
                status=ParseStatus.ERROR,
                data=MaterialParseData(
                    name=material_text,
                    original_unit="",
                    original_price=0.0
                ),
                confidence=0.0,
                processing_time=0.0,
                error_message=str(e),
                request_id=f"material_parse_{id(material_text)}"
            )
    
    async def extract_unit(self, text: str) -> Optional[str]:
        """
        Extract unit from text.
        
        Args:
            text: Text to extract unit from
            
        Returns:
            Optional[str]: Extracted unit or None if not found
        """
        try:
            # Parse text to extract unit
            result = await self.parse_material(text)
            
            if result.status == ParseStatus.SUCCESS and result.data.unit_parsed:
                return result.data.unit_parsed
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting unit from {text}: {e}")
            return None
    
    async def extract_color(self, text: str) -> Optional[str]:
        """
        Extract color from text.
        
        Args:
            text: Text to extract color from
            
        Returns:
            Optional[str]: Extracted color or None if not found
        """
        try:
            # Parse text to extract color
            result = await self.parse_material(text)
            
            if result.status == ParseStatus.SUCCESS and result.data.color:
                return result.data.color
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting color from {text}: {e}")
            return None
    
    async def parse_batch(self, materials: List[str]) -> BatchParseResult[MaterialParseData]:
        """
        Parse multiple materials.
        
        Args:
            materials: List of material description texts
            
        Returns:
            BatchParseResult: Batch parsing results
        """
        self.logger.info(f"Parsing batch of {len(materials)} materials")
        
        context = MaterialParseContext(
            operation_id=f"batch_parse_{id(materials)}",
            start_time=asyncio.get_event_loop().time(),
            total_materials=len(materials)
        )
        
        try:
            # Create AI parse requests
            requests = [
                AIParseRequest(
                    input_data=material,
                    request_id=f"batch_item_{i}",
                    options={"enable_embeddings": True}
                )
                for i, material in enumerate(materials)
            ]
            
            # Process batch with AI service
            results = await self.ai_parser_service.parse_batch(requests)
            
            # Update context and statistics
            context.processed_materials = len(results)
            for result in results:
                if result.status == ParseStatus.SUCCESS:
                    context.successful_parses += 1
                    self.stats["successful_parses"] += 1
                else:
                    context.failed_parses += 1
                    self.stats["failed_parses"] += 1
            
            self.stats["total_processed"] += len(materials)
            self.stats["batch_operations"] += 1
            
            # Log batch metrics
            self.metrics.record_batch_parse(
                batch_size=len(materials),
                success_count=context.successful_parses,
                failure_count=context.failed_parses,
                processing_time=asyncio.get_event_loop().time() - context.start_time
            )
            
            # Create batch result
            batch_result = BatchParseResult(
                results=results,
                total_processed=context.processed_materials,
                successful_count=context.successful_parses,
                failed_count=context.failed_parses,
                success_rate=context.success_rate,
                processing_time=asyncio.get_event_loop().time() - context.start_time
            )
            
            self.logger.info(f"Batch parsing completed: {context.successful_parses}/{context.total_materials} successful")
            return batch_result
            
        except Exception as e:
            self.logger.error(f"Error parsing batch: {e}")
            self.stats["failed_parses"] += len(materials)
            
            # Return error batch result
            error_results = [
                AIParseResult(
                    status=ParseStatus.ERROR,
                    data=MaterialParseData(
                        name=material,
                        original_unit="",
                        original_price=0.0
                    ),
                    confidence=0.0,
                    processing_time=0.0,
                    error_message=str(e),
                    request_id=f"batch_item_{i}"
                )
                for i, material in enumerate(materials)
            ]
            
            return BatchParseResult(
                results=error_results,
                total_processed=len(materials),
                successful_count=0,
                failed_count=len(materials),
                success_rate=0.0,
                processing_time=asyncio.get_event_loop().time() - context.start_time
            )
    
    async def parse_from_file(self, file_path: Union[str, Path]) -> BatchParseResult[MaterialParseData]:
        """
        Parse materials from JSON file.
        
        Args:
            file_path: Path to JSON file with materials
            
        Returns:
            BatchParseResult: Batch parsing results
        """
        file_path = Path(file_path)
        self.logger.info(f"Parsing materials from file: {file_path}")
        
        try:
            # Load materials from file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract material texts
            materials = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        materials.append(item)
                    elif isinstance(item, dict):
                        # Try to extract material name from various possible keys
                        name = item.get('name') or item.get('material') or item.get('description') or str(item)
                        materials.append(name)
            else:
                raise ValueError("File must contain a list of materials")
            
            # Parse materials
            result = await self.parse_batch(materials)
            
            self.stats["file_operations"] += 1
            
            return result
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing file {file_path}: {e}")
            raise
    
    async def save_results(
        self, 
        results: BatchParseResult[MaterialParseData], 
        output_path: Union[str, Path]
    ) -> None:
        """
        Save parsing results to JSON file.
        
        Args:
            results: Batch parsing results
            output_path: Path for output file
        """
        output_path = Path(output_path)
        self.logger.info(f"Saving {len(results.results)} results to: {output_path}")
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert results to serializable format
            serializable_results = []
            for result in results.results:
                result_dict = {
                    "status": result.status.value,
                    "data": {
                        "name": result.data.name,
                        "original_unit": result.data.original_unit,
                        "original_price": result.data.original_price,
                        "unit_parsed": result.data.unit_parsed,
                        "price_coefficient": result.data.price_coefficient,
                        "price_parsed": result.data.price_parsed,
                        "color": result.data.color,
                        "parsing_method": result.data.parsing_method,
                        "confidence": result.data.confidence
                    },
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "error_message": result.error_message,
                    "request_id": result.request_id
                }
                serializable_results.append(result_dict)
            
            # Create full output structure
            output_data = {
                "metadata": {
                    "total_processed": results.total_processed,
                    "successful_count": results.successful_count,
                    "failed_count": results.failed_count,
                    "success_rate": results.success_rate,
                    "processing_time": results.processing_time,
                    "service_version": self.version
                },
                "results": serializable_results
            }
            
            # Save results
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Results saved successfully to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get parsing statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        # Get AI parser statistics
        ai_stats = self.ai_parser_service.get_statistics()
        
        # Combine statistics
        combined_stats = {
            "service_name": self.service_name,
            "version": self.version,
            "material_parser_stats": self.stats.copy(),
            "ai_parser_stats": ai_stats,
            "success_rate": (
                self.stats["successful_parses"] / self.stats["total_processed"] 
                if self.stats["total_processed"] > 0 else 0.0
            ),
            "health_status": self.get_health_details()
        }
        
        return combined_stats
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        self.ai_parser_service.clear_cache()
        self.logger.info("All caches cleared")
    
    def get_supported_units(self) -> List[str]:
        """
        Get list of supported units.
        
        Returns:
            List[str]: List of supported units
        """
        if not LEGACY_IMPORTS_AVAILABLE:
            return ["шт", "м", "м²", "м³", "кг", "т", "л", "упак"]
        
        return get_common_units_for_ai()
    
    def validate_unit(self, unit: str) -> Optional[str]:
        """
        Validate and normalize unit.
        
        Args:
            unit: Unit to validate
            
        Returns:
            Optional[str]: Normalized unit or None if invalid
        """
        if not LEGACY_IMPORTS_AVAILABLE:
            # Basic validation without legacy imports
            common_units = ["шт", "м", "м²", "м³", "кг", "т", "л", "упак"]
            unit_lower = unit.lower().strip()
            
            for common_unit in common_units:
                if unit_lower == common_unit.lower():
                    return common_unit
            
            return None
        
        try:
            normalized = normalize_unit(unit)
            return normalized if normalized else None
        except Exception:
            return None
    
    def export_config(self, output_path: Union[str, Path]) -> None:
        """
        Export current configuration to file.
        
        Args:
            output_path: Path for config export
        """
        output_path = Path(output_path)
        self.logger.info(f"Exporting configuration to: {output_path}")
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export configuration
            config_dict = {
                "service_name": self.service_name,
                "version": self.version,
                "configuration": {
                    "models": {
                        "openai_model": self.config.models.openai_model,
                        "embedding_model": self.config.models.embedding_model,
                        "temperature": self.config.models.temperature,
                        "max_tokens": self.config.models.max_tokens
                    },
                    "performance": {
                        "batch_size": self.config.performance.batch_size,
                        "timeout": self.config.performance.timeout,
                        "retry_attempts": self.config.performance.retry_attempts,
                        "enable_caching": self.config.performance.enable_caching
                    },
                    "validation": {
                        "confidence_threshold": self.config.validation.confidence_threshold,
                        "min_price_coefficient": self.config.validation.min_price_coefficient,
                        "max_price_coefficient": self.config.validation.max_price_coefficient
                    },
                    "features": {
                        "embeddings_enabled": self.config.features.embeddings_enabled,
                        "embeddings_dimensions": self.config.features.embeddings_dimensions,
                        "color_extraction_enabled": self.config.features.color_extraction_enabled
                    }
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Configuration exported successfully to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            raise
    
    async def create_example_data(self, output_path: Union[str, Path]) -> None:
        """
        Create example data for testing.
        
        Args:
            output_path: Path for example data file
        """
        output_path = Path(output_path)
        self.logger.info(f"Creating example data at: {output_path}")
        
        try:
            # Create example materials
            example_materials = [
                "Кирпич красный облицовочный 250x120x65 мм",
                "Цемент портландцемент М400, 50 кг мешок",
                "Песок строительный речной, 1 тонна",
                "Доска обрезная сосна 50x150x6000 мм",
                "Плитка керамическая белая 300x300 мм",
                "Арматура рифленая А500С диаметр 12 мм",
                "Гипсокартон влагостойкий 12.5 мм",
                "Утеплитель минеральная вата 50 мм",
                "Краска водоэмульсионная белая 10 л",
                "Профнастил С21 оцинкованный 0.5 мм"
            ]
            
            # Parse example materials
            batch_result = await self.parse_batch(example_materials)
            
            # Save example data
            await self.save_results(batch_result, output_path)
            
            self.logger.info(f"Example data created successfully at: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating example data: {e}")
            raise


# Service factory
@lru_cache(maxsize=1)
def get_material_parser_service() -> MaterialParserService:
    """
    Get Material Parser Service instance (singleton).
    
    Returns:
        MaterialParserService: Service instance
    """
    return MaterialParserService()


# Async context manager for service
@asynccontextmanager
async def material_parser_service_context():
    """
    Async context manager for Material Parser Service.
    
    Yields:
        MaterialParserService: Service instance
    """
    service = get_material_parser_service()
    try:
        yield service
    finally:
        # Cleanup if needed
        pass


# Convenience functions for backward compatibility
async def parse_material(material_text: str) -> AIParseResult[MaterialParseData]:
    """
    Quick parse single material.
    
    Args:
        material_text: Material description text
        
    Returns:
        AIParseResult: Parse result
    """
    service = get_material_parser_service()
    return await service.parse_material(material_text)


async def parse_batch(materials: List[str]) -> BatchParseResult[MaterialParseData]:
    """
    Quick parse multiple materials.
    
    Args:
        materials: List of material descriptions
        
    Returns:
        BatchParseResult: Batch parsing results
    """
    service = get_material_parser_service()
    return await service.parse_batch(materials)


async def parse_file(file_path: Union[str, Path]) -> BatchParseResult[MaterialParseData]:
    """
    Quick parse materials from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        BatchParseResult: Batch parsing results
    """
    service = get_material_parser_service()
    return await service.parse_from_file(file_path) 