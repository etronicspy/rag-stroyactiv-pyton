"""
Pipeline Models for Material Processing

Модели пайплайна для обработки материалов согласно диаграмме интеграции.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class ProcessingStage(str, Enum):
    """Stages of material processing pipeline."""
    AI_PARSING = "ai_parsing"
    RAG_NORMALIZATION = "rag_normalization"
    COMBINED_EMBEDDING = "combined_embedding"
    SKU_SEARCH = "sku_search"
    DATABASE_SAVE = "database_save"
    COMPLETED = "completed"


class ProcessingStatus(str, Enum):
    """Status of processing operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


class MaterialProcessRequest(BaseModel):
    """Input request for material processing pipeline."""
    
    id: str = Field(..., description="Unique material identifier")
    name: str = Field(..., description="Material name")
    unit: str = Field(..., description="Original unit of measurement")
    price: Optional[float] = Field(None, description="Optional price for context")
    
    # Processing options
    enable_color_extraction: bool = Field(True, description="Enable color extraction")
    enable_unit_normalization: bool = Field(True, description="Enable unit normalization")
    enable_sku_search: bool = Field(True, description="Enable SKU search")
    
    # Similarity thresholds
    color_similarity_threshold: float = Field(0.8, ge=0.0, le=1.0)
    unit_similarity_threshold: float = Field(0.8, ge=0.0, le=1.0)
    sku_similarity_threshold: float = Field(0.85, ge=0.0, le=1.0)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "mat_001",
                "name": "Кирпич керамический белый",
                "unit": "м3",
                "price": 15000.0,
                "enable_color_extraction": True,
                "enable_unit_normalization": True,
                "enable_sku_search": True,
                "color_similarity_threshold": 0.8,
                "unit_similarity_threshold": 0.8,
                "sku_similarity_threshold": 0.85
            }
        }


class AIParsingResult(BaseModel):
    """Result of AI parsing stage."""
    
    success: bool = Field(..., description="Whether AI parsing was successful")
    color: Optional[str] = Field(None, description="Extracted color")
    unit_coefficient: Optional[float] = Field(None, description="Unit conversion coefficient")
    parsed_unit: Optional[str] = Field(None, description="Parsed unit from AI")
    
    # Embeddings
    material_embedding: Optional[List[float]] = Field(None, description="Material embedding (1536dim)")
    color_embedding: Optional[List[float]] = Field(None, description="Color embedding (1536dim)")
    unit_embedding: Optional[List[float]] = Field(None, description="Unit embedding (1536dim)")
    
    # Processing metadata
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence_score: Optional[float] = Field(None, description="AI confidence score")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "color": "белый",
                "unit_coefficient": 0.00195,
                "parsed_unit": "м3",
                "material_embedding": [0.1, 0.2, 0.3],  # Truncated for example
                "color_embedding": [0.4, 0.5, 0.6],    # Truncated for example
                "unit_embedding": [0.7, 0.8, 0.9],     # Truncated for example
                "processing_time": 2.5,
                "confidence_score": 0.92,
                "error_message": None
            }
        }


