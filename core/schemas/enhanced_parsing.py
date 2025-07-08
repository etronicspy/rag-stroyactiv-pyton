"""
Enhanced Parsing Schemas for RAG Construction Materials API

This module contains Pydantic models for enhanced material parsing 
with color extraction and embeddings support.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ColorExtractionResult(BaseModel):
    """Result of color extraction from material name"""
    color: Optional[str] = Field(None, description="Extracted color name")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Extraction confidence (0-1)")
    
    class Config:
        schema_extra = {
            "example": {
                "color": "белый",
                "confidence": 0.9
            }
        }


class EmbeddingResult(BaseModel):
    """Embedding generation result"""
    embedding: Optional[List[float]] = Field(None, description="1536-dimensional embedding vector")
    dimensions: int = Field(1536, description="Embedding dimensions")
    model: str = Field("text-embedding-3-small", description="Model used for embedding generation")
    
    @validator('embedding')
    def validate_embedding_dimensions(cls, v, values):
        if v is not None and len(v) != values.get('dimensions', 1536):
            raise ValueError(f"Embedding must have {values.get('dimensions', 1536)} dimensions")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "embedding": [0.1, -0.2, 0.3],  # Shortened for example
                "dimensions": 1536,
                "model": "text-embedding-3-small"
            }
        }


class EnhancedParsingRequest(BaseModel):
    """Request for enhanced material parsing"""
    name: str = Field(..., min_length=1, max_length=500, description="Material name")
    unit: str = Field(..., min_length=1, max_length=50, description="Original unit of measurement")
    price: Optional[float] = Field(0.0, ge=0.0, description="Original price (optional)")
    extract_color: bool = Field(True, description="Enable color extraction")
    generate_embeddings: bool = Field(True, description="Enable embeddings generation")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Цемент белый М500 50кг",
                "unit": "меш",
                "price": 450.0,
                "extract_color": True,
                "generate_embeddings": True
            }
        }


class EnhancedParsingResponse(BaseModel):
    """Response from enhanced material parsing"""
    
    # Basic parsing results
    name: str = Field(..., description="Original material name")
    original_unit: str = Field(..., description="Original unit of measurement")
    original_price: float = Field(0.0, description="Original price")
    
    # Parsed results
    unit_parsed: Optional[str] = Field(None, description="Parsed metric unit")
    price_coefficient: Optional[float] = Field(None, description="Coefficient for price conversion")
    price_parsed: Optional[float] = Field(None, description="Price per metric unit")
    
    # Color extraction
    color: Optional[str] = Field(None, description="Extracted color")
    color_confidence: float = Field(0.0, description="Color extraction confidence")
    
    # Embeddings (1536 dimensions each)
    color_embedding: Optional[List[float]] = Field(None, description="Color embedding vector")
    parsed_unit_embedding: Optional[List[float]] = Field(None, description="Parsed unit embedding vector")
    material_embedding: Optional[List[float]] = Field(None, description="Material embedding vector")
    
    # RAG normalization results (populated by pipeline)
    normalized_color: Optional[str] = Field(None, description="RAG normalized color")
    normalized_unit: Optional[str] = Field(None, description="RAG normalized unit")
    
    # Metadata
    parsing_method: str = Field("enhanced_ai", description="Parsing method used")
    confidence: float = Field(0.0, description="Overall parsing confidence")
    success: bool = Field(True, description="Parsing success status")
    error_message: Optional[str] = Field(None, description="Error message if parsing failed")
    processing_time: float = Field(0.0, description="Processing time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Цемент белый М500 50кг",
                "original_unit": "меш",
                "original_price": 450.0,
                "unit_parsed": "кг",
                "price_coefficient": 50.0,
                "price_parsed": 9.0,
                "color": "белый",
                "color_confidence": 0.9,
                "color_embedding": [0.1, -0.2, 0.3],  # Shortened for example
                "parsed_unit_embedding": [0.2, -0.1, 0.4],  # Shortened for example  
                "material_embedding": [0.15, -0.15, 0.35],  # Shortened for example
                "normalized_color": "белый",
                "normalized_unit": "кг",
                "parsing_method": "enhanced_ai",
                "confidence": 0.9,
                "success": True,
                "error_message": None,
                "processing_time": 1.2
            }
        }


class BatchEnhancedParsingRequest(BaseModel):
    """Request for batch enhanced parsing"""
    materials: List[EnhancedParsingRequest] = Field(
        ..., 
        min_items=1, 
        max_items=100, 
        description="List of materials to parse"
    )
    extract_color: bool = Field(True, description="Enable color extraction for all materials")
    generate_embeddings: bool = Field(True, description="Enable embeddings generation for all materials")
    
    class Config:
        schema_extra = {
            "example": {
                "materials": [
                    {
                        "name": "Цемент белый М500 50кг",
                        "unit": "меш",
                        "price": 450.0
                    },
                    {
                        "name": "Кирпич красный керамический",
                        "unit": "шт",
                        "price": 25.0
                    }
                ],
                "extract_color": True,
                "generate_embeddings": True
            }
        }


class BatchEnhancedParsingResponse(BaseModel):
    """Response from batch enhanced parsing"""
    results: List[EnhancedParsingResponse] = Field(..., description="Parsing results")
    total_processed: int = Field(..., description="Total materials processed")
    successful_count: int = Field(..., description="Number of successful parsings")
    failed_count: int = Field(..., description="Number of failed parsings")
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "name": "Цемент белый М500 50кг",
                        "original_unit": "меш",
                        "success": True,
                        "color": "белый"
                    }
                ],
                "total_processed": 2,
                "successful_count": 2,
                "failed_count": 0,
                "total_processing_time": 2.5
            }
        }


class EnhancedParsingStatistics(BaseModel):
    """Statistics for enhanced parsing operations"""
    total_requests: int = Field(0, description="Total parsing requests")
    successful_parsings: int = Field(0, description="Successful parsing operations")
    color_extractions: int = Field(0, description="Successful color extractions")
    embeddings_generated: int = Field(0, description="Total embeddings generated")
    average_processing_time: float = Field(0.0, description="Average processing time")
    color_extraction_rate: float = Field(0.0, description="Color extraction success rate")
    parsing_success_rate: float = Field(0.0, description="Overall parsing success rate")
    
    class Config:
        schema_extra = {
            "example": {
                "total_requests": 100,
                "successful_parsings": 95,
                "color_extractions": 80,
                "embeddings_generated": 285,
                "average_processing_time": 1.5,
                "color_extraction_rate": 0.8,
                "parsing_success_rate": 0.95
            }
        }


class MaterialEmbeddingData(BaseModel):
    """Material data with embeddings for storage"""
    
    # Basic material info
    name: str = Field(..., description="Material name")
    unit_parsed: Optional[str] = Field(None, description="Parsed unit")
    color: Optional[str] = Field(None, description="Extracted color")
    
    # Embeddings (1536 dimensions each)
    color_embedding: Optional[List[float]] = Field(None, description="Color embedding")
    parsed_unit_embedding: Optional[List[float]] = Field(None, description="Unit embedding")
    material_embedding: Optional[List[float]] = Field(None, description="Material embedding")
    
    # Metadata
    embedding_model: str = Field("text-embedding-3-small", description="Model used for embeddings")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Цемент белый М500",
                "unit_parsed": "кг",
                "color": "белый",
                "color_embedding": [0.1, -0.2, 0.3],  # Shortened
                "parsed_unit_embedding": [0.2, -0.1, 0.4],  # Shortened
                "material_embedding": [0.15, -0.15, 0.35],  # Shortened
                "embedding_model": "text-embedding-3-small",
                "created_at": "2025-01-25T10:00:00Z"
            }
        }


class ValidationResult(BaseModel):
    """Result of parsing validation"""
    is_valid: bool = Field(..., description="Validation result")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Color confidence is low"]
            }
        }


class EnhancedParsingConfig(BaseModel):
    """Configuration for enhanced parsing"""
    extract_color: bool = Field(True, description="Enable color extraction")
    generate_embeddings: bool = Field(True, description="Enable embeddings generation")
    color_confidence_threshold: float = Field(0.7, description="Minimum color confidence")
    parsing_confidence_threshold: float = Field(0.8, description="Minimum parsing confidence")
    enable_ai_color_extraction: bool = Field(True, description="Use AI for complex color extraction")
    
    class Config:
        schema_extra = {
            "example": {
                "extract_color": True,
                "generate_embeddings": True,
                "color_confidence_threshold": 0.7,
                "parsing_confidence_threshold": 0.8,
                "enable_ai_color_extraction": True
            }
        } 