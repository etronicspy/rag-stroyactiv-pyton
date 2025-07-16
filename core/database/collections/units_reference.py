"""
Units Reference Database Collection

Справочник единиц измерения с embeddings для RAG нормализации.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from core.logging import get_logger
from core.database.interfaces import IVectorDatabase
from core.database.factories import DatabaseFactory
import uuid

logger = get_logger(__name__)

class UnitsReferenceCollection:
    """
    Units reference database for embedding-based normalization.
    
    Справочник единиц измерения с embeddings.
    """
    def __init__(self, vector_db: Optional[IVectorDatabase] = None):
        self.vector_db = vector_db or DatabaseFactory.create_vector_database()
        self.collection_name = "units_reference"
        self.logger = logger
        self.logger.info(f"✅ Units Reference Collection initialized")

    async def save_unit_reference(
        self,
        unit_name: str,
        aliases: List[str],
        embedding: List[float]
    ) -> bool:
        """
        Save unit to reference database.
        
        Args:
            unit_name: Main unit name
            aliases: List of aliases
            embedding: Embedding vector
        Returns:
            True if saved successfully
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            payload = {
                "unit_name": unit_name,
                "aliases": aliases,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            unit_id = str(uuid.uuid4())
            result = await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": unit_id,
                    "vector": embedding,
                    "payload": payload
                }]
            )
            self.logger.info(f"✅ Saved unit reference: {unit_name} (id: {unit_id})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to save unit reference {unit_name}: {e}")
            return False

    async def find_unit_by_embedding(
        self,
        embedding: List[float],
        threshold: float = 0.8
    ) -> Optional[Dict]:
        """
        Find unit by embedding similarity.
        
        Args:
            embedding: Query embedding
            threshold: Similarity threshold
        Returns:
            Best matching unit or None
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
                self.logger.debug(f"Found unit by embedding: {result.get('payload', {}).get('unit_name')}")
                return result
            else:
                self.logger.debug("No unit found by embedding")
                return None
        except Exception as e:
            self.logger.error(f"Error finding unit by embedding: {e}")
            return None 