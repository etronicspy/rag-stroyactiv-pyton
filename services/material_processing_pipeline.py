"""
Material Processing Pipeline Service

Сервис пайплайна обработки материалов согласно диаграмме интеграции:
id, name, unit → AI_parser → RAG нормализация → Поиск SKU → Сохранение в БД → id, sku
"""

import asyncio
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys

from core.logging import get_logger
from core.config.base import get_settings
from core.database.interfaces import IVectorDatabase
from core.schemas.pipeline_models import (
    MaterialProcessRequest,
    ProcessingResult,
    BatchProcessingRequest,
    BatchProcessingResponse,
    AIParsingResult,
    RAGNormalizationResult,
    SKUSearchResult,
    DatabaseSaveResult,
    ProcessingStage,
    ProcessingStatus,
    PipelineConfiguration,
    PipelineStatistics
)
from core.schemas.enhanced_parsing import (
    EnhancedParseRequest,
    EnhancedParseResult,
    ParsingMethod
)
from services.enhanced_parser_integration import EnhancedParserIntegrationService
from services.embedding_comparison import EmbeddingComparisonService
from services.sku_search_service import get_sku_search_service
from core.database.collections.colors import ColorCollection
from core.database.collections.units import UnitsCollection

logger = get_logger(__name__)


