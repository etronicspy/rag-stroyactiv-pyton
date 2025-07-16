"""
Materials Reference Database Collection

Справочник материалов для SKU поиска с embeddings.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from core.logging import get_logger
from core.database.interfaces import IVectorDatabase
from core.database.factories import DatabaseFactory

logger = get_logger(__name__)


class MaterialsReferenceCollection:
    """
    Materials reference database for SKU search.
    
    Справочник материалов для поиска SKU.
    """
    
    def __init__(self, vector_db: Optional[IVectorDatabase] = None):
        """
        Initialize materials reference collection.
        
        Args:
            vector_db: Vector database instance
        """
        self.vector_db = vector_db or DatabaseFactory.create_vector_database()
        self.collection_name = "materials_reference"
        self.logger = logger
        
        self.logger.info(f"✅ Materials Reference Collection initialized")
    
    async def save_material_reference(
        self,
        sku: str,
        name: str,
        unit: str,
        color: Optional[str],
        embedding: List[float]
    ) -> bool:
        """
        Save material to reference database.
        
        Сохранение материала в справочник.
        
        Args:
            sku: Material SKU
            name: Material name
            unit: Unit of measurement
            color: Material color (None for colorless)
            embedding: Material embedding vector
            
        Returns:
            True if saved successfully
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            
            # Prepare payload
            payload = {
                "sku": sku,
                "name": name,
                "unit": unit,
                "color": color,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Save to vector database
            result = await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": sku,  # Use SKU as unique ID
                    "vector": embedding,
                    "payload": payload
                }]
            )
            
            self.logger.info(f"✅ Saved material reference: {sku} - {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save material reference {sku}: {e}")
            return False
    
    async def find_material_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Find material by SKU.
        
        Поиск материала по SKU.
        
        Args:
            sku: Material SKU
            
        Returns:
            Material data or None if not found
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            
            # Get by ID
            result = await self.vector_db.get_by_id(
                collection_name=self.collection_name,
                point_id=sku
            )
            
            if result:
                self.logger.debug(f"Found material by SKU: {sku}")
                return result
            else:
                self.logger.debug(f"Material not found by SKU: {sku}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error finding material by SKU {sku}: {e}")
            return None
    
    async def search_similar_materials(
        self,
        embedding: List[float],
        unit_filter: str,
        color_filter: Optional[str],
        limit: int = 20,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search similar materials using embedding.
        
        Поиск похожих материалов через embedding.
        
        Args:
            embedding: Query embedding
            unit_filter: Required unit
            color_filter: Required color (None for any)
            limit: Maximum results
            threshold: Similarity threshold
            
        Returns:
            List of similar materials
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            
            # Search by embedding
            search_results = await self.vector_db.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                score_threshold=threshold
            )
            
            # Filter by unit and color
            filtered_results = []
            for result in search_results:
                payload = result.get("payload", {})
                result_unit = payload.get("unit", "")
                result_color = payload.get("color")
                
                # Check unit match
                unit_match = result_unit.lower() == unit_filter.lower()
                
                # Check color match (None color accepts any)
                color_match = True
                if color_filter and result_color:
                    color_match = result_color.lower() == color_filter.lower()
                
                if unit_match and color_match:
                    filtered_results.append({
                        "id": result.get("id"),
                        "sku": payload.get("sku"),
                        "name": payload.get("name"),
                        "unit": result_unit,
                        "color": result_color,
                        "similarity_score": result.get("score", 0.0),
                        "payload": payload
                    })
            
            self.logger.debug(f"Found {len(filtered_results)} similar materials after filtering")
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error searching similar materials: {e}")
            return []
    
    async def update_material_reference(
        self,
        sku: str,
        name: Optional[str] = None,
        unit: Optional[str] = None,
        color: Optional[str] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Update material reference.
        
        Обновление материала в справочнике.
        
        Args:
            sku: Material SKU
            name: New name (optional)
            unit: New unit (optional)
            color: New color (optional)
            embedding: New embedding (optional)
            
        Returns:
            True if updated successfully
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            
            # Get existing material
            existing = await self.find_material_by_sku(sku)
            if not existing:
                self.logger.warning(f"Material not found for update: {sku}")
                return False
            
            # Prepare updated payload
            payload = existing.get("payload", {})
            if name:
                payload["name"] = name
            if unit:
                payload["unit"] = unit
            if color is not None:  # Allow None color
                payload["color"] = color
            
            payload["updated_at"] = datetime.utcnow().isoformat()
            
            # Use existing embedding if not provided
            vector = embedding or existing.get("vector", [])
            
            # Update in vector database
            result = await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": sku,
                    "vector": vector,
                    "payload": payload
                }]
            )
            
            self.logger.info(f"✅ Updated material reference: {sku}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update material reference {sku}: {e}")
            return False
    
    async def delete_material_reference(self, sku: str) -> bool:
        """
        Delete material from reference database.
        
        Удаление материала из справочника.
        
        Args:
            sku: Material SKU
            
        Returns:
            True if deleted successfully
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            
            # Delete from vector database
            result = await self.vector_db.delete(
                collection_name=self.collection_name,
                points_selector=[sku]
            )
            
            self.logger.info(f"✅ Deleted material reference: {sku}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete material reference {sku}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Получить статистику коллекции.
        
        Returns:
            Collection statistics
        """
        try:
            if not self.vector_db:
                raise ValueError("Vector database not available")
            
            # Get collection info
            info = await self.vector_db.get_collection_info(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "total_points": info.get("points_count", 0),
                "vector_size": info.get("config", {}).get("params", {}).get("vectors", {}).get("size", 0),
                "distance": info.get("config", {}).get("params", {}).get("vectors", {}).get("distance", "Unknown")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "error": str(e)
            } 