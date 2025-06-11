"""
Тесты для проверки подключения к реальной базе данных
"""
import pytest
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

logger = logging.getLogger(__name__)

class TestRealDBConnection:
    """Тесты для проверки подключения к реальной БД"""
    
    def test_qdrant_connection(self, qdrant_client):
        """Тест подключения к Qdrant"""
        try:
            collections = qdrant_client.get_collections()
            logger.info(f"✅ Connected to Qdrant. Collections count: {len(collections.collections)}")
            
            # Выводим информацию о существующих коллекциях
            for collection in collections.collections:
                logger.info(f"📚 Collection: {collection.name}")
            
            assert True, "Connection successful"
        except Exception as e:
            pytest.fail(f"Failed to connect to Qdrant: {e}")
    
    def test_create_test_collection(self, qdrant_client):
        """Тест создания тестовой коллекции"""
        test_collection_name = f"test_connection_{int(time.time())}"
        
        try:
            # Создаем тестовую коллекцию
            qdrant_client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            
            # Проверяем, что коллекция создана
            collections = qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            assert test_collection_name in collection_names
            logger.info(f"✅ Test collection '{test_collection_name}' created successfully")
            
        except Exception as e:
            pytest.fail(f"Failed to create test collection: {e}")
        
        finally:
            # Очищаем тестовую коллекцию
            try:
                qdrant_client.delete_collection(test_collection_name)
                logger.info(f"🧹 Cleaned up test collection '{test_collection_name}'")
            except Exception as e:
                logger.warning(f"Failed to cleanup test collection: {e}")
    
    def test_insert_and_retrieve_data(self, qdrant_client):
        """Тест вставки и получения данных"""
        test_collection_name = f"test_data_{int(time.time())}"
        
        try:
            # Создаем коллекцию
            qdrant_client.create_collection(
                collection_name=test_collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            
            # Подготавливаем тестовые данные
            test_vector = [0.1] * 384  # Простой тестовый вектор
            test_payload = {
                "name": "Test Material",
                "use_category": "Test Category",
                "price": 100.0,
                "supplier": "TEST_SUPPLIER"
            }
            
            # Вставляем данные
            qdrant_client.upsert(
                collection_name=test_collection_name,
                points=[
                    PointStruct(
                        id=1,
                        vector=test_vector,
                        payload=test_payload
                    )
                ]
            )
            
            # Получаем данные
            retrieved = qdrant_client.retrieve(
                collection_name=test_collection_name,
                ids=[1]
            )
            
            assert len(retrieved) == 1
            assert retrieved[0].payload["name"] == "Test Material"
            assert retrieved[0].payload["supplier"] == "TEST_SUPPLIER"
            
            logger.info("✅ Data insert and retrieve test passed")
            
        except Exception as e:
            pytest.fail(f"Failed to insert/retrieve data: {e}")
        
        finally:
            # Очищаем
            try:
                qdrant_client.delete_collection(test_collection_name)
                logger.info(f"🧹 Cleaned up test collection '{test_collection_name}'")
            except Exception as e:
                logger.warning(f"Failed to cleanup: {e}")
    
    def test_list_existing_collections(self, qdrant_client):
        """Тест для просмотра существующих коллекций"""
        try:
            collections = qdrant_client.get_collections()
            
            logger.info(f"📊 Database contains {len(collections.collections)} collections:")
            for collection in collections.collections:
                # Получаем информацию о коллекции
                try:
                    info = qdrant_client.get_collection(collection.name)
                    logger.info(f"  📚 {collection.name}: {info.points_count} points, vector size: {info.config.params.vectors.size}")
                except Exception as e:
                    logger.info(f"  📚 {collection.name}: (error getting details: {e})")
            
            assert True, "Collection listing successful"
            
        except Exception as e:
            pytest.fail(f"Failed to list collections: {e}") 