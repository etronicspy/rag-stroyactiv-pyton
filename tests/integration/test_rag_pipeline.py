"""
Integration tests for complete RAG pipeline.

Тесты для полного RAG pipeline согласно схеме:
id, name, unit → AI_parser → RAG нормализация → Поиск SKU → Сохранение в БД → id, sku
"""

import pytest
import asyncio
from typing import Dict, Any
from core.schemas.pipeline_models import (
    MaterialProcessRequest,
    ProcessingResult,
    ProcessingStatus,
    ProcessingStage
)
from services.material_processing_pipeline import MaterialProcessingPipeline
from core.logging import get_logger

logger = get_logger(__name__)


class TestRAGPipeline:
    """Test complete RAG pipeline implementation."""
    
    @pytest.fixture
    async def pipeline(self):
        """Create material processing pipeline instance."""
        return MaterialProcessingPipeline()
    
    @pytest.mark.asyncio
    async def test_complete_rag_pipeline(self, pipeline):
        """
        Test complete RAG pipeline from input to output.
        
        Тест полного RAG pipeline от входа до выхода.
        """
        # Test material with color and unit
        request = MaterialProcessRequest(
            id="test_mat_001",
            name="Кирпич керамический белый",
            unit="м3",
            price=1500.0,
            enable_color_extraction=True,
            enable_unit_normalization=True,
            enable_sku_search=True,
            color_similarity_threshold=0.8,
            unit_similarity_threshold=0.8,
            sku_similarity_threshold=0.85
        )
        
        # Process material through complete pipeline
        result = await pipeline.process_material(request)
        
        # Verify pipeline stages
        assert result is not None
        assert result.request_id == "test_mat_001"
        assert result.material_name == "Кирпич керамический белый"
        assert result.original_unit == "м3"
        
        # Verify AI Parsing stage
        assert result.ai_parsing.success is True
        assert result.ai_parsing.color is not None  # Should extract "белый"
        assert result.ai_parsing.parsed_unit is not None  # Should parse "м3"
        assert result.ai_parsing.processing_time > 0
        
        # Verify RAG Normalization stage
        assert result.rag_normalization.success is True
        assert result.rag_normalization.normalized_color is not None
        assert result.rag_normalization.normalized_unit is not None
        assert result.rag_normalization.processing_time > 0
        
        # Verify embedding-based normalization
        assert result.rag_normalization.color_embedding is not None
        assert result.rag_normalization.unit_embedding is not None
        assert result.rag_normalization.color_embedding_similarity is not None
        assert result.rag_normalization.unit_embedding_similarity is not None
        
        # Verify SKU Search stage
        assert result.sku_search.success is True
        assert result.sku_search.processing_time > 0
        
        # Verify combined embedding for SKU search
        assert result.sku_search.combined_embedding is not None
        assert result.sku_search.embedding_similarity is not None
        assert result.sku_search.embedding_text is not None
        
        # Verify Database Save stage
        assert result.database_save.success is True
        assert result.database_save.saved_id is not None
        assert result.database_save.processing_time > 0
        
        # Verify final output
        assert result.sku is not None
        assert result.overall_success is True
        assert result.processing_status == ProcessingStatus.SUCCESS
        assert result.current_stage == ProcessingStage.COMPLETED
        assert result.total_processing_time > 0
        
        logger.info(f"✅ Complete RAG pipeline test passed: SKU={result.sku}")
    
    @pytest.mark.asyncio
    async def test_embedding_comparison(self, pipeline):
        """
        Test embedding comparison for normalization.
        
        Тест embedding comparison для нормализации.
        """
        # Test color normalization with embedding
        request = MaterialProcessRequest(
            id="test_color_001",
            name="Цемент портландский серый",
            unit="кг",
            enable_color_extraction=True,
            enable_unit_normalization=True,
            enable_sku_search=False  # Skip SKU search for this test
        )
        
        result = await pipeline.process_material(request)
        
        # Verify color normalization with embedding
        assert result.rag_normalization.success is True
        assert result.rag_normalization.color_embedding is not None
        assert result.rag_normalization.color_embedding_similarity is not None
        assert result.rag_normalization.color_normalization_method == "embedding_comparison"
        
        # Verify unit normalization with embedding
        assert result.rag_normalization.unit_embedding is not None
        assert result.rag_normalization.unit_embedding_similarity is not None
        assert result.rag_normalization.unit_normalization_method == "embedding_comparison"
        
        logger.info(f"✅ Embedding comparison test passed")
    
    @pytest.mark.asyncio
    async def test_sku_assignment(self, pipeline):
        """
        Test SKU assignment through combined embedding.
        
        Тест присвоения SKU через combined embedding.
        """
        # Test material that should find a SKU
        request = MaterialProcessRequest(
            id="test_sku_001",
            name="Кирпич керамический красный",
            unit="шт",
            enable_color_extraction=True,
            enable_unit_normalization=True,
            enable_sku_search=True,
            sku_similarity_threshold=0.7  # Lower threshold for testing
        )
        
        result = await pipeline.process_material(request)
        
        # Verify SKU search with combined embedding
        assert result.sku_search.success is True
        assert result.sku_search.combined_embedding is not None
        assert result.sku_search.embedding_similarity is not None
        assert result.sku_search.embedding_text is not None
        assert result.sku_search.search_method == "combined_embedding_search"
        
        # Verify SKU assignment
        if result.sku:
            logger.info(f"✅ SKU assignment test passed: SKU={result.sku}")
        else:
            logger.info(f"⚠️ SKU assignment test: No SKU found (this may be normal for test data)")
    
    @pytest.mark.asyncio
    async def test_database_save(self, pipeline):
        """
        Test saving to materials reference database.
        
        Тест сохранения в справочник материалов.
        """
        # Test material with SKU for database save
        request = MaterialProcessRequest(
            id="test_save_001",
            name="Бетон М300",
            unit="м3",
            enable_color_extraction=True,
            enable_unit_normalization=True,
            enable_sku_search=True,
            sku_similarity_threshold=0.7
        )
        
        result = await pipeline.process_material(request)
        
        # Verify database save
        assert result.database_save.success is True
        assert result.database_save.saved_id is not None
        assert result.database_save.processing_time > 0
        
        logger.info(f"✅ Database save test passed: saved_id={result.database_save.saved_id}")
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, pipeline):
        """
        Test pipeline error handling.
        
        Тест обработки ошибок в pipeline.
        """
        # Test with invalid material (should handle gracefully)
        request = MaterialProcessRequest(
            id="test_error_001",
            name="",  # Empty name should cause issues
            unit="invalid_unit",
            enable_color_extraction=True,
            enable_unit_normalization=True,
            enable_sku_search=True
        )
        
        result = await pipeline.process_material(request)
        
        # Verify error handling
        assert result is not None
        assert result.processing_status in [ProcessingStatus.FAILED, ProcessingStatus.PARTIAL_SUCCESS]
        
        logger.info(f"✅ Error handling test passed: status={result.processing_status}")
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, pipeline):
        """
        Test batch processing of multiple materials.
        
        Тест пакетной обработки нескольких материалов.
        """
        from core.schemas.pipeline_models import BatchProcessingRequest
        
        # Create batch request
        materials = [
            MaterialProcessRequest(
                id=f"batch_test_{i}",
                name=f"Материал {i}",
                unit="кг",
                enable_color_extraction=True,
                enable_unit_normalization=True,
                enable_sku_search=True
            )
            for i in range(3)
        ]
        
        batch_request = BatchProcessingRequest(
            materials=materials,
            parallel_processing=True,
            max_workers=2,
            continue_on_error=True
        )
        
        # Process batch
        batch_result = await pipeline.process_batch_materials(batch_request)
        
        # Verify batch processing
        assert batch_result is not None
        assert len(batch_result.results) == 3
        assert batch_result.total_processed == 3
        assert batch_result.total_processing_time > 0
        
        # Check individual results
        for result in batch_result.results:
            assert result is not None
            assert result.request_id.startswith("batch_test_")
        
        logger.info(f"✅ Batch processing test passed: {batch_result.successful_processed}/{batch_result.total_processed} successful")
    
    @pytest.mark.asyncio
    async def test_pipeline_configuration(self, pipeline):
        """
        Test pipeline configuration and statistics.
        
        Тест конфигурации pipeline и статистики.
        """
        # Get pipeline configuration
        config = pipeline.get_configuration()
        assert config is not None
        assert config.ai_parser_enabled is True
        assert config.rag_normalization_enabled is True
        assert config.sku_search_enabled is True
        assert config.database_save_enabled is True
        
        # Get pipeline statistics
        stats = pipeline.get_statistics()
        assert stats is not None
        assert stats.total_requests >= 0
        assert stats.statistics_updated_at is not None
        
        logger.info(f"✅ Pipeline configuration test passed")
    
    @pytest.mark.asyncio
    async def test_pipeline_health_check(self, pipeline):
        """
        Test pipeline health check.
        
        Тест проверки здоровья pipeline.
        """
        # Perform health check
        health = await pipeline.health_check()
        
        # Verify health check response
        assert health is not None
        assert "status" in health
        assert "services" in health
        assert "database" in health
        
        logger.info(f"✅ Pipeline health check test passed: status={health.get('status')}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 


@pytest.mark.asyncio
async def test_full_rag_pipeline_normalization_and_reference_ids():
    pipeline = MaterialProcessingPipeline()
    # Пример материала: белый кирпич, м3
    request = MaterialProcessRequest(
        id="test_001",
        name="Кирпич керамический белый",
        unit="м3",
        price=15000.0,
        enable_color_extraction=True,
        enable_unit_normalization=True,
        enable_sku_search=True
    )
    result = await pipeline.process_material(request)
    # Проверяем успешность пайплайна
    assert result.overall_success, f"Pipeline failed: {result}"
    # Проверяем наличие новых полей
    assert result.normalized_color_id is not None, "normalized_color_id missing"
    assert result.normalized_color_name is not None, "normalized_color_name missing"
    assert result.normalized_unit_id is not None, "normalized_unit_id missing"
    assert result.normalized_unit_name is not None, "normalized_unit_name missing"
    # Проверяем, что значения совпадают с ожидаемыми из reference-коллекций
    assert result.normalized_color_name.lower() == "white"
    assert result.normalized_unit_name.lower() == "cubic meter"
    # Проверяем, что SKU найден
    assert result.sku is not None, "SKU not assigned"
    print("Pipeline result:", result) 