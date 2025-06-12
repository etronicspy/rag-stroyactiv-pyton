"""Refactored Materials Service using new multi-database architecture.

Рефакторенный сервис материалов с новой мульти-БД архитектурой.
"""

from typing import List, Optional, Dict, Any
import logging
import uuid
import asyncio
from datetime import datetime

from core.schemas.materials import (
    Material, MaterialCreate, MaterialUpdate, MaterialBatchResponse, MaterialImportItem
)
from core.database.interfaces import IVectorDatabase
from core.database.exceptions import DatabaseError, ConnectionError, QueryError
from core.repositories.base import BaseRepository


logger = logging.getLogger(__name__)


class MaterialsService(BaseRepository):
    """Refactored Materials Service using new database architecture.
    
    Рефакторенный сервис материалов с новой архитектурой БД.
    """
    
    def __init__(self, vector_db: IVectorDatabase = None, ai_client = None):
        """Initialize Materials Service with dependency injection.
        
        Args:
            vector_db: Vector database client (injected)
            ai_client: AI client for embeddings (injected)
        """
        super().__init__(vector_db=vector_db, ai_client=ai_client)
        self.collection_name = "materials"
        
        logger.info("MaterialsService initialized with new architecture")
    
    async def initialize(self) -> None:
        """Initialize service and ensure collection exists.
        
        Raises:
            DatabaseError: If initialization fails
        """
        try:
            await self._ensure_collection_exists()
            logger.info(f"MaterialsService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MaterialsService: {e}")
            raise DatabaseError(
                message="Failed to initialize MaterialsService",
                details=str(e)
            )
    
    async def _ensure_collection_exists(self) -> None:
        """Ensure materials collection exists with proper configuration."""
        try:
            if not await self.vector_db.collection_exists(self.collection_name):
                logger.info(f"Creating collection: {self.collection_name}")
                await self.vector_db.create_collection(
                    collection_name=self.collection_name,
                    vector_size=1536,  # OpenAI text-embedding-3-small
                    distance_metric="cosine"
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.debug(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise DatabaseError(
                message=f"Failed to create collection {self.collection_name}",
                details=str(e)
            )
    
    async def create_material(self, material: MaterialCreate) -> Material:
        """Create a new material with semantic embedding.
        
        Args:
            material: Material data to create
            
        Returns:
            Created material with ID and embedding
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            await self._ensure_collection_exists()
            
            # Generate embedding for semantic search
            text_for_embedding = self._prepare_text_for_embedding(material)
            embedding = await self.get_embedding(text_for_embedding)
            
            # Create material ID and timestamps
            material_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Prepare vector data
            vector_data = {
                "id": material_id,
                "vector": embedding,
                "payload": {
                    "name": material.name,
                    "use_category": material.use_category,
                    "unit": material.unit,
                    "sku": material.sku,
                    "description": material.description,
                    "created_at": current_time.isoformat(),
                    "updated_at": current_time.isoformat()
                }
            }
            
            # Store in vector database
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[vector_data]
            )
            
            logger.info(f"Material created successfully: {material.name} (ID: {material_id})")
            
            return Material(
                id=material_id,
                name=material.name,
                use_category=material.use_category,
                unit=material.unit,
                sku=material.sku,
                description=material.description,
                embedding=embedding[:10],  # Truncate for response
                created_at=current_time,
                updated_at=current_time
            )
            
        except Exception as e:
            logger.error(f"Failed to create material '{material.name}': {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to create material '{material.name}'",
                details=str(e)
            )
    
    async def search_materials(self, query: str, limit: int = 10) -> List[Material]:
        """Search materials using semantic search with fallback.
        
        Implements fallback strategy: vector search → SQL LIKE search if 0 results
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching materials
            
        Raises:
            DatabaseError: If search fails
        """
        try:
            await self._ensure_collection_exists()
            
            # Primary: Vector semantic search
            logger.debug(f"Performing vector search for: '{query}'")
            vector_results = await self._search_vector(query, limit)
            
            if vector_results:
                logger.info(f"Vector search returned {len(vector_results)} results")
                return vector_results
            
            # Fallback: Text search (будет реализовано в этапе 3 с PostgreSQL)
            logger.info(f"Vector search returned 0 results, fallback not yet implemented")
            return []
            
        except Exception as e:
            logger.error(f"Failed to search materials for query '{query}': {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to search materials for query '{query}'",
                details=str(e)
            )
    
    async def _search_vector(self, query: str, limit: int) -> List[Material]:
        """Perform vector semantic search."""
        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Search in vector database
            results = await self.vector_db.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                filter_conditions=None
            )
            
            # Convert results to Material objects
            materials = []
            for result in results:
                material = self._convert_vector_result_to_material(result)
                if material:
                    materials.append(material)
            
            return materials
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise DatabaseError(
                message="Vector search failed",
                details=str(e)
            )
    
    def _prepare_text_for_embedding(self, material: MaterialCreate) -> str:
        """Prepare text for embedding generation."""
        return f"{material.name} {material.use_category} {material.sku or ''} {material.description or ''}"
    
    def _convert_vector_result_to_material(self, result: Dict[str, Any]) -> Optional[Material]:
        """Convert vector database result to Material object."""
        try:
            payload = result.get("payload", {})
            
            # Parse timestamps
            created_at = self._parse_timestamp(payload.get("created_at"))
            updated_at = self._parse_timestamp(payload.get("updated_at"))
            
            return Material(
                id=str(result.get("id")),
                name=payload.get("name"),
                use_category=payload.get("use_category", ""),
                unit=payload.get("unit"),
                sku=payload.get("sku"),
                description=payload.get("description"),
                embedding=result.get("vector", [])[:10] if result.get("vector") else None,
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            logger.error(f"Failed to convert vector result to material: {e}")
            return None
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string or return current time."""
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str)
            except:
                pass
        return datetime.utcnow()
    
    async def get_material(self, material_id: str) -> Optional[Material]:
        """Get material by ID.
        
        Args:
            material_id: Material identifier
            
        Returns:
            Material if found, None otherwise
            
        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            await self._ensure_collection_exists()
            
            result = await self.vector_db.get_by_id(
                collection_name=self.collection_name,
                vector_id=material_id
            )
            
            if not result:
                logger.debug(f"Material not found: {material_id}")
                return None
            
            return self._convert_vector_result_to_material(result)
            
        except Exception as e:
            logger.error(f"Failed to get material {material_id}: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to get material {material_id}",
                details=str(e)
            )
    
    async def update_material(self, material_id: str, material_update: MaterialUpdate) -> Optional[Material]:
        """Update existing material.
        
        Args:
            material_id: Material identifier
            material_update: Updated material data
            
        Returns:
            Updated material if found, None otherwise
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            # Get existing material
            existing = await self.get_material(material_id)
            if not existing:
                logger.debug(f"Material not found for update: {material_id}")
                return None
            
            # Update fields
            updated_data = existing.model_dump()
            for field, value in material_update.model_dump(exclude_unset=True).items():
                updated_data[field] = value
            
            # Generate new embedding if content changed
            material_create = MaterialCreate(**{
                k: v for k, v in updated_data.items() 
                if k in MaterialCreate.model_fields
            })
            text_for_embedding = self._prepare_text_for_embedding(material_create)
            embedding = await self.get_embedding(text_for_embedding)
            
            # Update timestamps
            current_time = datetime.utcnow()
            updated_data["updated_at"] = current_time
            
            # Prepare vector data
            vector_data = {
                "id": material_id,
                "vector": embedding,
                "payload": {
                    "name": updated_data["name"],
                    "use_category": updated_data["use_category"],
                    "unit": updated_data["unit"],
                    "sku": updated_data.get("sku"),
                    "description": updated_data.get("description"),
                    "created_at": updated_data["created_at"].isoformat(),
                    "updated_at": current_time.isoformat()
                }
            }
            
            # Update in vector database
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[vector_data]
            )
            
            logger.info(f"Material updated successfully: {material_id}")
            
            return Material(**updated_data)
            
        except Exception as e:
            logger.error(f"Failed to update material {material_id}: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to update material {material_id}",
                details=str(e)
            )
    
    async def delete_material(self, material_id: str) -> bool:
        """Delete material by ID.
        
        Args:
            material_id: Material identifier
            
        Returns:
            True if deleted successfully
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            await self.vector_db.delete(
                collection_name=self.collection_name,
                vector_id=material_id
            )
            
            logger.info(f"Material deleted successfully: {material_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete material {material_id}: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to delete material {material_id}",
                details=str(e)
            )
    
    async def get_materials(self, skip: int = 0, limit: int = 100, category: Optional[str] = None) -> List[Material]:
        """Get all materials with optional category filter.
        
        Args:
            skip: Number of materials to skip
            limit: Maximum number of materials to return
            category: Optional category filter
            
        Returns:
            List of materials
            
        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            await self._ensure_collection_exists()
            
            # Build filter conditions
            filter_conditions = None
            if category:
                filter_conditions = {"use_category": category}
            
            # Get materials from vector database
            # Note: This is a simplified implementation
            # In production, you might want to use scroll/pagination
            all_results = await self.vector_db.search(
                collection_name=self.collection_name,
                query_vector=[0.0] * 1536,  # Dummy vector for getting all
                limit=limit + skip,
                filter_conditions=filter_conditions
            )
            
            # Apply skip and convert to Material objects
            materials = []
            for i, result in enumerate(all_results):
                if i < skip:
                    continue
                if len(materials) >= limit:
                    break
                    
                material = self._convert_vector_result_to_material(result)
                if material:
                    materials.append(material)
            
            logger.info(f"Retrieved {len(materials)} materials (skip={skip}, limit={limit})")
            return materials
            
        except Exception as e:
            logger.error(f"Failed to get materials: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message="Failed to get materials",
                details=str(e)
            )
    
    async def create_materials_batch(self, materials: List[MaterialCreate], batch_size: int = 100) -> MaterialBatchResponse:
        """Create multiple materials in batches with optimized performance.
        
        Args:
            materials: List of materials to create
            batch_size: Size of processing batches
            
        Returns:
            Batch operation results
            
        Raises:
            DatabaseError: If batch creation fails
        """
        import time
        
        start_time = time.time()
        successful_creates = 0
        failed_creates = 0
        errors = []
        created_materials = []
        
        try:
            await self._ensure_collection_exists()
            
            logger.info(f"Starting batch creation of {len(materials)} materials")
            
            # Process materials in chunks
            for i in range(0, len(materials), batch_size):
                chunk = materials[i:i + batch_size]
                logger.debug(f"Processing batch {i//batch_size + 1}: {len(chunk)} materials")
                
                # Generate embeddings in parallel for the chunk
                embedding_tasks = []
                for material in chunk:
                    text_for_embedding = self._prepare_text_for_embedding(material)
                    embedding_tasks.append(self.get_embedding(text_for_embedding))
                
                try:
                    embeddings = await asyncio.gather(*embedding_tasks)
                except Exception as e:
                    logger.error(f"Error generating embeddings for batch: {e}")
                    failed_creates += len(chunk)
                    errors.append(f"Batch {i//batch_size + 1}: Failed to generate embeddings - {str(e)}")
                    continue
                
                # Prepare vectors for bulk insert
                vectors = []
                current_time = datetime.utcnow()
                
                for j, (material, embedding) in enumerate(zip(chunk, embeddings)):
                    try:
                        material_id = str(uuid.uuid4())
                        
                        vector_data = {
                            "id": material_id,
                            "vector": embedding,
                            "payload": {
                                "name": material.name,
                                "use_category": material.use_category,
                                "unit": material.unit,
                                "sku": material.sku,
                                "description": material.description,
                                "created_at": current_time.isoformat(),
                                "updated_at": current_time.isoformat()
                            }
                        }
                        vectors.append(vector_data)
                        
                        # Create Material object for response
                        created_material = Material(
                            id=material_id,
                            name=material.name,
                            use_category=material.use_category,
                            unit=material.unit,
                            sku=material.sku,
                            description=material.description,
                            embedding=embedding[:10],  # Truncate for response
                            created_at=current_time,
                            updated_at=current_time
                        )
                        created_materials.append(created_material)
                        
                    except Exception as e:
                        failed_creates += 1
                        errors.append(f"Material '{material.name}': {str(e)}")
                        continue
                
                # Bulk insert to vector database
                if vectors:
                    try:
                        await self.vector_db.batch_upsert(
                            collection_name=self.collection_name,
                            vectors=vectors,
                            batch_size=batch_size
                        )
                        successful_creates += len(vectors)
                        logger.info(f"Successfully inserted {len(vectors)} materials")
                    except Exception as e:
                        failed_creates += len(vectors)
                        errors.append(f"Batch {i//batch_size + 1}: Failed to insert to vector DB - {str(e)}")
                        # Remove from created materials if insert failed
                        created_materials = created_materials[:-len(vectors)]
                        continue
                
                # Small delay between batches to avoid overwhelming the system
                await asyncio.sleep(0.1)
            
            processing_time = time.time() - start_time
            success = failed_creates == 0
            
            logger.info(f"Batch creation completed: {successful_creates} success, {failed_creates} failed")
            
            return MaterialBatchResponse(
                success=success,
                total_processed=len(materials),
                successful_creates=successful_creates,
                failed_creates=failed_creates,
                processing_time_seconds=round(processing_time, 2),
                errors=errors,
                created_materials=created_materials
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Batch creation failed: {e}")
            return MaterialBatchResponse(
                success=False,
                total_processed=len(materials),
                successful_creates=successful_creates,
                failed_creates=len(materials) - successful_creates,
                processing_time_seconds=round(processing_time, 2),
                errors=[f"Batch processing failed: {str(e)}"] + errors,
                created_materials=created_materials
            )
    
    async def import_materials_from_json(self, 
                                       import_items: List[MaterialImportItem], 
                                       default_category: str = "Стройматериалы",
                                       default_unit: str = "шт",
                                       batch_size: int = 100) -> MaterialBatchResponse:
        """Import materials from JSON format with sku and name.
        
        Args:
            import_items: List of import items with sku and name
            default_category: Default category for materials
            default_unit: Default unit for materials
            batch_size: Batch processing size
            
        Returns:
            Batch import results
        """
        try:
            # Convert import items to MaterialCreate objects
            materials_to_create = []
            category_map = self._get_category_mapping()
            unit_map = self._get_unit_mapping()
            
            for item in import_items:
                # Try to infer category from name or use default
                category = self._infer_category(item.name, category_map) or default_category
                
                # Try to infer unit from name or use default  
                unit = self._infer_unit(item.name, unit_map) or default_unit
                
                material = MaterialCreate(
                    name=item.name,
                    use_category=category,
                    unit=unit,
                    sku=item.sku,
                    description=None
                )
                materials_to_create.append(material)
            
            logger.info(f"Importing {len(materials_to_create)} materials from JSON")
            
            # Use existing batch create method
            return await self.create_materials_batch(materials_to_create, batch_size)
            
        except Exception as e:
            logger.error(f"Failed to import materials from JSON: {e}")
            raise DatabaseError(
                message="Failed to import materials from JSON",
                details=str(e)
            )
    
    def _get_category_mapping(self) -> Dict[str, str]:
        """Get category mapping based on keywords."""
        return {
            "цемент": "Цемент",
            "бетон": "Бетон", 
            "кирпич": "Кирпич",
            "блок": "Блоки",
            "песок": "Песок",
            "щебень": "Щебень",
            "арматура": "Арматура",
            "металл": "Металлопрокат",
            "доска": "Пиломатериалы",
            "брус": "Пиломатериалы",
            "фанера": "Листовые материалы",
            "гипсокартон": "Листовые материалы",
            "плитка": "Плитка",
            "краска": "Лакокрасочные материалы",
            "эмаль": "Лакокрасочные материалы",
            "шпатлевка": "Сухие смеси",
            "штукатурка": "Сухие смеси",
            "утеплитель": "Теплоизоляция",
            "черепица": "Кровельные материалы",
            "профнастил": "Кровельные материалы",
            "труба": "Трубы и фитинги",
            "кабель": "Электротехника",
            "провод": "Электротехника",
            "окно": "Окна и двери",
            "дверь": "Окна и двери",
            "саморез": "Крепеж",
            "гвоздь": "Крепеж",
            "болт": "Крепеж"
        }
    
    def _get_unit_mapping(self) -> Dict[str, str]:
        """Get unit mapping based on keywords."""
        return {
            "цемент": "кг",
            "песок": "м³",
            "щебень": "м³",
            "бетон": "м³",
            "доска": "м³",
            "брус": "м³",
            "кирпич": "шт",
            "блок": "шт",
            "плитка": "м²",
            "краска": "кг",
            "эмаль": "кг",
            "лист": "м²",
            "рулон": "м²",
            "труба": "м",
            "кабель": "м",
            "провод": "м"
        }
    
    def _infer_category(self, name: str, category_map: Dict[str, str]) -> Optional[str]:
        """Infer category from material name."""
        name_lower = name.lower()
        for keyword, category in category_map.items():
            if keyword in name_lower:
                return category
        return None
    
    def _infer_unit(self, name: str, unit_map: Dict[str, str]) -> Optional[str]:
        """Infer unit from material name."""
        name_lower = name.lower()
        for keyword, unit in unit_map.items():
            if keyword in name_lower:
                return unit
        return None 