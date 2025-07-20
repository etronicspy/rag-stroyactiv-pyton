"""
Единая конфигурация для всех тестов RAG Construction Materials API
Поддерживает автоматическое переключение между mock и real DB
"""
import os

import pytest

# Ensure Watchfiles hot-reload is disabled in all processes spawned during the
# pytest session. Uvicorn/Watchfiles honours the ``WATCHFILES_DISABLE`` env var.
os.environ.setdefault("WATCHFILES_DISABLE", "true")
import logging
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

from core.logging import get_logger

# Настраиваем логирование для тестов
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

# Константы для тестирования
TEST_SETTINGS = {
    "ENVIRONMENT": "testing",
    "BACKEND_CORS_ORIGINS": '["http://localhost:3000", "http://127.0.0.1:3000"]',
    "QDRANT_URL": "https://test-cluster.qdrant.tech:6333",
    "QDRANT_API_KEY": "test-api-key",
    "QDRANT_COLLECTION_NAME": "materials_test",
    "QDRANT_VECTOR_SIZE": "1536",
    "OPENAI_API_KEY": "sk-test-key",
    "OPENAI_MODEL": "text-embedding-3-small",
    "AI_PROVIDER": "openai",
    "DATABASE_TYPE": "qdrant_cloud",
    "QDRANT_ONLY_MODE": "true",
    "ENABLE_FALLBACK_DATABASES": "true",
    "DISABLE_REDIS_CONNECTION": "true",
    "DISABLE_POSTGRESQL_CONNECTION": "true",
    "POSTGRESQL_URL": "postgresql://test:test@localhost:5432/stbr_rag1",
    "REDIS_URL": "redis://localhost:6379/0",
    "MAX_UPLOAD_SIZE": "52428800",
    "BATCH_SIZE": "50",
    "AUTO_MIGRATE": "false",
    "AUTO_SEED": "false",
    "LOG_GENERAL_DEFAULT_LEVEL": "INFO",
    "ENABLE_RATE_LIMITING": "true",
    "RATE_LIMIT_RPM": "60",
    "PROJECT_NAME": "RAG Construction Materials API",
    "VERSION": "1.0.0",
    "API_V1_STR": "/api/v1"
}

# Маркеры для разных типов тестов
def pytest_configure(config):
    """Конфигурация pytest с маркерами"""
    config.addinivalue_line("markers", "unit: Quick unit tests with mocks")
    config.addinivalue_line("markers", "integration: Integration tests with real databases")
    config.addinivalue_line("markers", "functional: End-to-end functional tests")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "slow: Tests that take more than 5 seconds")

# ============================================================================
# БАЗОВЫЕ ФИКСТУРЫ ДЛЯ УПРАВЛЕНИЯ РЕЖИМОМ ТЕСТИРОВАНИЯ
# ============================================================================

