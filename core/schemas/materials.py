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

class MaterialUpdate(MaterialBase):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    category: Optional[str] = None
    unit: Optional[str] = None

class MaterialInDB(MaterialBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MaterialResponse(MaterialInDB):
    pass

class MaterialSearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryInDB(CategoryBase):
    id: str

    class Config:
        from_attributes = True

class UnitBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None

class UnitCreate(UnitBase):
    pass

class UnitInDB(UnitBase):
    id: str

    class Config:
        from_attributes = True 