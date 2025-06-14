"""
Mock endpoints for middleware testing.
Only available in development environment.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json

router = APIRouter()

class TestMaterial(BaseModel):
    name: str
    description: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Test Material",
                "description": "Test description for middleware validation"
            }
        }
    }

@router.post("/materials")
async def test_create_material(material: TestMaterial) -> Dict[str, Any]:
    """Mock endpoint for testing middleware POST validation."""
    return {
        "status": "success",
        "data": material.dict(),
        "message": "Test material processed successfully",
        "middleware_test": True
    }

@router.get("/materials/{material_id}")
async def test_get_material(material_id: int) -> Dict[str, Any]:
    """Mock endpoint for testing middleware GET validation."""
    return {
        "status": "success",
        "data": {"id": material_id, "name": f"Test Material {material_id}"},
        "message": "Test material retrieved successfully",
        "middleware_test": True
    }

@router.get("/large-data")
async def test_large_data() -> Dict[str, Any]:
    """Endpoint for testing compression middleware with large responses."""
    # Generate data > 50KB for compression testing
    base_text = "This is a test string for compression testing middleware with various patterns and data types. " \
                "Включаем текст на русском языке для лучшего тестирования Unicode сжатия. " \
                "Adding numbers: 1234567890, symbols: !@#$%^&*()_+-=[]{}|;':\",./<>? " \
                "Повторяющиеся паттерны для демонстрации эффективности алгоритма сжатия. "
    
    # Create approximately 50KB of data
    large_text = base_text * 500  # ~50KB
    
    # Add structured data for better compression
    structured_data = {
        "repeated_pattern": "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 100,
        "numbers": list(range(1000)),
        "cyrillic_text": "Тестирование кириллического текста для проверки UTF-8 сжатия" * 50,
        "json_structure": [{"id": i, "name": f"Item {i}", "value": i * 2} for i in range(100)]
    }
    
    return {
        "status": "success",
        "large_text": large_text,
        "structured_data": structured_data,
        "size_bytes": len(large_text) + len(str(structured_data)),
        "message": "Large data response for compression testing (~50KB)",
        "middleware_test": True,
        "test_type": "compression",
        "compression_note": "This response should be compressed with Brotli or Gzip"
    }

@router.post("/upload-test")
async def test_file_upload_security(
    content_type: Optional[str] = Header(None),
    content_length: Optional[int] = Header(None)
) -> Dict[str, Any]:
    """Mock endpoint for testing file upload security middleware."""
    return {
        "status": "success",
        "content_type": content_type,
        "content_length": content_length,
        "message": "File upload security test endpoint",
        "middleware_test": True,
        "test_type": "security"
    }

@router.get("/sql-injection-test")
async def test_sql_injection_query(q: Optional[str] = None) -> Dict[str, Any]:
    """Endpoint for testing SQL injection protection in query params."""
    return {
        "status": "success",
        "query": q,
        "message": "SQL injection test endpoint - query parameters",
        "middleware_test": True,
        "test_type": "security_query"
    }

@router.get("/xss-test")
async def test_xss_query(search: Optional[str] = None) -> Dict[str, Any]:
    """Endpoint for testing XSS protection in query params."""
    return {
        "status": "success", 
        "search": search,
        "message": "XSS test endpoint - query parameters",
        "middleware_test": True,
        "test_type": "security_xss"
    }

@router.get("/cyrillic-test")
async def test_cyrillic_content(text: Optional[str] = None) -> Dict[str, Any]:
    """Endpoint for testing Cyrillic content handling."""
    return {
        "status": "success",
        "text": text,
        "message": "Cyrillic content test endpoint",
        "middleware_test": True,
        "test_type": "cyrillic"
    } 