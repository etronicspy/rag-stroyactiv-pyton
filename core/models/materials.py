from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class Material(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    use_category: str  # Renamed from category
    unit: str
    article: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Портландцемент М500",
                "use_category": "Cement",  # Updated field name
                "unit": "bag",
                "article": "CEM0001",
                "description": "Высококачественный цемент для строительных работ"
            }
        }
    )

class Category(BaseModel):
    name: str
    description: Optional[str] = None

class Unit(BaseModel):
    name: str
    description: Optional[str] = None 