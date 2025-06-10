from typing import List, Optional, Dict, Any
from datetime import datetime
import openai
from qdrant_client import QdrantClient
from qdrant_client.http import models
import uuid

from core.models.materials import Material, Category, Unit
from core.schemas.materials import MaterialCreate, MaterialUpdate
from core.config import settings

class MaterialsService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Ensure collection exists
        self._init_collection()
    
    def _init_collection(self):
        """Initialize Qdrant collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        if not any(c.name == settings.QDRANT_COLLECTION_NAME for c in collections):
            self.client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=1536,  # OpenAI embedding dimension
                    distance=models.Distance.COSINE
                )
            )
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI API"""
        response = await self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    async def create_material(self, material: MaterialCreate) -> Material:
        # Generate embedding
        text = f"{material.name} {material.description or ''}"
        embedding = await self._get_embedding(text)
        
        # Create material with ID
        material_id = str(uuid.uuid4())
        material_dict = material.model_dump()
        material_dict.update({
            "id": material_id,
            "embedding": embedding,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Store in Qdrant
        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[models.PointStruct(
                id=material_id,
                vector=embedding,
                payload=material_dict
            )]
        )
        
        return Material(**material_dict)
    
    async def get_material(self, material_id: str) -> Optional[Material]:
        response = self.client.retrieve(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            ids=[material_id]
        )
        if not response:
            return None
        return Material(**response[0].payload)
    
    async def get_materials(
        self, 
        skip: int = 0, 
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Material]:
        # Prepare filter conditions
        filter_conditions = []
        if category:
            filter_conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=category)
                )
            )
        
        # Get materials from Qdrant
        response = self.client.scroll(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=filter_conditions
            ) if filter_conditions else None,
            limit=limit,
            offset=skip
        )
        
        return [Material(**point.payload) for point in response[0]]
    
    async def update_material(
        self, 
        material_id: str, 
        material_update: MaterialUpdate
    ) -> Optional[Material]:
        # Get existing material
        existing = await self.get_material(material_id)
        if not existing:
            return None
        
        # Update fields
        update_data = material_update.model_dump(exclude_unset=True)
        
        # If name or description changed, update embedding
        if "name" in update_data or "description" in update_data:
            name = update_data.get("name", existing.name)
            description = update_data.get("description", existing.description)
            text = f"{name} {description or ''}"
            update_data["embedding"] = await self._get_embedding(text)
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in Qdrant
        material_dict = existing.model_dump()
        material_dict.update(update_data)
        
        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[models.PointStruct(
                id=material_id,
                vector=material_dict["embedding"],
                payload=material_dict
            )]
        )
        
        return Material(**material_dict)
    
    async def delete_material(self, material_id: str) -> bool:
        try:
            self.client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=models.PointIdsList(
                    points=[material_id]
                )
            )
            return True
        except Exception:
            return False
    
    async def search_materials(self, query: str, limit: int = 10) -> List[Material]:
        # Get query embedding
        query_embedding = await self._get_embedding(query)
        
        # Search in Qdrant
        response = self.client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit
        )
        
        return [Material(**point.payload) for point in response]

class CategoryService:
    _categories: Dict[str, Category] = {}
    
    @classmethod
    async def create_category(cls, name: str, description: Optional[str] = None) -> Category:
        category = Category(name=name, description=description)
        cls._categories[name] = category
        return category
    
    @classmethod
    async def get_categories(cls) -> List[Category]:
        return list(cls._categories.values())
    
    @classmethod
    async def delete_category(cls, name: str) -> bool:
        if name in cls._categories:
            del cls._categories[name]
            return True
        return False

class UnitService:
    _units: Dict[str, Unit] = {}
    
    @classmethod
    async def create_unit(cls, name: str, description: Optional[str] = None) -> Unit:
        unit = Unit(name=name, description=description)
        cls._units[name] = unit
        return unit
    
    @classmethod
    async def get_units(cls) -> List[Unit]:
        return list(cls._units.values())
    
    @classmethod
    async def delete_unit(cls, name: str) -> bool:
        if name in cls._units:
            del cls._units[name]
            return True
        return False 