"""Services module for RAG Construction Materials API.

Модуль сервисов для RAG Construction Materials API.
"""

from .embedding_comparison import EmbeddingComparisonService
from .collection_initializer import CollectionInitializerService
from .enhanced_parser_integration import EnhancedParserIntegrationService
from .material_processing_pipeline import MaterialProcessingPipeline

# Combined embedding service (STAGE 5)
from .combined_embedding_service import CombinedEmbeddingService, get_combined_embedding_service

# SKU search service (STAGE 6)  
from .sku_search_service import SKUSearchService, get_sku_search_service

# Batch processing service
from .batch_processing_service import BatchProcessingService, get_batch_processing_service

__all__ = [
    "MaterialsService",
    "get_materials_service",
    "SSHTunnelService",
    "get_ssh_tunnel_service",
    "AdvancedSearchService",
    "get_advanced_search_service",
    "OptimizedSearchService",
    "get_optimized_search_service",
    "PriceProcessor",
    "get_price_processor",
    "MaterialProcessingPipeline",
    "get_material_processing_pipeline",
    "EnhancedParserIntegrationService",
    "get_enhanced_parser_integration_service",
    "EmbeddingComparisonService",
    "get_embedding_comparison_service",
    "CollectionInitializer",
    "get_collection_initializer",
    "DynamicBatchProcessor",
    "get_dynamic_batch_processor",
    "CombinedEmbeddingService",
    "get_combined_embedding_service",
    "SKUSearchService",
    "get_sku_search_service",
    "BatchProcessingService",
    "get_batch_processing_service"
] 