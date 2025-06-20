"""Pinecone Vector Database Adapter.

Адаптер для работы с Pinecone векторной базой данных с поддержкой всех обязательных методов.
"""

from core.monitoring.logger import get_logger
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from core.database.interfaces import IVectorDatabase
from core.database.exceptions import DatabaseError, ConnectionError, ConfigurationError

logger = get_logger(__name__)


class PineconeVectorDatabase(IVectorDatabase):
    """Pinecone vector database implementation.
    
    Provides vector storage and semantic search capabilities using Pinecone.
    Supports all required methods: search, upsert, delete, batch_upsert, get_by_id, health_check
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Pinecone database client.
        
        Args:
            config: Pinecone configuration dictionary
                Required keys: api_key, environment
                Optional keys: index_name, vector_size, timeout
        """
        self.config = config
        self.api_key = config.get("api_key")
        self.environment = config.get("environment")
        self.index_name = config.get("index_name", "materials")
        self.vector_size = config.get("vector_size", 1536)
        self.timeout = config.get("timeout", 30)
        
        self.pinecone = None
        self.index = None
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.api_key:
            raise ConfigurationError(
                config_key="PINECONE_API_KEY",
                message="Pinecone API key is required"
            )
        
        if not self.environment:
            raise ConfigurationError(
                config_key="PINECONE_ENVIRONMENT",
                message="Pinecone environment is required"
            )
    
    async def connect(self) -> None:
        """Connect to Pinecone database."""
        try:
            import pinecone
            
            # Initialize Pinecone
            pinecone.init(
                api_key=self.api_key,
                environment=self.environment
            )
            self.pinecone = pinecone
            
            # Create index if it doesn't exist
            if self.index_name not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.vector_size,
                    metric="cosine"
                )
                
                # Wait for index to be ready
                import time
                while self.index_name not in pinecone.list_indexes():
                    time.sleep(1)
            
            # Connect to index
            self.index = pinecone.Index(self.index_name)
            
            # Test connection
            stats = self.index.describe_index_stats()
            if stats is None:
                raise ConnectionError(
                    database_type="Pinecone",
                    message="Failed to connect to Pinecone index",
                    details="Unable to get index stats"
                )
            
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except ImportError:
            raise ConfigurationError(
                config_key="DEPENDENCIES",
                message="pinecone-client package is required. Install with: pip install pinecone-client"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            raise ConnectionError(
                database_type="Pinecone",
                message="Failed to connect to Pinecone",
                details=str(e)
            )
    
    async def disconnect(self) -> None:
        """Disconnect from Pinecone database."""
        if self.index:
            self.index = None
        if self.pinecone:
            self.pinecone = None
        logger.info("Disconnected from Pinecone")
    
    async def create_collection(self, name: str, vector_size: int, distance_metric: str = "cosine") -> bool:
        """Create a new collection (index) in Pinecone.
        
        Args:
            name: Index name
            vector_size: Dimension of vectors
            distance_metric: Distance calculation method ("cosine", "euclidean", "dotproduct")
            
        Returns:
            True if index created successfully
        """
        try:
            if not self.pinecone:
                await self.connect()
            
            # Check if index already exists
            if name in self.pinecone.list_indexes():
                logger.info(f"Pinecone index {name} already exists")
                return True
            
            # Create new index
            self.pinecone.create_index(
                name=name,
                dimension=vector_size,
                metric=distance_metric
            )
            
            # Wait for index to be ready
            import time
            while name not in self.pinecone.list_indexes():
                time.sleep(1)
            
            logger.info(f"Created Pinecone index: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Pinecone index {name}: {e}")
            raise DatabaseError(f"Failed to create Pinecone index: {e}")
    
    async def collection_exists(self, name: str) -> bool:
        """Check if collection (index) exists in Pinecone.
        
        Args:
            name: Index name
            
        Returns:
            True if index exists
        """
        try:
            if not self.pinecone:
                await self.connect()
            
            return name in self.pinecone.list_indexes()
            
        except Exception as e:
            logger.error(f"Failed to check if Pinecone index {name} exists: {e}")
            return False
    
    async def search(self, collection_name: str, query_vector: List[float], 
                    limit: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors in Pinecone.
        
        Args:
            collection_name: Collection name (not used in Pinecone, using default index)
            query_vector: Query vector for similarity search
            limit: Maximum number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results with vectors and metadata
        """
        try:
            if not self.index:
                await self.connect()
            
            # Build query parameters
            query_params = {
                "vector": query_vector,
                "top_k": limit,
                "include_metadata": True,
                "include_values": True
            }
            
            # Add filters if provided
            if filter_dict:
                query_params["filter"] = self._build_filter(filter_dict)
            
            # Execute query
            response = self.index.query(**query_params)
            
            # Process results
            results = []
            for match in response.get("matches", []):
                metadata = match.get("metadata", {})
                
                results.append({
                    "id": match.get("id", ""),
                    "vector": match.get("values", []),
                    "metadata": metadata,
                    "score": match.get("score", 0.0)
                })
            
            logger.info(f"Found {len(results)} results for vector search")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise DatabaseError(f"Vector search failed: {e}")
    
    def _build_filter(self, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Build Pinecone filter from filter dictionary."""
        pinecone_filter = {}
        
        for key, value in filter_dict.items():
            if key == "category":
                pinecone_filter["category"] = {"$eq": str(value)}
            elif key == "price_min":
                if "price" not in pinecone_filter:
                    pinecone_filter["price"] = {}
                pinecone_filter["price"]["$gte"] = float(value)
            elif key == "price_max":
                if "price" not in pinecone_filter:
                    pinecone_filter["price"] = {}
                pinecone_filter["price"]["$lte"] = float(value)
            elif key == "unit":
                pinecone_filter["unit"] = {"$eq": str(value)}
        
        return pinecone_filter
    
    async def upsert(self, collection_name: str, vectors: List[Dict[str, Any]], 
                    batch_size: int = 100) -> Dict[str, Any]:
        """Upsert vectors into Pinecone.
        
        Args:
            collection_name: Collection name (not used in Pinecone)
            vectors: List of vector dictionaries with id, vector, and metadata
            batch_size: Batch size for processing
            
        Returns:
            Operation results
        """
        try:
            if not self.index:
                await self.connect()
            
            total_vectors = len(vectors)
            upserted_count = 0
            failed_count = 0
            
            # Process in batches
            for i in range(0, total_vectors, batch_size):
                batch = vectors[i:i + batch_size]
                
                # Prepare batch data for Pinecone
                upsert_data = []
                for vector_data in batch:
                    try:
                        vector_id = vector_data.get("id", f"vec_{i}")
                        vector = vector_data.get("vector", [])
                        metadata = vector_data.get("metadata", {})
                        
                        # Ensure metadata is JSON serializable and within Pinecone limits
                        clean_metadata = self._clean_metadata(metadata)
                        
                        upsert_data.append({
                            "id": vector_id,
                            "values": vector,
                            "metadata": clean_metadata
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to prepare vector for upsert: {e}")
                        failed_count += 1
                
                # Upsert batch to Pinecone
                try:
                    response = self.index.upsert(vectors=upsert_data)
                    if response and response.get("upserted_count", 0) > 0:
                        upserted_count += response.get("upserted_count", 0)
                    else:
                        failed_count += len(upsert_data)
                        
                except Exception as e:
                    logger.error(f"Batch upsert failed: {e}")
                    failed_count += len(upsert_data)
            
            result = {
                "upserted_count": upserted_count,
                "failed_count": failed_count,
                "total_count": total_vectors
            }
            
            logger.info(f"Upserted {upserted_count}/{total_vectors} vectors to Pinecone")
            return result
            
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            raise DatabaseError(f"Batch upsert failed: {e}")
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata for Pinecone compatibility.
        
        Pinecone has limitations on metadata:
        - Values must be strings, numbers, booleans, or lists of strings
        - Total metadata size per vector must be under 40KB
        """
        clean_metadata = {}
        
        for key, value in metadata.items():
            try:
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif isinstance(value, list):
                    # Convert list items to strings if needed
                    clean_metadata[key] = [str(item) for item in value]
                elif isinstance(value, dict):
                    # Convert dict to JSON string
                    clean_metadata[key] = json.dumps(value)
                else:
                    # Convert other types to string
                    clean_metadata[key] = str(value)
                    
            except Exception as e:
                logger.warning(f"Failed to clean metadata key {key}: {e}")
                continue
        
        return clean_metadata
    
    async def delete(self, collection_name: str, vector_ids: List[str]) -> Dict[str, Any]:
        """Delete vectors from Pinecone.
        
        Args:
            collection_name: Collection name (not used in Pinecone)
            vector_ids: List of vector IDs to delete
            
        Returns:
            Deletion results
        """
        try:
            if not self.index:
                await self.connect()
            
            # Delete vectors
            response = self.index.delete(ids=vector_ids)
            
            # Pinecone doesn't return detailed deletion results
            # Assume success if no exception is raised
            result = {
                "deleted_count": len(vector_ids),
                "failed_count": 0,
                "total_count": len(vector_ids)
            }
            
            logger.info(f"Deleted {len(vector_ids)} vectors from Pinecone")
            return result
            
        except Exception as e:
            logger.error(f"Delete operation failed: {e}")
            raise DatabaseError(f"Delete operation failed: {e}")
    
    async def batch_upsert(self, collection_name: str, vectors: List[Dict[str, Any]], 
                          batch_size: int = 100) -> Dict[str, Any]:
        """Batch upsert vectors into Pinecone (same as upsert).
        
        Args:
            collection_name: Collection name
            vectors: List of vector dictionaries
            batch_size: Batch size for processing
            
        Returns:
            Operation results
        """
        return await self.upsert(collection_name, vectors, batch_size)
    
    async def get_by_id(self, collection_name: str, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector by ID from Pinecone.
        
        Args:
            collection_name: Collection name (not used in Pinecone)
            vector_id: Vector ID to retrieve
            
        Returns:
            Vector data or None if not found
        """
        try:
            if not self.index:
                await self.connect()
            
            # Fetch vector by ID
            response = self.index.fetch(ids=[vector_id])
            
            if response and "vectors" in response and vector_id in response["vectors"]:
                vector_data = response["vectors"][vector_id]
                
                return {
                    "id": vector_id,
                    "vector": vector_data.get("values", []),
                    "metadata": vector_data.get("metadata", {})
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vector by ID {vector_id}: {e}")
            return None
    
    async def update_vector(self, collection_name: str, vector_id: str, 
                           vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Update vector and metadata in Pinecone.
        
        Args:
            collection_name: Collection name
            vector_id: Vector ID to update
            vector: New vector data
            metadata: New metadata
            
        Returns:
            True if updated successfully
        """
        try:
            if not self.index:
                await self.connect()
            
            # Clean metadata
            clean_metadata = self._clean_metadata(metadata)
            
            # Upsert (update) the vector
            response = self.index.upsert(vectors=[{
                "id": vector_id,
                "values": vector,
                "metadata": clean_metadata
            }])
            
            success = response and response.get("upserted_count", 0) > 0
            
            if success:
                logger.info(f"Updated vector {vector_id} in Pinecone")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update vector {vector_id}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Pinecone database health.
        
        Returns:
            Health status information
        """
        try:
            if not self.index:
                await self.connect()
            
            # Get index statistics
            stats = self.index.describe_index_stats()
            
            # Check if we can perform basic operations
            is_healthy = stats is not None
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "database_type": "Pinecone",
                "environment": self.environment,
                "index_name": self.index_name,
                "vector_count": stats.get("total_vector_count", 0) if stats else 0,
                "index_fullness": stats.get("index_fullness", 0.0) if stats else 0.0,
                "dimension": self.vector_size,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "database_type": "Pinecone",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            } 