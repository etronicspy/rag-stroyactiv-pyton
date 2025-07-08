"""
Color schemas for construction materials classification.

Схемы для цветовой классификации строительных материалов.
"""

from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ColorReference(BaseModel):
    """Reference color model for material classification.
    
    Справочная модель цвета для классификации материалов.
    """
    id: str = Field(
        ...,
        description="Unique color identifier (UUID)",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Standard color name in Russian",
        example="белый"
    )
    hex_code: Optional[str] = Field(
        None,
        pattern=r'^#[0-9A-Fa-f]{6}$',
        description="Hex color code (optional)",
        example="#FFFFFF"
    )
    rgb_values: Optional[List[int]] = Field(
        None,
        description="RGB color values [R, G, B] (0-255)",
        example=[255, 255, 255]
    )
    aliases: List[str] = Field(
        default=[],
        description="Alternative color names and variations",
        example=["светлый", "молочный", "снежный"]
    )
    embedding: List[float] = Field(
        ...,
        description="Color embedding vector for semantic search (1536 dimensions)",
        example=[0.1, 0.2, 0.3]
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Color creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "белый",
                    "hex_code": "#FFFFFF",
                    "rgb_values": [255, 255, 255],
                    "aliases": ["светлый", "молочный", "снежный"],
                    "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
                    "created_at": "2025-06-16T16:46:29.421964Z",
                    "updated_at": "2025-06-16T16:46:29.421964Z"
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "синий",
                    "hex_code": "#0066FF",
                    "rgb_values": [0, 102, 255],
                    "aliases": ["голубой", "васильковый", "небесный"],
                    "embedding": [0.4, 0.5, 0.6, "...", "(1536 dimensions)"],
                    "created_at": "2025-06-16T16:46:29.421964Z",
                    "updated_at": "2025-06-16T16:46:29.421964Z"
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440002",
                    "name": "коричневый",
                    "hex_code": "#8B4513",
                    "rgb_values": [139, 69, 19],
                    "aliases": ["кофейный", "шоколадный", "каштановый"],
                    "embedding": [0.7, 0.8, 0.9, "...", "(1536 dimensions)"],
                    "created_at": "2025-06-16T16:46:29.421964Z",
                    "updated_at": "2025-06-16T16:46:29.421964Z"
                }
            ]
        }
    )


class ColorCreate(BaseModel):
    """Schema for creating a new color reference.
    
    Схема для создания нового справочного цвета.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Standard color name in Russian",
        example="белый"
    )
    hex_code: Optional[str] = Field(
        None,
        pattern=r'^#[0-9A-Fa-f]{6}$',
        description="Hex color code (optional)",
        example="#FFFFFF"
    )
    rgb_values: Optional[List[int]] = Field(
        None,
        description="RGB color values [R, G, B] (0-255)",
        example=[255, 255, 255]
    )
    aliases: List[str] = Field(
        default=[],
        description="Alternative color names and variations",
        example=["светлый", "молочный", "снежный"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "белый",
                    "hex_code": "#FFFFFF",
                    "rgb_values": [255, 255, 255],
                    "aliases": ["светлый", "молочный", "снежный", "кремовый"]
                },
                {
                    "name": "синий",
                    "hex_code": "#0066FF",
                    "rgb_values": [0, 102, 255],
                    "aliases": ["голубой", "васильковый", "небесный"]
                },
                {
                    "name": "красный",
                    "hex_code": "#FF0000",
                    "rgb_values": [255, 0, 0],
                    "aliases": ["алый", "кирпичный", "багряный"]
                },
                {
                    "name": "зеленый",
                    "hex_code": "#00FF00",
                    "rgb_values": [0, 255, 0],
                    "aliases": ["травяной", "изумрудный", "малахитовый"]
                },
                {
                    "name": "коричневый",
                    "hex_code": "#8B4513",
                    "rgb_values": [139, 69, 19],
                    "aliases": ["кофейный", "шоколадный", "каштановый"]
                }
            ]
        }
    )


class ColorUpdate(BaseModel):
    """Schema for updating a color reference.
    
    Схема для обновления справочного цвета.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    hex_code: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    rgb_values: Optional[List[int]] = None
    aliases: Optional[List[str]] = None


class ColorNormalizationRequest(BaseModel):
    """Request for color normalization through RAG.
    
    Запрос на нормализацию цвета через RAG.
    """
    color_text: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Color text to normalize",
        example="красноватый"
    )
    similarity_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold for matching"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "color_text": "красноватый",
                "similarity_threshold": 0.8
            }
        }
    )


class ColorNormalizationResponse(BaseModel):
    """Response for color normalization.
    
    Ответ на нормализацию цвета.
    """
    original_text: str = Field(
        ...,
        description="Original color text"
    )
    normalized_color: Optional[str] = Field(
        None,
        description="Normalized color name (if found)"
    )
    similarity_score: Optional[float] = Field(
        None,
        description="Similarity score with matched color"
    )
    suggestions: List[str] = Field(
        default=[],
        description="Alternative color suggestions"
    )
    success: bool = Field(
        ...,
        description="Whether normalization was successful"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_text": "красноватый",
                "normalized_color": "красный",
                "similarity_score": 0.85,
                "suggestions": ["красный", "алый", "бордовый"],
                "success": True
            }
        }
    )


class ColorSearchQuery(BaseModel):
    """Query for color search.
    
    Запрос для поиска цветов.
    """
    query: str = Field(
        ...,
        min_length=1,
        description="Color search query"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
    similarity_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold"
    )


class ColorSearchResult(BaseModel):
    """Color search result.
    
    Результат поиска цвета.
    """
    color: ColorReference = Field(
        ...,
        description="Color reference"
    )
    score: float = Field(
        ...,
        description="Similarity score"
    )
    matched_field: str = Field(
        ...,
        description="Field that matched (name, alias, etc.)"
    )


class ColorListResponse(BaseModel):
    """Response for color list.
    
    Ответ со списком цветов.
    """
    colors: List[ColorReference] = Field(
        ...,
        description="List of color references"
    )
    total_count: int = Field(
        ...,
        description="Total number of colors"
    )
    page: int = Field(
        default=1,
        description="Current page number"
    )
    page_size: int = Field(
        default=20,
        description="Items per page"
    ) 