class RAGNormalizationResult(BaseModel):
    """Result of RAG normalization stage.

    Attributes:
        success: Whether normalization was successful.
        normalized_color: Normalized color name (human-readable).
        normalized_color_id: ID of the normalized color from reference database.
        normalized_color_name: Canonical color name from reference database (EN).
        color_similarity_score: Color similarity score.
        color_normalization_method: Color normalization method.
        normalized_unit: Normalized unit name (human-readable).
        normalized_unit_id: ID of the normalized unit from reference database.
        normalized_unit_name: Canonical unit name from reference database (EN).
        unit_similarity_score: Unit similarity score.
        unit_normalization_method: Unit normalization method.
        color_embedding: Color embedding for normalization.
        unit_embedding: Unit embedding for normalization.
        color_embedding_similarity: Color embedding similarity score.
        unit_embedding_similarity: Unit embedding similarity score.
        color_suggestions: Color alternatives.
        unit_suggestions: Unit alternatives.
        processing_time: Processing time in seconds.
        error_message: Error message if failed.
    """
    success: bool = Field(..., description="Whether normalization was successful")
    # Color normalization
    normalized_color: Optional[str] = Field(None, description="Normalized color (human-readable)")
    normalized_color_id: Optional[str] = Field(None, description="ID of the normalized color from reference database")
    normalized_color_name: Optional[str] = Field(None, description="Canonical color name from reference database (EN)")
    color_similarity_score: Optional[float] = Field(None, description="Color similarity score")
    color_normalization_method: Optional[str] = Field(None, description="Color normalization method")
    # Unit normalization
    normalized_unit: Optional[str] = Field(None, description="Normalized unit (human-readable)")
    normalized_unit_id: Optional[str] = Field(None, description="ID of the normalized unit from reference database")
    normalized_unit_name: Optional[str] = Field(None, description="Canonical unit name from reference database (EN)")
    unit_similarity_score: Optional[float] = Field(None, description="Unit similarity score")
    unit_normalization_method: Optional[str] = Field(None, description="Unit normalization method")
    # Embedding-based normalization fields
    color_embedding: Optional[List[float]] = Field(None, description="Color embedding for normalization")
    unit_embedding: Optional[List[float]] = Field(None, description="Unit embedding for normalization")
    color_embedding_similarity: Optional[float] = Field(None, description="Color embedding similarity score")
    unit_embedding_similarity: Optional[float] = Field(None, description="Unit embedding similarity score")
    # Suggestions
    color_suggestions: List[str] = Field(default_factory=list, description="Color alternatives")
    unit_suggestions: List[str] = Field(default_factory=list, description="Unit alternatives")
    # Processing metadata
    processing_time: float = Field(..., description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "normalized_color": "белый",
                "normalized_color_id": "color_01",
                "normalized_color_name": "white",
                "color_similarity_score": 1.0,
                "color_normalization_method": "embedding_comparison",
                "normalized_unit": "м³",
                "normalized_unit_id": "unit_01",
                "normalized_unit_name": "cubic meter",
                "unit_similarity_score": 0.95,
                "unit_normalization_method": "embedding_comparison",
                "color_embedding": [0.1, 0.2, 0.3, ...],
                "unit_embedding": [0.4, 0.5, 0.6, ...],
                "color_embedding_similarity": 0.92,
                "unit_embedding_similarity": 0.89,
                "color_suggestions": ["белый", "светлый"],
                "unit_suggestions": ["м³", "кубометр"],
                "processing_time": 0.8,
                "error_message": None
            }
        }


class SKUSearchResult(BaseModel):
    """Result of SKU search stage."""
    
    success: bool = Field(..., description="Whether SKU search was successful")
    sku: Optional[str] = Field(None, description="Found SKU")
    similarity_score: Optional[float] = Field(None, description="SKU similarity score")
    
    # NEW: Combined embedding fields
    combined_embedding: Optional[List[float]] = Field(None, description="Combined material embedding (name + unit + color)")
    embedding_similarity: Optional[float] = Field(None, description="Combined embedding similarity score")
    embedding_text: Optional[str] = Field(None, description="Text used for combined embedding generation")
    
    # Search metadata
    search_method: Optional[str] = Field(None, description="Search method used")
    candidates_found: int = Field(0, description="Number of candidates found")
    processing_time: float = Field(..., description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "sku": "SKU_12345",
                "similarity_score": 0.92,
                "combined_embedding": [0.1, 0.2, 0.3, ...],
                "embedding_similarity": 0.89,
                "embedding_text": "Кирпич керамический белый м³ белый",
                "search_method": "combined_embedding_search",
                "candidates_found": 3,
                "processing_time": 1.2,
                "error_message": None
            }
        }


class DatabaseSaveResult(BaseModel):
    """Result of database save stage."""
    
    success: bool = Field(..., description="Whether save was successful")
    saved_id: Optional[str] = Field(None, description="Saved record ID")
    
    # Save metadata
    processing_time: float = Field(..., description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "saved_id": "db_record_789",
                "processing_time": 0.3,
                "error_message": None
            }
        }


