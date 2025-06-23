"""
Mock объекты для unit тестов
"""
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import List, Any
from .data_fixtures import TestDataProvider


class MockFactories:
    """Фабрика для создания mock объектов"""
    
    @staticmethod
    def create_mock_vector_repository():
        """Mock для векторного репозитория"""
        mock_repo = Mock()
        
        # Методы поиска
        mock_repo.search = AsyncMock(return_value=[])
        mock_repo.similarity_search = AsyncMock(return_value=[])
        mock_repo.hybrid_search = AsyncMock(return_value=[])
        
        # CRUD операции
        mock_repo.upsert = AsyncMock(return_value=True)
        mock_repo.batch_upsert = AsyncMock(return_value=True)
        mock_repo.get_by_id = AsyncMock(return_value=None)
        mock_repo.delete = AsyncMock(return_value=True)
        mock_repo.delete_by_ids = AsyncMock(return_value=True)
        
        # Управление коллекциями
        mock_repo.create_collection = AsyncMock(return_value=True)
        mock_repo.delete_collection = AsyncMock(return_value=True)
        mock_repo.collection_exists = AsyncMock(return_value=True)
        mock_repo.get_collection_info = AsyncMock(return_value={"vectors_count": 0})
        
        return mock_repo
    
    @staticmethod
    def create_mock_materials_service():
        """Mock для сервиса материалов"""
        mock_service = Mock()
        
        # CRUD операции
        mock_service.create_material = AsyncMock()
        mock_service.get_material = AsyncMock(return_value=None)
        mock_service.get_materials = AsyncMock(return_value=[])
        mock_service.update_material = AsyncMock()
        mock_service.delete_material = AsyncMock(return_value=True)
        
        # Поиск
        mock_service.search_materials = AsyncMock(return_value=[])
        mock_service.vector_search = AsyncMock(return_value=[])
        mock_service.text_search = AsyncMock(return_value=[])
        
        # Batch операции
        mock_service.create_materials_batch = AsyncMock(return_value=[])
        mock_service.update_materials_batch = AsyncMock(return_value=[])
        mock_service.delete_materials_batch = AsyncMock(return_value=True)
        
        # Файловые операции
        mock_service.import_from_csv = AsyncMock(return_value={"imported": 0, "errors": []})
        mock_service.import_from_excel = AsyncMock(return_value={"imported": 0, "errors": []})
        mock_service.export_to_csv = AsyncMock(return_value="csv_data")
        
        return mock_service
    
    @staticmethod
    def create_mock_category_service():
        """Mock для сервиса категорий"""
        mock_service = Mock()
        
        mock_service.create_category = AsyncMock()
        mock_service.get_category = AsyncMock(return_value=None)
        mock_service.get_categories = AsyncMock(return_value=TestDataProvider.get_sample_categories())
        mock_service.update_category = AsyncMock()
        mock_service.delete_category = AsyncMock(return_value=True)
        mock_service.search_categories = AsyncMock(return_value=[])
        
        return mock_service
    
    @staticmethod
    def create_mock_unit_service():
        """Mock для сервиса единиц измерения"""
        mock_service = Mock()
        
        mock_service.create_unit = AsyncMock()
        mock_service.get_unit = AsyncMock(return_value=None)
        mock_service.get_units = AsyncMock(return_value=TestDataProvider.get_sample_units())
        mock_service.update_unit = AsyncMock()
        mock_service.delete_unit = AsyncMock(return_value=True)
        mock_service.search_units = AsyncMock(return_value=[])
        
        return mock_service
    
    @staticmethod
    def create_mock_ai_client():
        """Mock для AI клиента (OpenAI)"""
        mock_client = AsyncMock()
        
        # Embeddings
        mock_client.embeddings = AsyncMock()
        mock_client.embeddings.create = AsyncMock()
        mock_client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=TestDataProvider.get_embedding_vectors()["cement_vector"])]
        )
        
        # Chat completions (если используется)
        mock_client.chat = AsyncMock()
        mock_client.chat.completions = AsyncMock()
        mock_client.chat.completions.create = AsyncMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test AI response"))]
        )
        
        return mock_client
    
    @staticmethod
    def create_mock_qdrant_client():
        """Mock для Qdrant клиента"""
        mock_client = MagicMock()
        
        # Коллекции
        mock_client.get_collections.return_value = MagicMock(collections=[])
        mock_client.create_collection.return_value = True
        mock_client.delete_collection.return_value = True
        mock_client.collection_exists.return_value = True
        
        # Поиск
        mock_client.search.return_value = []
        mock_client.query.return_value = []
        
        # Загрузка данных
        mock_client.upsert.return_value = MagicMock(status="completed")
        mock_client.upload_points.return_value = MagicMock(status="completed")
        
        # Получение данных
        mock_client.retrieve.return_value = []
        mock_client.scroll.return_value = ([], None)
        
        # Удаление
        mock_client.delete.return_value = MagicMock(status="completed")
        
        return mock_client
    
    @staticmethod
    def create_mock_redis_client():
        """Mock для Redis клиента"""
        mock_client = AsyncMock()
        
        # Базовые операции
        mock_client.get = AsyncMock(return_value=None)
        mock_client.set = AsyncMock(return_value=True)
        mock_client.delete = AsyncMock(return_value=1)
        mock_client.exists = AsyncMock(return_value=False)
        
        # Операции с TTL
        mock_client.expire = AsyncMock(return_value=True)
        mock_client.ttl = AsyncMock(return_value=-1)
        
        # Hash операции
        mock_client.hget = AsyncMock(return_value=None)
        mock_client.hset = AsyncMock(return_value=True)
        mock_client.hgetall = AsyncMock(return_value={})
        
        # List операции
        mock_client.lpush = AsyncMock(return_value=1)
        mock_client.rpop = AsyncMock(return_value=None)
        mock_client.llen = AsyncMock(return_value=0)
        
        # Set операции
        mock_client.sadd = AsyncMock(return_value=1)
        mock_client.smembers = AsyncMock(return_value=set())
        
        # Подключение
        mock_client.ping = AsyncMock(return_value=True)
        
        return mock_client
    
    @staticmethod
    def create_mock_postgresql_client():
        """Mock для PostgreSQL клиента"""
        mock_client = AsyncMock()
        
        # Подключение
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.is_connected = Mock(return_value=True)
        
        # Выполнение запросов
        mock_client.execute = AsyncMock(return_value=None)
        mock_client.fetch_all = AsyncMock(return_value=[])
        mock_client.fetch_one = AsyncMock(return_value=None)
        mock_client.fetch_val = AsyncMock(return_value=None)
        
        # Транзакции
        mock_client.transaction = AsyncMock()
        
        return mock_client
    
    @staticmethod
    def create_mock_file_handler():
        """Mock для обработчика файлов"""
        mock_handler = Mock()
        
        # CSV операции
        mock_handler.read_csv = AsyncMock(return_value=TestDataProvider.get_sample_materials())
        mock_handler.write_csv = AsyncMock(return_value="csv_content")
        mock_handler.validate_csv = AsyncMock(return_value={"valid": True, "errors": []})
        
        # Excel операции
        mock_handler.read_excel = AsyncMock(return_value=TestDataProvider.get_sample_materials())
        mock_handler.write_excel = AsyncMock(return_value=b"excel_content")
        mock_handler.validate_excel = AsyncMock(return_value={"valid": True, "errors": []})
        
        # Файловые операции
        mock_handler.save_file = AsyncMock(return_value="file_path")
        mock_handler.delete_file = AsyncMock(return_value=True)
        mock_handler.get_file_info = AsyncMock(return_value={"size": 1024, "type": "text/csv"})
        
        return mock_handler
    
    @staticmethod
    def create_mock_monitoring_service():
        """Mock для сервиса мониторинга"""
        mock_service = Mock()
        
        # Метрики
        mock_service.get_metrics = AsyncMock(return_value={
            "requests_total": 100,
            "requests_per_second": 10,
            "response_time_avg": 0.25,
            "error_rate": 0.01
        })
        
        # Health checks
        mock_service.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_service.deep_health_check = AsyncMock(return_value={
            "database": "healthy",
            "vector_db": "healthy", 
            "cache": "healthy",
            "ai_service": "healthy"
        })
        
        # Алерты
        mock_service.create_alert = AsyncMock()
        mock_service.get_alerts = AsyncMock(return_value=[])
        
        return mock_service


class MockResponseFactory:
    """Фабрика для создания mock HTTP ответов"""
    
    @staticmethod
    def create_success_response(data: Any = None, status_code: int = 200):
        """Успешный ответ"""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = data or {"status": "success"}
        mock_response.text = str(data) if data else "success"
        mock_response.headers = {"Content-Type": "application/json"}
        return mock_response
    
    @staticmethod
    def create_error_response(error_message: str = "Error", status_code: int = 400):
        """Ответ с ошибкой"""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {"error": error_message}
        mock_response.text = error_message
        mock_response.headers = {"Content-Type": "application/json"}
        return mock_response
    
    @staticmethod
    def create_paginated_response(data: List[Any], page: int = 1, per_page: int = 10, total: int = None):
        """Ответ с пагинацией"""
        if total is None:
            total = len(data)
            
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }
        return mock_response 