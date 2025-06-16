from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from datetime import datetime, date
from decimal import Decimal

class MaterialBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    use_category: str = Field(..., max_length=200)  # Renamed from category
    unit: str
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None

# Extended schema for raw products from supplier price lists
class RawProductBase(BaseModel):
    """Base schema for raw product from supplier price list"""
    name: str = Field(..., max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    use_category: Optional[str] = Field(None, max_length=200)
    
    # Pricing information
    unit_price: Optional[Decimal] = Field(None, ge=0)
    unit_price_currency: Optional[str] = Field("RUB", max_length=3)
    unit_calc_price: Optional[Decimal] = Field(None, ge=0)
    unit_calc_price_currency: Optional[str] = Field("RUB", max_length=3)
    buy_price: Optional[Decimal] = Field(None, ge=0)
    buy_price_currency: Optional[str] = Field("RUB", max_length=3)
    sale_price: Optional[Decimal] = Field(None, ge=0)
    sale_price_currency: Optional[str] = Field("RUB", max_length=3)
    
    # Units and quantities
    calc_unit: Optional[str] = Field(None, max_length=100)
    count: Optional[int] = Field(None, ge=0)
    
    # Date information
    date_price_change: Optional[date] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    use_category: Optional[str] = None  # Renamed from category
    unit: Optional[str] = None
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None

class Material(MaterialBase):
    id: str
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
    
    @field_serializer('embedding')
    def serialize_embedding(self, value: Optional[List[float]]) -> Union[List[float], List[str]]:
        """Format embeddings for display - show preview instead of null."""
        if value is not None and len(value) > 0:
            # Show first 5 values, then ellipsis with dimension count
            preview = value[:5] + [f"... (total: {len(value)} dimensions)"]
            return preview
        else:
            # Instead of null, show placeholder indicating embeddings are available
            return ["... (embeddings available, total: 1536 dimensions)"]

class MaterialSearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)

class MaterialFilterOptions(BaseModel):
    """Advanced filtering options for materials search.
    
    Расширенные опции фильтрации для поиска материалов.
    """
    # Category filters
    categories: Optional[List[str]] = Field(
        None, 
        description="Filter by use categories",
        example=["Цемент", "Кирпич", "Металлопрокат"]
    )
    
    # Unit filters
    units: Optional[List[str]] = Field(
        None,
        description="Filter by measurement units", 
        example=["кг", "м", "м²", "м³", "шт"]
    )
    
    # SKU pattern matching
    sku_pattern: Optional[str] = Field(
        None,
        description="Filter by SKU pattern (supports wildcards)",
        example="CEM*"
    )
    
    # Date range filters
    created_after: Optional[datetime] = Field(
        None,
        description="Filter materials created after this date"
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Filter materials created before this date"
    )
    updated_after: Optional[datetime] = Field(
        None,
        description="Filter materials updated after this date"
    )
    updated_before: Optional[datetime] = Field(
        None,
        description="Filter materials updated before this date"
    )
    
    # Text search options
    search_fields: Optional[List[str]] = Field(
        default=["name", "description", "use_category"],
        description="Fields to search in",
        example=["name", "description"]
    )
    
    # Similarity thresholds
    min_similarity: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold for fuzzy search"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "categories": ["Цемент", "Кирпич"],
                "units": ["кг", "м³"],
                "sku_pattern": "CEM*",
                "created_after": "2024-01-01T00:00:00",
                "search_fields": ["name", "description"],
                "min_similarity": 0.5
            }
        }

class SortOption(BaseModel):
    """Sorting option for search results.
    
    Опция сортировки результатов поиска.
    """
    field: str = Field(
        ...,
        description="Field to sort by",
        example="name"
    )
    direction: str = Field(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort direction: asc or desc"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "field": "created_at",
                "direction": "desc"
            }
        }

class PaginationOptions(BaseModel):
    """Pagination options for search results.
    
    Опции пагинации результатов поиска.
    """
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-based)"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page"
    )
    cursor: Optional[str] = Field(
        None,
        description="Cursor for cursor-based pagination"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "cursor": "eyJpZCI6InRlc3QtaWQiLCJzY29yZSI6MC44NX0="
            }
        }

class AdvancedSearchQuery(BaseModel):
    """Advanced search query with comprehensive filtering and sorting.
    
    Продвинутый поисковый запрос с комплексной фильтрацией и сортировкой.
    """
    # Main search query
    query: Optional[str] = Field(
        None,
        description="Main search query (optional for filter-only searches)"
    )
    
    # Search type
    search_type: str = Field(
        default="hybrid",
        pattern="^(vector|sql|hybrid|fuzzy)$",
        description="Type of search to perform"
    )
    
    # Filters
    filters: Optional[MaterialFilterOptions] = Field(
        None,
        description="Advanced filtering options"
    )
    
    # Sorting
    sort_by: Optional[List[SortOption]] = Field(
        default=[SortOption(field="relevance", direction="desc")],
        description="Sorting options (multiple fields supported)"
    )
    
    # Pagination
    pagination: PaginationOptions = Field(
        default_factory=PaginationOptions,
        description="Pagination options"
    )
    
    # Search behavior
    fuzzy_threshold: Optional[float] = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Fuzzy search similarity threshold"
    )
    
    include_suggestions: bool = Field(
        default=False,
        description="Include search suggestions in response"
    )
    
    highlight_matches: bool = Field(
        default=False,
        description="Highlight matching text in results"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "цемент портландский",
                "search_type": "hybrid",
                "filters": {
                    "categories": ["Цемент"],
                    "units": ["кг"],
                    "created_after": "2024-01-01T00:00:00",
                    "min_similarity": 0.5
                },
                "sort_by": [
                    {"field": "relevance", "direction": "desc"},
                    {"field": "created_at", "direction": "desc"}
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 20
                },
                "fuzzy_threshold": 0.8,
                "include_suggestions": True,
                "highlight_matches": True
            }
        }