class ProcessingResult(BaseModel):
    """Complete processing result from pipeline.

    Attributes:
        request_id: Original request ID.
        material_name: Original material name.
        original_unit: Original unit.
        sku: Found or assigned SKU.
        normalized_color_id: ID of the normalized color from reference database.
        normalized_color_name: Canonical color name from reference database (EN).
        normalized_unit_id: ID of the normalized unit from reference database.
        normalized_unit_name: Canonical unit name from reference database (EN).
        ai_parsing: AI parsing results.
        rag_normalization: RAG normalization results.
        sku_search: SKU search results.
        database_save: Database save results.
        overall_success: Overall processing success.
        current_stage: Current processing stage.
        processing_status: Processing status.
        total_processing_time: Total processing time.
        started_at: Processing start time.
        completed_at: Processing completion time.
    """
    # Input data
    request_id: str = Field(..., description="Original request ID")
    material_name: str = Field(..., description="Original material name")
    original_unit: str = Field(..., description="Original unit")
    # Output data (as per diagram)
    sku: Optional[str] = Field(None, description="Found or assigned SKU")
    # Normalized color/unit info (flattened for convenience)
    normalized_color_id: Optional[str] = Field(None, description="ID of the normalized color from reference database")
    normalized_color_name: Optional[str] = Field(None, description="Canonical color name from reference database (EN)")
    normalized_unit_id: Optional[str] = Field(None, description="ID of the normalized unit from reference database")
    normalized_unit_name: Optional[str] = Field(None, description="Canonical unit name from reference database (EN)")
    # Processing stages results
    ai_parsing: AIParsingResult = Field(..., description="AI parsing results")
    rag_normalization: RAGNormalizationResult = Field(..., description="RAG normalization results")
    sku_search: SKUSearchResult = Field(..., description="SKU search results")
    database_save: DatabaseSaveResult = Field(..., description="Database save results")
    # Overall processing metadata
    overall_success: bool = Field(..., description="Overall processing success")
    current_stage: ProcessingStage = Field(..., description="Current processing stage")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    total_processing_time: float = Field(..., description="Total processing time")
    # Timestamps
    started_at: datetime = Field(..., description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    class Config:
        schema_extra = {
            "example": {
                "request_id": "mat_001",
                "material_name": "Кирпич керамический белый",
                "original_unit": "м3",
                "sku": "SKU_12345",
                "normalized_color_id": "color_01",
                "normalized_color_name": "white",
                "normalized_unit_id": "unit_01",
                "normalized_unit_name": "cubic meter",
                "ai_parsing": {
                    "success": True,
                    "color": "белый",
                    "unit_coefficient": 0.00195,
                    "parsed_unit": "м3",
                    "processing_time": 2.5
                },
                "rag_normalization": {
                    "success": True,
                    "normalized_color": "белый",
                    "normalized_color_id": "color_01",
                    "normalized_color_name": "white",
                    "normalized_unit": "м³",
                    "normalized_unit_id": "unit_01",
                    "normalized_unit_name": "cubic meter",
                    "processing_time": 0.8
                },
                "sku_search": {
                    "success": True,
                    "sku": "SKU_12345",
                    "similarity_score": 0.92,
                    "processing_time": 1.2
                },
                "database_save": {
                    "success": True,
                    "saved_id": "db_record_789",
                    "processing_time": 0.3
                },
                "overall_success": True,
                "current_stage": "completed",
                "processing_status": "success",
                "total_processing_time": 4.8,
                "started_at": "2025-01-25T10:00:00Z",
                "completed_at": "2025-01-25T10:00:05Z"
            }
        }


class BatchProcessingRequest(BaseModel):
    """Batch processing request for multiple materials."""
    
    materials: List[MaterialProcessRequest] = Field(..., description="List of materials to process")
    
    # Batch processing options
    parallel_processing: bool = Field(True, description="Enable parallel processing")
    max_workers: int = Field(5, ge=1, le=20, description="Maximum parallel workers")
    continue_on_error: bool = Field(True, description="Continue processing on individual errors")
    
    class Config:
        schema_extra = {
            "example": {
                "materials": [
                    {
                        "id": "mat_001",
                        "name": "Кирпич керамический белый",
                        "unit": "м3"
                    },
                    {
                        "id": "mat_002", 
                        "name": "Цемент портландский серый",
                        "unit": "кг"
                    }
                ],
                "parallel_processing": True,
                "max_workers": 5,
                "continue_on_error": True
            }
        }


class BatchProcessingResponse(BaseModel):
    """Batch processing response."""
    
    # Results
    results: List[ProcessingResult] = Field(..., description="Individual processing results")
    
    # Batch statistics
    total_processed: int = Field(..., description="Total materials processed")
    successful_processed: int = Field(..., description="Successfully processed materials")
    failed_processed: int = Field(..., description="Failed processing materials")
    success_rate: float = Field(..., description="Success rate percentage")
    
    # Processing metadata
    total_processing_time: float = Field(..., description="Total batch processing time")
    average_processing_time: float = Field(..., description="Average processing time per material")
    
    # Timestamps
    started_at: datetime = Field(..., description="Batch processing start time")
    completed_at: datetime = Field(..., description="Batch processing completion time")
    
    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "request_id": "mat_001",
                        "material_name": "Кирпич керамический белый",
                        "sku": "SKU_12345",
                        "overall_success": True,
                        "processing_status": "success"
                    }
                ],
                "total_processed": 2,
                "successful_processed": 2,
                "failed_processed": 0,
                "success_rate": 100.0,
                "total_processing_time": 8.5,
                "average_processing_time": 4.25,
                "started_at": "2025-01-25T10:00:00Z",
                "completed_at": "2025-01-25T10:00:09Z"
            }
        }


