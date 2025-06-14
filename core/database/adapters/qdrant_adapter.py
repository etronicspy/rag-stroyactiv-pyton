"""Qdrant vector database adapter implementation.

Адаптер для работы с Qdrant векторной БД.
"""

from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from core.database.interfaces import IVectorDatabase
from core.database.exceptions import ConnectionError, QueryError, DatabaseError


logger = logging.getLogger(__name__)


class QdrantVectorDatabase(IVectorDatabase):
    """Qdrant vector database adapter.
    
    Адаптер для работы с Qdrant, реализующий все обязательные методы:
    search, upsert, delete, batch_upsert, get_by_id
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Qdrant client.
        
        Args:
            config: Qdrant configuration dictionary
            
        Raises:
            ConnectionError: If connection fails
        """
        try:
            self.config = config
            self.client = QdrantClient(
                url=config["url"],
                api_key=config.get("api_key"),
                timeout=config.get("timeout", 30)
            )
            self.collection_name = config.get("collection_name", "materials")
            self.vector_size = config.get("vector_size", 1536)
            self.distance = getattr(Distance, config.get("distance", "COSINE").upper())
            
            logger.info(f"Qdrant client initialized for collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise ConnectionError(
                database_type="Qdrant",
                message="Failed to connect to Qdrant",
                details=str(e)
            )
    
    async def create_collection(self, name: str, vector_size: int, distance_metric: str = "cosine") -> bool:
        """Create a new collection for storing vectors.
        
        Args:
            name: Collection name
            vector_size: Dimension of vectors
            distance_metric: Distance calculation method
            
        Returns:
            True if collection created successfully
            
        Raises:
            DatabaseError: If collection creation fails
        """
        try:
            distance_map = {
                "cosine": Distance.COSINE,
                "euclidean": Distance.EUCLID,
                "dot": Distance.DOT
            }
            
            distance = distance_map.get(distance_metric.lower(), Distance.COSINE)
            
            await asyncio.to_thread(
                self.client.create_collection,
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            logger.info(f"Created Qdrant collection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            raise DatabaseError(f"Failed to create collection {name}", details=str(e))
    
    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists.
        
        Args:
            name: Collection name
            
        Returns:
            True if collection exists
        """
        try:
            collections = await asyncio.to_thread(self.client.get_collections)
            collection_names = [c.name for c in collections.collections]
            return name in collection_names
            
        except Exception as e:
            logger.error(f"Failed to check collection existence {name}: {e}")
            return False
    
    async def upsert(self, collection_name: str, vectors: List[Dict[str, Any]]) -> bool:
        """Insert or update vectors with metadata in collection.
        
        Args:
            collection_name: Target collection
            vectors: List of vector objects with id, vector, and payload
            
        Returns:
            True if upsert successful
            
        Raises:
            DatabaseError: If upsert operation fails
        """
        try:
            # Ensure collection exists
            if not await self.collection_exists(collection_name):
                await self.create_collection(collection_name, self.vector_size)
            
            points = []
            for vector_data in vectors:
                point = PointStruct(
                    id=vector_data["id"],
                    vector=vector_data["vector"],
                    payload=vector_data.get("payload", {})
                )
                points.append(point)
            
            # Use asyncio.to_thread to avoid blocking the event loop
            operation_info = await asyncio.to_thread(
                self.client.upsert,
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Upserted {len(points)} vectors to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors to {collection_name}: {e}")
            raise DatabaseError(f"Failed to upsert vectors", details=str(e))
    
    async def search(self, collection_name: str, query_vector: List[float], 
                    limit: int = 10, filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            collection_name: Collection to search in
            query_vector: Query vector
            limit: Maximum number of results
            filter_conditions: Optional filtering conditions
            
        Returns:
            List of search results with scores and metadata
            
        Raises:
            QueryError: If search operation fails
        """
        try:
            search_result = await asyncio.to_thread(
                self.client.search,
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_conditions
            )
            
            results = []
            for scored_point in search_result:
                result = {
                    "id": str(scored_point.id),
                    "score": scored_point.score,
                    "payload": scored_point.payload,
                    "vector": scored_point.vector
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} results in {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            raise QueryError(f"Search failed in {collection_name}", details=str(e))
    
    async def get_by_id(self, collection_name: str, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector by ID.
        
        Args:
            collection_name: Collection name
            vector_id: Vector ID
            
        Returns:
            Vector data or None if not found
        """
        try:
            results = await asyncio.to_thread(
                self.client.retrieve,
                collection_name=collection_name,
                ids=[vector_id],
                with_vectors=True
            )
            
            if not results:
                return None
            
            result = results[0]
            return {
                "id": str(result.id),
                "vector": result.vector,
                "payload": result.payload
            }
            
        except Exception as e:
            logger.error(f"Failed to get vector {vector_id} from {collection_name}: {e}")
            return None
    
    async def update_vector(self, collection_name: str, vector_id: str, 
                          vector: Optional[List[float]] = None, 
                          payload: Optional[Dict[str, Any]] = None) -> bool:
        """Update vector and/or its metadata.
        
        Args:
            collection_name: Collection name
            vector_id: Vector ID
            vector: New vector values
            payload: New metadata
            
        Returns:
            True if update successful
        """
        try:
            # Get existing data if partial update
            existing = await self.get_by_id(collection_name, vector_id)
            if not existing:
                return False
            
            # Prepare update data
            update_vector = vector or existing["vector"]
            update_payload = payload or existing["payload"]
            
            # Use upsert for update
            await self.upsert(collection_name, [{
                "id": vector_id,
                "vector": update_vector,
                "payload": update_payload
            }])
            
            logger.info(f"Updated vector {vector_id} in {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update vector {vector_id} in {collection_name}: {e}")
            return False
    
    async def delete(self, collection_name: str, vector_id: str) -> bool:
        """Delete vector by ID.
        
        Args:
            collection_name: Collection name
            vector_id: Vector ID
            
        Returns:
            True if deletion successful
        """
        try:
            operation_info = await asyncio.to_thread(
                self.client.delete,
                collection_name=collection_name,
                points_selector=[vector_id]
            )
            
            logger.info(f"Deleted vector {vector_id} from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vector {vector_id} from {collection_name}: {e}")
            return False
    
    async def batch_upsert(self, collection_name: str, vectors: List[Dict[str, Any]], 
                          batch_size: int = 100) -> bool:
        """Insert or update multiple vectors in batches.
        
        Args:
            collection_name: Target collection
            vectors: List of vector objects with id, vector, and payload
            batch_size: Size of processing batches
            
        Returns:
            True if batch upsert successful
        """
        try:
            # Process in batches
            total_processed = 0
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                await self.upsert(collection_name, batch)
                total_processed += len(batch)
                logger.info(f"Processed batch {i//batch_size + 1}, total: {total_processed}/{len(vectors)}")
            
            logger.info(f"Batch upsert completed: {total_processed} vectors to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed batch upsert to {collection_name}: {e}")
            raise DatabaseError(f"Batch upsert failed", details=str(e))
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health status.
        
        Returns:
            Health status information
        """
        try:
            # Simple connection test - get collections list
            collections = await asyncio.to_thread(self.client.get_collections)
            collections_count = len(collections.collections) if collections and hasattr(collections, 'collections') else 0
            
            # Check if default collection exists (without detailed info to avoid parsing errors)
            collection_exists = await self.collection_exists(self.collection_name)
            
            # Get basic collection stats if exists
            vectors_count = 0
            if collection_exists:
                try:
                    collection_info = await asyncio.to_thread(self.client.get_collection, self.collection_name)
                    # Safely extract vectors count without relying on strict parsing
                    if hasattr(collection_info, 'vectors_count'):
                        vectors_count = collection_info.vectors_count
                    elif hasattr(collection_info, 'result') and hasattr(collection_info.result, 'vectors_count'):
                        vectors_count = collection_info.result.vectors_count
                except:
                    # If we can't get collection info, that's okay - connection still works
                    pass
            
            return {
                "status": "healthy",
                "details": {
                    "database_type": "Qdrant",
                    "url": self.config["url"],
                    "collections_count": collections_count,
                    "default_collection": self.collection_name,
                    "default_collection_exists": collection_exists,
                    "vectors_count": vectors_count,
                    "connection_test": "passed"
                }
            }
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 