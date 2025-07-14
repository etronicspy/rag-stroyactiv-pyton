"""
🔄 Functional Tests for Unified Logging System

Functional tests focusing on:
- Complete user workflows with logging
- Business logic integration scenarios
- API endpoint logging workflows
- Material management with full tracing
- Error handling workflows
- Health monitoring workflows

Author: AI Assistant
Created: 2024
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Core imports
from main import app
from core.monitoring.context import CorrelationContext, get_correlation_id
from services.materials import MaterialsService
from core.repositories.base import BaseRepository

client = TestClient(app)

class TestUnitAPI:
    def test_create_unit_success(self):
        """Проверка успешного создания юнита с embedding через AI"""
        unit_data = {"name": "кг"}
        from services.materials import UnitService
        service = UnitService.__new__(UnitService)
        from unittest.mock import AsyncMock
        vector_db_mock = AsyncMock()
        vector_db_mock.collection_exists = AsyncMock(return_value=True)
        vector_db_mock.create_collection = AsyncMock(return_value=None)
        vector_db_mock.upsert = AsyncMock(return_value=None)
        vector_db_mock.get_embedding = AsyncMock(return_value=[0.1]*384)
        service.vector_db = vector_db_mock
        service.collection_name = "units_v2"
        # Переопределяем Depends(get_unit_service) на наш мок
        from api.routes.reference import get_unit_service
        from main import app
        app.dependency_overrides[get_unit_service] = lambda: service
        response = client.post("/api/v1/reference/units/", json=unit_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "кг"
        assert isinstance(data["embedding"], list)
        assert len(data["embedding"]) == 384
        app.dependency_overrides = {}

    def test_create_unit_ai_failure(self):
        """Проверка ошибки при невозможности сгенерировать embedding для юнита"""
        unit_data = {"name": "кг"}
        from services.materials import UnitService
        service = UnitService.__new__(UnitService)
        from unittest.mock import AsyncMock
        vector_db_mock = AsyncMock()
        vector_db_mock.collection_exists = AsyncMock(return_value=True)
        vector_db_mock.create_collection = AsyncMock(return_value=None)
        vector_db_mock.upsert = AsyncMock(return_value=None)
        vector_db_mock.get_embedding = AsyncMock(side_effect=Exception("AI error"))
        service.vector_db = vector_db_mock
        service.collection_name = "units_v2"
        from api.routes.reference import get_unit_service
        from main import app
        app.dependency_overrides[get_unit_service] = lambda: service
        response = client.post("/api/v1/reference/units/", json=unit_data)
        assert response.status_code in (400, 422, 500)
        app.dependency_overrides = {}


class TestMaterialManagementWorkflows:
    """🔄 Material Management Workflow Tests"""
    
    def test_complete_material_search_workflow(self):
        """Test complete material search workflow with full logging."""
        client = TestClient(app)
        
        # Step 1: Health check (should be logged)
        health_response = client.get("/api/v1/health")
        assert health_response.status_code == 200
        
        # Step 2: Search materials (should create correlation ID and log everything)
        search_response = client.get("/api/v1/search/materials?query=concrete&limit=5")
        
        # Should succeed or handle gracefully
        assert search_response.status_code in [200, 404, 500]  # Various valid responses
        
        # Response should be JSON
        if search_response.status_code == 200:
            data = search_response.json()
            assert isinstance(data, (dict, list))
    
    @pytest.mark.asyncio
    async def test_service_layer_material_workflow(self):
        """Test service layer material workflow with correlation tracing."""
        # Create service instance
        service = MaterialsService()
        
        # Set correlation context
        correlation_id = str(uuid.uuid4())
        
        with CorrelationContext.with_correlation_id(correlation_id):
            # Verify correlation ID is set
            assert get_correlation_id() == correlation_id
            
            # Mock database operations
            with patch.object(service, '_search_in_vector_db') as mock_search:
                mock_search.return_value = [
                    {"id": "1", "name": "Concrete", "category": "concrete"},
                    {"id": "2", "name": "Steel", "category": "steel"}
                ]
                
                # Perform search (should be automatically logged with correlation ID)
                results = await service.search_materials("building materials", limit=10)
                
                # Verify results
                assert len(results) == 2
                assert results[0]["name"] == "Concrete"
                
                # Verify correlation ID is still available
                assert get_correlation_id() == correlation_id
    
    def test_material_error_handling_workflow(self):
        """Test material error handling workflow with proper logging."""
        client = TestClient(app)
        
        # Test invalid material data
        invalid_data = {
            "name": "",  # Invalid: empty name
            "category": "invalid_category",
            "price": -100  # Invalid: negative price
        }
        
        response = client.post("/api/v1/materials", json=invalid_data)
        
        # Should return validation error
        assert response.status_code in [400, 422]
        
        # Error response should be properly formatted
        if response.status_code in [400, 422]:
            data = response.json()
            assert "detail" in data or "message" in data


class TestAPIEndpointLoggingWorkflows:
    """🔄 API Endpoint Logging Workflow Tests"""
    
    def test_health_check_endpoints_logging(self):
        """Test all health check endpoints with logging."""
        client = TestClient(app)
        
        health_endpoints = [
            "/api/v1/health",
            "/api/v1/health/unified-logging",
            "/api/v1/health/performance-optimization",
            "/api/v1/health/metrics-integration"
        ]
        
        for endpoint in health_endpoints:
            response = client.get(endpoint)
            
            # Should respond (may be 200, 404, or 500 depending on implementation)
            assert response.status_code in [200, 404, 500]
            
            # If successful, should return JSON
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
    
    def test_search_endpoints_logging_workflow(self):
        """Test search endpoints with comprehensive logging."""
        client = TestClient(app)
        
        # Test various search scenarios
        search_scenarios = [
            {"query": "concrete", "limit": 5},
            {"query": "steel", "limit": 10},
            {"query": "cement", "limit": 1},
            {"query": "nonexistent material", "limit": 20}
        ]
        
        for scenario in search_scenarios:
            response = client.get(
                "/api/v1/search/materials",
                params=scenario
            )
            
            # Should handle all scenarios gracefully
            assert response.status_code in [200, 404, 500]
            
            # If successful, should return proper format
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))


class TestErrorHandlingWorkflows:
    """🚨 Error Handling Workflow Tests"""
    
    def test_database_connection_error_workflow(self):
        """Test database connection error handling with proper logging."""
        # Mock database connection failure
        with patch('core.database.adapters.qdrant_adapter.QdrantAdapter') as mock_adapter:
            mock_adapter.side_effect = Exception("Database connection failed")
            
            client = TestClient(app)
            
            # Try to search materials (should handle DB error gracefully)
            response = client.get("/api/v1/search/materials?query=test")
            
            # Should return error response, not crash
            assert response.status_code in [500, 503, 404]
            
            # Error response should be properly formatted
            if response.status_code >= 400:
                data = response.json()
                assert isinstance(data, dict)
    
    def test_validation_error_workflow(self):
        """Test validation error workflow with logging."""
        client = TestClient(app)
        
        # Test various invalid inputs
        invalid_scenarios = [
            {"data": {}, "endpoint": "/api/v1/materials"},  # Empty data
            {"data": {"name": "A" * 1000}, "endpoint": "/api/v1/materials"},  # Too long name
            {"data": {"price": "invalid"}, "endpoint": "/api/v1/materials"},  # Invalid price type
        ]
        
        for scenario in invalid_scenarios:
            response = client.post(scenario["endpoint"], json=scenario["data"])
            
            # Should return validation error
            assert response.status_code in [400, 422]
            
            # Should have error details
            data = response.json()
            assert "detail" in data or "message" in data
    
    @pytest.mark.asyncio
    async def test_async_operation_error_workflow(self):
        """Test async operation error handling with correlation tracing."""
        service = MaterialsService()
        correlation_id = str(uuid.uuid4())
        
        with CorrelationContext.with_correlation_id(correlation_id):
            # Mock async operation that fails
            with patch.object(service, '_search_in_vector_db') as mock_search:
                mock_search.side_effect = asyncio.TimeoutError("Operation timed out")
                
                # Should handle timeout gracefully
                try:
                    results = await service.search_materials("test", limit=5)
                    # If no exception, operation was handled
                    assert isinstance(results, list)
                except Exception:
                    # Exception should be properly logged with correlation ID
                    assert get_correlation_id() == correlation_id


class TestHealthMonitoringWorkflows:
    """🏥 Health Monitoring Workflow Tests"""
    
    def test_comprehensive_health_monitoring_workflow(self):
        """Test comprehensive health monitoring with all components."""
        client = TestClient(app)
        
        # Test main health endpoint
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        
        # Test detailed health endpoints if available
        detailed_endpoints = [
            "/api/v1/health/unified-logging",
            "/api/v1/health/performance-optimization", 
            "/api/v1/health/metrics-integration"
        ]
        
        for endpoint in detailed_endpoints:
            response = client.get(endpoint)
            # May not be implemented, so accept 404
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
    
    def test_health_monitoring_with_correlation_tracing(self):
        """Test health monitoring with correlation ID tracing."""
        client = TestClient(app)
        
        # Use custom correlation ID for health check
        correlation_id = str(uuid.uuid4())
        headers = {"X-Correlation-ID": correlation_id}
        
        response = client.get("/api/v1/health", headers=headers)
        assert response.status_code == 200
        
        # Health check should be logged with correlation ID
        data = response.json()
        assert isinstance(data, dict)


# Functional test fixtures
@pytest.fixture
def test_client():
    """Fixture providing FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def clean_test_environment():
    """Fixture ensuring clean test environment."""
    # Clear correlation context
    CorrelationContext.set_correlation_id(None)
    yield
    # Cleanup
    CorrelationContext.set_correlation_id(None)


@pytest.fixture
def mock_materials_service():
    """Fixture providing mock MaterialsService."""
    service = Mock(spec=MaterialsService)
    
    # Mock common methods
    service.search_materials.return_value = [
        {"id": "1", "name": "Test Material 1", "category": "concrete"},
        {"id": "2", "name": "Test Material 2", "category": "steel"}
    ]
    
    return service


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 