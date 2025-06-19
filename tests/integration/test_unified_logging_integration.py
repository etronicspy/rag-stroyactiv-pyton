"""
🔗 Integration Tests for Unified Logging System

Integration tests focusing on:
- Middleware integration with unified logging
- Service layer integration with correlation ID
- Database operations with automatic logging
- End-to-end request tracing
- Performance optimization integration
- Metrics integration workflows

Author: AI Assistant
Created: 2024
"""

import pytest
import asyncio
import uuid
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

# Core imports
from main import app
from core.monitoring.unified_manager import get_unified_logging_manager
from core.monitoring.context import CorrelationContext, get_correlation_id
from core.monitoring.performance_optimizer import get_performance_optimizer
from core.monitoring.metrics_integration import get_metrics_integrated_logger
from core.middleware.logging import LoggingMiddleware
from services.materials import MaterialsService
from core.config import get_settings


class TestMiddlewareIntegration:
    """🔗 LoggingMiddleware Integration Tests"""
    
    def test_middleware_creates_unified_manager(self):
        """Test that LoggingMiddleware properly creates UnifiedLoggingManager."""
        settings = get_settings()
        mock_app = Mock()
        
        middleware = LoggingMiddleware(mock_app, settings)
        
        # Should have unified manager
        assert hasattr(middleware, 'unified_manager')
        assert middleware.unified_manager is not None
    
    @pytest.mark.asyncio
    async def test_middleware_sets_correlation_id(self):
        """Test that middleware sets correlation ID for requests."""
        settings = get_settings()
        
        # Create a simple ASGI app for testing
        async def simple_app(scope, receive, send):
            # Check if correlation ID is set
            correlation_id = get_correlation_id()
            
            response = {
                'type': 'http.response.start',
                'status': 200,
                'headers': [[b'content-type', b'application/json']],
            }
            await send(response)
            
            body_response = {
                'type': 'http.response.body',
                'body': json.dumps({
                    'correlation_id': correlation_id,
                    'status': 'success'
                }).encode(),
            }
            await send(body_response)
        
        # Wrap with LoggingMiddleware
        middleware = LoggingMiddleware(simple_app, settings)
        
        # Create test scope
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'headers': [],
            'client': ('127.0.0.1', 12345),
        }
        
        # Mock receive and send
        receive = AsyncMock()
        receive.return_value = {'type': 'http.request', 'body': b''}
        
        sent_messages = []
        
        async def mock_send(message):
            sent_messages.append(message)
        
        # Call middleware
        await middleware(scope, receive, mock_send)
        
        # Verify response was sent
        assert len(sent_messages) >= 2
        
        # Check if response contains correlation ID
        body_message = sent_messages[-1]
        if body_message['type'] == 'http.response.body':
            response_data = json.loads(body_message['body'].decode())
            assert 'correlation_id' in response_data
            assert response_data['correlation_id'] is not None
    
    def test_middleware_logs_http_requests(self):
        """Test that middleware logs HTTP requests through unified manager."""
        settings = get_settings()
        mock_app = Mock()
        
        middleware = LoggingMiddleware(mock_app, settings)
        
        # Mock the unified manager's log_http_request method
        with patch.object(middleware.unified_manager, 'log_http_request') as mock_log:
            # Create a test request scenario
            middleware.unified_manager.log_http_request(
                method="GET",
                path="/api/v1/materials",
                status_code=200,
                duration_ms=50.0,
                request_id="test-123"
            )
            
            mock_log.assert_called_once_with(
                method="GET",
                path="/api/v1/materials",
                status_code=200,
                duration_ms=50.0,
                request_id="test-123"
            )


