from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class Material(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    use_category: str  # Renamed from category
    unit: str
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None
    # Enhanced fields for parsing and normalization
    color: Optional[str] = None
    normalized_color: Optional[str] = None
    normalized_parsed_unit: Optional[str] = None
    unit_coefficient: Optional[float] = None
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Портландцемент М500",
                "use_category": "Cement",  # Updated field name
                "unit": "bag",
                "sku": "CEM0001",
                "description": "Высококачественный цемент для строительных работ",
                "color": "серый",
                "normalized_color": "серый",
                "normalized_parsed_unit": "мешок",
                "unit_coefficient": 1.0
            }
        }
    )

class Category(BaseModel):
    name: str
    description: Optional[str] = None

class Unit(BaseModel):
    name: str
    description: Optional[str] = None 