"""
Фикстуры для работы с базами данных в тестах
"""
import pytest
from typing import Dict, List
from unittest.mock import AsyncMock, Mock
from .data_fixtures import TestDataProvider


class DatabaseTestHelpers:
    """Вспомогательные методы для тестирования БД"""
    
    @staticmethod
    async def create_test_collection(client, collection_name: str, vector_size: int = 1536):
        """Создание тестовой коллекции"""
        try:
            if hasattr(client, 'create_collection'):
                await client.create_collection(collection_name, vector_size=vector_size)
                return True
        except Exception:
            pass
        return False
    
    @staticmethod
    async def cleanup_test_collections(client, prefix: str = "test_"):
        """Очистка тестовых коллекций"""
        try:
            if hasattr(client, 'get_collections'):
                collections = await client.get_collections()
                for collection in collections:
                    if collection.name.startswith(prefix):
                        await client.delete_collection(collection.name)
        except Exception:
            pass
    
    @staticmethod
    def generate_test_vectors(count: int, dimension: int = 1536) -> List[List[float]]:
        """Генерация тестовых векторов"""
        vectors = []
        for i in range(count):
            vector = [0.1 * (i + 1)] * dimension
            vectors.append(vector)
        return vectors
    
    @staticmethod
    def create_test_points(materials: List[Dict], vectors: List[List[float]]) -> List[Dict]:
        """Создание тестовых точек для векторной БД"""
        points = []
        for i, (material, vector) in enumerate(zip(materials, vectors)):
            point = {
                "id": f"test_{i}",
                "vector": vector,
                "payload": material
            }
            points.append(point)
        return points


@pytest.fixture
def db_test_helpers():
    """Фикстура с вспомогательными методами для БД"""
    return DatabaseTestHelpers


@pytest.fixture
async def test_vector_collection():
    """Создание и очистка тестовой векторной коллекции"""
    collection_name = "test_materials_collection"
    # В реальных тестах здесь будет настоящий клиент
    # В unit тестах - mock
    yield collection_name
    # Cleanup after test


@pytest.fixture
def sample_vector_points():
    """Образцы векторных точек для тестирования"""
    materials = TestDataProvider.get_sample_materials()
    vectors = DatabaseTestHelpers.generate_test_vectors(len(materials))
    return DatabaseTestHelpers.create_test_points(materials, vectors)


@pytest.fixture
def mock_vector_search_results():
    """Mock результаты векторного поиска"""
    materials = TestDataProvider.get_sample_materials()
    results = []
    
    for i, material in enumerate(materials[:3]):  # Топ 3 результата
        result = {
            "id": f"test_{i}",
            "score": 0.9 - (i * 0.1),  # Убывающий score
            "payload": material,
            "vector": [0.1 * (i + 1)] * 1536
        }
        results.append(result)
    
    return results


@pytest.fixture
def database_connection_params():
    """Параметры подключения к тестовым БД"""
    return {
        "qdrant": {
            "url": "https://test-cluster.qdrant.tech:6333",
            "api_key": "test-api-key",
            "collection_name": "test_materials",
            "vector_size": 1536
        },
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "test_materials",
            "username": "test",
            "password": "test"
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None
        }
    }


@pytest.fixture
def batch_operation_data():
    """Данные для тестирования batch операций"""
    return TestDataProvider.get_batch_operations_data()


class VectorDBFixtures:
    """Фикстуры для векторных БД"""
    
    @staticmethod
    @pytest.fixture
    def mock_qdrant_operations():
        """Mock операций с Qdrant"""
        mock_ops = Mock()
        
        # Поиск
        mock_ops.search = AsyncMock(return_value=[])
        mock_ops.query = AsyncMock(return_value=[])
        
        # Загрузка
        mock_ops.upsert = AsyncMock(return_value={"status": "completed", "operation_id": "test_op"})
        mock_ops.upload_points = AsyncMock(return_value={"status": "completed"})
        
        # Получение
        mock_ops.retrieve = AsyncMock(return_value=[])
        mock_ops.scroll = AsyncMock(return_value=([], None))
        
        # Удаление
        mock_ops.delete = AsyncMock(return_value={"status": "completed"})
        
        return mock_ops
    
    @staticmethod
    @pytest.fixture
    def vector_search_scenarios():
        """Сценарии для тестирования векторного поиска"""
        return [
            {
                "name": "exact_match",
                "query": "Portland Cement M400",
                "expected_count": 1,
                "min_score": 0.9
            },
            {
                "name": "partial_match",
                "query": "cement",
                "expected_count": 2,
                "min_score": 0.7
            },
            {
                "name": "no_match",
                "query": "nonexistent material",
                "expected_count": 0,
                "min_score": 0.0
            },
            {
                "name": "category_search",
                "query": "building materials",
                "expected_count": 3,
                "min_score": 0.6
            }
        ]