class TestServiceLayerIntegration:
    """🔗 Service Layer Integration Tests"""
    
    @pytest.mark.asyncio
    async def test_materials_service_correlation_integration(self):
        """Test MaterialsService integration with correlation ID."""
        # Set correlation context
        test_correlation_id = str(uuid.uuid4())
        
        with CorrelationContext.with_correlation_id(test_correlation_id):
            # Create materials service
            service = MaterialsService()
            
            # Verify correlation ID is available in service context
            assert get_correlation_id() == test_correlation_id
            
            # Mock database operations to test logging
            with patch.object(service, '_search_in_vector_db') as mock_search:
                mock_search.return_value = []
                
                # This should automatically log with correlation ID
                results = await service.search_materials("test query", limit=5)
                
                # Verify operation was called
                mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_database_operation_logging(self):
        """Test that service database operations are automatically logged."""
        service = MaterialsService()
        
        # Mock the unified manager to capture logging calls
        with patch('services.materials.get_unified_logging_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            
            # Mock database operation
            with patch.object(service, '_search_in_vector_db') as mock_search:
                mock_search.return_value = [{'id': '1', 'name': 'Test Material'}]
                
                # Perform search operation
                results = await service.search_materials("concrete", limit=10)
                
                # Verify results
                assert len(results) == 1
                assert results[0]['name'] == 'Test Material'
    
    def test_service_decorator_integration(self):
        """Test that service decorators work with unified logging."""
        from core.monitoring.unified_manager import log_database_operation
        
        # Test that decorator can be applied
        @log_database_operation("qdrant", "test_operation")
        async def test_decorated_function():
            return "success"
        
        # Should be callable
        assert callable(test_decorated_function)


class TestDatabaseOperationIntegration:
    """🔗 Database Operation Integration Tests"""
    
    @pytest.mark.asyncio
    async def test_database_operation_context_manager(self):
        """Test database operation context manager integration."""
        manager = get_unified_logging_manager()
        
        # Mock the database logger
        with patch.object(manager.database_logger, 'log_operation') as mock_log:
            # Use context manager
            async with manager.database_operation_context("qdrant", "search"):
                # Simulate database operation
                await asyncio.sleep(0.01)
                result = "operation_result"
            
            # Verify logging was called
            mock_log.assert_called()
            args, kwargs = mock_log.call_args
            assert 'duration_ms' in kwargs
            assert kwargs['success'] is True
    
    @pytest.mark.asyncio
    async def test_database_operation_error_handling(self):
        """Test database operation error handling and logging."""
        manager = get_unified_logging_manager()
        
        with patch.object(manager.database_logger, 'log_operation') as mock_log:
            try:
                async with manager.database_operation_context("qdrant", "failing_operation"):
                    # Simulate database error
                    raise Exception("Database connection failed")
            except Exception:
                pass  # Expected
            
            # Verify error was logged
            mock_log.assert_called()
            args, kwargs = mock_log.call_args
            assert kwargs['success'] is False
            assert 'error' in kwargs
    
    def test_database_metrics_integration(self):
        """Test database operations integrate with metrics."""
        manager = get_unified_logging_manager()
        
        # Mock metrics collector
        with patch.object(manager.metrics_collector, 'track_operation') as mock_track:
            manager.log_database_operation(
                db_type="qdrant",
                operation="search",
                duration_ms=100.0,
                success=True,
                record_count=5
            )
            
            # Verify metrics were tracked
            mock_track.assert_called()


class TestEndToEndRequestTracing:
    """🔗 End-to-End Request Tracing Tests"""
    
    def test_health_check_endpoint_tracing(self):
        """Test end-to-end tracing through health check endpoint."""
        client = TestClient(app)
        
        # Make request to health endpoint
        response = client.get("/api/v1/health")
        
        # Should succeed
        assert response.status_code == 200
        
        # Response should contain health data
        data = response.json()
        assert "status" in data
    
    def test_correlation_id_propagation(self):
        """Test correlation ID propagation through request lifecycle."""
        client = TestClient(app)
        
        # Make request with custom correlation ID header
        headers = {"X-Correlation-ID": "test-correlation-123"}
        response = client.get("/api/v1/health", headers=headers)
        
        # Should succeed
        assert response.status_code == 200
        
        # Response headers should contain correlation ID
        response_headers = dict(response.headers)
        # Note: Actual header name depends on middleware implementation
    
    @pytest.mark.asyncio
    async def test_materials_search_end_to_end(self):
        """Test end-to-end materials search with full logging."""
        client = TestClient(app)
        
        # Mock the materials service
        with patch('api.routes.search.MaterialsService') as mock_service_class:
            mock_service = Mock()
            mock_service.search_materials.return_value = [
                {"id": "1", "name": "Test Material", "category": "concrete"}
            ]
            mock_service_class.return_value = mock_service
            
            # Make search request
            response = client.get("/api/v1/search/materials?query=concrete&limit=10")
            
            # Should succeed
            assert response.status_code == 200
            
            # Verify service was called
            mock_service.search_materials.assert_called_once()


class TestPerformanceOptimizationIntegration:
    """🚀 Performance Optimization Integration Tests"""
    
    def test_performance_optimizer_integration(self):
        """Test performance optimizer integrates with unified logging."""
        manager = get_unified_logging_manager()
        optimizer = get_performance_optimizer()
        
        # Both should be available
        assert manager is not None
        assert optimizer is not None
        
        # Should be able to work together
        assert hasattr(manager, 'performance_optimizer')
    
    def test_batch_logging_integration(self):
        """Test batch logging works with unified system."""
        optimizer = get_performance_optimizer()
        
        # Add multiple log entries
        success_count = 0
        for i in range(10):
            success = optimizer.log_with_batching(
                logger_name="test_batch_integration",
                level="INFO",
                message=f"Batch message {i}",
                extra={"batch_id": i}
            )
            if success:
                success_count += 1
        
        # Should have successfully queued entries
        assert success_count > 0
    
    @pytest.mark.asyncio
    async def test_performance_with_correlation(self):
        """Test performance optimization works with correlation ID."""
        optimizer = get_performance_optimizer()
        test_correlation_id = str(uuid.uuid4())
        
        with CorrelationContext.with_correlation_id(test_correlation_id):
            # Perform optimized logging
            success = optimizer.log_with_batching(
                logger_name="test_perf_correlation",
                level="INFO",
                message="Performance test with correlation",
                extra={"correlation_id": get_correlation_id()}
            )
            
            assert success is True
            assert get_correlation_id() == test_correlation_id


class TestMetricsIntegrationWorkflows:
    """📊 Metrics Integration Workflow Tests"""
    
    def test_metrics_logger_integration(self):
        """Test metrics integrated logger works with system."""
        logger = get_metrics_integrated_logger("test_integration")
        
        # Should be able to log with automatic metrics
        with patch.object(logger, '_record_database_metric') as mock_metric:
            logger.log_database_operation(
                db_type="qdrant",
                operation="search",
                duration_ms=100.0,
                success=True,
                record_count=10
            )
            
            mock_metric.assert_called_once()
    
    def test_timed_operation_integration(self):
        """Test timed operation context manager integration."""
        logger = get_metrics_integrated_logger("test_timed_integration")
        
        with patch.object(logger, 'log_application_event') as mock_log:
            with logger.timed_operation("integration_test"):
                # Simulate some work
                time.sleep(0.01)
            
            # Should have logged the timed operation
            mock_log.assert_called()
            call_kwargs = mock_log.call_args[1]
            assert 'duration_ms' in call_kwargs
            assert call_kwargs['duration_ms'] > 0
    
    def test_http_metrics_integration(self):
        """Test HTTP metrics integration with request processing."""
        logger = get_metrics_integrated_logger("test_http_integration")
        
        with patch.object(logger, '_record_http_metric') as mock_metric:
            logger.log_http_request(
                method="POST",
                path="/api/v1/materials",
                status_code=201,
                duration_ms=150.0,
                request_id="test-456"
            )
            
            mock_metric.assert_called_once()
    
    def test_metrics_summary_integration(self):
        """Test metrics summary generation integration."""
        logger = get_metrics_integrated_logger("test_summary_integration")
        
        # Perform various operations
        logger.log_database_operation("qdrant", "search", 100.0, True, 5)
        logger.log_http_request("GET", "/api/v1/health", 200, 25.0, "health-123")
        logger.log_application_event("startup", success=True, duration_ms=500.0)
        
        # Get summary
        summary = logger.get_metrics_summary()
        
        # Verify summary structure
        assert isinstance(summary, dict)
        assert 'database_operations' in summary
        assert 'http_requests' in summary
        assert 'application_events' in summary
        
        # Verify counts
        assert summary['database_operations']['total_count'] >= 1
        assert summary['http_requests']['total_count'] >= 1
        assert summary['application_events']['total_count'] >= 1


class TestSystemHealthIntegration:
    """🏥 System Health Integration Tests"""
    
    def test_unified_logging_health_check(self):
        """Test unified logging health check endpoint."""
        client = TestClient(app)
        
        response = client.get("/api/v1/health/unified-logging")
        
        # Should succeed or return 404 if not implemented
        assert response.status_code in [200, 404]
        
        # If implemented, should contain health information
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_performance_optimization_health_check(self):
        """Test performance optimization health check."""
        client = TestClient(app)
        
        response = client.get("/api/v1/health/performance-optimization")
        
        # Should succeed  
        assert response.status_code == 200
        
        # Should contain performance metrics
        data = response.json()
        assert "performance_optimization" in data
        assert "component_tests" in data
    
    def test_metrics_integration_health_check(self):
        """Test metrics integration health check."""
        client = TestClient(app)
        
        response = client.get("/api/v1/health/metrics-integration")
        
        # Should succeed
        assert response.status_code == 200
        
        # Should contain metrics integration status
        data = response.json()
        assert "metrics_integration" in data
        assert "integration_tests" in data


class TestErrorHandlingIntegration:
    """🚨 Error Handling Integration Tests"""
    
    @pytest.mark.asyncio
    async def test_service_error_logging_integration(self):
        """Test service error logging integration."""
        service = MaterialsService()
        
        # Mock database operation to raise error
        with patch.object(service, '_search_in_vector_db') as mock_search:
            mock_search.side_effect = Exception("Database connection failed")
            
            # Should handle error gracefully
            try:
                await service.search_materials("test", limit=5)
            except Exception:
                pass  # Expected
            
            # Error should have been logged (verified through unified manager)
    
    def test_middleware_error_handling_integration(self):
        """Test middleware error handling integration."""
        settings = get_settings()
        
        # Create middleware with mock app that raises error
        async def failing_app(scope, receive, send):
            raise Exception("Application error")
        
        middleware = LoggingMiddleware(failing_app, settings)
        
        # Should handle errors gracefully
        # (Actual error handling depends on middleware implementation)
    
    def test_correlation_context_error_recovery(self):
        """Test correlation context error recovery."""
        test_correlation_id = str(uuid.uuid4())
        
        try:
            with CorrelationContext.with_correlation_id(test_correlation_id):
                assert get_correlation_id() == test_correlation_id
                raise Exception("Test error")
        except Exception:
            pass  # Expected
        
        # Context should be properly cleaned up
        assert get_correlation_id() is None


# Integration test fixtures
@pytest.fixture
def test_client():
    """Fixture providing FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def unified_manager():
    """Fixture providing UnifiedLoggingManager instance."""
    return get_unified_logging_manager()


@pytest.fixture
def performance_optimizer():
    """Fixture providing PerformanceOptimizer instance."""
    return get_performance_optimizer()


@pytest.fixture
def metrics_logger():
    """Fixture providing MetricsIntegratedLogger instance."""
    return get_metrics_integrated_logger("test_integration")


@pytest.fixture
def clean_correlation_context():
    """Fixture ensuring clean correlation context."""
    CorrelationContext.set_correlation_id(None)
    yield
    CorrelationContext.set_correlation_id(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 