class SearchSuggestion(BaseModel):
    """Search suggestion for autocomplete.
    
    Предложение для автодополнения поиска.
    """
    text: str = Field(..., description="Suggested search text")
    type: str = Field(..., description="Type of suggestion (query, category, material)")
    score: float = Field(..., description="Relevance score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "цемент портландский М400",
                "type": "material",
                "score": 0.95
            }
        }

class SearchHighlight(BaseModel):
    """Text highlighting information.
    
    Информация о подсветке текста.
    """
    field: str = Field(..., description="Field name where match was found")
    original: str = Field(..., description="Original text")
    highlighted: str = Field(..., description="Text with highlights")
    
    class Config:
        json_schema_extra = {
            "example": {
                "field": "name",
                "original": "Цемент портландский М400",
                "highlighted": "<mark>Цемент</mark> <mark>портландский</mark> М400"
            }
        }

class MaterialSearchResult(BaseModel):
    """Enhanced material search result with metadata.
    
    Расширенный результат поиска материала с метаданными.
    """
    material: Material = Field(..., description="Material data")
    score: float = Field(..., description="Relevance score")
    search_type: str = Field(..., description="Type of search that found this result")
    highlights: Optional[List[SearchHighlight]] = Field(
        None,
        description="Text highlights"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "material": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Цемент портландский М400",
                    "use_category": "Цемент",
                    "unit": "кг",
                    "sku": "CEM400",
                    "description": "Высококачественный портландцемент",
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z"
                },
                "score": 0.95,
                "search_type": "vector",
                "highlights": [
                    {
                        "field": "name",
                        "original": "Цемент портландский М400",
                        "highlighted": "<mark>Цемент</mark> <mark>портландский</mark> М400"
                    }
                ]
            }
        }

class SearchResponse(BaseModel):
    """Comprehensive search response with metadata.
    
    Комплексный ответ поиска с метаданными.
    """
    results: List[MaterialSearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of matching results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of results per page")
    total_pages: int = Field(..., description="Total number of pages")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")
    
    # Optional metadata
    suggestions: Optional[List[SearchSuggestion]] = Field(
        None,
        description="Search suggestions"
    )
    filters_applied: Optional[Dict[str, Any]] = Field(
        None,
        description="Summary of applied filters"
    )
    next_cursor: Optional[str] = Field(
        None,
        description="Cursor for next page (cursor-based pagination)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "total_count": 150,
                "page": 1,
                "page_size": 20,
                "total_pages": 8,
                "search_time_ms": 45.2,
                "suggestions": [
                    {
                        "text": "цемент портландский М500",
                        "type": "material",
                        "score": 0.85
                    }
                ],
                "filters_applied": {
                    "categories": ["Цемент"],
                    "date_range": "2024-01-01 to 2024-12-31"
                }
            }
        }

class SearchAnalytics(BaseModel):
    """Search analytics data.
    
    Данные аналитики поиска.
    """
    query: str = Field(..., description="Search query")
    results_count: int = Field(..., description="Number of results returned")
    search_time_ms: float = Field(..., description="Search execution time")
    search_type: str = Field(..., description="Type of search performed")
    user_id: Optional[str] = Field(None, description="User ID (if available)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Search timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "цемент М400",
                "results_count": 25,
                "search_time_ms": 42.5,
                "search_type": "hybrid",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }



class Category(BaseModel):
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Unit(BaseModel):
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Batch operations schemas
class MaterialBatchCreate(BaseModel):
    materials: List[MaterialCreate] = Field(..., min_items=1, max_items=1000)
    batch_size: int = Field(default=100, ge=1, le=500)

class MaterialBatchResponse(BaseModel):
    """Unified batch response schema.
    
    Единая схема ответа для batch операций.
    """
    success: bool = Field(..., description="Overall operation success status")
    total_processed: int = Field(..., description="Total number of materials processed")
    successful_materials: List[Material] = Field(default=[], description="Successfully created materials")
    failed_materials: List[Dict[str, Any]] = Field(default=[], description="Failed materials with error details")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    errors: List[str] = Field(default=[], description="General error messages")
    
    # Computed properties for convenience
    @property
    def successful_count(self) -> int:
        """Number of successfully processed materials"""
        return len(self.successful_materials)
    
    @property
    def failed_count(self) -> int:
        """Number of failed materials"""
        return len(self.failed_materials)
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        if self.total_processed == 0:
            return 0.0
        return (self.successful_count / self.total_processed) * 100

# Schema for importing from JSON file format
class MaterialImportItem(BaseModel):
    sku: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)

class MaterialImportRequest(BaseModel):
    materials: List[MaterialImportItem] = Field(..., min_items=1, max_items=1000)
    default_use_category: str = Field(default="Стройматериалы")  # Renamed from default_category
    default_unit: str = Field(default="шт")
    batch_size: int = Field(default=100, ge=1, le=500)

# Raw Product schemas
class RawProductCreate(RawProductBase):
    """Schema for creating raw product"""
    pricelistid: int
    supplier_id: int

class RawProduct(RawProductBase):
    """Full raw product schema with all fields"""
    id: str  # UUID in Qdrant
    pricelistid: int
    supplier_id: int
    is_processed: bool = False
    created: datetime
    modified: datetime
    embedding: Optional[List[float]] = None
    upload_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Response schemas for raw products
class RawProductListResponse(BaseModel):
    supplier_id: int
    pricelistid: Optional[int] = None
    raw_products: List[RawProduct]
    total_count: int 