@pytest.fixture(scope="session")
def test_mode():
    """Определяет режим тестирования: mock или real"""
    return os.environ.get("TEST_MODE", "mock")

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Устанавливаем переменные окружения для тестов"""
    original_env = {}
    for key, value in TEST_SETTINGS.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Восстанавливаем оригинальные значения
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

# ============================================================================
# CLIENT ФИКСТУРЫ
# ============================================================================

@pytest.fixture
def client_mock():
    """Test client с моками для unit тестов"""
    with (
        patch('core.config.get_settings') as mock_settings,
        patch('core.database.factories.DatabaseFactory.create_vector_database') as mock_create_vdb,
    ):
        from core.config import Settings
        settings = Settings(
            PROJECT_NAME="Test API",
            QDRANT_URL="https://test.qdrant.com",
            QDRANT_API_KEY="test-key",
            OPENAI_API_KEY="sk-test-openai-key-1234567890",
            QDRANT_ONLY_MODE=True,
            ENABLE_FALLBACK_DATABASES=True,
            DISABLE_REDIS_CONNECTION=True,
            DISABLE_POSTGRESQL_CONNECTION=True,
            ENABLE_RATE_LIMITING=False,
            LOG_REQUEST_BODY=False,
            LOG_RESPONSE_BODY=False
        )
        mock_settings.return_value = settings
        
        # Provide stub vector database before any application modules import
        from unittest.mock import MagicMock
        stub_vdb = MagicMock()
        stub_vdb.upsert = AsyncMock(side_effect=lambda *a, **k: True)
        stub_vdb.search = AsyncMock(side_effect=lambda *a, **k: [])
        stub_vdb.batch_upsert = AsyncMock(side_effect=lambda *a, **k: True)
        stub_vdb.delete = AsyncMock(side_effect=lambda *a, **k: True)
        stub_vdb.get_by_id = AsyncMock(return_value=None)
        mock_create_vdb.return_value = stub_vdb
        
        # Создаем минимальное приложение без middleware для unit тестов
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from api.routes import health, materials, prices, reference, search
        
        app = FastAPI(title="Test API")
        
        # Добавляем только роутеры без middleware
        app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
        app.include_router(reference.router, prefix="/api/v1/reference", tags=["reference"])
        app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
        app.include_router(prices.router, prefix="/api/v1/prices", tags=["prices"])
        app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
        
        @app.get("/")
        async def root():
            return {"message": "Welcome to Test API", "version": "1.0.0"}
        
        with patch('core.config.get_vector_db_client') as mock_vector_client, \
             patch('core.config.get_ai_client') as mock_ai, \
             patch('qdrant_client.QdrantClient') as mock_qdrant:
            
            mock_vector_client.return_value = Mock()
            mock_ai.return_value = Mock()
            mock_qdrant.return_value.get_collections.return_value = Mock()
            
            return TestClient(app)

@pytest.fixture
def client_real():
    """Test client с реальными БД для интеграционных тестов"""
    with patch.dict(os.environ, TEST_SETTINGS):
        from main import app
        return TestClient(app)

@pytest.fixture
def client(test_mode):
    """Автоматический выбор клиента в зависимости от режима"""
    if test_mode == "real":
        return client_real()
    else:
        return client_mock()

# ============================================================================
# QDRANT ФИКСТУРЫ
# ============================================================================

@pytest.fixture(scope="session")
def qdrant_client_real():
    """Real Qdrant client для интеграционных тестов"""
    from core.config import settings
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=30
            )
            client.get_collections()
            logger.info(f"✅ Successfully connected to Qdrant at {settings.QDRANT_URL}")
            return client
        except Exception as e:
            logger.warning(f"❌ Attempt {attempt + 1} failed to connect to Qdrant: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise Exception(f"Failed to connect to Qdrant after {max_retries} attempts: {e}")

@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client для unit тестов"""
    client = MagicMock()
    client.get_collections.return_value = MagicMock(collections=[])
    client.create_collection.return_value = True
    client.delete_collection.return_value = True
    client.search.return_value = []
    client.upsert.return_value = True
    return client

@pytest.fixture
def qdrant_client(test_mode):
    """Автоматический выбор Qdrant клиента"""
    if test_mode == "real":
        return qdrant_client_real()
    else:
        return mock_qdrant_client()

# ============================================================================
# CLEANUP ФИКСТУРЫ
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_collections(test_mode, request):
    """Очистка тестовых коллекций (только для реальных БД)"""
    if test_mode != "real":
        yield
        return
        
    try:
        # Получаем реальный клиент для очистки
        from core.config import settings
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=30
        )
        
        # Cleanup before test
        _cleanup_test_collections(client)
        
        yield
        
        # Cleanup after test (только если не production)
        if not _is_production_db():
            _cleanup_test_collections(client)
    except Exception as e:
        logger.warning(f"⚠️ Error in cleanup: {e}")
        yield

def _is_production_db() -> bool:
    """Проверка на production БД"""
    from core.config import settings
    return "prod" in settings.QDRANT_URL.lower() or "production" in settings.QDRANT_URL.lower()

def _cleanup_test_collections(client: QdrantClient):
    """Очистка тестовых коллекций"""
    try:
        collections = client.get_collections()
        test_collections = [
            c.name for c in collections.collections 
            if (c.name.startswith('supplier_TEST') or 
                c.name.startswith('test_') or
                c.name.startswith('supplier_SUP_TEST'))
        ]
        
        for collection_name in test_collections:
            try:
                client.delete_collection(collection_name)
                logger.info(f"🧹 Deleted test collection: {collection_name}")
            except Exception as e:
                logger.warning(f"⚠️ Error deleting collection {collection_name}: {e}")
                
    except Exception as e:
        logger.warning(f"⚠️ Error getting collections: {e}")

# ============================================================================
# MOCK SERVICES ФИКСТУРЫ
# ============================================================================

@pytest.fixture
def mock_vector_db():
    """Mock vector database"""
    mock_db = Mock()
    mock_db.upsert = AsyncMock(return_value=True)
    mock_db.search = AsyncMock(return_value=[])
    mock_db.get_by_id = AsyncMock(return_value=None)
    mock_db.delete = AsyncMock(return_value=True)
    mock_db.create_collection = AsyncMock(return_value=True)
    mock_db.collection_exists = AsyncMock(return_value=True)
    return mock_db

@pytest.fixture
def mock_materials_service(sample_material):
    """Mock MaterialsService"""
    from core.schemas.materials import MaterialBatchResponse
    
    service = Mock()
    service.create_material = AsyncMock(return_value=sample_material)
    service.get_material = AsyncMock(return_value=sample_material)
    service.get_materials = AsyncMock(return_value=[sample_material])
    service.update_material = AsyncMock(return_value=sample_material)
    service.delete_material = AsyncMock(return_value=True)
    service.search_materials = AsyncMock(return_value=[sample_material])
    
    # Mock batch response
    batch_response = MaterialBatchResponse(
        success=True,
        total_processed=1,
        successful_creates=1,
        failed_creates=0,
        created_materials=[sample_material],
        errors=[],
        processing_time_seconds=0.1
    )
    service.create_materials_batch = AsyncMock(return_value=batch_response)
    return service

