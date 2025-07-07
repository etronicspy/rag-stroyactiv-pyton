"""
Collection Initializer Service for RAG reference data.

Сервис инициализации коллекций для справочных данных RAG.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from core.logging import get_logger
from core.database.interfaces import IVectorDatabase
from core.database.collections import ColorCollection, UnitsCollection
from core.config.base import get_settings

logger = get_logger(__name__)


class CollectionInitializerService:
    """Service for initializing vector collections with reference data.
    
    Сервис для инициализации векторных коллекций со справочными данными.
    """
    
    def __init__(self, vector_db: IVectorDatabase, embedding_generator: Optional[Callable] = None):
        """Initialize the collection initializer service.
        
        Args:
            vector_db: Vector database instance
            embedding_generator: Function to generate embeddings
        """
        self.vector_db = vector_db
        self.embedding_generator = embedding_generator
        self.settings = get_settings()
        self.logger = logger
        
    async def initialize_all_collections(self, force_recreate: bool = False) -> Dict[str, Any]:
        """Initialize all reference collections.
        
        Инициализировать все справочные коллекции.
        
        Args:
            force_recreate: Whether to recreate existing collections
            
        Returns:
            Initialization results
        """
        results = {
            "colors": {"success": False, "message": "", "count": 0},
            "units": {"success": False, "message": "", "count": 0},
            "overall_success": False,
            "total_collections": 0,
            "successful_collections": 0
        }
        
        try:
            # Initialize colors collection
            self.logger.info("Initializing colors collection...")
            colors_result = await self.initialize_colors_collection(force_recreate)
            results["colors"] = colors_result
            
            # Initialize units collection
            self.logger.info("Initializing units collection...")
            units_result = await self.initialize_units_collection(force_recreate)
            results["units"] = units_result
            
            # Calculate overall results
            results["total_collections"] = 2
            results["successful_collections"] = sum(1 for r in [colors_result, units_result] if r["success"])
            results["overall_success"] = results["successful_collections"] == results["total_collections"]
            
            if results["overall_success"]:
                self.logger.info("All collections initialized successfully!")
            else:
                self.logger.warning(f"Only {results['successful_collections']}/{results['total_collections']} collections initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize collections: {e}")
            results["overall_success"] = False
            results["error"] = str(e)
        
        return results
    
    async def initialize_colors_collection(self, force_recreate: bool = False) -> Dict[str, Any]:
        """Initialize colors collection with reference data.
        
        Инициализировать коллекцию цветов со справочными данными.
        
        Args:
            force_recreate: Whether to recreate existing collection
            
        Returns:
            Initialization result
        """
        collection_name = ColorCollection.collection_name
        
        try:
            # Check if collection exists
            collection_exists = await self._collection_exists(collection_name)
            
            if collection_exists and not force_recreate:
                count = await self._get_collection_count(collection_name)
                self.logger.info(f"Colors collection already exists with {count} items")
                return {
                    "success": True,
                    "message": f"Collection already exists with {count} items",
                    "count": count,
                    "action": "skipped"
                }
            
            # Create or recreate collection
            if collection_exists and force_recreate:
                await self._delete_collection(collection_name)
                self.logger.info(f"Deleted existing colors collection")
            
            # Create collection
            collection_config = ColorCollection.get_collection_config()
            await self._create_collection(collection_config)
            self.logger.info(f"Created colors collection: {collection_name}")
            
            # Generate colors data with embeddings
            colors_data = ColorCollection.generate_colors_data(self.embedding_generator)
            
            # Insert data in batches
            batch_size = 50
            total_inserted = 0
            
            for i in range(0, len(colors_data), batch_size):
                batch = colors_data[i:i + batch_size]
                await self._insert_batch(collection_name, batch)
                total_inserted += len(batch)
                self.logger.debug(f"Inserted {len(batch)} colors, total: {total_inserted}")
            
            self.logger.info(f"Successfully initialized colors collection with {total_inserted} items")
            
            return {
                "success": True,
                "message": f"Successfully initialized with {total_inserted} items",
                "count": total_inserted,
                "action": "created" if not collection_exists else "recreated"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initialize colors collection: {e}")
            return {
                "success": False,
                "message": f"Failed to initialize: {str(e)}",
                "count": 0,
                "action": "failed"
            }
    
    async def initialize_units_collection(self, force_recreate: bool = False) -> Dict[str, Any]:
        """Initialize units collection with reference data.
        
        Инициализировать коллекцию единиц со справочными данными.
        
        Args:
            force_recreate: Whether to recreate existing collection
            
        Returns:
            Initialization result
        """
        collection_name = UnitsCollection.collection_name
        
        try:
            # Check if collection exists
            collection_exists = await self._collection_exists(collection_name)
            
            if collection_exists and not force_recreate:
                count = await self._get_collection_count(collection_name)
                self.logger.info(f"Units collection already exists with {count} items")
                return {
                    "success": True,
                    "message": f"Collection already exists with {count} items",
                    "count": count,
                    "action": "skipped"
                }
            
            # Create or recreate collection
            if collection_exists and force_recreate:
                await self._delete_collection(collection_name)
                self.logger.info(f"Deleted existing units collection")
            
            # Create collection
            collection_config = UnitsCollection.get_collection_config()
            await self._create_collection(collection_config)
            self.logger.info(f"Created units collection: {collection_name}")
            
            # Generate units data with embeddings
            units_data = UnitsCollection.generate_units_data(self.embedding_generator)
            
            # Insert data in batches
            batch_size = 50
            total_inserted = 0
            
            for i in range(0, len(units_data), batch_size):
                batch = units_data[i:i + batch_size]
                await self._insert_batch(collection_name, batch)
                total_inserted += len(batch)
                self.logger.debug(f"Inserted {len(batch)} units, total: {total_inserted}")
            
            self.logger.info(f"Successfully initialized units collection with {total_inserted} items")
            
            return {
                "success": True,
                "message": f"Successfully initialized with {total_inserted} items",
                "count": total_inserted,
                "action": "created" if not collection_exists else "recreated"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initialize units collection: {e}")
            return {
                "success": False,
                "message": f"Failed to initialize: {str(e)}",
                "count": 0,
                "action": "failed"
            }
    
    async def _collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists in vector database.
        
        Проверить существует ли коллекция в векторной базе данных.
        """
        try:
            # Try to get collection info
            # This is a placeholder - implementation depends on vector DB interface
            # await self.vector_db.get_collection_info(collection_name)
            return False  # Default to False for now
        except Exception:
            return False
    
    async def _get_collection_count(self, collection_name: str) -> int:
        """Get count of items in collection.
        
        Получить количество элементов в коллекции.
        """
        try:
            # This is a placeholder - implementation depends on vector DB interface
            # return await self.vector_db.count(collection_name)
            return 0  # Default to 0 for now
        except Exception:
            return 0
    
    async def _delete_collection(self, collection_name: str) -> None:
        """Delete collection from vector database.
        
        Удалить коллекцию из векторной базы данных.
        """
        try:
            # This is a placeholder - implementation depends on vector DB interface
            # await self.vector_db.delete_collection(collection_name)
            pass
        except Exception as e:
            self.logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise
    
    async def _create_collection(self, collection_config: Dict[str, Any]) -> None:
        """Create collection in vector database.
        
        Создать коллекцию в векторной базе данных.
        """
        try:
            # This is a placeholder - implementation depends on vector DB interface
            # await self.vector_db.create_collection(collection_config)
            pass
        except Exception as e:
            self.logger.error(f"Failed to create collection {collection_config['collection_name']}: {e}")
            raise
    
    async def _insert_batch(self, collection_name: str, batch_data: List[Dict[str, Any]]) -> None:
        """Insert batch of data into collection.
        
        Вставить пакет данных в коллекцию.
        """
        try:
            # This is a placeholder - implementation depends on vector DB interface
            # await self.vector_db.upsert(collection_name, batch_data)
            pass
        except Exception as e:
            self.logger.error(f"Failed to insert batch into {collection_name}: {e}")
            raise
    
    async def get_collection_status(self) -> Dict[str, Any]:
        """Get status of all reference collections.
        
        Получить статус всех справочных коллекций.
        """
        status = {
            "colors": {
                "collection_name": ColorCollection.collection_name,
                "exists": False,
                "count": 0,
                "last_updated": None
            },
            "units": {
                "collection_name": UnitsCollection.collection_name,
                "exists": False,
                "count": 0,
                "last_updated": None
            }
        }
        
        try:
            # Check colors collection
            colors_exists = await self._collection_exists(ColorCollection.collection_name)
            status["colors"]["exists"] = colors_exists
            if colors_exists:
                status["colors"]["count"] = await self._get_collection_count(ColorCollection.collection_name)
            
            # Check units collection
            units_exists = await self._collection_exists(UnitsCollection.collection_name)
            status["units"]["exists"] = units_exists
            if units_exists:
                status["units"]["count"] = await self._get_collection_count(UnitsCollection.collection_name)
                
        except Exception as e:
            self.logger.error(f"Failed to get collection status: {e}")
            status["error"] = str(e)
        
        return status
    
    async def reset_all_collections(self) -> Dict[str, Any]:
        """Reset all reference collections (delete and recreate).
        
        Сбросить все справочные коллекции (удалить и пересоздать).
        """
        self.logger.info("Resetting all reference collections...")
        return await self.initialize_all_collections(force_recreate=True) 