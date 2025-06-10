from typing import List, Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer
import numpy as np

from core.models.materials import Material, Category, Unit
from core.schemas.materials import MaterialCreate, MaterialUpdate
from core.config import settings

class MaterialsService:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    async def create_material(self, material: MaterialCreate) -> Material:
        # Generate embedding for the material
        embedding = self.model.encode(f"{material.name} {material.description or ''}")
        
        db_material = Material(
            **material.model_dump(),
            embedding=embedding.tolist()
        )
        await db_material.insert()
        return db_material
    
    async def get_material(self, material_id: str) -> Optional[Material]:
        return await Material.get(material_id)
    
    async def get_materials(
        self, 
        skip: int = 0, 
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Material]:
        query = {}
        if category:
            query["category"] = category
        
        return await Material.find(query).skip(skip).limit(limit).to_list()
    
    async def update_material(
        self, 
        material_id: str, 
        material_update: MaterialUpdate
    ) -> Optional[Material]:
        material = await self.get_material(material_id)
        if not material:
            return None
            
        update_data = material_update.model_dump(exclude_unset=True)
        
        if "name" in update_data or "description" in update_data:
            # Re-generate embedding if name or description changed
            embedding = self.model.encode(
                f"{update_data.get('name', material.name)} {update_data.get('description', material.description or '')}"
            )
            update_data["embedding"] = embedding.tolist()
        
        update_data["updated_at"] = datetime.utcnow()
        
        await material.update({"$set": update_data})
        return material
    
    async def delete_material(self, material_id: str) -> bool:
        material = await self.get_material(material_id)
        if not material:
            return False
        await material.delete()
        return True
    
    async def search_materials(self, query: str, limit: int = 10) -> List[Material]:
        # Generate embedding for the search query
        query_embedding = self.model.encode(query)
        
        # Get all materials (in a real application, you'd want to optimize this)
        all_materials = await Material.find_all().to_list()
        
        if not all_materials:
            return []
        
        # Calculate similarities
        similarities = []
        for material in all_materials:
            if material.embedding:
                similarity = np.dot(query_embedding, material.embedding)
                similarities.append((similarity, material))
        
        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [material for _, material in similarities[:limit]]

class CategoryService:
    @staticmethod
    async def create_category(name: str, description: Optional[str] = None) -> Category:
        category = Category(name=name, description=description)
        await category.insert()
        return category
    
    @staticmethod
    async def get_categories() -> List[Category]:
        return await Category.find_all().to_list()
    
    @staticmethod
    async def delete_category(name: str) -> bool:
        category = await Category.find_one(Category.name == name)
        if not category:
            return False
        await category.delete()
        return True

class UnitService:
    @staticmethod
    async def create_unit(name: str, description: Optional[str] = None) -> Unit:
        unit = Unit(name=name, description=description)
        await unit.insert()
        return unit
    
    @staticmethod
    async def get_units() -> List[Unit]:
        return await Unit.find_all().to_list()
    
    @staticmethod
    async def delete_unit(name: str) -> bool:
        unit = await Unit.find_one(Unit.name == name)
        if not unit:
            return False
        await unit.delete()
        return True 