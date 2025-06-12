"""Hybrid Materials Repository using both Vector and Relational databases.

Гибридный репозиторий материалов, использующий векторную и реляционную БД для оптимального поиска.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import asyncio
import uuid

from core.repositories.base import BaseRepository
from core.database.interfaces import IVectorDatabase, IRelationalDatabase
from core.database.exceptions import DatabaseError, QueryError
from core.schemas.materials import Material, MaterialCreate, MaterialUpdate


logger = logging.getLogger(__name__)


class HybridMaterialsRepository(BaseRepository):
    """Hybrid repository using both vector and relational databases.
    
    Гибридный репозиторий, использующий векторную БД для семантического поиска
    и реляционную БД для структурированных запросов и аналитики.
    
    Search Strategy:
    1. Vector search for semantic similarity (primary)
    2. SQL hybrid search for text matching (fallback)
    3. Combined results with deduplication and scoring
    """
    
    def __init__(
        self, 
        vector_db: IVectorDatabase,
        relational_db: IRelationalDatabase,
        ai_client=None
    ):
        """Initialize hybrid repository.
        
        Args:
            vector_db: Vector database client (Qdrant)
            relational_db: Relational database client (PostgreSQL)
            ai_client: AI client for embeddings
            
        Raises:
            DatabaseError: If initialization fails
        """
        super().__init__()
        self.vector_db = vector_db
        self.relational_db = relational_db
        self.ai_client = ai_client
        self.collection_name = "materials"
        
        logger.info("Hybrid Materials Repository initialized")
    
    async def create_material(self, material: MaterialCreate) -> Material:
        """Create material in both vector and relational databases.
        
        Args:
            material: Material data to create
            
        Returns:
            Created material with ID and embedding
            
        Raises:
            DatabaseError: If creation fails in either database
        """
        try:
            # Generate embedding for semantic search
            text_for_embedding = self._prepare_text_for_embedding(material)
            embedding = await self.get_embedding(text_for_embedding)
            
            # Create material ID and timestamps
            material_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Prepare material data
            material_data = {
                "id": material_id,
                "name": material.name,
                "use_category": material.use_category,
                "unit": material.unit,
                "sku": material.sku,
                "description": material.description,
                "embedding": embedding,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            # Store in both databases concurrently
            vector_task = self._create_in_vector_db(material_data)
            relational_task = self._create_in_relational_db(material_data)
            
            # Wait for both operations to complete
            await asyncio.gather(vector_task, relational_task)
            
            logger.info(f"Material created in both databases: {material.name} (ID: {material_id})")
            
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
            logger.error(f"Failed to create material in hybrid repository: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to create material '{material.name}'",
                details=str(e)
            )
    
    async def search_materials_hybrid(
        self, 
        query: str, 
        limit: int = 10,
        vector_weight: float = 0.7,
        sql_weight: float = 0.3,
        min_vector_score: float = 0.6,
        min_sql_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Advanced hybrid search combining vector and SQL approaches.
        
        Продвинутый гибридный поиск, объединяющий векторный и SQL подходы.
        
        Args:
            query: Search query
            limit: Maximum results
            vector_weight: Weight for vector search results (0.0-1.0)
            sql_weight: Weight for SQL search results (0.0-1.0)
            min_vector_score: Minimum vector similarity score
            min_sql_similarity: Minimum SQL similarity threshold
            
        Returns:
            Combined and ranked search results
            
        Raises:
            DatabaseError: If search fails
        """
        try:
            # Run both searches concurrently
            vector_task = self._search_vector_db(query, limit * 2, min_vector_score)
            sql_task = self._search_relational_db(query, limit * 2, min_sql_similarity)
            
            vector_results, sql_results = await asyncio.gather(
                vector_task, sql_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(vector_results, Exception):
                logger.warning(f"Vector search failed: {vector_results}")
                vector_results = []
            
            if isinstance(sql_results, Exception):
                logger.warning(f"SQL search failed: {sql_results}")
                sql_results = []
            
            # Combine and rank results
            combined_results = self._combine_search_results(
                vector_results, sql_results, vector_weight, sql_weight
            )
            
            # Deduplicate and limit results
            final_results = self._deduplicate_results(combined_results)[:limit]
            
            logger.info(
                f"Hybrid search completed: {len(vector_results)} vector + "
                f"{len(sql_results)} SQL = {len(final_results)} final results"
            )
            
            return final_results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise DatabaseError(
                message="Hybrid search failed",
                details=str(e)
            )
    
    async def search_materials(self, query: str, limit: int = 10) -> List[Material]:
        """Search materials with fallback strategy.
        
        Implements fallback strategy: vector search → SQL search if 0 results
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching materials
            
        Raises:
            DatabaseError: If search fails
        """
        try:
            # Try vector search first
            vector_results = await self._search_vector_db(query, limit)
            
            if vector_results:
                # Convert to Material objects
                materials = [self._dict_to_material(result) for result in vector_results]
                logger.info(f"Vector search found {len(materials)} results")
                return materials
            
            # Fallback to SQL search
            logger.info("Vector search returned 0 results, falling back to SQL search")
            sql_results = await self._search_relational_db(query, limit)
            
            if sql_results:
                materials = [self._dict_to_material(result) for result in sql_results]
                logger.info(f"SQL fallback search found {len(materials)} results")
                return materials
            
            logger.info("Both vector and SQL searches returned 0 results")
            return []
            
        except Exception as e:
            logger.error(f"Material search failed: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message="Material search failed",
                details=str(e)
            )
    
    async def get_material_by_id(self, material_id: str) -> Optional[Material]:
        """Get material by ID from relational database (faster for exact lookups).
        
        Args:
            material_id: Material ID
            
        Returns:
            Material if found, None otherwise
            
        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            # Use SQL for exact ID lookups (faster than vector search)
            results = await self.relational_db.execute_query(
                "SELECT * FROM materials WHERE id = :id",
                {"id": material_id}
            )
            
            if not results:
                return None
            
            return self._dict_to_material(results[0])
            
        except Exception as e:
            logger.error(f"Failed to get material by ID {material_id}: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to get material by ID {material_id}",
                details=str(e)
            )
    
    async def get_materials(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        category: Optional[str] = None
    ) -> List[Material]:
        """Get materials with pagination using relational database.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            category: Filter by category
            
        Returns:
            List of materials
            
        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            # Use PostgreSQL for structured queries
            results = await self.relational_db.get_materials(skip, limit, category)
            return [self._dict_to_material(result) for result in results]
            
        except Exception as e:
            logger.error(f"Failed to get materials: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message="Failed to get materials",
                details=str(e)
            )
    
    async def update_material(self, material_id: str, material_update: MaterialUpdate) -> Optional[Material]:
        """Update material in both databases.
        
        Args:
            material_id: Material ID to update
            material_update: Updated material data
            
        Returns:
            Updated material if found, None otherwise
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            # Get current material
            current_material = await self.get_material_by_id(material_id)
            if not current_material:
                return None
            
            # Prepare update data
            update_data = material_update.model_dump(exclude_unset=True)
            if not update_data:
                return current_material
            
            # Update embedding if text fields changed
            text_fields = ['name', 'description', 'use_category']
            if any(field in update_data for field in text_fields):
                # Create temporary material for embedding
                temp_material = MaterialCreate(
                    name=update_data.get('name', current_material.name),
                    use_category=update_data.get('use_category', current_material.use_category),
                    unit=update_data.get('unit', current_material.unit),
                    sku=update_data.get('sku', current_material.sku),
                    description=update_data.get('description', current_material.description)
                )
                
                text_for_embedding = self._prepare_text_for_embedding(temp_material)
                embedding = await self.get_embedding(text_for_embedding)
                update_data['embedding'] = embedding
            
            update_data['updated_at'] = datetime.utcnow()
            
            # Update in both databases concurrently
            vector_task = self._update_in_vector_db(material_id, update_data)
            relational_task = self._update_in_relational_db(material_id, update_data)
            
            await asyncio.gather(vector_task, relational_task)
            
            # Return updated material
            return await self.get_material_by_id(material_id)
            
        except Exception as e:
            logger.error(f"Failed to update material {material_id}: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to update material {material_id}",
                details=str(e)
            )
    
    async def delete_material(self, material_id: str) -> bool:
        """Delete material from both databases.
        
        Args:
            material_id: Material ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            # Check if material exists
            material = await self.get_material_by_id(material_id)
            if not material:
                return False
            
            # Delete from both databases concurrently
            vector_task = self._delete_from_vector_db(material_id)
            relational_task = self._delete_from_relational_db(material_id)
            
            await asyncio.gather(vector_task, relational_task)
            
            logger.info(f"Material deleted from both databases: {material_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete material {material_id}: {e}")
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(
                message=f"Failed to delete material {material_id}",
                details=str(e)
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of both databases.
        
        Returns:
            Combined health status
        """
        try:
            # Check both databases concurrently
            vector_task = self.vector_db.health_check()
            relational_task = self.relational_db.health_check()
            
            vector_health, relational_health = await asyncio.gather(
                vector_task, relational_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(vector_health, Exception):
                vector_health = {
                    "status": "unhealthy",
                    "error": str(vector_health)
                }
            
            if isinstance(relational_health, Exception):
                relational_health = {
                    "status": "unhealthy", 
                    "error": str(relational_health)
                }
            
            # Determine overall status
            overall_status = "healthy"
            if (vector_health.get("status") != "healthy" or 
                relational_health.get("status") != "healthy"):
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "repository_type": "hybrid",
                "vector_database": vector_health,
                "relational_database": relational_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "repository_type": "hybrid",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # === Private helper methods ===
    
    async def _create_in_vector_db(self, material_data: Dict[str, Any]) -> None:
        """Create material in vector database."""
        vector_data = {
            "id": material_data["id"],
            "vector": material_data["embedding"],
            "payload": {
                "name": material_data["name"],
                "use_category": material_data["use_category"],
                "unit": material_data["unit"],
                "sku": material_data["sku"],
                "description": material_data["description"],
                "created_at": material_data["created_at"].isoformat(),
                "updated_at": material_data["updated_at"].isoformat()
            }
        }
        
        await self.vector_db.upsert(
            collection_name=self.collection_name,
            vectors=[vector_data]
        )
    
    async def _create_in_relational_db(self, material_data: Dict[str, Any]) -> None:
        """Create material in relational database."""
        await self.relational_db.create_material(material_data)
    
    async def _search_vector_db(
        self, 
        query: str, 
        limit: int, 
        min_score: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Search in vector database."""
        # Generate query embedding
        query_embedding = await self.get_embedding(query)
        
        # Search in vector database
        results = await self.vector_db.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=min_score
        )
        
        # Convert to standard format
        materials = []
        for result in results:
            material_data = {
                'id': str(result.id),
                'name': result.payload.get('name'),
                'use_category': result.payload.get('use_category'),
                'unit': result.payload.get('unit'),
                'sku': result.payload.get('sku'),
                'description': result.payload.get('description'),
                'embedding': result.vector,
                'created_at': datetime.fromisoformat(result.payload.get('created_at')),
                'updated_at': datetime.fromisoformat(result.payload.get('updated_at')),
                'vector_score': result.score,
                'search_type': 'vector'
            }
            materials.append(material_data)
        
        return materials
    
    async def _search_relational_db(
        self, 
        query: str, 
        limit: int, 
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search in relational database using hybrid approach."""
        results = await self.relational_db.search_materials_hybrid(
            query, limit, min_similarity
        )
        
        # Add search type marker
        for result in results:
            result['search_type'] = 'sql'
        
        return results
    
    def _combine_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        sql_results: List[Dict[str, Any]],
        vector_weight: float,
        sql_weight: float
    ) -> List[Dict[str, Any]]:
        """Combine and score results from both search methods."""
        combined = []
        
        # Add vector results with weighted scores
        for result in vector_results:
            result['combined_score'] = result.get('vector_score', 0.0) * vector_weight
            combined.append(result)
        
        # Add SQL results with weighted scores
        for result in sql_results:
            sql_score = result.get('similarity_score', 0.0)
            result['combined_score'] = sql_score * sql_weight
            combined.append(result)
        
        # Sort by combined score
        combined.sort(key=lambda x: x.get('combined_score', 0.0), reverse=True)
        
        return combined
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results, keeping the highest scored version."""
        seen_ids = set()
        deduplicated = []
        
        for result in results:
            material_id = result.get('id')
            if material_id and material_id not in seen_ids:
                seen_ids.add(material_id)
                deduplicated.append(result)
        
        return deduplicated
    
    async def _update_in_vector_db(self, material_id: str, update_data: Dict[str, Any]) -> None:
        """Update material in vector database."""
        # Get current vector data
        current_results = await self.vector_db.get_by_id(self.collection_name, material_id)
        if not current_results:
            return
        
        current_payload = current_results[0].payload
        
        # Update payload
        for key, value in update_data.items():
            if key == 'updated_at':
                current_payload[key] = value.isoformat()
            elif key != 'embedding':
                current_payload[key] = value
        
        # Prepare vector data
        vector_data = {
            "id": material_id,
            "vector": update_data.get('embedding', current_results[0].vector),
            "payload": current_payload
        }
        
        await self.vector_db.upsert(
            collection_name=self.collection_name,
            vectors=[vector_data]
        )
    
    async def _update_in_relational_db(self, material_id: str, update_data: Dict[str, Any]) -> None:
        """Update material in relational database."""
        # Build SQL update query
        set_clauses = []
        params = {"id": material_id}
        
        for key, value in update_data.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        if set_clauses:
            query = f"UPDATE materials SET {', '.join(set_clauses)} WHERE id = :id"
            await self.relational_db.execute_command(query, params)
    
    async def _delete_from_vector_db(self, material_id: str) -> None:
        """Delete material from vector database."""
        await self.vector_db.delete(
            collection_name=self.collection_name,
            point_ids=[material_id]
        )
    
    async def _delete_from_relational_db(self, material_id: str) -> None:
        """Delete material from relational database."""
        await self.relational_db.execute_command(
            "DELETE FROM materials WHERE id = :id",
            {"id": material_id}
        )
    
    def _dict_to_material(self, data: Dict[str, Any]) -> Material:
        """Convert dictionary to Material object."""
        return Material(
            id=data.get('id'),
            name=data.get('name'),
            use_category=data.get('use_category'),
            unit=data.get('unit'),
            sku=data.get('sku'),
            description=data.get('description'),
            embedding=data.get('embedding'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def _prepare_text_for_embedding(self, material: MaterialCreate) -> str:
        """Prepare text for embedding generation."""
        return f"{material.name} {material.use_category} {material.sku or ''} {material.description or ''}" 