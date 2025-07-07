"""
Integration module for AI Material Parser with main RAG project

This module provides integration functions for connecting the AI Material Parser
with the main project's vector databases (Qdrant, Weaviate, Pinecone) and search functionality.
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    # Try to import from main project
    from core.database.adapters.qdrant_adapter import QdrantAdapter
    from core.database.adapters.weaviate_adapter import WeaviateAdapter
    from core.database.adapters.pinecone_adapter import PineconeAdapter
    from core.config.base import Settings
    from core.models.materials import Material
    MAIN_PROJECT_AVAILABLE = True
except ImportError:
    MAIN_PROJECT_AVAILABLE = False
    logging.warning("Main project imports not available. Integration functions will work in standalone mode.")

from .material_parser import MaterialParser
from .parser_config import get_config


class MaterialVectorIntegration:
    """
    Integration class for storing and searching parsed materials with embeddings
    in the main project's vector databases.
    """
    
    def __init__(self, vector_db_type: str = "qdrant", config_env: str = "integration"):
        """
        Initialize integration with vector database
        
        Args:
            vector_db_type: Type of vector DB (qdrant, weaviate, pinecone)
            config_env: Configuration environment
        """
        self.vector_db_type = vector_db_type
        self.config_env = config_env
        self.logger = logging.getLogger(__name__)
        
        # Initialize parser
        self.parser = MaterialParser(env=config_env)
        
        # Initialize vector DB adapter
        self.vector_adapter = None
        if MAIN_PROJECT_AVAILABLE:
            self._init_vector_adapter()
        else:
            self.logger.warning("Main project not available. Using standalone mode.")
    
    def _init_vector_adapter(self):
        """Initialize vector database adapter"""
        try:
            if self.vector_db_type == "qdrant":
                self.vector_adapter = QdrantAdapter()
            elif self.vector_db_type == "weaviate":
                self.vector_adapter = WeaviateAdapter()
            elif self.vector_db_type == "pinecone":
                self.vector_adapter = PineconeAdapter()
            else:
                raise ValueError(f"Unsupported vector DB type: {self.vector_db_type}")
                
            self.logger.info(f"Initialized {self.vector_db_type} adapter")
        except Exception as e:
            self.logger.error(f"Failed to initialize vector adapter: {e}")
            self.vector_adapter = None
    
    async def parse_and_store_materials(self, materials: List[Dict[str, Any]], 
                                      collection_name: str = "construction_materials") -> Dict[str, Any]:
        """
        Parse materials and store them in vector database
        
        Args:
            materials: List of material dictionaries with name, unit, price
            collection_name: Name of the vector collection
            
        Returns:
            Dictionary with processing statistics
        """
        self.logger.info(f"Processing {len(materials)} materials for vector storage")
        
        # Parse materials with embeddings
        parsed_results = self.parser.parse_batch(materials)
        
        # Filter successful results with embeddings
        valid_results = [
            result for result in parsed_results 
            if result.get('success', False) and result.get('embeddings')
        ]
        
        self.logger.info(f"Successfully parsed {len(valid_results)}/{len(materials)} materials")
        
        # Store in vector database if available
        stored_count = 0
        if self.vector_adapter:
            try:
                stored_count = await self._store_in_vector_db(valid_results, collection_name)
            except Exception as e:
                self.logger.error(f"Failed to store in vector DB: {e}")
        
        return {
            "total_materials": len(materials),
            "successfully_parsed": len(valid_results),
            "stored_in_vector_db": stored_count,
            "success_rate": len(valid_results) / len(materials) if materials else 0,
            "parsed_results": valid_results
        }
    
    async def _store_in_vector_db(self, parsed_results: List[Dict], collection_name: str) -> int:
        """Store parsed results in vector database"""
        if not self.vector_adapter:
            return 0
        
        stored_count = 0
        
        for result in parsed_results:
            try:
                # Prepare document for vector storage
                document = {
                    "id": f"material_{hash(result['name'])}",
                    "content": result['name'],
                    "metadata": {
                        "original_unit": result['original_unit'],
                        "original_price": result['original_price'],
                        "unit_parsed": result['unit_parsed'],
                        "price_coefficient": result['price_coefficient'],
                        "price_parsed": result['price_parsed'],
                        "confidence": result['confidence'],
                        "parsing_method": result['parsing_method']
                    },
                    "vector": result['embeddings']
                }
                
                # Store in vector DB
                await self.vector_adapter.upsert(
                    collection_name=collection_name,
                    documents=[document]
                )
                
                stored_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to store material {result['name']}: {e}")
        
        self.logger.info(f"Stored {stored_count} materials in {collection_name}")
        return stored_count
    
    async def search_similar_materials(self, query_text: str, collection_name: str = "construction_materials",
                                     limit: int = 5, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar materials using vector search
        
        Args:
            query_text: Search query (material name)
            collection_name: Vector collection name
            limit: Maximum number of results
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of similar materials with scores
        """
        if not self.vector_adapter:
            self.logger.warning("Vector adapter not available. Cannot perform search.")
            return []
        
        try:
            # Generate embedding for query
            config = get_config(self.config_env)
            query_embedding = self.parser.ai_parser._generate_embeddings(query_text)
            
            if not query_embedding:
                self.logger.error("Failed to generate embedding for query")
                return []
            
            # Perform vector search
            search_results = await self.vector_adapter.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=min_confidence
            )
            
            # Format results
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    "material_name": result.get("content", ""),
                    "similarity_score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {}),
                    "unit_parsed": result.get("metadata", {}).get("unit_parsed"),
                    "price_coefficient": result.get("metadata", {}).get("price_coefficient"),
                    "original_price": result.get("metadata", {}).get("original_price"),
                    "price_per_unit": result.get("metadata", {}).get("price_parsed")
                }
                formatted_results.append(formatted_result)
            
            self.logger.info(f"Found {len(formatted_results)} similar materials for query: {query_text}")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def find_similar_in_batch(self, target_material: str, parsed_results: List[Dict], 
                             top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find similar materials within a batch of parsed results
        
        Args:
            target_material: Name of target material
            parsed_results: List of parsed results with embeddings
            top_k: Number of top similar materials to return
            
        Returns:
            List of tuples (material_name, similarity_score)
        """
        target_embedding = None
        
        # Find target material embedding
        for result in parsed_results:
            if result['name'] == target_material and result.get('embeddings'):
                target_embedding = result['embeddings']
                break
        
        if not target_embedding:
            self.logger.warning(f"Target material '{target_material}' not found or has no embedding")
            return []
        
        # Calculate similarities
        similarities = []
        for result in parsed_results:
            if result['name'] != target_material and result.get('embeddings'):
                similarity = self.calculate_similarity(target_embedding, result['embeddings'])
                similarities.append((result['name'], similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


async def demo_integration():
    """Demonstration of integration functionality"""
    print("🔗 ДЕМОНСТРАЦИЯ ИНТЕГРАЦИИ С ВЕКТОРНЫМИ БД")
    print("=" * 50)
    
    # Initialize integration
    integration = MaterialVectorIntegration(vector_db_type="qdrant")
    
    # Sample materials
    sample_materials = [
        {"name": "Цемент М400 50кг", "unit": "меш", "price": 350.0},
        {"name": "Кирпич красный (250x120x65)", "unit": "шт", "price": 12.0},
        {"name": "Газобетон D500 600x300x200", "unit": "шт", "price": 95.0},
        {"name": "OSB-3 плита 2500x1250x9мм", "unit": "шт", "price": 850.0},
        {"name": "Утеплитель базальтовый 50мм", "unit": "м2", "price": 120.0}
    ]
    
    print(f"📊 Обработка {len(sample_materials)} материалов...")
    
    # Process materials
    result = await integration.parse_and_store_materials(sample_materials)
    
    print(f"✅ Результаты обработки:")
    print(f"   Всего материалов: {result['total_materials']}")
    print(f"   Успешно обработано: {result['successfully_parsed']}")
    print(f"   Сохранено в векторной БД: {result['stored_in_vector_db']}")
    print(f"   Процент успеха: {result['success_rate']:.1%}")
    print()
    
    # Demonstrate similarity search within batch
    if result['parsed_results']:
        print("🔍 ПОИСК ПОХОЖИХ МАТЕРИАЛОВ В БАТЧЕ:")
        target = result['parsed_results'][0]['name']
        similar = integration.find_similar_in_batch(target, result['parsed_results'])
        
        print(f"   Поиск материалов, похожих на: {target}")
        for material, score in similar:
            print(f"   {score:.3f} - {material}")
        print()
    
    print("🎯 Интеграция завершена успешно!")


if __name__ == "__main__":
    asyncio.run(demo_integration()) 