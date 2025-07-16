"""
Colors Reference Database Collection

Справочник цветов с embeddings для RAG нормализации.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.logging import get_logger
from core.database.interfaces import IVectorDatabase
from core.database.factories import DatabaseFactory
import uuid

logger = get_logger(__name__)

class ColorsReferenceCollection:
    """
    Colors reference database for embedding-based normalization.
    
    Справочник цветов с embeddings.
    """
    def __init__(self, vector_db: Optional[IVectorDatabase] = None):
        self.vector_db = vector_db or DatabaseFactory.create_vector_database()
        self.collection_name = "colors_reference"
        self.logger = logger
        self.logger.info(f"✅ Colors Reference Collection initialized")

    async def save_color_reference(
        self,
        color_name: str,
        aliases: List[str],
        embedding: List[float]
    ) -> bool:
        """
        Save color to reference database.
        
        Args:
            color_name: Main color name
            aliases: List of aliases
            embedding: Embedding vector
        Returns:
            True if saved successfully
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            payload = {
                "color_name": color_name,
                "aliases": aliases,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            color_id = str(uuid.uuid4())
            result = await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": color_id,
                    "vector": embedding,
                    "payload": payload
                }]
            )
            self.logger.info(f"✅ Saved color reference: {color_name} (id: {color_id})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to save color reference {color_name}: {e}")
            return False

    async def find_color_by_embedding(
        self,
        embedding: List[float],
        threshold: float = 0.8
    ) -> Optional[Dict]:
        """
        Find color by embedding similarity.
        
        Args:
            embedding: Query embedding
            threshold: Similarity threshold
        Returns:
            Best matching color or None
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            search_results = await self.vector_db.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=1,
                score_threshold=threshold
            )
            if search_results:
                result = search_results[0]
                self.logger.debug(f"Found color by embedding: {result.get('payload', {}).get('color_name')}")
                return result
            else:
                self.logger.debug("No color found by embedding")
                return None
        except Exception as e:
            self.logger.error(f"Error finding color by embedding: {e}")
            return None 