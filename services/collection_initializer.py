"""
Collection Initializer Service for RAG reference data.

Сервис инициализации коллекций для справочных данных RAG.
"""

from typing import Any, Callable, Dict, Optional

from core.config.base import get_settings
from core.database.collections import ColorCollection, UnitsCollection
from core.logging import get_logger

logger = get_logger(__name__)


class CollectionInitializerService:
    """Service for initializing vector collections with reference data (через fallback manager)."""
    def __init__(self, embedding_generator: Optional[Callable] = None):
        self.embedding_generator = embedding_generator
        self.settings = get_settings()
        self.logger = logger

    async def initialize_all_collections(self, force_recreate: bool = False) -> Dict[str, Any]:
        from core.database.factories import (
            AllDatabasesUnavailableError,
            get_fallback_manager,
        )
        fallback_manager = get_fallback_manager()
        results = {
            "construction_colors": {"success": False, "message": "", "count": 0},
            "construction_units": {"success": False, "message": "", "count": 0},
            "construction_categories": {"success": False, "message": "", "count": 0},
            "overall_success": False,
            "total_collections": 3,
            "successful_collections": 0
        }
        try:
            self.logger.info("Initializing construction_colors collection...")
            colors_result = await self.initialize_colors_collection(force_recreate)
            results["construction_colors"] = colors_result
            self.logger.info("Initializing construction_units collection...")
            units_result = await self.initialize_units_collection(force_recreate)
            results["construction_units"] = units_result
            self.logger.info("Initializing construction_categories collection...")
            categories_result = await self.initialize_categories_collection(force_recreate)
            results["construction_categories"] = categories_result
            results["successful_collections"] = sum(1 for k in ["construction_colors", "construction_units", "construction_categories"] if results[k]["success"])
            results["overall_success"] = results["successful_collections"] == results["total_collections"]
            if results["overall_success"]:
                self.logger.info("All collections initialized successfully!")
            else:
                self.logger.warning(f"Only {results['successful_collections']}/{results['total_collections']} collections initialized successfully")
        except AllDatabasesUnavailableError as e:
            self.logger.error(f"All databases unavailable: {e}")
            results["overall_success"] = False
            results["error"] = str(e)
        except Exception as e:
            self.logger.error(f"Failed to initialize collections: {e}")
            results["overall_success"] = False
            results["error"] = str(e)
        return results

    async def initialize_colors_collection(self, force_recreate: bool = False) -> Dict[str, Any]:
        from core.database.factories import (
            AllDatabasesUnavailableError,
            get_fallback_manager,
        )
        fallback_manager = get_fallback_manager()
        collection_name = ColorCollection.collection_name
        try:
            collection_exists = await fallback_manager.collection_exists(collection_name)
            if collection_exists and not force_recreate:
                count = await fallback_manager.get_collection_count(collection_name)
                self.logger.info(f"Colors collection already exists with {count} items")
                return {
                    "success": True,
                    "message": f"Collection already exists with {count} items",
                    "count": count,
                    "action": "skipped"
                }
            if collection_exists and force_recreate:
                await fallback_manager.delete_collection(collection_name)
                self.logger.info("Deleted existing colors collection")
            collection_config = ColorCollection.get_collection_config()
            await fallback_manager.create_collection(collection_config)
            self.logger.info(f"Created colors collection: {collection_name}")
            colors_data = ColorCollection.generate_colors_data(self.embedding_generator)
            batch_size = 50
            total_inserted = 0
            for i in range(0, len(colors_data), batch_size):
                batch = colors_data[i:i + batch_size]
                await fallback_manager.insert_batch(collection_name, batch)
                total_inserted += len(batch)
                self.logger.debug(f"Inserted {len(batch)} colors, total: {total_inserted}")
            self.logger.info(f"Successfully initialized colors collection with {total_inserted} items")
            return {
                "success": True,
                "message": f"Successfully initialized with {total_inserted} items",
                "count": total_inserted,
                "action": "created" if not collection_exists else "recreated"
            }
        except AllDatabasesUnavailableError as e:
            self.logger.error(f"All databases unavailable: {e}")
            return {
                "success": False,
                "message": f"All databases unavailable: {str(e)}",
                "count": 0,
                "action": "failed"
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
        from core.database.factories import (
            AllDatabasesUnavailableError,
            get_fallback_manager,
        )
        fallback_manager = get_fallback_manager()
        collection_name = UnitsCollection.collection_name
        try:
            collection_exists = await fallback_manager.collection_exists(collection_name)
            if collection_exists and not force_recreate:
                count = await fallback_manager.get_collection_count(collection_name)
                self.logger.info(f"Units collection already exists with {count} items")
                return {
                    "success": True,
                    "message": f"Collection already exists with {count} items",
                    "count": count,
                    "action": "skipped"
                }
            if collection_exists and force_recreate:
                await fallback_manager.delete_collection(collection_name)
                self.logger.info("Deleted existing units collection")
            collection_config = UnitsCollection.get_collection_config()
            await fallback_manager.create_collection(collection_config)
            self.logger.info(f"Created units collection: {collection_name}")
            units_data = UnitsCollection.generate_units_data(self.embedding_generator)
            batch_size = 50
            total_inserted = 0
            for i in range(0, len(units_data), batch_size):
                batch = units_data[i:i + batch_size]
                await fallback_manager.insert_batch(collection_name, batch)
                total_inserted += len(batch)
                self.logger.debug(f"Inserted {len(batch)} units, total: {total_inserted}")
            self.logger.info(f"Successfully initialized units collection with {total_inserted} items")
            return {
                "success": True,
                "message": f"Successfully initialized with {total_inserted} items",
                "count": total_inserted,
                "action": "created" if not collection_exists else "recreated"
            }
        except AllDatabasesUnavailableError as e:
            self.logger.error(f"All databases unavailable: {e}")
            return {
                "success": False,
                "message": f"All databases unavailable: {str(e)}",
                "count": 0,
                "action": "failed"
            }
        except Exception as e:
            self.logger.error(f"Failed to initialize units collection: {e}")
            return {
                "success": False,
                "message": f"Failed to initialize: {str(e)}",
                "count": 0,
                "action": "failed"
            }
    
    async def initialize_categories_collection(self, force_recreate: bool = False) -> Dict[str, Any]:
        from core.database.factories import (
            AllDatabasesUnavailableError,
            get_fallback_manager,
        )
        fallback_manager = get_fallback_manager()
        collection_name = "construction_categories"
        try:
            collection_exists = await fallback_manager.collection_exists(collection_name)
            if collection_exists and not force_recreate:
                count = await fallback_manager.get_collection_count(collection_name)
                self.logger.info(f"Categories collection already exists with {count} items")
                return {
                    "success": True,
                    "message": f"Collection already exists with {count} items",
                    "count": count,
                    "action": "skipped"
                }
            if collection_exists and force_recreate:
                await fallback_manager.delete_collection(collection_name)
                self.logger.info("Deleted existing categories collection")
            # Пример конфигурации для categories
            collection_config = {
                "collection_name": collection_name,
                "vector_size": 1536,
                "distance": "cosine"
            }
            await fallback_manager.create_collection(collection_config)
            self.logger.info(f"Created categories collection: {collection_name}")
            # Пример данных для категорий
            categories_data = [
                {
                    "id": "cat-1",
                    "vector": [0.0] * 1536,
                    "payload": {
                        "name": "Кирпич",
                        "aliases": ["кирпич", "brick", "кирпич керамический"],
                        "description": "Строительный материал для возведения стен"
                    }
                },
                {
                    "id": "cat-2",
                    "vector": [0.0] * 1536,
                    "payload": {
                        "name": "Бетон",
                        "aliases": ["бетон", "concrete", "монолит"],
                        "description": "Материал для монолитных и сборных конструкций"
                    }
                },
                {
                    "id": "cat-3",
                    "vector": [0.0] * 1536,
                    "payload": {
                        "name": "Доска",
                        "aliases": ["доска", "board", "пиломатериал"],
                        "description": "Пиломатериал для строительных работ"
                    }
                }
            ]
            await fallback_manager.insert_batch(collection_name, categories_data)
            self.logger.info(f"Successfully initialized categories collection with {len(categories_data)} items")
            return {
                "success": True,
                "message": f"Successfully initialized with {len(categories_data)} items",
                "count": len(categories_data),
                "action": "created" if not collection_exists else "recreated"
            }
        except AllDatabasesUnavailableError as e:
            self.logger.error(f"All databases unavailable: {e}")
            return {
                "success": False,
                "message": f"All databases unavailable: {str(e)}",
                "count": 0,
                "action": "failed"
            }
        except Exception as e:
            self.logger.error(f"Failed to initialize categories collection: {e}")
            return {
                "success": False,
                "message": f"Failed to initialize: {str(e)}",
                "count": 0,
                "action": "failed"
            }

    # Удалить устаревшие внутренние методы _collection_exists, _get_collection_count, _delete_collection, _create_collection, _insert_batch 