@pytest.fixture
def mock_category_service(sample_category):
    """Mock CategoryService"""
    service = Mock()
    service.create_category = AsyncMock(return_value=sample_category)
    service.get_categories = AsyncMock(return_value=[sample_category])
    service.delete_category = AsyncMock(return_value=True)
    return service

@pytest.fixture
def mock_unit_service(sample_unit):
    """Mock UnitService"""
    service = Mock()
    service.create_unit = AsyncMock(return_value=sample_unit)
    service.get_units = AsyncMock(return_value=[sample_unit])
    service.delete_unit = AsyncMock(return_value=True)
    return service

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    client = AsyncMock()
    client.embeddings = AsyncMock()
    client.embeddings.create = AsyncMock()
    client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    )
    return client

@pytest.fixture
def mock_database_services():
    """Mock all database services"""
    return {
        "vector_db": Mock(),
        "postgresql": Mock(),
        "redis": Mock()
    }

# ============================================================================
# SAMPLE DATA ФИКСТУРЫ
# ============================================================================

@pytest.fixture
def sample_material():
    """Sample material для тестов"""
    from core.schemas.materials import Material
    return Material(
        id="test-id",
        name="Тестовый материал",
        use_category="Тестовая категория",
        unit="кг",
        sku="TEST001",
        description="Тестовое описание",
        embedding=[0.1, 0.2, 0.3],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_category():
    """Sample category для тестов"""
    from core.schemas.materials import Category
    return Category(name="Тестовая категория", description="Описание")

@pytest.fixture
def sample_unit():
    """Sample unit для тестов"""
    from core.schemas.materials import Unit
    return Unit(name="кг", description="Килограмм")

@pytest.fixture
def sample_material_data():
    """Sample material data dictionary"""
    return {
        "name": "Test Cement",
        "use_category": "Building Materials",
        "unit": "kg",
        "price": 45.50,
        "description": "Test cement for unit testing",
        "sku": "TEST_001"
    }

@pytest.fixture
def sample_material_create():
    """Sample MaterialCreate для тестов"""
    from core.schemas.materials import MaterialCreate
    return MaterialCreate(
        name="Портландцемент М500",
        use_category="Цемент",
        unit="кг",
        description="Высококачественный цемент",
        sku="PC500"
    )

@pytest.fixture
def sample_price_data():
    """Sample price data для тестов с корректными названиями колонок"""
    return [
        {
            "name": "Cement Portland Test",
            "use_category": "Building Materials", 
            "unit": "kg",
            "price": 45.50,
            "description": "High quality cement for testing"
        },
        {
            "name": "Sand Construction Test",
            "use_category": "Building Materials",
            "unit": "m3", 
            "price": 1200.00,
            "description": "Washed construction sand for testing"
        }
    ]

@pytest.fixture
def test_supplier_id():
    """Generate unique test supplier ID"""
    return f"TEST_{int(time.time())}"

# ============================================================================
# AUTO-MOCK ФИКСТУРА ДЛЯ UNIT ТЕСТОВ
# ============================================================================

@pytest.fixture(autouse=True)
def auto_mock_for_unit_tests(request, mock_materials_service, mock_category_service, mock_unit_service):
    """Автоматическое мокирование для unit тестов"""
    # Проверяем если тест помечен как unit
    if request.node.get_closest_marker("unit"):
        try:
            with patch('services.materials.MaterialsService', return_value=mock_materials_service), \
                 patch('services.materials.CategoryService', return_value=mock_category_service), \
                 patch('services.materials.UnitService', return_value=mock_unit_service):
                yield
        except (ImportError, AttributeError):
            # Если моки не могут быть применены, просто пропускаем
            yield
    else:
        yield 

# ---------------------------------------------------------------------------
# GLOBAL PATCHES FOR UNIT/FUNCTIONAL TESTS (mock mode)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_qdrant_client(monkeypatch, test_mode):
    """Patch qdrant_client.QdrantClient with a lightweight fake in mock mode."""
    if test_mode == "real":
        # Do nothing in real mode
        yield
        return

    from unittest.mock import MagicMock

    class _FakeQdrantClient(MagicMock):
        def __init__(self, *args, **kwargs):
            super().__init__()
            # default mock behaviour
            self.get_collections.return_value = {"result": {"collections": []}}
            self.upsert.return_value = None
            self.recreate_collection.return_value = None
            self.delete_collection.return_value = None
            self.search.return_value = []

    monkeypatch.setattr("qdrant_client.QdrantClient", _FakeQdrantClient)
    yield 

@pytest.fixture(autouse=True)
def _patch_openai(monkeypatch, test_mode):
    """Provide dummy OpenAI client to avoid real network calls."""
    if test_mode == "real":
        yield
        return

    import sys
    import types

    fake_module = types.ModuleType("openai")

    class _FakeEmbeddings:
        def create(self, *args, **kwargs):
            # Return deterministic vector size 1536 filled with zeros
            return {"data": [{"embedding": [0.0] * 1536}]}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            self.embeddings = _FakeEmbeddings()

    fake_module.OpenAI = lambda *args, **kwargs: _FakeClient()
    sys.modules["openai"] = fake_module
    yield

# ---------------------------------------------------------------------------
# Disable Uvicorn auto-reload in test sessions to avoid infinite restart loops
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _disable_uvicorn_reload():
    """Disable Uvicorn reload **only** via WATCHFILES_DISABLE env-var.

    The official recommendation from Uvicorn maintainers is to rely on the
    ``WATCHFILES_DISABLE`` environment variable (see https://www.uvicorn.org/settings/#development).
    All test processes inherit this variable, so additional monkey-patching of
    ``uvicorn.run`` / ``uvicorn.Config`` is no longer required.
    """
    # All heavy monkey-patching was removed – the environment variable is
    # sufficient to keep the reloader off during tests.
    yield

# ---------------------------------------------------------------------------
# Ensure hot-reload subsystem (watchfiles) is disabled for the entire pytest
# session (including any child processes).  Uvicorn respects the standard
# env-var ``WATCHFILES_DISABLE`` – when it is truthy, autoreload is skipped.
# This approach is officially documented and avoids the need for heavy monkey
#-patching or sys.modules stubbing.
# ---------------------------------------------------------------------------
os.environ.setdefault("WATCHFILES_DISABLE", "true")

# ---------------------------------------------------------------------------
# Patch DatabaseFactory.create_vector_database to avoid real initialization
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_vector_db_factory(monkeypatch):
    """Patch DatabaseFactory.create_vector_database to return a lightweight stub
    that adheres to the IVectorDatabase interface signatures used in tests.
    This prevents expensive (or recursive) initialisation when core services
    call `get_vector_database()` during functional workflows.
    """
    from unittest.mock import MagicMock

    from core.database.factories import DatabaseFactory

    class _StubVectorDB(MagicMock):
        async def collection_exists(self, *args, **kwargs):
            return False

        async def create_collection(self, *args, **kwargs):
            return True

        async def scroll_all(self, *args, **kwargs):
            return []

        async def upsert(self, *args, **kwargs):
            return True

        async def search(self, *args, **kwargs):
            return []

        async def batch_upsert(self, *args, **kwargs):
            return True

        async def delete(self, *args, **kwargs):
            return True

        async def get_by_id(self, *args, **kwargs):
            return None

    stub_instance = _StubVectorDB()

    monkeypatch.setattr(DatabaseFactory, "create_vector_database", lambda *a, **kw: stub_instance)
    # Also patch the convenience accessor that might be cached already
    monkeypatch.setattr("core.database.factories.get_vector_database", lambda: stub_instance, raising=False)
    yield

# ---------------------------------------------------------------------------
# Stub out QdrantVectorDatabase entirely so any direct import uses stub.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_qdrant_adapter(monkeypatch):
    """Replace QdrantVectorDatabase with a stub that satisfies used methods."""
    try:
        import core.database.adapters.qdrant_adapter as qa
    except ImportError:
        yield
        return

    from unittest.mock import MagicMock

    class _StubQdrantVectorDB(MagicMock):
        async def collection_exists(self, *args, **kwargs):
            return False

        async def create_collection(self, *args, **kwargs):
            return True

        async def scroll_all(self, *args, **kwargs):
            return []

        async def upsert(self, *args, **kwargs):
            return True

        async def search(self, *args, **kwargs):
            return []

        async def batch_upsert(self, *args, **kwargs):
            return True

        async def delete(self, *args, **kwargs):
            return True

        async def get_by_id(self, *args, **kwargs):
            return None

        async def health_check(self):
            return {"status": "ok"}

    monkeypatch.setattr(qa, "QdrantVectorDatabase", _StubQdrantVectorDB)
    yield

# ---------------------------------------------------------------------------
# Replace Uvicorn WatchFilesReload supervisor with dummy to prevent restarts
# in processes where reload still gets enabled (e.g., when command-line
# arguments force it).  This patch affects the *current* interpreter only but
# will make the supervisor inert so that even if created it will not loop.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_uvicorn_watchfiles(monkeypatch):
    """No-op: we rely on WATCHFILES_DISABLE instead of patching WatchFilesReload."""
    yield