class PostgreSQLFixtures:
    """Фикстуры для PostgreSQL"""
    
    @staticmethod
    @pytest.fixture
    def mock_postgresql_operations():
        """Mock операций с PostgreSQL"""
        mock_ops = AsyncMock()
        
        # Выполнение SQL
        mock_ops.execute = AsyncMock(return_value=None)
        mock_ops.executemany = AsyncMock(return_value=None)
        
        # Получение данных
        mock_ops.fetch_all = AsyncMock(return_value=[])
        mock_ops.fetch_one = AsyncMock(return_value=None)
        mock_ops.fetch_val = AsyncMock(return_value=None)
        
        # Транзакции
        mock_ops.begin = AsyncMock()
        mock_ops.commit = AsyncMock()
        mock_ops.rollback = AsyncMock()
        
        return mock_ops
    
    @staticmethod
    @pytest.fixture
    def sql_test_queries():
        """Тестовые SQL запросы"""
        return {
            "create_materials_table": """
                CREATE TABLE IF NOT EXISTS materials (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    use_category VARCHAR(100),
                    unit VARCHAR(20),
                    price DECIMAL(10,2),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "insert_material": """
                INSERT INTO materials (name, use_category, unit, price, description)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """,
            "select_materials": """
                SELECT * FROM materials WHERE name ILIKE $1
            """,
            "update_material": """
                UPDATE materials SET price = $1 WHERE id = $2
            """,
            "delete_material": """
                DELETE FROM materials WHERE id = $1
            """
        }


class RedisFixtures:
    """Фикстуры для Redis"""
    
    @staticmethod
    @pytest.fixture
    def mock_redis_operations():
        """Mock операций с Redis"""
        mock_ops = AsyncMock()
        
        # Базовые операции
        mock_ops.get = AsyncMock(return_value=None)
        mock_ops.set = AsyncMock(return_value=True)
        mock_ops.delete = AsyncMock(return_value=1)
        mock_ops.exists = AsyncMock(return_value=False)
        
        # Операции с TTL
        mock_ops.expire = AsyncMock(return_value=True)
        mock_ops.ttl = AsyncMock(return_value=-1)
        
        # Hash операции
        mock_ops.hget = AsyncMock(return_value=None)
        mock_ops.hset = AsyncMock(return_value=True)
        mock_ops.hgetall = AsyncMock(return_value={})
        mock_ops.hdel = AsyncMock(return_value=1)
        
        # Pub/Sub
        mock_ops.publish = AsyncMock(return_value=1)
        mock_ops.subscribe = AsyncMock()
        
        return mock_ops
    
    @staticmethod
    @pytest.fixture
    def cache_test_scenarios():
        """Сценарии тестирования кеширования"""
        return [
            {
                "name": "cache_hit",
                "key": "materials:search:cement",
                "value": TestDataProvider.get_sample_materials()[:2],
                "ttl": 300
            },
            {
                "name": "cache_miss",
                "key": "materials:search:nonexistent",
                "value": None,
                "ttl": 0
            },
            {
                "name": "cache_expiry",
                "key": "materials:temp:data",
                "value": {"temp": "data"},
                "ttl": 1  # Быстрое истечение
            }
        ]


# Объединяем все фикстуры в одном модуле
pytest_plugins = [
    VectorDBFixtures,
    PostgreSQLFixtures,
    RedisFixtures
] 