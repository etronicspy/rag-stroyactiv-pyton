from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class MaterialBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    category: str
    unit: str
    article: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    category: Optional[str] = None
    unit: Optional[str] = None
    article: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None

class Material(MaterialBase):
    id: str
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MaterialSearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)

class Category(BaseModel):
    name: str
    description: Optional[str] = None

class Unit(BaseModel):
    name: str
    description: Optional[str] = None

# Batch operations schemas
class MaterialBatchCreate(BaseModel):
    materials: List[MaterialCreate] = Field(..., min_items=1, max_items=1000)
    batch_size: int = Field(default=100, ge=1, le=500)

class MaterialBatchResponse(BaseModel):
    success: bool
    total_processed: int
    successful_creates: int
    failed_creates: int
    processing_time_seconds: float
    errors: List[str] = []
    created_materials: List[Material] = []

# Schema for importing from JSON file format
class MaterialImportItem(BaseModel):
    article: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)

class MaterialImportRequest(BaseModel):
    materials: List[MaterialImportItem] = Field(..., min_items=1, max_items=1000)
    default_category: str = Field(default="Стройматериалы")
    default_unit: str = Field(default="шт")
    batch_size: int = Field(default=100, ge=1, le=500) 