class PipelineConfiguration(BaseModel):
    """Configuration for material processing pipeline."""
    
    # AI Parser settings
    ai_parser_enabled: bool = Field(True, description="Enable AI parsing")
    ai_parser_timeout: int = Field(30, description="AI parser timeout in seconds")
    ai_parser_retries: int = Field(3, description="AI parser retry attempts")
    
    # RAG Normalization settings
    rag_normalization_enabled: bool = Field(True, description="Enable RAG normalization")
    vector_search_enabled: bool = Field(True, description="Enable vector search in RAG")
    
    # SKU Search settings
    sku_search_enabled: bool = Field(True, description="Enable SKU search")
    sku_search_timeout: int = Field(15, description="SKU search timeout in seconds")
    
    # Database settings
    database_save_enabled: bool = Field(True, description="Enable database save")
    database_timeout: int = Field(10, description="Database timeout in seconds")
    
    # Performance settings
    enable_caching: bool = Field(True, description="Enable result caching")
    cache_ttl: int = Field(3600, description="Cache TTL in seconds")
    
    # Logging settings
    detailed_logging: bool = Field(True, description="Enable detailed logging")
    log_performance_metrics: bool = Field(True, description="Log performance metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "ai_parser_enabled": True,
                "ai_parser_timeout": 30,
                "ai_parser_retries": 3,
                "rag_normalization_enabled": True,
                "vector_search_enabled": True,
                "sku_search_enabled": True,
                "sku_search_timeout": 15,
                "database_save_enabled": True,
                "database_timeout": 10,
                "enable_caching": True,
                "cache_ttl": 3600,
                "detailed_logging": True,
                "log_performance_metrics": True
            }
        }


