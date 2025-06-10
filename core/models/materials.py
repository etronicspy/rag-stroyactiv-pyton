from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class Material(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    category: str
    unit: str
    description: Optional[str] = None
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Портландцемент М500",
                "category": "Cement",
                "unit": "bag",
                "description": "Высококачественный цемент для строительных работ"
            }
        }

class Category(BaseModel):
    name: str
    description: Optional[str] = None

class Unit(BaseModel):
    name: str
    description: Optional[str] = None 