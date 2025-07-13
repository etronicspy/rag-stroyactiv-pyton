# Project Rules for RAG Construction Materials API

> Development standards AI should follow for the current project

## 1. Framework Version and Dependencies

### Python Environment
- **Python Version**: 3.9+
- **Main Framework**: FastAPI (latest stable)
- **Database ORM**: SQLAlchemy 2.0+
- **Migration Tool**: Alembic
- **Validation**: Pydantic v2
- **Testing**: pytest with async support
- **Code Quality**: Black, isort, mypy

### Key Dependencies
```python
# Core API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
alembic>=1.12.0

# Vector Databases
qdrant-client>=1.6.0
weaviate-client>=3.24.0
pinecone-client>=2.2.0

# AI/ML
openai>=1.0.0
langchain>=0.1.0

# Caching & Performance
redis>=5.0.0
aioredis>=2.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
```

## 2. Testing Framework Details

### Testing Strategy
- **Unit Tests**: pytest with async support
- **Integration Tests**: Real database connections with rollback
- **API Tests**: httpx.AsyncClient for FastAPI testing
- **Mock Strategy**: unittest.mock.AsyncMock for external services
- **Fixtures**: Shared test data and database sessions

### Test Structure
```python
# Test file naming: test_{module_name}.py
# Test class naming: TestClassName
# Test method naming: test_method_description

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

class TestMaterialService:
    @pytest.fixture
    async def service(self):
        mock_repo = AsyncMock()
        return MaterialService(repository=mock_repo)
    
    async def test_create_material_success(self, service):
        # Arrange, Act, Assert pattern
        pass
```

### Coverage Requirements
- **Minimum Coverage**: 80% for core business logic
- **Critical Paths**: 95% coverage for API endpoints
- **Database Operations**: 90% coverage for repositories
- **External Integrations**: Mock all external API calls

## 3. APIs to Avoid

### Deprecated/Unsafe Patterns
```python
# ❌ AVOID: Direct database connections
import sqlite3
conn = sqlite3.connect('database.db')

# ✅ USE: SQLAlchemy with dependency injection
from core.dependencies.database import get_db_session

# ❌ AVOID: Synchronous operations in async context
def sync_function():
    time.sleep(1)
    
# ✅ USE: Proper async patterns
async def async_function():
    await asyncio.sleep(1)

# ❌ AVOID: Hardcoded configuration
API_KEY = "sk-1234567890"
DATABASE_URL = "postgresql://user:pass@localhost/db"

# ✅ USE: Environment variables with Pydantic
from core.config.base import settings
api_key = settings.OPENAI_API_KEY
database_url = settings.DATABASE_URL
```

### Forbidden Libraries/Patterns
- **requests** → Use **httpx** for async HTTP calls
- **json.loads/dumps** → Use **Pydantic** for data validation
- **os.environ** → Use **Pydantic Settings** for configuration
- **time.sleep** → Use **asyncio.sleep** in async functions
- **threading** → Use **asyncio** for concurrency
- **pickle** → Use **JSON** or **Pydantic** for serialization

## 4. Architecture Patterns

### Repository Pattern
```python
# Always use abstract interfaces
from abc import ABC, abstractmethod

class MaterialRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, material: MaterialModel) -> MaterialModel:
        pass
    
    @abstractmethod
    async def get_by_id(self, material_id: str) -> Optional[MaterialModel]:
        pass

class MaterialRepository(MaterialRepositoryInterface):
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create(self, material: MaterialModel) -> MaterialModel:
        # Implementation with proper error handling
        pass
```

### Dependency Injection
```python
# Use FastAPI's dependency injection system
from fastapi import Depends
from core.dependencies.database import get_db_session
from core.repositories.material_repository import MaterialRepository

def get_material_repository(
    db: AsyncSession = Depends(get_db_session)
) -> MaterialRepository:
    return MaterialRepository(db)

@router.post("/materials/")
async def create_material(
    material_data: MaterialCreateModel,
    repo: MaterialRepository = Depends(get_material_repository)
) -> StandardResponse:
    # Implementation
    pass
```

### Error Handling
```python
# Always use proper HTTP status codes and error models
from fastapi import HTTPException
from core.schemas.response_models import ErrorResponse

try:
    result = await service.process_material(material_data)
    return StandardResponse(success=True, data=result)
except ValidationError as e:
    raise HTTPException(
        status_code=422,
        detail=ErrorResponse(
            error="Validation failed",
            details=str(e)
        ).dict()
    )
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )
```

## 5. Security Requirements

### Environment Variables
```python
# All configuration through Pydantic Settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    
    # API Keys (never hardcode!)
    OPENAI_API_KEY: str
    QDRANT_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env.local"
        case_sensitive = True
```

### Input Validation
```python
# Always validate inputs with Pydantic
from pydantic import BaseModel, Field, validator

class MaterialCreateModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0, le=1000000)
    category: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
```

## 6. Performance Guidelines

### Database Operations
```python
# Use batching for bulk operations
async def batch_insert_materials(
    materials: List[MaterialModel],
    batch_size: int = 100
) -> List[MaterialModel]:
    results = []
    for i in range(0, len(materials), batch_size):
        batch = materials[i:i + batch_size]
        batch_results = await repository.bulk_create(batch)
        results.extend(batch_results)
    return results

# Use connection pooling
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600
)
```

### Vector Operations
```python
# Batch vector operations
async def batch_upsert_embeddings(
    embeddings: List[Dict],
    collection_name: str,
    batch_size: int = 100
) -> bool:
    for i in range(0, len(embeddings), batch_size):
        batch = embeddings[i:i + batch_size]
        await vector_client.upsert(
            collection_name=collection_name,
            points=batch
        )
    return True
```

## 7. Logging and Monitoring

### Structured Logging
```python
import structlog
from core.logging.config import get_logger

logger = get_logger(__name__)

# Log all database operations
async def create_material(material_data: dict) -> dict:
    logger.info(
        "Creating material",
        material_name=material_data.get("name"),
        user_id=current_user.id
    )
    
    try:
        result = await repository.create(material_data)
        logger.info(
            "Material created successfully",
            material_id=result["id"],
            duration_ms=timer.elapsed()
        )
        return result
    except Exception as e:
        logger.error(
            "Failed to create material",
            error=str(e),
            material_data=material_data
        )
        raise
```

### Health Checks
```python
# Implement health checks for all external dependencies
@router.get("/health")
async def health_check() -> Dict[str, str]:
    checks = {
        "database": await check_database_connection(),
        "qdrant": await check_qdrant_connection(),
        "redis": await check_redis_connection(),
        "openai": await check_openai_connection()
    }
    
    status = "healthy" if all(
        check == "ok" for check in checks.values()
    ) else "unhealthy"
    
    return {"status": status, **checks}
```

## 8. File Naming Conventions

### Safe File Names
```python
# ✅ GOOD: Descriptive, non-conflicting names
material_service.py
material_repository.py
material_models.py
api_exceptions.py
app_config.py
log_config.py

# ❌ BAD: Conflicts with Python stdlib
config.py  # conflicts with stdlib
logging.py  # conflicts with stdlib
os.py      # conflicts with stdlib
time.py    # conflicts with stdlib
```

### Module Structure
```
api/routes/
├── material_routes.py
├── search_routes.py
└── health_routes.py

core/services/
├── material_service.py
├── embedding_service.py
└── search_service.py

core/repositories/
├── material_repository.py
├── vector_repository.py
└── cache_repository.py
```

---

> 🎯 **Remember**: These rules ensure code quality, security, and maintainability. Always follow these patterns when generating or modifying code for this project.