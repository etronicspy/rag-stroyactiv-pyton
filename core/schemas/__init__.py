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
    "ColorListResponse"
] 