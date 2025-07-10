"""Pydantic schemas for RAG Construction Materials API.

Pydantic схемы для RAG Construction Materials API.
"""

# Material schemas
from .materials import (
    MaterialBase,
    MaterialCreate,
    MaterialUpdate,
    Material,
    MaterialSearchQuery,
    MaterialFilterOptions,
    SortOption,
    PaginationOptions,
    AdvancedSearchQuery,
    SearchSuggestion,
    SearchHighlight,
    MaterialSearchResult,
    SearchResponse,
    SearchAnalytics,
    Category,
    Unit,
    MaterialBatchCreate,
    MaterialBatchResponse,
    MaterialImportItem,
    MaterialImportRequest,
    RawProductCreate,
    RawProduct,
    RawProductListResponse
)

# Color schemas - NEW
from .colors import (
    ColorReference,
    ColorCreate,
    ColorUpdate,
    ColorNormalizationRequest,
    ColorNormalizationResponse,
    ColorSearchQuery,
    ColorSearchResult,
    ColorListResponse
)

# Enhanced parsing schemas - NEW (Updated for RAG Integration)
from .enhanced_parsing import (
    EnhancedParseRequest,
    EnhancedParseResult,
    BatchParseRequest,
    BatchParseResponse,
    ParserIntegrationConfig,
    ColorExtractionResult,
    EmbeddingGenerationResult
)

# Pipeline processing schemas - NEW (Stage 4)
from .pipeline_models import (
    ProcessingStage,
    ProcessingStatus,
    MaterialProcessRequest,
    AIParsingResult,
    RAGNormalizationResult,
    SKUSearchResult,
    DatabaseSaveResult,
    ProcessingResult,
    BatchProcessingRequest,
    BatchProcessingResponse,
    PipelineConfiguration,
    PipelineStatistics,
    # Combined Embedding models
    CombinedEmbeddingRequest,
    CombinedEmbeddingResult,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    EmbeddingCacheEntry,
    CombinedEmbeddingConfig
)

# Processing models for batch API
from .processing_models import (
    ProcessingStatus,
    MaterialInput,
    BatchMaterialsRequest,
    BatchProcessingResponse,
    BatchValidationError,
    ProcessingProgress,
    ProcessingStatusResponse,
    MaterialProcessingResult,
    ProcessingResultsResponse,
    ProcessingJobConfig,
    ProcessingStatistics,
    BatchResponse
)

__all__ = [
    # Material schemas
    "MaterialBase",
    "MaterialCreate", 
    "MaterialUpdate",
    "Material",
    "MaterialSearchQuery",
    "MaterialFilterOptions",
    "SortOption",
    "PaginationOptions",
    "AdvancedSearchQuery",
    "SearchSuggestion",
    "SearchHighlight", 
    "MaterialSearchResult",
    "SearchResponse",
    "SearchAnalytics",
    "Category",
    "Unit",
    "MaterialBatchCreate",
    "MaterialBatchResponse",
    "MaterialImportItem",
    "MaterialImportRequest",
    "RawProductCreate",
    "RawProduct",
    "RawProductListResponse",
    # Color schemas - NEW
    "ColorReference",
    "ColorCreate",
    "ColorUpdate", 
    "ColorNormalizationRequest",
    "ColorNormalizationResponse",
    "ColorSearchQuery",
    "ColorSearchResult",
    "ColorListResponse",
    # Enhanced parsing schemas - NEW (Updated for RAG Integration)
    "EnhancedParseRequest",
    "EnhancedParseResult",
    "BatchParseRequest", 
    "BatchParseResponse",
    "ParserIntegrationConfig",
    "ColorExtractionResult",
    "EmbeddingGenerationResult",
    # Pipeline processing schemas - NEW (Stage 4)
    "ProcessingStage",
    "ProcessingStatus",
    "MaterialProcessRequest",
    "AIParsingResult",
    "RAGNormalizationResult",
    "SKUSearchResult",
    "DatabaseSaveResult",
    "ProcessingResult",
    "BatchProcessingRequest",
    "BatchProcessingResponse",
    "PipelineConfiguration",
    "PipelineStatistics",
    # Combined Embedding models
    "CombinedEmbeddingRequest",
    "CombinedEmbeddingResult",
    "BatchEmbeddingRequest",
    "BatchEmbeddingResponse",
    "EmbeddingCacheEntry",
    "CombinedEmbeddingConfig",
    # SKU Search models (STAGE 6)
    "SKUSearchRequest",
    "SKUSearchResponse", 
    "SKUSearchCandidate",
    "SKUSearchConfig",
    # Processing models for batch API
    "ProcessingStatus",
    "MaterialInput",
    "BatchMaterialsRequest",
    "BatchProcessingResponse",
    "BatchValidationError",
    "ProcessingProgress",
    "ProcessingStatusResponse",
    "MaterialProcessingResult",
    "ProcessingResultsResponse",
    "ProcessingJobConfig",
    "ProcessingStatistics",
    "BatchResponse"
] 