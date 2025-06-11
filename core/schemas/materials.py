from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
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