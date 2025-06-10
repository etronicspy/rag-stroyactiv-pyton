from typing import List, Optional, Dict, Any
from qdrant_client.models import Distance, VectorParams, PointStruct
from core.schemas.materials import Material, MaterialCreate, MaterialUpdate, Category, Unit
from core.config import get_vector_db_client, get_ai_client, settings
import uuid

class MaterialsService:
    def __init__(self):
        # Use centralized client factories
        self.qdrant_client = get_vector_db_client()
        self.ai_client = get_ai_client()
        
        # Get database configuration
        self.db_config = settings.get_vector_db_config()
        self.collection_name = self.db_config["collection_name"]
        
        # Initialize collection if needed
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the materials collection exists"""
        try:
            collections = self.qdrant_client.get_collections()
            if not any(c.name == self.collection_name for c in collections.collections):
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.db_config["vector_size"], 
                        distance=Distance.COSINE
                    ),
                )
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using configured AI provider"""
        try:
            if settings.AI_PROVIDER.value == "openai":
                ai_config = settings.get_ai_config()
                # For text-embedding-3-small, specify dimensions to get 1536-dimensional vectors
                if "text-embedding-3" in ai_config["model"]:
                    response = await self.ai_client.embeddings.create(
                        input=text,
                        model=ai_config["model"],
                        dimensions=1536
                    )
                else:
                    response = await self.ai_client.embeddings.create(
                        input=text,
                        model=ai_config["model"]
                    )
                return response.data[0].embedding
            elif settings.AI_PROVIDER.value == "huggingface":
                # For HuggingFace, client is SentenceTransformer
                embedding = self.ai_client.encode([text])
                return embedding[0].tolist()
            else:
                raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise
    
    async def create_material(self, material: MaterialCreate) -> Material:
        """Create a new material"""
        try:
            # Generate embedding
            text_for_embedding = f"{material.name} {material.category} {material.description or ''}"
            embedding = await self._get_embedding(text_for_embedding)
            
            # Create material ID
            material_id = str(uuid.uuid4())
            
            # Prepare point for Qdrant
            point = PointStruct(
                id=material_id,
                vector=embedding,
                payload={
                    "name": material.name,
                    "category": material.category,
                    "unit": material.unit,
                    "description": material.description,
                }
            )
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            from datetime import datetime
            current_time = datetime.utcnow()
            
            return Material(
                id=material_id,
                name=material.name,
                category=material.category,
                unit=material.unit,
                description=material.description,
                embedding=embedding,
                created_at=current_time,
                updated_at=current_time
            )
        except Exception as e:
            print(f"Error creating material: {e}")
            raise
    
    async def get_material(self, material_id: str) -> Optional[Material]:
        """Get material by ID"""
        try:
            results = self.qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[material_id]
            )
            
            if not results:
                return None
                
            result = results[0]
            return Material(
                id=str(result.id),
                name=result.payload.get("name"),
                category=result.payload.get("category"),
                unit=result.payload.get("unit"),
                description=result.payload.get("description")
            )
        except Exception as e:
            print(f"Error getting material: {e}")
            return None
    
    async def update_material(self, material_id: str, material_update: MaterialUpdate) -> Optional[Material]:
        """Update an existing material"""
        try:
            # Get existing material
            existing = await self.get_material(material_id)
            if not existing:
                return None
            
            # Update fields
            updated_data = existing.model_dump()
            for field, value in material_update.model_dump(exclude_unset=True).items():
                updated_data[field] = value
            
            # Generate new embedding if content changed
            text_for_embedding = f"{updated_data['name']} {updated_data['category']} {updated_data.get('description', '')}"
            embedding = await self._get_embedding(text_for_embedding)
            
            # Update in Qdrant
            point = PointStruct(
                id=material_id,
                vector=embedding,
                payload={
                    "name": updated_data["name"],
                    "category": updated_data["category"],
                    "unit": updated_data["unit"],
                    "description": updated_data.get("description"),
                }
            )
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return Material(**updated_data)
        except Exception as e:
            print(f"Error updating material: {e}")
            raise
    
    async def delete_material(self, material_id: str) -> bool:
        """Delete a material"""
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=[material_id]
            )
            return True
        except Exception as e:
            print(f"Error deleting material: {e}")
            return False
    
    async def search_materials(self, query: str, limit: int = 10) -> List[Material]:
        """Search materials using semantic search"""
        try:
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            
            # Search in Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            # Format results
            materials = []
            for result in results:
                material = Material(
                    id=str(result.id),
                    name=result.payload.get("name"),
                    category=result.payload.get("category"),
                    unit=result.payload.get("unit"),
                    description=result.payload.get("description")
                )
                materials.append(material)
            
            return materials
        except Exception as e:
            print(f"Error searching materials: {e}")
            return []
    
    async def get_materials(self, skip: int = 0, limit: int = 100, category: Optional[str] = None) -> List[Material]:
        """Get all materials with optional category filter"""
        try:
            # Use scroll to get all materials
            all_materials = []
            offset = None
            
            # Get all materials first
            while True:
                results = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True
                )
                
                if isinstance(results, tuple):
                    points, next_offset = results
                else:
                    points = results
                    next_offset = None
                
                for point in points:
                    material = Material(
                        id=str(point.id),
                        name=point.payload.get("name"),
                        category=point.payload.get("category"),
                        unit=point.payload.get("unit"),
                        description=point.payload.get("description")
                    )
                    
                    # Apply category filter if specified
                    if category is None or material.category == category:
                        all_materials.append(material)
                
                # Break if no more results
                if next_offset is None or not points:
                    break
                
                offset = next_offset
            
            # Apply skip and limit
            return all_materials[skip:skip + limit]
        except Exception as e:
            print(f"Error getting materials: {e}")
            return []

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