class PipelineStatistics(BaseModel):
    """Pipeline processing statistics."""
    
    # Processing counts
    total_requests: int = Field(0, description="Total processing requests")
    successful_requests: int = Field(0, description="Successful processing requests")
    failed_requests: int = Field(0, description="Failed processing requests")
    
    # Stage success rates
    ai_parsing_success_rate: float = Field(0.0, description="AI parsing success rate")
    rag_normalization_success_rate: float = Field(0.0, description="RAG normalization success rate")
    sku_search_success_rate: float = Field(0.0, description="SKU search success rate")
    database_save_success_rate: float = Field(0.0, description="Database save success rate")
    
    # Performance metrics
    average_processing_time: float = Field(0.0, description="Average processing time")
    average_ai_parsing_time: float = Field(0.0, description="Average AI parsing time")
    average_rag_normalization_time: float = Field(0.0, description="Average RAG normalization time")
    average_sku_search_time: float = Field(0.0, description="Average SKU search time")
    average_database_save_time: float = Field(0.0, description="Average database save time")
    
    # Cache statistics
    cache_hit_rate: float = Field(0.0, description="Cache hit rate")
    cache_miss_rate: float = Field(0.0, description="Cache miss rate")
    
    # Timestamps
    statistics_updated_at: datetime = Field(..., description="Statistics last updated")
    
    class Config:
        schema_extra = {
            "example": {
                "total_requests": 1000,
                "successful_requests": 950,
                "failed_requests": 50,
                "ai_parsing_success_rate": 98.5,
                "rag_normalization_success_rate": 96.2,
                "sku_search_success_rate": 87.5,
                "database_save_success_rate": 99.8,
                "average_processing_time": 4.2,
                "average_ai_parsing_time": 2.1,
                "average_rag_normalization_time": 0.7,
                "average_sku_search_time": 1.1,
                "average_database_save_time": 0.3,
                "cache_hit_rate": 65.3,
                "cache_miss_rate": 34.7,
                "statistics_updated_at": "2025-01-25T10:00:00Z"
            }
        } 

@dataclass
class ProcessingStatistics:
    total_processed: int = 0
    successful_parsing: int = 0
    successful_normalization: int = 0
    successful_sku_search: int = 0
    processing_time: float = 0.0
    average_time_per_item: float = 0.0

# === COMBINED EMBEDDING MODELS ===

class CombinedEmbeddingRequest(BaseModel):
    """Request model for generating combined material embedding"""
    material_name: str = Field(..., description="Material name")
    normalized_unit: str = Field(..., description="Normalized unit of measurement")
    normalized_color: Optional[str] = Field(None, description="Normalized color (None for colorless materials)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "material_name": "Кирпич керамический",
                "normalized_unit": "м³",
                "normalized_color": "красный"
            }
        }

class CombinedEmbeddingResult(BaseModel):
    """Result of combined material embedding generation"""
    material_embedding: List[float] = Field(..., description="Combined material embedding (1536 dimensions)")
    embedding_text: str = Field(..., description="Text used for embedding generation")
    processing_time: float = Field(..., description="Time taken for embedding generation (seconds)")
    success: bool = Field(..., description="Whether embedding generation was successful")
    
    class Config:
        json_schema_extra = {
            "example": {
                "material_embedding": [0.123, -0.456, 0.789],  # Shortened for example
                "embedding_text": "Кирпич керамический м³ красный",
                "processing_time": 0.245,
                "success": True
            }
        }

class BatchEmbeddingRequest(BaseModel):
    """Request for batch generation of combined embeddings"""
    materials: List[CombinedEmbeddingRequest] = Field(..., description="List of materials for embedding generation")
    batch_size: int = Field(default=10, description="Number of materials to process in parallel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "materials": [
                    {"material_name": "Кирпич керамический", "normalized_unit": "м³", "normalized_color": "красный"},
                    {"material_name": "Цемент портландский", "normalized_unit": "кг", "normalized_color": None}
                ],
                "batch_size": 5
            }
        }

class BatchEmbeddingResponse(BaseModel):
    """Response for batch embedding generation"""
    results: List[CombinedEmbeddingResult] = Field(..., description="Results for each material")
    total_processed: int = Field(..., description="Total number of materials processed")
    successful_count: int = Field(..., description="Number of successful embeddings")
    failed_count: int = Field(..., description="Number of failed embeddings")
    total_processing_time: float = Field(..., description="Total processing time (seconds)")
    average_time_per_item: float = Field(..., description="Average time per material (seconds)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [],  # Would contain CombinedEmbeddingResult objects
                "total_processed": 2,
                "successful_count": 2,
                "failed_count": 0,
                "total_processing_time": 0.892,
                "average_time_per_item": 0.446
            }
        }

class EmbeddingCacheEntry(BaseModel):
    """Cache entry for combined embeddings"""
    embedding: List[float]
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime

