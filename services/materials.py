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
            # Get list of existing collections
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                print(f"Creating collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.db_config["vector_size"], 
                        distance=Distance.COSINE
                    ),
                )
                print(f"Collection {self.collection_name} created successfully")
            else:
                print(f"Collection {self.collection_name} already exists")
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            # Try to create collection anyway
            try:
                print(f"Attempting to create collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.db_config["vector_size"], 
                        distance=Distance.COSINE
                    ),
                )
                print(f"Collection {self.collection_name} created successfully on retry")
            except Exception as e2:
                print(f"Failed to create collection on retry: {e2}")
                raise e2
    
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
            # Ensure collection exists before creating material
            self._ensure_collection_exists()
            
            # Generate embedding
            text_for_embedding = f"{material.name} {material.category} {material.description or ''}"
            embedding = await self._get_embedding(text_for_embedding)
            
            # Create material ID
            material_id = str(uuid.uuid4())
            
            from datetime import datetime
            current_time = datetime.utcnow()
            
            # Prepare point for Qdrant
            point = PointStruct(
                id=material_id,
                vector=embedding,
                payload={
                    "name": material.name,
                    "category": material.category,
                    "unit": material.unit,
                    "description": material.description,
                    "created_at": current_time.isoformat(),
                    "updated_at": current_time.isoformat()
                }
            )
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
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
            # Ensure collection exists before querying
            self._ensure_collection_exists()
            
            results = self.qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[material_id]
            )
            
            if not results:
                return None
                
            result = results[0]
            from datetime import datetime
            
            # Parse timestamps or use current time as fallback
            created_at = None
            updated_at = None
            if result.payload.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(result.payload["created_at"])
                except:
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()
                
            if result.payload.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(result.payload["updated_at"])
                except:
                    updated_at = datetime.utcnow()
            else:
                updated_at = datetime.utcnow()
            
            return Material(
                id=str(result.id),
                name=result.payload.get("name"),
                category=result.payload.get("category"),
                unit=result.payload.get("unit"),
                description=result.payload.get("description"),
                created_at=created_at,
                updated_at=updated_at
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
            
            from datetime import datetime
            current_time = datetime.utcnow()
            updated_data["updated_at"] = current_time
            
            # Update in Qdrant
            point = PointStruct(
                id=material_id,
                vector=embedding,
                payload={
                    "name": updated_data["name"],
                    "category": updated_data["category"],
                    "unit": updated_data["unit"],
                    "description": updated_data.get("description"),
                    "created_at": updated_data["created_at"].isoformat(),
                    "updated_at": current_time.isoformat()
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
            # Ensure collection exists before searching
            self._ensure_collection_exists()
            
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            
            # Search in Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            from datetime import datetime
            
            # Format results
            materials = []
            for result in results:
                # Parse timestamps or use current time as fallback
                created_at = None
                updated_at = None
                if result.payload.get("created_at"):
                    try:
                        created_at = datetime.fromisoformat(result.payload["created_at"])
                    except:
                        created_at = datetime.utcnow()
                else:
                    created_at = datetime.utcnow()
                    
                if result.payload.get("updated_at"):
                    try:
                        updated_at = datetime.fromisoformat(result.payload["updated_at"])
                    except:
                        updated_at = datetime.utcnow()
                else:
                    updated_at = datetime.utcnow()
                
                material = Material(
                    id=str(result.id),
                    name=result.payload.get("name"),
                    category=result.payload.get("category"),
                    unit=result.payload.get("unit"),
                    description=result.payload.get("description"),
                    created_at=created_at,
                    updated_at=updated_at
                )
                materials.append(material)
            
            return materials
        except Exception as e:
            print(f"Error searching materials: {e}")
            return []
    
    async def get_materials(self, skip: int = 0, limit: int = 100, category: Optional[str] = None) -> List[Material]:
        """Get all materials with optional category filter"""
        try:
            # Ensure collection exists before querying
            self._ensure_collection_exists()
            
            # Use scroll to get all materials
            all_materials = []
            offset = None
            
            from datetime import datetime
            
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
                    # Parse timestamps or use current time as fallback
                    created_at = None
                    updated_at = None
                    if point.payload.get("created_at"):
                        try:
                            created_at = datetime.fromisoformat(point.payload["created_at"])
                        except:
                            created_at = datetime.utcnow()
                    else:
                        created_at = datetime.utcnow()
                        
                    if point.payload.get("updated_at"):
                        try:
                            updated_at = datetime.fromisoformat(point.payload["updated_at"])
                        except:
                            updated_at = datetime.utcnow()
                    else:
                        updated_at = datetime.utcnow()
                    
                    material = Material(
                        id=str(point.id),
                        name=point.payload.get("name"),
                        category=point.payload.get("category"),
                        unit=point.payload.get("unit"),
                        description=point.payload.get("description"),
                        created_at=created_at,
                        updated_at=updated_at
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
    def __init__(self):
        # Use centralized client factories
        self.qdrant_client = get_vector_db_client()
        self.collection_name = "categories"
        
        # Initialize collection if needed
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the categories collection exists"""
        try:
            # Get list of existing collections
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                print(f"Creating collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1,  # Simple collection, just need 1D vector
                        distance=Distance.COSINE
                    ),
                )
                print(f"Collection {self.collection_name} created successfully")
            else:
                print(f"Collection {self.collection_name} already exists")
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            # Try to create collection anyway
            try:
                print(f"Attempting to create collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1,  # Simple collection, just need 1D vector
                        distance=Distance.COSINE
                    ),
                )
                print(f"Collection {self.collection_name} created successfully on retry")
            except Exception as e2:
                print(f"Failed to create collection on retry: {e2}")
                raise e2
    
    async def create_category(self, name: str, description: Optional[str] = None) -> Category:
        """Create a new category"""
        try:
            # Ensure collection exists before creating category
            self._ensure_collection_exists()
            
            category_id = str(uuid.uuid4())
            
            # Prepare point for Qdrant
            point = PointStruct(
                id=category_id,
                vector=[1.0],  # Simple 1D vector
                payload={
                    "name": name,
                    "description": description
                }
            )
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return Category(name=name, description=description)
        except Exception as e:
            print(f"Error creating category: {e}")
            raise
    
    async def get_categories(self) -> List[Category]:
        """Get all categories"""
        try:
            # Ensure collection exists before querying
            self._ensure_collection_exists()
            
            # Use scroll to get all categories
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True
            )
            
            categories = []
            if isinstance(results, tuple):
                points, _ = results
            else:
                points = results
                
            for point in points:
                category = Category(
                    name=point.payload.get("name"),
                    description=point.payload.get("description")
                )
                categories.append(category)
            
            return categories
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []
    
    async def delete_category(self, name: str) -> bool:
        """Delete a category"""
        try:
            # Ensure collection exists before querying
            self._ensure_collection_exists()
            
            # Find category by name
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True
            )
            
            if isinstance(results, tuple):
                points, _ = results
            else:
                points = results
                
            for point in points:
                if point.payload.get("name") == name:
                    # Delete the point
                    self.qdrant_client.delete(
                        collection_name=self.collection_name,
                        points_selector=[str(point.id)]
                    )
                    return True
            
            return False
        except Exception as e:
            print(f"Error deleting category: {e}")
            return False

class UnitService:
    def __init__(self):
        # Use centralized client factories
        self.qdrant_client = get_vector_db_client()
        self.collection_name = "units"
        
        # Initialize collection if needed
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Ensure the units collection exists"""
        try:
            # Get list of existing collections
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                print(f"Creating collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1,  # Simple collection, just need 1D vector
                        distance=Distance.COSINE
                    ),
                )
                print(f"Collection {self.collection_name} created successfully")
            else:
                print(f"Collection {self.collection_name} already exists")
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            # Try to create collection anyway
            try:
                print(f"Attempting to create collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1,  # Simple collection, just need 1D vector
                        distance=Distance.COSINE
                    ),
                )
                print(f"Collection {self.collection_name} created successfully on retry")
            except Exception as e2:
                print(f"Failed to create collection on retry: {e2}")
                raise e2
    
    async def create_unit(self, name: str, description: Optional[str] = None) -> Unit:
        """Create a new unit"""
        try:
            # Ensure collection exists before creating unit
            self._ensure_collection_exists()
            
            unit_id = str(uuid.uuid4())
            
            # Prepare point for Qdrant
            point = PointStruct(
                id=unit_id,
                vector=[1.0],  # Simple 1D vector
                payload={
                    "name": name,
                    "description": description
                }
            )
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return Unit(name=name, description=description)
        except Exception as e:
            print(f"Error creating unit: {e}")
            raise
    
    async def get_units(self) -> List[Unit]:
        """Get all units"""
        try:
            # Ensure collection exists before querying
            self._ensure_collection_exists()
            
            # Use scroll to get all units
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True
            )
            
            units = []
            if isinstance(results, tuple):
                points, _ = results
            else:
                points = results
                
            for point in points:
                unit = Unit(
                    name=point.payload.get("name"),
                    description=point.payload.get("description")
                )
                units.append(unit)
            
            return units
        except Exception as e:
            print(f"Error getting units: {e}")
            return []
    
    async def delete_unit(self, name: str) -> bool:
        """Delete a unit"""
        try:
            # Ensure collection exists before querying
            self._ensure_collection_exists()
            
            # Find unit by name
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True
            )
            
            if isinstance(results, tuple):
                points, _ = results
            else:
                points = results
                
            for point in points:
                if point.payload.get("name") == name:
                    # Delete the point
                    self.qdrant_client.delete(
                        collection_name=self.collection_name,
                        points_selector=[str(point.id)]
                    )
                    return True
            
            return False
        except Exception as e:
            print(f"Error deleting unit: {e}")
            return False 