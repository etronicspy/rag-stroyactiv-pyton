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
    ParsingMethod,
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
    PipelineStatistics
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
    "ParsingMethod",
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
    "PipelineStatistics"
] 