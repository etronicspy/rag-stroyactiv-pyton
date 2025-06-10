from typing import Optional, List
from beanie import Document
from pydantic import BaseModel, Field
import datetime

class Material(Document):
    name: str = Field(..., min_length=2, max_length=200)
    category: str
    unit: str
    description: Optional[str] = None
    embedding: Optional[List[float]] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "materials"
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Портландцемент М500",
                "category": "Cement",
                "unit": "bag",
                "description": "Высококачественный цемент для строительных работ"
            }
        }

class Category(Document):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None

    class Settings:
        name = "categories"

class Unit(Document):
    name: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None

    class Settings:
        name = "units" 