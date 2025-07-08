"""
Enhanced Parsing Schemas for RAG Construction Materials API

This module provides Pydantic schemas for the enhanced AI parser integration
with support for color extraction and multiple embeddings.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ParsingMethod(str, Enum):
    """Available parsing methods"""
    AI_GPT = "ai_gpt"
    REGEX = "regex"
    HYBRID = "hybrid"
    MANUAL = "manual"


class EnhancedParseRequest(BaseModel):
    """Request model for enhanced material parsing"""
    
    name: str = Field(..., description="Material name to parse", min_length=1, max_length=500)
    unit: str = Field(..., description="Original unit from price list", max_length=50)
    price: float = Field(..., description="Original price", ge=0)
    
    # Optional parsing configuration
    extract_color: bool = Field(default=True, description="Whether to extract color from name")
    generate_embeddings: bool = Field(default=True, description="Whether to generate embeddings")
    parsing_method: ParsingMethod = Field(default=ParsingMethod.AI_GPT, description="Preferred parsing method")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Кирпич керамический белый одинарный",
                "unit": "шт",
                "price": 15.50,
                "extract_color": True,
                "generate_embeddings": True,
                "parsing_method": "ai_gpt"
            }
        }


class EnhancedParseResult(BaseModel):
    """Enhanced result model with color and embeddings support"""
    
    # Original input data
    name: str = Field(..., description="Original material name")
    original_unit: str = Field(..., description="Original unit from price list")
    original_price: float = Field(..., description="Original price")
    
    # Parsed results
    unit_parsed: Optional[str] = Field(None, description="Extracted metric unit")
    price_coefficient: Optional[float] = Field(None, description="Price coefficient for metric conversion", ge=0)
    price_parsed: Optional[float] = Field(None, description="Price per metric unit", ge=0)
    
    # Enhanced fields for RAG integration
    color: Optional[str] = Field(None, description="Extracted color from material name")
    
    # Multiple embeddings for vector search (1536 dimensions each)
    embeddings: Optional[List[float]] = Field(None, description="Material name embedding (1536dim)")
    color_embedding: Optional[List[float]] = Field(None, description="Color embedding (1536dim)")
    unit_embedding: Optional[List[float]] = Field(None, description="Unit embedding (1536dim)")
    
    # Metadata
    parsing_method: ParsingMethod = Field(default=ParsingMethod.AI_GPT, description="Method used for parsing")
    confidence: float = Field(default=0.0, description="Parsing confidence score", ge=0, le=1)
    success: bool = Field(default=False, description="Whether parsing was successful")
    error_message: Optional[str] = Field(None, description="Error message if parsing failed")
    processing_time: float = Field(default=0.0, description="Processing time in seconds", ge=0)
    
    @validator('embeddings', 'color_embedding', 'unit_embedding')
    def validate_embedding_dimensions(cls, v):
        """Validate that embeddings have correct dimensions (1536)"""
        if v is not None and len(v) != 1536:
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Кирпич керамический белый одинарный",
                "original_unit": "шт",
                "original_price": 15.50,
                "unit_parsed": "м3",
                "price_coefficient": 0.00195,
                "price_parsed": 7948.72,
                "color": "белый",
                "embeddings": "List[float] with 1536 dimensions",
                "color_embedding": "List[float] with 1536 dimensions", 
                "unit_embedding": "List[float] with 1536 dimensions",
                "parsing_method": "ai_gpt",
                "confidence": 0.90,
                "success": True,
                "error_message": None,
                "processing_time": 2.145
            }
        }


class BatchParseRequest(BaseModel):
    """Request model for batch parsing multiple materials"""
    
    materials: List[EnhancedParseRequest] = Field(..., description="List of materials to parse", min_items=1, max_items=100)
    
    # Batch processing options
    parallel_processing: bool = Field(default=True, description="Enable parallel processing")
    max_workers: int = Field(default=5, description="Maximum number of parallel workers", ge=1, le=10)
    fail_fast: bool = Field(default=False, description="Stop on first error")
    
    class Config:
        schema_extra = {
            "example": {
                "materials": [
                    {
                        "name": "Цемент М500 50кг",
                        "unit": "меш",
                        "price": 350.0
                    },
                    {
                        "name": "Кирпич красный одинарный", 
                        "unit": "шт",
                        "price": 12.50
                    }
                ],
                "parallel_processing": True,
                "max_workers": 3,
                "fail_fast": False
            }
        }


class BatchParseResponse(BaseModel):
    """Response model for batch parsing"""
    
    results: List[EnhancedParseResult] = Field(..., description="Parsing results for each material")
    
    # Batch statistics
    total_processed: int = Field(..., description="Total number of materials processed", ge=0)
    successful_parses: int = Field(..., description="Number of successful parses", ge=0)
    failed_parses: int = Field(..., description="Number of failed parses", ge=0)
    success_rate: float = Field(..., description="Success rate percentage", ge=0, le=100)
    total_processing_time: float = Field(..., description="Total processing time in seconds", ge=0)
    
    @validator('success_rate')
    def calculate_success_rate(cls, v, values):
        """Calculate success rate percentage"""
        if 'total_processed' in values and values['total_processed'] > 0:
            successful = values.get('successful_parses', 0)
            return (successful / values['total_processed']) * 100
        return 0.0
    
    class Config:
        schema_extra = {
            "example": {
                "results": "List[EnhancedParseResult]",
                "total_processed": 2,
                "successful_parses": 2,
                "failed_parses": 0,
                "success_rate": 100.0,
                "total_processing_time": 4.567
            }
        }


class ParserIntegrationConfig(BaseModel):
    """Configuration for parser integration with main system"""
    
    # Parser module settings
    use_enhanced_parser: bool = Field(default=True, description="Use enhanced parser with color extraction")
    embedding_cache_enabled: bool = Field(default=True, description="Enable embedding caching")
    
    # OpenAI settings
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model for parsing")
    embeddings_model: str = Field(default="text-embedding-3-small", description="OpenAI embeddings model")
    embeddings_dimensions: int = Field(default=1536, description="Embedding dimensions")
    
    # Performance settings
    max_concurrent_requests: int = Field(default=5, description="Max concurrent OpenAI requests", ge=1, le=20)
    request_timeout: int = Field(default=30, description="Request timeout in seconds", ge=5, le=300)
    retry_attempts: int = Field(default=3, description="Number of retry attempts", ge=1, le=10)
    
    # Quality settings
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for results", ge=0, le=1)
    enable_validation: bool = Field(default=True, description="Enable result validation")
    
    class Config:
        schema_extra = {
            "example": {
                "use_enhanced_parser": True,
                "embedding_cache_enabled": True,
                "openai_model": "gpt-4o-mini",
                "embeddings_model": "text-embedding-3-small",
                "embeddings_dimensions": 1536,
                "max_concurrent_requests": 5,
                "request_timeout": 30,
                "retry_attempts": 3,
                "confidence_threshold": 0.8,
                "enable_validation": True
            }
        }


class ColorExtractionResult(BaseModel):
    """Result of color extraction from material name"""
    
    original_text: str = Field(..., description="Original material name")
    extracted_color: Optional[str] = Field(None, description="Extracted color")
    confidence: float = Field(..., description="Extraction confidence", ge=0, le=1)
    method: str = Field(..., description="Extraction method used")
    
    class Config:
        schema_extra = {
            "example": {
                "original_text": "Кирпич керамический белый одинарный",
                "extracted_color": "белый",
                "confidence": 0.95,
                "method": "ai_gpt"
            }
        }


class EmbeddingGenerationResult(BaseModel):
    """Result of embedding generation"""
    
    text: str = Field(..., description="Original text")
    embedding: List[float] = Field(..., description="Generated embedding (1536dim)")
    model: str = Field(..., description="Model used for generation") 
    dimensions: int = Field(..., description="Embedding dimensions")
    processing_time: float = Field(..., description="Generation time in seconds", ge=0)
    
    @validator('embedding')
    def validate_dimensions(cls, v):
        """Validate embedding dimensions"""
        if len(v) != 1536:
            raise ValueError(f"Expected 1536 dimensions, got {len(v)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "text": "белый",
                "embedding": "List[float] with 1536 dimensions",
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "processing_time": 0.234
            }
        } 