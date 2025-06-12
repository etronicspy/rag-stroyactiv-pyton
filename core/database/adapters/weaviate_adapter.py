"""Weaviate Vector Database Adapter.

Адаптер для работы с Weaviate векторной базой данных с поддержкой всех обязательных методов.
"""

import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from core.database.interfaces import IVectorDatabase
from core.database.exceptions import DatabaseError, ConnectionError, ConfigurationError

logger = logging.getLogger(__name__)


class WeaviateVectorDatabase(IVectorDatabase):
    """Weaviate vector database implementation.
    
    Provides vector storage and semantic search capabilities using Weaviate.
    Supports all required methods: search, upsert, delete, batch_upsert, get_by_id, health_check
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Weaviate database client.
        
        Args:
            config: Weaviate configuration dictionary
                Required keys: url, api_key
                Optional keys: timeout, class_name, vector_size
        """
        self.config = config
        self.url = config.get("url")
        self.api_key = config.get("api_key")
        self.class_name = config.get("class_name", "Materials")
        self.vector_size = config.get("vector_size", 1536)
        self.timeout = config.get("timeout", 30)
        
        self.client = None
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.url:
            raise ConfigurationError(
                config_key="WEAVIATE_URL",
                message="Weaviate URL is required"
            )
        
        if not self.api_key:
            raise ConfigurationError(
                config_key="WEAVIATE_API_KEY", 
                message="Weaviate API key is required"
            )
    
    async def connect(self) -> None:
        """Connect to Weaviate database."""
        try:
            import weaviate
            
            # Create client with authentication
            auth_config = weaviate.AuthApiKey(api_key=self.api_key)
            
            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config,
                timeout_config=(5, self.timeout)
            )
            
            # Test connection
            if not self.client.is_ready():
                raise ConnectionError(
                    database_type="Weaviate",
                    message="Failed to connect to Weaviate",
                    details="Client is not ready"
                )
            
            # Create schema if it doesn't exist
            await self._ensure_schema()
            
            logger.info(f"Connected to Weaviate at {self.url}")
            
        except ImportError:
            raise ConfigurationError(
                config_key="DEPENDENCIES",
                message="weaviate-client package is required. Install with: pip install weaviate-client"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise ConnectionError(
                database_type="Weaviate",
                message="Failed to connect to Weaviate",
                details=str(e)
            )
    
    async def disconnect(self) -> None:
        """Disconnect from Weaviate database."""
        if self.client:
            self.client = None
            logger.info("Disconnected from Weaviate")
    
    async def _ensure_schema(self) -> None:
        """Ensure the Materials schema exists in Weaviate."""
        try:
            # Check if class exists
            existing_schema = self.client.schema.get()
            class_exists = any(
                cls["class"] == self.class_name 
                for cls in existing_schema.get("classes", [])
            )
            
            if not class_exists:
                # Create the Materials class schema
                materials_class = {
                    "class": self.class_name,
                    "description": "Construction materials with semantic search",
                    "vectorizer": "none",  # We'll provide our own vectors
                    "properties": [
                        {
                            "name": "material_id",
                            "dataType": ["text"],
                            "description": "Unique material identifier"
                        },
                        {
                            "name": "name",
                            "dataType": ["text"],
                            "description": "Material name"
                        },
                        {
                            "name": "description",
                            "dataType": ["text"],
                            "description": "Material description"
                        },
                        {
                            "name": "category",
                            "dataType": ["text"],
                            "description": "Material category"
                        },
                        {
                            "name": "unit",
                            "dataType": ["text"],
                            "description": "Unit of measurement"
                        },
                        {
                            "name": "price",
                            "dataType": ["number"],
                            "description": "Material price"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["text"],
                            "description": "Additional metadata (JSON string)"
                        },
                        {
                            "name": "created_at",
                            "dataType": ["date"],
                            "description": "Creation timestamp"
                        }
                    ]
                }
                
                self.client.schema.create_class(materials_class)
                logger.info(f"Created Weaviate class: {self.class_name}")
            
        except Exception as e:
            logger.error(f"Failed to ensure schema: {e}")
            raise DatabaseError(f"Schema creation failed: {e}")
    
    async def search(self, collection_name: str, query_vector: List[float], 
                    limit: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors in Weaviate.
        
        Args:
            collection_name: Collection name (mapped to Weaviate class)
            query_vector: Query vector for similarity search
            limit: Maximum number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results with vectors and metadata
        """
        try:
            if not self.client:
                await self.connect()
            
            # Build the query
            query = (
                self.client.query
                .get(self.class_name, ["material_id", "name", "description", "category", "unit", "price", "metadata", "created_at"])
                .with_near_vector({
                    "vector": query_vector,
                    "certainty": 0.7  # Minimum similarity threshold
                })
                .with_limit(limit)
                .with_additional(["certainty", "id"])
            )
            
            # Add filters if provided
            if filter_dict:
                where_filter = self._build_where_filter(filter_dict)
                if where_filter:
                    query = query.with_where(where_filter)
            
            # Execute query
            result = query.do()
            
            # Process results
            results = []
            if "data" in result and "Get" in result["data"] and self.class_name in result["data"]["Get"]:
                for item in result["data"]["Get"][self.class_name]:
                    # Extract metadata
                    metadata = {
                        "id": item["_additional"]["id"],
                        "score": item["_additional"]["certainty"],
                        "material_id": item.get("material_id", ""),
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "category": item.get("category", ""),
                        "unit": item.get("unit", ""),
                        "price": item.get("price", 0.0),
                        "metadata": item.get("metadata", "{}"),
                        "created_at": item.get("created_at", "")
                    }
                    
                    results.append({
                        "id": item["_additional"]["id"],
                        "vector": query_vector,  # Weaviate doesn't return vectors by default
                        "metadata": metadata,
                        "score": item["_additional"]["certainty"]
                    })
            
            logger.info(f"Found {len(results)} results for vector search")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise DatabaseError(f"Vector search failed: {e}")
    
    def _build_where_filter(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build Weaviate where filter from filter dictionary."""
        if not filter_dict:
            return None
        
        conditions = []
        for key, value in filter_dict.items():
            if key == "category":
                conditions.append({
                    "path": ["category"],
                    "operator": "Equal",
                    "valueString": str(value)
                })
            elif key == "price_min":
                conditions.append({
                    "path": ["price"],
                    "operator": "GreaterThanEqual",
                    "valueNumber": float(value)
                })
            elif key == "price_max":
                conditions.append({
                    "path": ["price"],
                    "operator": "LessThanEqual", 
                    "valueNumber": float(value)
                })
        
        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return {
                "operator": "And",
                "operands": conditions
            }
        
        return None
    
    async def upsert(self, collection_name: str, vectors: List[Dict[str, Any]], 
                    batch_size: int = 100) -> Dict[str, Any]:
        """Upsert vectors into Weaviate.
        
        Args:
            collection_name: Collection name (mapped to Weaviate class)
            vectors: List of vector dictionaries with id, vector, and metadata
            batch_size: Batch size for processing
            
        Returns:
            Operation results
        """
        try:
            if not self.client:
                await self.connect()
            
            total_vectors = len(vectors)
            upserted_count = 0
            failed_count = 0
            
            # Process in batches
            for i in range(0, total_vectors, batch_size):
                batch = vectors[i:i + batch_size]
                
                with self.client.batch as batch_client:
                    batch_client.batch_size = len(batch)
                    
                    for vector_data in batch:
                        try:
                            # Prepare object data
                            vector_id = vector_data.get("id", str(uuid.uuid4()))
                            vector = vector_data.get("vector", [])
                            metadata = vector_data.get("metadata", {})
                            
                            # Prepare properties for Weaviate
                            properties = {
                                "material_id": metadata.get("material_id", vector_id),
                                "name": metadata.get("name", ""),
                                "description": metadata.get("description", ""),
                                "category": metadata.get("category", ""),
                                "unit": metadata.get("unit", ""),
                                "price": float(metadata.get("price", 0.0)),
                                "metadata": str(metadata.get("metadata", "{}")),
                                "created_at": metadata.get("created_at", datetime.utcnow().isoformat())
                            }
                            
                            # Check if object exists (for update)
                            existing = None
                            try:
                                existing = self.client.data_object.get_by_id(
                                    vector_id,
                                    class_name=self.class_name
                                )
                            except:
                                pass  # Object doesn't exist, will create new
                            
                            if existing:
                                # Update existing object
                                self.client.data_object.update(
                                    uuid=vector_id,
                                    class_name=self.class_name,
                                    data_object=properties,
                                    vector=vector
                                )
                            else:
                                # Add new object to batch
                                batch_client.add_data_object(
                                    data_object=properties,
                                    class_name=self.class_name,
                                    uuid=vector_id,
                                    vector=vector
                                )
                            
                            upserted_count += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to upsert vector {vector_data.get('id', 'unknown')}: {e}")
                            failed_count += 1
            
            result = {
                "upserted_count": upserted_count,
                "failed_count": failed_count,
                "total_count": total_vectors
            }
            
            logger.info(f"Upserted {upserted_count}/{total_vectors} vectors to Weaviate")
            return result
            
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            raise DatabaseError(f"Batch upsert failed: {e}")
    
    async def delete(self, collection_name: str, vector_ids: List[str]) -> Dict[str, Any]:
        """Delete vectors from Weaviate.
        
        Args:
            collection_name: Collection name (mapped to Weaviate class)
            vector_ids: List of vector IDs to delete
            
        Returns:
            Deletion results
        """
        try:
            if not self.client:
                await self.connect()
            
            deleted_count = 0
            failed_count = 0
            
            for vector_id in vector_ids:
                try:
                    self.client.data_object.delete(
                        uuid=vector_id,
                        class_name=self.class_name
                    )
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to delete vector {vector_id}: {e}")
                    failed_count += 1
            
            result = {
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "total_count": len(vector_ids)
            }
            
            logger.info(f"Deleted {deleted_count}/{len(vector_ids)} vectors from Weaviate")
            return result
            
        except Exception as e:
            logger.error(f"Delete operation failed: {e}")
            raise DatabaseError(f"Delete operation failed: {e}")
    
    async def batch_upsert(self, collection_name: str, vectors: List[Dict[str, Any]], 
                          batch_size: int = 100) -> Dict[str, Any]:
        """Batch upsert vectors into Weaviate (same as upsert).
        
        Args:
            collection_name: Collection name
            vectors: List of vector dictionaries
            batch_size: Batch size for processing
            
        Returns:
            Operation results
        """
        return await self.upsert(collection_name, vectors, batch_size)
    
    async def get_by_id(self, collection_name: str, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector by ID from Weaviate.
        
        Args:
            collection_name: Collection name (mapped to Weaviate class)
            vector_id: Vector ID to retrieve
            
        Returns:
            Vector data or None if not found
        """
        try:
            if not self.client:
                await self.connect()
            
            # Get object by ID
            result = self.client.data_object.get_by_id(
                vector_id,
                class_name=self.class_name,
                with_vector=True
            )
            
            if result:
                # Extract metadata
                properties = result.get("properties", {})
                metadata = {
                    "id": result.get("id", vector_id),
                    "material_id": properties.get("material_id", ""),
                    "name": properties.get("name", ""),
                    "description": properties.get("description", ""),
                    "category": properties.get("category", ""),
                    "unit": properties.get("unit", ""),
                    "price": properties.get("price", 0.0),
                    "metadata": properties.get("metadata", "{}"),
                    "created_at": properties.get("created_at", "")
                }
                
                return {
                    "id": vector_id,
                    "vector": result.get("vector", []),
                    "metadata": metadata
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vector by ID {vector_id}: {e}")
            return None
    
    async def update_vector(self, collection_name: str, vector_id: str, 
                           vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Update vector and metadata in Weaviate.
        
        Args:
            collection_name: Collection name
            vector_id: Vector ID to update
            vector: New vector data
            metadata: New metadata
            
        Returns:
            True if updated successfully
        """
        try:
            if not self.client:
                await self.connect()
            
            # Prepare properties
            properties = {
                "material_id": metadata.get("material_id", vector_id),
                "name": metadata.get("name", ""),
                "description": metadata.get("description", ""),
                "category": metadata.get("category", ""),
                "unit": metadata.get("unit", ""),
                "price": float(metadata.get("price", 0.0)),
                "metadata": str(metadata.get("metadata", "{}")),
                "created_at": metadata.get("created_at", datetime.utcnow().isoformat())
            }
            
            # Update object
            self.client.data_object.update(
                uuid=vector_id,
                class_name=self.class_name,
                data_object=properties,
                vector=vector
            )
            
            logger.info(f"Updated vector {vector_id} in Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update vector {vector_id}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Weaviate database health.
        
        Returns:
            Health status information
        """
        try:
            if not self.client:
                await self.connect()
            
            # Check if client is ready
            is_ready = self.client.is_ready()
            
            # Get cluster status
            cluster_status = {}
            try:
                cluster_status = self.client.cluster.get_nodes_status()
            except:
                cluster_status = {"error": "Unable to get cluster status"}
            
            # Get schema info
            schema_info = {}
            try:
                schema = self.client.schema.get()
                schema_info = {
                    "classes": len(schema.get("classes", [])),
                    "has_materials_class": any(
                        cls["class"] == self.class_name 
                        for cls in schema.get("classes", [])
                    )
                }
            except:
                schema_info = {"error": "Unable to get schema info"}
            
            return {
                "status": "healthy" if is_ready else "unhealthy",
                "database_type": "Weaviate",
                "url": self.url,
                "class_name": self.class_name,
                "is_ready": is_ready,
                "cluster_status": cluster_status,
                "schema_info": schema_info,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "database_type": "Weaviate",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            } 