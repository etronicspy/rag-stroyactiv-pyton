from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class MaterialBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    category: str
    unit: str
    description: Optional[str] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    category: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None

class Material(MaterialBase):
    id: str
    embedding: List[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MaterialSearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)

class Category(BaseModel):
    name: str
    description: Optional[str] = None

class Unit(BaseModel):
    name: str
    description: Optional[str] = None 