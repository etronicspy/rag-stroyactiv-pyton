# 🎯 Trae IDE Configuration for RAG Construction Materials API

> Специальная конфигурация и правила применения для Trae IDE

## 🔧 IDE-Specific Rules

### Auto-completion & Suggestions
- **Приоритет**: Предлагать безопасные имена файлов из approved списка
- **Блокировка**: Предупреждать о конфликтных именах файлов из forbidden списка
- **Контекст**: Учитывать текущую папку при предложении имен

### Code Generation Patterns

#### FastAPI Endpoints
```python
# Template for new API endpoints
from fastapi import APIRouter, Depends, HTTPException
from core.dependencies.database import get_db_session
from core.schemas.response_models import StandardResponse
from typing import List

router = APIRouter(prefix="/api/v1", tags=["materials"])

@router.get("/endpoint", response_model=StandardResponse)
async def endpoint_name(
    db: AsyncSession = Depends(get_db_session)
) -> StandardResponse:
    """Endpoint description.
    
    Args:
        db: Database session
        
    Returns:
        StandardResponse: Response with data
        
    Raises:
        HTTPException: When operation fails
    """
    try:
        # Implementation here
        return StandardResponse(success=True, data={})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### Repository Pattern
```python
# Template for new repository classes
from abc import ABC, abstractmethod
from typing import List, Optional
from core.database.interfaces import BaseRepository

class MaterialRepositoryInterface(ABC):
    """Abstract interface for material repository."""
    
    @abstractmethod
    async def create(self, material_data: dict) -> dict:
        """Create new material."""
        pass
    
    @abstractmethod
    async def get_by_id(self, material_id: str) -> Optional[dict]:
        """Get material by ID."""
        pass

