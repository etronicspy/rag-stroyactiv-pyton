"""Qdrant vector database adapter for both cloud and local instances.

Адаптер для Qdrant Vector Database с поддержкой облачной и локальной версий.
"""

from typing import List, Dict, Any, Optional
from core.logging import get_logger
import asyncio

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from core.database.interfaces import IVectorDatabase
from core.database.exceptions import ConnectionError, QueryError, DatabaseError
from core.repositories.interfaces import IBatchProcessingRepository
from datetime import datetime


logger = get_logger(__name__)


class QdrantVectorDatabase(IVectorDatabase, IBatchProcessingRepository):
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
    
    async def scroll_all(self, collection_name: str, with_payload: bool = True, with_vectors: bool = False) -> List[Dict[str, Any]]:
        """Get all records from collection using scroll method.
        
        Args:
            collection_name: Collection name
            with_payload: Include payload data
            with_vectors: Include vector data
            
        Returns:
            List of all records in collection
        """
        try:
            all_records = []
            next_page_offset = None
            
            while True:
                # Scroll through records
                records, next_page_offset = await asyncio.to_thread(
                    self.client.scroll,
                    collection_name=collection_name,
                    limit=100,  # Process in chunks of 100
                    offset=next_page_offset,
                    with_payload=with_payload,
                    with_vectors=with_vectors
                )
                
                # Convert to standard format
                for record in records:
                    result = {
                        "id": str(record.id),
                        "payload": record.payload if with_payload else {}
                    }
                    if with_vectors:
                        result["vector"] = record.vector
                    all_records.append(result)
                
                # Break if no more records
                if next_page_offset is None:
                    break
            
            return all_records
            
        except Exception as e:
            logger.error(f"Failed to scroll all records from {collection_name}: {e}")
            return []

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

    # === IBatchProcessingRepository methods (stubs, to be implemented) ===

    async def create_processing_records(self, request_id: str, materials: list) -> list:
        """Create initial records for batch processing in Qdrant.

        Args:
            request_id: Request identifier
            materials: List of materials to process (dicts with at least material_id)

        Returns:
            List of created material_ids
        """
        import uuid
        from datetime import datetime

        collection_name = "processing_records"
        vector_size = 1  # Minimal vector size for Qdrant
        now_iso = datetime.utcnow().isoformat()
        # 1. Ensure collection exists
        if not await self.collection_exists(collection_name):
            await self.create_collection(collection_name, vector_size)

        points = []
        material_ids = []
        for material in materials:
            material_id = material.get("material_id") or str(uuid.uuid4())
            # Генерируем UUID для точки в Qdrant
            point_id = str(uuid.uuid4())
            payload = {
                "request_id": request_id,
                "material_id": material_id,
                "status": "pending",
                "error": None,
                "created_at": now_iso,
                "updated_at": now_iso,
                "original_name": material.get("name", "Unknown Material"),
                "original_unit": material.get("unit", "шт"),
                "processed_at": None,
                "sku": None,
                "similarity_score": None,
                "normalized_color": None,
                "normalized_unit": None,
                "unit_coefficient": None
            }
            point = PointStruct(
                id=point_id,  # Используем UUID для точки
                vector=[0.0],
                payload=payload
            )
            points.append(point)
            material_ids.append(material_id)

        # 2. Upsert all points in batch
        await asyncio.to_thread(
            self.client.upsert,
            collection_name=collection_name,
            points=points
        )
        logger.info(f"Created {len(points)} processing records in Qdrant for request {request_id}")
        return material_ids

    async def update_processing_status(self, request_id: str, material_id: str, status: str, error: str = None, **kwargs) -> bool:
        collection_name = "processing_records"
        if not material_id or not isinstance(material_id, str):
            logger.error(f"Invalid material_id for update_processing_status: {material_id} ({type(material_id)})")
            raise ValueError("material_id must be a non-empty string")
        
        # 1. Получить все записи и найти нужную по material_id в payload
        all_records = await self.scroll_all(collection_name, with_payload=True, with_vectors=False)
        target_record = None
        for record in all_records:
            if record["payload"].get("material_id") == material_id:
                target_record = record
                break
        
        if not target_record:
            logger.error(f"Material {material_id} not found in processing records")
            return False
        
        payload = target_record["payload"]
        
        # 2. Verify request_id matches
        if payload.get("request_id") != request_id:
            return False
        
        # 3. Update payload with new status and additional fields
        now_iso = datetime.utcnow().isoformat()
        updated_payload = {
            **payload,
            "status": status,
            "error": error,
            "updated_at": now_iso
        }
        
        # Add additional fields if provided
        if kwargs.get('sku') is not None:
            updated_payload['sku'] = kwargs['sku']
        if kwargs.get('similarity_score') is not None:
            updated_payload['similarity_score'] = kwargs['similarity_score']
        if kwargs.get('normalized_color') is not None:
            updated_payload['normalized_color'] = kwargs['normalized_color']
        if kwargs.get('normalized_unit') is not None:
            updated_payload['normalized_unit'] = kwargs['normalized_unit']
        if kwargs.get('unit_coefficient') is not None:
            updated_payload['unit_coefficient'] = kwargs['unit_coefficient']
        if kwargs.get('processed_at') is not None:
            updated_payload['processed_at'] = kwargs['processed_at']
        elif status in ['completed', 'failed']:
            # Set processed_at for completed/failed status
            updated_payload['processed_at'] = now_iso
        
        # 4. Upsert updated record
        point = PointStruct(
            id=target_record["id"],  # Используем оригинальный ID точки
            vector=[0.0],  # Dummy vector
            payload=updated_payload
        )
        
        await asyncio.to_thread(
            self.client.upsert,
            collection_name,
            [point]
        )
        
        return True

    async def get_processing_progress(self, request_id: str):
        """Get processing progress for a batch request (Qdrant).

        Args:
            request_id: Request identifier

        Returns:
            Dict with progress info: total, completed, failed, pending (int)
        """
        collection_name = "processing_records"
        # 1. Получить все записи с данным request_id
        all_records = await self.scroll_all(collection_name, with_payload=True, with_vectors=False)
        batch_records = [rec for rec in all_records if rec["payload"].get("request_id") == request_id]
        total = len(batch_records)
        status_counts = {"completed": 0, "failed": 0, "pending": 0}
        for rec in batch_records:
            status = rec["payload"].get("status", "pending")
            if status in ("done", "completed"):  # поддержка разных вариантов
                status_counts["completed"] += 1
            elif status in ("error", "failed"):
                status_counts["failed"] += 1
            else:
                status_counts["pending"] += 1
        return {
            "total": total,
            "completed": status_counts["completed"],
            "failed": status_counts["failed"],
            "pending": status_counts["pending"]
        }

    async def get_processing_results(self, request_id: str, limit: int = None, offset: int = None) -> list:
        """Get processing results for a batch request (Qdrant).

        Args:
            request_id: Request identifier
            limit: Optional limit
            offset: Optional offset

        Returns:
            List of processing record payloads
        """
        collection_name = "processing_records"
        all_records = await self.scroll_all(collection_name, with_payload=True, with_vectors=False)
        batch_records = [rec["payload"] for rec in all_records if rec["payload"].get("request_id") == request_id]
        if offset is not None:
            batch_records = batch_records[offset:]
        if limit is not None:
            batch_records = batch_records[:limit]
        return batch_records

    async def get_processing_statistics(self):
        """Get overall processing statistics (Qdrant).

        Returns:
            Dict with statistics: total_batches, total_records, status_counts
        """
        collection_name = "processing_records"
        all_records = await self.scroll_all(collection_name, with_payload=True, with_vectors=False)
        total_records = len(all_records)
        request_ids = set()
        status_counts = {}
        for rec in all_records:
            payload = rec["payload"]
            request_id = payload.get("request_id")
            if request_id:
                request_ids.add(request_id)
            status = payload.get("status", "pending")
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        return {
            "total_batches": len(request_ids),
            "total_records": total_records,
            "status_counts": status_counts
        }

    async def cleanup_old_records(self, days_old: int = 30) -> int:
        """Cleanup old processing records (Qdrant).

        Args:
            days_old: Number of days to keep

        Returns:
            Number of deleted records
        """
        from datetime import datetime, timedelta
        collection_name = "processing_records"
        all_records = await self.scroll_all(collection_name, with_payload=True, with_vectors=False)
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days_old)
        to_delete = []
        for rec in all_records:
            payload = rec["payload"]
            created_at = payload.get("created_at")
            try:
                created_dt = datetime.fromisoformat(created_at)
                if created_dt < cutoff:
                    to_delete.append(rec["id"])
            except Exception:
                continue
        if to_delete:
            await asyncio.to_thread(
                self.client.delete,
                collection_name=collection_name,
                points_selector=to_delete
            )
        logger.info(f"Deleted {len(to_delete)} old processing records from Qdrant (older than {days_old} days)")
        return len(to_delete) 

    async def get_failed_materials_for_retry(self, max_retries=3, retry_delay_minutes=0):
        from datetime import datetime, timedelta
        collection_name = "processing_records"
        all_records = await self.scroll_all(collection_name, with_payload=True, with_vectors=False)
        now = datetime.utcnow()
        retry_materials = []
        for rec in all_records:
            payload = rec["payload"]
            material_id = rec["id"]  # ID записи из Qdrant
            status = payload.get("status")
            retries = payload.get("retries", 0)
            last_error_time = payload.get("updated_at")
            if status in ("failed", "pending") and retries < max_retries:
                if last_error_time:
                    last_error_dt = datetime.fromisoformat(last_error_time)
                    if now - last_error_dt > timedelta(minutes=retry_delay_minutes):
                        # Создаем словарь с id и всеми полями из payload
                        material_data = {
                            "id": material_id,
                            **payload
                        }
                        retry_materials.append(material_data)
                else:
                    # Создаем словарь с id и всеми полями из payload
                    material_data = {
                        "id": material_id,
                        **payload
                    }
                    retry_materials.append(material_data)
        return retry_materials

    async def increment_retry_count(self, material_id: str):
        collection_name = "processing_records"
        # Получить все записи и найти нужную по material_id в payload
        all_records = await self.scroll_all(collection_name, with_payload=True, with_vectors=False)
        target_record = None
        for record in all_records:
            if record["payload"].get("material_id") == material_id:
                target_record = record
                break
        
        if not target_record:
            return False
        
        payload = target_record["payload"]
        retries = payload.get("retries", 0) + 1
        payload["retries"] = retries
        from qdrant_client.models import PointStruct
        point = PointStruct(
            id=target_record["id"],  # Используем оригинальный ID точки
            vector=[0.0],
            payload=payload
        )
        await asyncio.to_thread(
            self.client.upsert,
            collection_name=collection_name,
            points=[point]
        )
        return True 