class CombinedEmbeddingConfig(BaseModel):
    """Configuration for combined embedding generation"""
    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    max_cache_size: int = 1000
    batch_size: int = 10
    text_format: str = "{name} {normalized_unit} {normalized_color}"
    embedding_model: str = "text-embedding-3-small"

# === SKU SEARCH MODELS (STAGE 6) ===

class SKUSearchRequest(BaseModel):
    """Request model for SKU search in materials reference"""
    material_name: str = Field(..., description="Material name to search for")
    normalized_unit: str = Field(..., description="Normalized unit of measurement")
    normalized_color: Optional[str] = Field(None, description="Normalized color (None for any color)")
    material_embedding: Optional[List[float]] = Field(None, description="Pre-computed material embedding")
    
    # Search parameters
    similarity_threshold: float = Field(0.35, ge=0.0, le=1.0, description="Minimum similarity threshold")
    max_candidates: int = Field(20, ge=1, le=100, description="Maximum candidates to retrieve")
    
    class Config:
        json_schema_extra = {
            "example": {
                "material_name": "Цемент портландский белый",
                "normalized_unit": "кг",
                "normalized_color": "белый",
                "similarity_threshold": 0.75,
                "max_candidates": 10
            }
        }

class SKUSearchCandidate(BaseModel):
    """Candidate material from reference database (adapted to real DB structure)"""
    material_id: str = Field(..., description="Material ID in reference database")
    sku: Optional[str] = Field(..., description="SKU from reference database")
    name: str = Field(..., description="Material name from reference (field: 'name')")
    unit: str = Field(..., description="Unit from reference (field: 'unit')")
    description: Optional[str] = Field(None, description="Description from reference")
    
    # Search scores
    similarity_score: float = Field(..., description="Vector similarity score")
    unit_match: bool = Field(..., description="Exact unit match")
    color_match: bool = Field(..., description="Color compatibility match (always True - no color field)")
    overall_match: bool = Field(..., description="Overall match result")
    
    class Config:
        json_schema_extra = {
            "example": {
                "material_id": "uuid-string",
                "sku": "CEM001",
                "material_name": "Цемент портландский М400",
                "normalized_unit": "кг",
                "normalized_color": "белый",
                "similarity_score": 0.89,
                "unit_match": True,
                "color_match": True,
                "overall_match": True
            }
        }

class SKUSearchResponse(BaseModel):
    """Response from SKU search service"""
    found_sku: Optional[str] = Field(None, description="Found SKU or None")
    search_successful: bool = Field(..., description="Whether search completed successfully")
    candidates_evaluated: int = Field(..., description="Number of candidates evaluated")
    matching_candidates: int = Field(..., description="Number of matching candidates")
    best_match: Optional[SKUSearchCandidate] = Field(None, description="Best matching candidate")
    
    # Search details
    search_method: str = Field(..., description="Search method used")
    processing_time: float = Field(..., description="Processing time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if any")
    
    # All candidates for debugging
    all_candidates: List[SKUSearchCandidate] = Field(default_factory=list, description="All evaluated candidates")
    
    class Config:
        json_schema_extra = {
            "example": {
                "found_sku": "CEM001",
                "search_successful": True,
                "candidates_evaluated": 15,
                "matching_candidates": 3,
                "search_method": "two_phase_vector_filtering",
                "processing_time": 0.245,
                "best_match": {
                    "sku": "CEM001",
                    "material_name": "Цемент портландский М400",
                    "similarity_score": 0.89,
                    "overall_match": True
                }
            }
        }

class SKUSearchConfig(BaseModel):
    """Configuration for SKU search service"""
    similarity_threshold: float = Field(0.35, description="Default similarity threshold")
    max_candidates: int = Field(20, description="Maximum candidates per search")
    strict_unit_matching: bool = Field(True, description="Require exact unit match")
    flexible_color_matching: bool = Field(True, description="Allow None color to match any color")
    reference_collection: str = Field("materials", description="Reference materials collection name")
    cache_enabled: bool = Field(True, description="Enable search result caching")
    cache_ttl: int = Field(3600, description="Cache TTL in seconds") 