class MaterialRepository(MaterialRepositoryInterface):
    """Concrete implementation of material repository."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def create(self, material_data: dict) -> dict:
        """Create new material in database."""
        # Implementation here
        pass
```

#### Pydantic Models
```python
# Template for new Pydantic models
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class MaterialModel(BaseModel):
    """Material data model.
    
    Attributes:
        name: Material name
        description: Material description
        price: Material price
    """
    
    name: str = Field(
        ..., 
        description="Material name",
        example="Cement Portland"
    )
    description: str = Field(
        ..., 
        description="Material description",
        example="High-quality Portland cement"
    )
    price: float = Field(
        ..., 
        gt=0,
        description="Material price per unit",
        example=25.50
    )
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Cement Portland",
                "description": "High-quality Portland cement",
                "price": 25.50
            }
        }
```

### File Naming Suggestions

#### When creating new files, suggest:
```
API Routes:
- material_routes.py (NOT routes.py)
- search_routes.py (NOT search.py)
- price_routes.py (NOT prices.py)

Services:
- material_service.py (NOT service.py)
- embedding_service.py (NOT embeddings.py)
- search_service.py (NOT search.py)

Repositories:
- material_repository.py (NOT repository.py)
- vector_repository.py (NOT vector.py)
- cache_repository.py (NOT cache.py)

Models:
- material_models.py (NOT models.py)
- response_models.py (NOT responses.py)
- request_models.py (NOT requests.py)

Config:
- app_settings.py (NOT config.py)
- database_config.py (NOT db.py)
- log_config.py (NOT logging.py)

Exceptions:
- api_exceptions.py (NOT exceptions.py)
- database_exceptions.py (NOT db_exceptions.py)
- custom_exceptions.py (NOT custom.py)
```

## 🚨 Real-time Validation Rules

### File Creation Warnings
```yaml
Forbidden Patterns:
  - "*.py" files matching Python stdlib names
  - Files without proper prefixes in core modules
  - Generic names like "utils.py", "helpers.py", "base.py"

Warning Messages:
  - "⚠️ Filename '{filename}' conflicts with Python stdlib. Suggest: '{alternative}'"
  - "🚨 CRITICAL: This filename will cause import conflicts!"
  - "💡 Better name suggestion: '{suggested_name}'"
```

### Code Quality Checks
```yaml
Required Elements:
  - Type hints for all function parameters and returns
  - Docstrings for all public functions and classes
  - Pydantic validation for all API models
  - Error handling with proper HTTP status codes
  - Logging for all database operations

Forbidden Patterns:
  - Hardcoded URLs, ports, timeouts
  - Magic numbers without constants
  - Direct database credentials in code
  - Missing async/await for database operations
```

## 🎨 Code Formatting Rules

### Import Organization
```python
# Standard library imports
import os
import sys
from typing import List, Optional, Dict

# Third-party imports
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Local application imports
from core.config.app_settings import settings
from core.database.repositories.material_repository import MaterialRepository
from core.schemas.material_models import MaterialModel
```

### Function Signatures
```python
# Always include type hints and docstrings
async def process_materials(
    materials: List[MaterialModel],
    db_session: AsyncSession,
    batch_size: int = 100
) -> Dict[str, int]:
    """Process materials in batches.
    
    Args:
        materials: List of material models to process
        db_session: Database session for operations
        batch_size: Number of materials to process in one batch
        
    Returns:
        Dict with processing statistics
        
    Raises:
        DatabaseError: When database operation fails
        ValidationError: When material data is invalid
    """
```

## 🔍 Context-Aware Suggestions

### Based on Current Directory
```yaml
api/routes/:
  - Suggest: "*_routes.py" pattern
  - Template: FastAPI router with proper imports
  - Validation: Ensure /api/v1/ prefix

core/config/:
  - Suggest: "*_config.py" or "*_settings.py" pattern
  - Template: Pydantic Settings class
  - Validation: Environment variable usage

core/repositories/:
  - Suggest: "*_repository.py" pattern
  - Template: Repository interface + implementation
  - Validation: Abstract base class usage

services/:
  - Suggest: "*_service.py" pattern
  - Template: Service class with dependency injection
  - Validation: Proper error handling

core/schemas/:
  - Suggest: "*_models.py" pattern
  - Template: Pydantic models with examples
  - Validation: Field descriptions and validators
```

## 🛡️ Security Enforcement

### Environment Variables
```yaml
Required Validation:
  - All config values from environment variables
  - No hardcoded secrets or API keys
  - Proper Pydantic field validation
  - Default values or required fields

Forbidden Patterns:
  - Direct string literals for URLs/ports
  - Embedded API keys or passwords
  - Unvalidated environment variable access
```

### Input Validation
```yaml
API Endpoints:
  - All inputs through Pydantic models
  - Proper HTTP status codes
  - Error handling with try/catch
  - Request size limitations

Database Operations:
  - SQL injection prevention
  - Parameterized queries only
  - Connection timeout handling
  - Proper transaction management
```

## 📊 Performance Guidelines

### Database Operations
```python
# Preferred patterns for database operations

# ✅ GOOD: Batch operations
async def batch_insert_materials(materials: List[MaterialModel]):
    async with get_db_session() as session:
        batch_size = settings.DATABASE_BATCH_SIZE
        for i in range(0, len(materials), batch_size):
            batch = materials[i:i + batch_size]
            await session.execute(insert_statement, batch)
        await session.commit()

# ✅ GOOD: Connection pooling
async def get_materials_with_pool():
    async with get_db_session() as session:
        result = await session.execute(select_statement)
        return result.fetchall()

# ❌ BAD: Individual operations
for material in materials:
    await insert_single_material(material)  # Too many DB calls
```

### Vector Operations
```python
# ✅ GOOD: Batch vector operations
async def batch_upsert_embeddings(
    embeddings: List[Dict],
    collection_name: str
) -> bool:
    """Upsert embeddings in batches for better performance."""
    batch_size = settings.VECTOR_DB_BATCH_SIZE
    
    for i in range(0, len(embeddings), batch_size):
        batch = embeddings[i:i + batch_size]
        await vector_client.upsert(
            collection_name=collection_name,
            points=batch
        )
    return True
```

## 🧪 Testing Patterns

### Test File Naming
```yaml
Test Files:
  - test_material_service.py (for services/material_service.py)
  - test_material_routes.py (for api/routes/material_routes.py)
  - test_vector_repository.py (for repositories/vector_repository.py)

Test Structure:
  - tests/unit/ - Unit tests
  - tests/integration/ - Integration tests
  - tests/fixtures/ - Test fixtures
  - tests/mocks/ - Mock objects
```

### Test Templates
```python
# Unit test template
import pytest
from unittest.mock import AsyncMock, patch
from services.material_service import MaterialService

class TestMaterialService:
    """Test cases for MaterialService."""
    
    @pytest.fixture
    async def service(self):
        """Create service instance for testing."""
        mock_repo = AsyncMock()
        return MaterialService(repository=mock_repo)
    
    async def test_create_material_success(self, service):
        """Test successful material creation."""
        # Arrange
        material_data = {"name": "Test Material", "price": 10.0}
        
        # Act
        result = await service.create_material(material_data)
        
        # Assert
        assert result["success"] is True
        assert "id" in result["data"]
```

## 🚀 Quick Actions

### Trae IDE Commands
```yaml
Quick Commands:
  - "Create FastAPI Route" → Generate router template
  - "Create Repository" → Generate repository interface + implementation
  - "Create Pydantic Model" → Generate model with validation
  - "Check Filename Conflicts" → Validate against forbidden names
  - "Generate Test File" → Create corresponding test file
  - "Add Docstring" → Generate docstring template
  - "Fix Import Order" → Reorganize imports per PEP 8
  - "Add Type Hints" → Add missing type annotations
```

### Code Snippets
```yaml
Snippets:
  - "fastapi-route" → Complete route template
  - "pydantic-model" → Model with validation
  - "repository-class" → Repository pattern implementation
  - "async-function" → Async function with proper typing
  - "error-handler" → Exception handling template
  - "test-class" → Test class with fixtures
```

---

> 🎯 **Цель**: Этот файл конфигурации обеспечивает интеграцию всех правил проекта с возможностями Trae IDE для максимальной продуктивности разработки.

> 🔄 **Синхронизация**: Автоматически обновляется при изменениях в основных правилах проекта.