class MaterialProcessingPipeline:
    """
    Main service for material processing pipeline according to diagram:
    
    id, name, unit → AI_parser → RAG normalization → SKU search → Database save → id, sku
    
    Основной сервис для пайплайна обработки материалов согласно диаграмме:
    id, name, unit → AI_parser → RAG нормализация → Поиск SKU → Сохранение в БД → id, sku
    """
    
    def __init__(
        self,
        vector_db: Optional[IVectorDatabase] = None,
        config: Optional[PipelineConfiguration] = None
    ):
        """
        Initialize the material processing pipeline
        
        Args:
            vector_db: Vector database instance
            config: Pipeline configuration
        """
        self.settings = get_settings()
        self.logger = logger
        self.config = config or PipelineConfiguration()
        
        # Initialize services
        self.parser_service = EnhancedParserIntegrationService()
        self.rag_service = EmbeddingComparisonService()
        self.sku_search_service = get_sku_search_service()  # NEW: SKU search service
        
        # Statistics tracking
        self.statistics = PipelineStatistics(
            statistics_updated_at=datetime.utcnow()
        )
        
        self.logger.info("Material Processing Pipeline initialized")
    
    async def process_material(self, request: MaterialProcessRequest) -> ProcessingResult:
        """
        Process single material through complete pipeline
        
        Args:
            request: Material processing request
            
        Returns:
            Complete processing result
        """
        start_time = time.time()
        started_at = datetime.utcnow()
        
        self.logger.info(f"Starting processing for material: {request.id} - {request.name}")
        
        # Initialize result with default values
        result = ProcessingResult(
            request_id=request.id,
            material_name=request.name,
            original_unit=request.unit,
            sku=None,
            ai_parsing=AIParsingResult(
                success=False,
                processing_time=0.0
            ),
            rag_normalization=RAGNormalizationResult(
                success=False,
                processing_time=0.0
            ),
            sku_search=SKUSearchResult(
                success=False,
                processing_time=0.0
            ),
            database_save=DatabaseSaveResult(
                success=False,
                processing_time=0.0
            ),
            overall_success=False,
            current_stage=ProcessingStage.AI_PARSING,
            processing_status=ProcessingStatus.IN_PROGRESS,
            total_processing_time=0.0,
            started_at=started_at,
            completed_at=None
        )
        
        try:
            # Stage 1: AI Parsing
            if self.config.ai_parser_enabled:
                result.ai_parsing = await self._ai_parsing_stage(request)
                result.current_stage = ProcessingStage.RAG_NORMALIZATION
                
                if not result.ai_parsing.success:
                    return self._finalize_result(result, ProcessingStatus.FAILED, start_time)
            
            # Stage 2: RAG Normalization
            if self.config.rag_normalization_enabled:
                result.rag_normalization = await self._rag_normalization_stage(
                    request, result.ai_parsing
                )
                result.current_stage = ProcessingStage.SKU_SEARCH
                
                if not result.rag_normalization.success:
                    return self._finalize_result(result, ProcessingStatus.PARTIAL_SUCCESS, start_time)
            
            # Stage 3: SKU Search (placeholder for now)
            if self.config.sku_search_enabled:
                result.sku_search = await self._sku_search_stage(
                    request, result.ai_parsing, result.rag_normalization
                )
                result.current_stage = ProcessingStage.DATABASE_SAVE
                
                # Set SKU from search result
                result.sku = result.sku_search.sku
            
            # Stage 4: Database Save (placeholder for now)
            if self.config.database_save_enabled:
                result.database_save = await self._database_save_stage(
                    request, result
                )
                result.current_stage = ProcessingStage.COMPLETED
            
            # Finalize result
            return self._finalize_result(result, ProcessingStatus.SUCCESS, start_time)
            
        except Exception as e:
            self.logger.error(f"Error processing material {request.id}: {e}")
            result.ai_parsing.error_message = str(e)
            return self._finalize_result(result, ProcessingStatus.FAILED, start_time)
    
    async def _ai_parsing_stage(self, request: MaterialProcessRequest) -> AIParsingResult:
        """
        Stage 1: AI Parsing - Extract color, unit_coefficient, parsed_unit + generate embeddings
        
        Args:
            request: Material processing request
            
        Returns:
            AI parsing result
        """
        stage_start = time.time()
        
        try:
            self.logger.debug(f"AI Parsing stage for: {request.name}")
            
            # Create enhanced parse request
            parse_request = EnhancedParseRequest(
                name=request.name,
                unit=request.unit,
                price=request.price,
                parsing_method=ParsingMethod.AI_GPT
            )
            
            # Use parser integration service
            parse_result = await self.parser_service.parse_single_material(parse_request)
            
            # Convert result to AI parsing result
            ai_result = AIParsingResult(
                success=parse_result.success,
                color=getattr(parse_result, 'color', None),
                unit_coefficient=getattr(parse_result, 'price_coefficient', None),
                parsed_unit=getattr(parse_result, 'unit_parsed', None),
                material_embedding=getattr(parse_result, 'embeddings', None),
                color_embedding=getattr(parse_result, 'color_embedding', None),
                unit_embedding=getattr(parse_result, 'unit_embedding', None),
                processing_time=getattr(parse_result, 'processing_time', time.time() - stage_start),
                confidence_score=getattr(parse_result, 'confidence', None),
                error_message=getattr(parse_result, 'error_message', None)
            )
            
            self.logger.info(
                f"AI Parsing completed for {request.name}: "
                f"success={ai_result.success}, color={ai_result.color}, "
                f"unit={ai_result.parsed_unit}, time={ai_result.processing_time:.2f}s"
            )
            
            return ai_result
            
        except Exception as e:
            self.logger.error(f"AI Parsing stage failed for {request.name}: {e}")
            return AIParsingResult(
                success=False,
                processing_time=time.time() - stage_start,
                error_message=str(e)
            )
    
    async def _rag_normalization_stage(
        self, 
        request: MaterialProcessRequest,
        ai_result: AIParsingResult
    ) -> RAGNormalizationResult:
        """
        Stage 2: RAG Normalization - Normalize color and unit using embedding comparison
        
        Args:
            request: Material processing request
            ai_result: AI parsing result
            
        Returns:
            RAG normalization result
        """
        stage_start = time.time()
        
        try:
            self.logger.debug(f"RAG Normalization stage for: {request.name}")
            
            # Normalize color if extracted using embedding comparison
            color_normalization = None
            if ai_result.color and request.enable_color_extraction:
                color_normalization = await self._normalize_color(ai_result.color, ai_result.color_embedding)
            
            # Normalize unit using embedding comparison
            unit_normalization = None
            if ai_result.parsed_unit and request.enable_unit_normalization:
                unit_normalization = await self._normalize_unit(ai_result.parsed_unit, ai_result.unit_embedding)
            elif request.enable_unit_normalization:
                # Fallback to original unit if AI didn't parse any unit
                unit_normalization = await self._normalize_unit(request.unit, None) # Pass None for embedding
            
            # Create normalization result
            rag_result = RAGNormalizationResult(
                success=True,
                processing_time=time.time() - stage_start
            )
            
            # Color normalization results with embedding data
            if color_normalization:
                rag_result.normalized_color = color_normalization.get("normalized_color")
                rag_result.color_similarity_score = color_normalization.get("similarity_score")
                rag_result.color_normalization_method = color_normalization.get("method")
                rag_result.color_suggestions = color_normalization.get("suggestions", [])
                
                # NEW: Embedding data for color
                rag_result.color_embedding = color_normalization.get("color_embedding")
                rag_result.color_embedding_similarity = color_normalization.get("color_embedding_similarity")
                
                if not color_normalization.get("success", False):
                    self.logger.warning(
                        f"Color normalization failed for {request.name}: "
                        f"'{ai_result.color}' -> suggestions: {rag_result.color_suggestions}"
                    )
            
            # Unit normalization results with embedding data
            if unit_normalization:
                rag_result.normalized_unit = unit_normalization.get("normalized_unit")
                rag_result.unit_similarity_score = unit_normalization.get("similarity_score")
                rag_result.unit_normalization_method = unit_normalization.get("method")
                rag_result.unit_suggestions = unit_normalization.get("suggestions", [])
                
                # NEW: Embedding data for unit
                rag_result.unit_embedding = unit_normalization.get("unit_embedding")
                rag_result.unit_embedding_similarity = unit_normalization.get("unit_embedding_similarity")
                
                if not unit_normalization.get("success", False):
                    self.logger.warning(
                        f"Unit normalization failed for {request.name}: "
                        f"'{ai_result.parsed_unit or request.unit}' -> suggestions: {rag_result.unit_suggestions}"
                    )
            
            # Validate normalized data through reference databases
            validation_results = self._validate_normalized_data(rag_result, request.name)
            
            # Update success status based on validation
            if not validation_results["overall_success"]:
                rag_result.success = False
                rag_result.error_message = validation_results["error_message"]
                self.logger.warning(
                    f"RAG normalization validation failed for {request.name}: "
                    f"{validation_results['error_message']}"
                )
            
            return rag_result
            
        except Exception as e:
            self.logger.error(f"Error in RAG normalization stage for {request.name}: {e}")
            return RAGNormalizationResult(
                success=False,
                processing_time=time.time() - stage_start,
                error_message=str(e)
            )
    
    def _validate_normalized_data(
        self,
        rag_result: RAGNormalizationResult,
        material_name: str
    ) -> Dict[str, Any]:
        """
        Validate normalized data through reference databases
        
        Args:
            rag_result: RAG normalization result
            material_name: Material name for logging
            
        Returns:
            Validation results
        """
        validation_results = {
            "color_valid": False,
            "unit_valid": False,
            "color_validation_method": None,
            "unit_validation_method": None,
            "validation_messages": [],
            "overall_success": True # Assume success until proven otherwise
        }
        
        # Validate normalized color through ColorCollection
        if rag_result.normalized_color:
            try:
                # Check if normalized color exists in reference database
                color_found = ColorCollection.find_color_by_name(rag_result.normalized_color)
                if color_found:
                    validation_results["color_valid"] = True
                    validation_results["color_validation_method"] = "reference_database"
                    validation_results["validation_messages"].append(
                        f"Color '{rag_result.normalized_color}' validated through reference database"
                    )
                else:
                    validation_results["validation_messages"].append(
                        f"Warning: Color '{rag_result.normalized_color}' not found in reference database"
                    )
                    validation_results["overall_success"] = False
                    validation_results["error_message"] = f"Color normalization failed: '{rag_result.normalized_color}' not found in reference database."
            except Exception as e:
                validation_results["validation_messages"].append(
                    f"Error validating color '{rag_result.normalized_color}': {str(e)}"
                )
                validation_results["overall_success"] = False
                validation_results["error_message"] = f"Error validating color '{rag_result.normalized_color}': {str(e)}"
        
        # Validate normalized unit through UnitsCollection
        if rag_result.normalized_unit:
            try:
                # Check if normalized unit exists in reference database
                unit_found = UnitsCollection.find_unit_by_name(rag_result.normalized_unit)
                if unit_found:
                    validation_results["unit_valid"] = True
                    validation_results["unit_validation_method"] = "reference_database"
                    validation_results["validation_messages"].append(
                        f"Unit '{rag_result.normalized_unit}' validated through reference database"
                    )
                else:
                    validation_results["validation_messages"].append(
                        f"Warning: Unit '{rag_result.normalized_unit}' not found in reference database"
                    )
                    validation_results["overall_success"] = False
                    validation_results["error_message"] = f"Unit normalization failed: '{rag_result.normalized_unit}' not found in reference database."
            except Exception as e:
                validation_results["validation_messages"].append(
                    f"Error validating unit '{rag_result.normalized_unit}': {str(e)}"
                )
                validation_results["overall_success"] = False
                validation_results["error_message"] = f"Error validating unit '{rag_result.normalized_unit}': {str(e)}"
        
        # Log validation results
        if validation_results["color_valid"] and validation_results["unit_valid"]:
            self.logger.info(f"Validation successful for {material_name}")
        else:
            self.logger.warning(
                f"Validation issues for {material_name}: "
                f"color_valid={validation_results['color_valid']}, "
                f"unit_valid={validation_results['unit_valid']}"
            )
        
        return validation_results
    
    async def _sku_search_stage(
        self,
        request: MaterialProcessRequest,
        ai_result: AIParsingResult,
        rag_result: RAGNormalizationResult
    ) -> SKUSearchResult:
        """
        Stage 3: SKU Search - Find SKU using combined material embedding
        
        Args:
            request: Material processing request
            ai_result: AI parsing result
            rag_result: RAG normalization result
            
        Returns:
            SKU search result
        """
        stage_start = time.time()
        
        try:
            self.logger.debug(f"SKU Search stage for: {request.name}")
            
            # Generate combined material embedding for SKU search
            from services.combined_embedding_service import get_combined_embedding_service
            
            embedding_service = get_combined_embedding_service()
            
            # Use normalized unit and color from RAG normalization
            normalized_unit = rag_result.normalized_unit or ai_result.parsed_unit or request.unit
            normalized_color = rag_result.normalized_color or ai_result.color
            
            # Generate combined embedding from name + parsed_unit + color
            material_embedding = await embedding_service.generate_material_embedding_for_sku(
                name=request.name,
                parsed_unit=normalized_unit,
                color=normalized_color
            )
            
            # Search SKU using combined embedding
            sku_response = await self.sku_search_service.find_sku_by_combined_embedding(
                material_embedding=material_embedding,
                normalized_unit=normalized_unit,
                normalized_color=normalized_color
            )
            
            # Convert response to SKU search result
            sku_result = SKUSearchResult(
                success=sku_response.search_successful,
                sku=sku_response.found_sku,
                similarity_score=sku_response.best_match.similarity_score if sku_response.best_match else None,
                combined_embedding=material_embedding,
                embedding_similarity=sku_response.best_match.similarity_score if sku_response.best_match else None,
                embedding_text=f"{request.name} {normalized_unit} {normalized_color or 'без_цвета'}",
                search_method=sku_response.search_method,
                candidates_found=sku_response.candidates_evaluated,
                processing_time=time.time() - stage_start,
                error_message=sku_response.error_message
            )
            
            if sku_result.success:
                self.logger.info(
                    f"✅ SKU found for {request.name}: {sku_result.sku} "
                    f"(similarity: {sku_result.similarity_score:.3f}, "
                    f"candidates: {sku_result.candidates_found})"
                )
            else:
                self.logger.warning(
                    f"❌ SKU not found for {request.name}: "
                    f"candidates evaluated: {sku_result.candidates_found}"
                )
            
            return sku_result
            
        except Exception as e:
            self.logger.error(f"Error in SKU search stage for {request.name}: {e}")
            return SKUSearchResult(
                success=False,
                processing_time=time.time() - stage_start,
                error_message=str(e)
            )
    
    async def _database_save_stage(
        self,
        request: MaterialProcessRequest,
        result: ProcessingResult
    ) -> DatabaseSaveResult:
        """
        Stage 4: Database Save - Save processed material to reference database
        
        Args:
            request: Material processing request
            result: Complete processing result
            
        Returns:
            Database save result
        """
        stage_start = time.time()
        
        try:
            self.logger.debug(f"Database Save stage for: {request.name}")
            
            # Import materials reference collection
            from core.database.collections.materials_reference import MaterialsReferenceCollection
            
            materials_ref = MaterialsReferenceCollection()
            
            # Get SKU from search result
            sku = result.sku
            if not sku:
                self.logger.warning(f"No SKU found for {request.name}, skipping database save")
                return DatabaseSaveResult(
                    success=False,
                    processing_time=time.time() - stage_start,
                    error_message="No SKU found for database save"
                )
            
            # Get normalized data from RAG normalization
            normalized_unit = result.rag_normalization.normalized_unit
            normalized_color = result.rag_normalization.normalized_color
            
            # Get combined embedding from SKU search
            material_embedding = result.sku_search.combined_embedding
            if not material_embedding:
                self.logger.warning(f"No combined embedding found for {request.name}")
                return DatabaseSaveResult(
                    success=False,
                    processing_time=time.time() - stage_start,
                    error_message="No combined embedding found for database save"
                )
            
            # Save material to reference database
            save_success = await materials_ref.save_material_reference(
                sku=sku,
                name=request.name,
                unit=normalized_unit or request.unit,
                color=normalized_color,
                embedding=material_embedding
            )
            
            if save_success:
                self.logger.info(
                    f"✅ Saved material to reference database: {sku} - {request.name}"
                )
                
                return DatabaseSaveResult(
                    success=True,
                    saved_id=sku,
                    processing_time=time.time() - stage_start
                )
            else:
                self.logger.error(f"❌ Failed to save material to reference database: {sku}")
                
                return DatabaseSaveResult(
                    success=False,
                    processing_time=time.time() - stage_start,
                    error_message="Failed to save material to reference database"
                )
                
        except Exception as e:
            self.logger.error(f"Error in database save stage for {request.name}: {e}")
            return DatabaseSaveResult(
                success=False,
                processing_time=time.time() - stage_start,
                error_message=str(e)
            )
    
    def _finalize_result(
        self,
        result: ProcessingResult,
        status: ProcessingStatus,
        start_time: float
    ) -> ProcessingResult:
        """
        Finalize processing result with overall status and timing
        
        Args:
            result: Processing result to finalize
            status: Final processing status
            start_time: Processing start time
            
        Returns:
            Finalized processing result
        """
        result.processing_status = status
        result.total_processing_time = time.time() - start_time
        result.completed_at = datetime.utcnow()
        
        # Determine overall success
        if status == ProcessingStatus.SUCCESS:
            result.overall_success = True
        elif status == ProcessingStatus.PARTIAL_SUCCESS:
            result.overall_success = result.ai_parsing.success and result.rag_normalization.success
        else:
            result.overall_success = False
        
        # Update statistics
        self._update_statistics(result)
        
        self.logger.info(
            f"Processing completed for {result.request_id}: "
            f"status={result.processing_status}, success={result.overall_success}, "
            f"time={result.total_processing_time:.2f}s"
        )
        
        return result
    
    def _update_statistics(self, result: ProcessingResult):
        """
        Update pipeline statistics based on processing result
        
        Args:
            result: Processing result
        """
        self.statistics.total_requests += 1
        
        if result.overall_success:
            self.statistics.successful_requests += 1
        else:
            self.statistics.failed_requests += 1
        
        # Update stage success rates
        if result.ai_parsing.success:
            # Simplified calculation - in real implementation would use proper averaging
            self.statistics.ai_parsing_success_rate = (
                self.statistics.ai_parsing_success_rate * 0.9 + 10.0
            ) if self.statistics.ai_parsing_success_rate > 0 else 100.0
        
        if result.rag_normalization.success:
            self.statistics.rag_normalization_success_rate = (
                self.statistics.rag_normalization_success_rate * 0.9 + 10.0
            ) if self.statistics.rag_normalization_success_rate > 0 else 100.0
        
        # Update processing times
        self.statistics.average_processing_time = (
            self.statistics.average_processing_time * 0.9 + result.total_processing_time * 0.1
        )
        
        self.statistics.average_ai_parsing_time = (
            self.statistics.average_ai_parsing_time * 0.9 + result.ai_parsing.processing_time * 0.1
        )
        
        self.statistics.average_rag_normalization_time = (
            self.statistics.average_rag_normalization_time * 0.9 + result.rag_normalization.processing_time * 0.1
        )
        
        self.statistics.statistics_updated_at = datetime.utcnow()
    
    async def process_batch_materials(
        self,
        request: BatchProcessingRequest
    ) -> BatchProcessingResponse:
        """
        Process multiple materials in batch
        
        Args:
            request: Batch processing request
            
        Returns:
            Batch processing response
        """
        start_time = time.time()
        started_at = datetime.utcnow()
        
        self.logger.info(f"Starting batch processing of {len(request.materials)} materials")
        
        # Process materials
        if request.parallel_processing and len(request.materials) > 1:
            results = await self._process_batch_parallel(
                request.materials,
                request.max_workers
            )
        else:
            results = await self._process_batch_sequential(request.materials)
        
        # Calculate statistics
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.overall_success)
        failed = len(results) - successful
        
        response = BatchProcessingResponse(
            results=results,
            total_processed=len(results),
            successful_processed=successful,
            failed_processed=failed,
            success_rate=(successful / len(results)) * 100 if results else 0,
            total_processing_time=total_time,
            average_processing_time=total_time / len(results) if results else 0,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )
        
        self.logger.info(
            f"Batch processing completed: {successful}/{len(results)} successful "
            f"({response.success_rate:.1f}%) in {total_time:.2f}s"
        )
        
        return response
    
    async def _process_batch_parallel(
        self,
        materials: List[MaterialProcessRequest],
        max_workers: int
    ) -> List[ProcessingResult]:
        """Process materials in parallel"""
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_with_semaphore(material):
            async with semaphore:
                return await self.process_material(material)
        
        # Execute all tasks concurrently
        tasks = [process_with_semaphore(material) for material in materials]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error processing material {materials[i].id}: {result}")
                
                # Create error result
                error_result = ProcessingResult(
                    request_id=materials[i].id,
                    material_name=materials[i].name,
                    original_unit=materials[i].unit,
                    sku=None,
                    ai_parsing=AIParsingResult(
                        success=False,
                        processing_time=0.0,
                        error_message=str(result)
                    ),
                    rag_normalization=RAGNormalizationResult(
                        success=False,
                        processing_time=0.0
                    ),
                    sku_search=SKUSearchResult(
                        success=False,
                        processing_time=0.0
                    ),
                    database_save=DatabaseSaveResult(
                        success=False,
                        processing_time=0.0
                    ),
                    overall_success=False,
                    current_stage=ProcessingStage.AI_PARSING,
                    processing_status=ProcessingStatus.FAILED,
                    total_processing_time=0.0,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_batch_sequential(
        self,
        materials: List[MaterialProcessRequest]
    ) -> List[ProcessingResult]:
        """Process materials sequentially"""
        
        results = []
        for material in materials:
            result = await self.process_material(material)
            results.append(result)
            
            # Small delay to avoid overwhelming external services
            await asyncio.sleep(0.1)
        
        return results
    
    def get_statistics(self) -> PipelineStatistics:
        """
        Get current pipeline statistics
        
        Returns:
            Pipeline statistics
        """
        return self.statistics
    
    def get_configuration(self) -> PipelineConfiguration:
        """
        Get current pipeline configuration
        
        Returns:
            Pipeline configuration
        """
        return self.config
    
    def update_configuration(self, new_config: PipelineConfiguration):
        """
        Update pipeline configuration
        
        Args:
            new_config: New pipeline configuration
        """
        self.config = new_config
        self.logger.info("Pipeline configuration updated")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of all pipeline components
        
        Returns:
            Health check results
        """
        health_status = {
            "pipeline": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Check parser service
            parser_health = await self.parser_service.test_connection()
            health_status["components"]["parser"] = "healthy" if parser_health else "unhealthy"
            
            # Check RAG service
            health_status["components"]["rag_service"] = "healthy"  # Simple check for now
            
            # Check vector database
            health_status["components"]["vector_db"] = "healthy"  # Simple check for now
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status["pipeline"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status 

    async def _normalize_color(self, color_text: str, embedding: list) -> list:
        """Normalize color using embedding comparison service (через fallback-менеджер)."""
        comparison_service = EmbeddingComparisonService()
        return await comparison_service.normalize_color_by_embedding(color_text, embedding)

    async def _suggest_color(self, color_text: str) -> list:
        """Suggest color using embedding comparison service (через fallback-менеджер)."""
        comparison_service = EmbeddingComparisonService()
        return await comparison_service.suggest_color(color_text)

    async def _normalize_unit(self, unit_text: str, embedding: list) -> list:
        """Normalize unit using embedding comparison service (через fallback-менеджер)."""
        comparison_service = EmbeddingComparisonService()
        return await comparison_service.normalize_unit_by_embedding(unit_text, embedding)

    async def _suggest_unit(self, unit_text: str) -> list:
        """Suggest unit using embedding comparison service (через fallback-менеджер)."""
        comparison_service = EmbeddingComparisonService()
        return await comparison_service.suggest_unit(unit_text) 