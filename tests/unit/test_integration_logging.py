"""
🧪 Unit Tests for Logging Integration

Test suite for the logging integration system covering:
- FastAPI integration
- SQLAlchemy integration
- Vector database integration

Author: AI Assistant
Created: 2024
"""

import pytest
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from core.logging.integration.fastapi import LoggingMiddleware, LoggingRoute, setup_fastapi_logging
from core.logging.integration.sqlalchemy import SQLAlchemyEventListener, SessionExtension, setup_sqlalchemy_logging
from core.logging.integration.vector_db import QdrantLoggerMixin, WeaviateLoggerMixin, PineconeLoggerMixin, log_vector_db_operation


class TestFastAPIIntegration:
    """Tests for FastAPI integration"""
    
    def test_logging_middleware_creation(self):
        """Test that LoggingMiddleware can be created."""
        app = MagicMock(spec=ASGIApp)
        middleware = LoggingMiddleware(app)
        
        assert middleware is not None
        assert middleware._app is app
    
    @pytest.mark.asyncio
    async def test_middleware_dispatch(self):
        """Test middleware dispatch method."""
        app = MagicMock(spec=ASGIApp)
        call_next = AsyncMock()
        call_next.return_value = Response(content="Test response")
        
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        
        middleware = LoggingMiddleware(app)
        middleware._correlation_provider = MagicMock()
        middleware._correlation_provider.get_or_create_correlation_id.return_value = "test-correlation-id"
        middleware._correlation_provider.header_name = "X-Correlation-ID"
        middleware._request_logger = AsyncMock()
        
        response = await middleware.dispatch(request, call_next)
        
        assert response is not None
        assert middleware._request_logger.log_request.called
        assert middleware._request_logger.log_response.called
        assert response.headers["X-Correlation-ID"] == "test-correlation-id"
    
    @pytest.mark.asyncio
    async def test_middleware_exception_handling(self):
        """Test middleware exception handling."""
        app = MagicMock(spec=ASGIApp)
        call_next = AsyncMock()
        call_next.side_effect = ValueError("Test exception")
        
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        
        middleware = LoggingMiddleware(app)
        middleware._correlation_provider = MagicMock()
        middleware._correlation_provider.get_or_create_correlation_id.return_value = "test-correlation-id"
        middleware._request_logger = AsyncMock()
        
        with pytest.raises(ValueError):
            await middleware.dispatch(request, call_next)
        
        assert middleware._request_logger.log_request.called
        assert middleware._request_logger.log_exception.called
    
    def test_middleware_exclusion(self):
        """Test middleware path and method exclusion."""
        app = MagicMock(spec=ASGIApp)
        middleware = LoggingMiddleware(
            app,
            exclude_paths=["/health", "/metrics"],
            exclude_methods=["OPTIONS"]
        )
        
        # Test excluded path
        request = MagicMock(spec=Request)
        request.url.path = "/health"
        request.method = "GET"
        assert middleware._should_exclude(request) is True
        
        # Test excluded method
        request = MagicMock(spec=Request)
        request.url.path = "/api/users"
        request.method = "OPTIONS"
        assert middleware._should_exclude(request) is True
        
        # Test non-excluded request
        request = MagicMock(spec=Request)
        request.url.path = "/api/users"
        request.method = "GET"
        assert middleware._should_exclude(request) is False
    
    def test_setup_fastapi_logging(self):
        """Test setup_fastapi_logging function."""
        app = MagicMock(spec=FastAPI)
        
        setup_fastapi_logging(app, exclude_paths=["/health"], exclude_methods=["OPTIONS"])
        
        app.add_middleware.assert_called_once()
        args, kwargs = app.add_middleware.call_args
        assert args[0] is LoggingMiddleware
        assert kwargs.get("exclude_paths") == ["/health"]
        assert kwargs.get("exclude_methods") == ["OPTIONS"]
    
    @pytest.mark.asyncio
    async def test_logging_route(self):
        """Test LoggingRoute decorator."""
        route = LoggingRoute()
        route._correlation_provider = MagicMock()
        route._correlation_provider.get_or_create_correlation_id.return_value = "test-correlation-id"
        route._correlation_provider.header_name = "X-Correlation-ID"
        route._request_logger = AsyncMock()
        
        # Create a test handler
        async def test_handler(request: Request):
            return Response(content="Test response")
        
        # Apply the decorator
        decorated_handler = route(test_handler)
        
        # Call the decorated handler
        request = MagicMock(spec=Request)
        request.headers = {}
        response = await decorated_handler(request)
        
        assert response is not None
        assert route._request_logger.log_request.called
        assert route._request_logger.log_response.called


class TestSQLAlchemyIntegration:
    """Tests for SQLAlchemy integration"""
    
    def test_event_listener_creation(self):
        """Test that SQLAlchemyEventListener can be created."""
        listener = SQLAlchemyEventListener()
        
        assert listener is not None
        assert hasattr(listener, '_sql_logger')
    
    def test_event_listener_registration(self):
        """Test event listener registration."""
        engine = MagicMock(spec=Engine)
        
        with patch('core.logging.integration.sqlalchemy.listen') as mock_listen:
            listener = SQLAlchemyEventListener()
            listener.register(engine)
            
            # Should register before and after cursor execute events
            assert mock_listen.call_count == 2
    
    def test_before_cursor_execute(self):
        """Test before_cursor_execute event handler."""
        listener = SQLAlchemyEventListener()
        
        conn = MagicMock()
        cursor = MagicMock()
        statement = "SELECT * FROM users"
        parameters = {"user_id": 1}
        context = MagicMock()
        executemany = False
        
        listener._before_cursor_execute(conn, cursor, statement, parameters, context, executemany)
        
        # Should set start time in context
        assert hasattr(context, '_logging_start_time')
    
    def test_after_cursor_execute(self):
        """Test after_cursor_execute event handler."""
        listener = SQLAlchemyEventListener()
        listener._sql_logger = MagicMock()
        
        conn = MagicMock()
        cursor = MagicMock()
        statement = "SELECT * FROM users"
        parameters = {"user_id": 1}
        context = MagicMock()
        context._logging_start_time = 0  # Set to 0 for simplicity
        executemany = False
        
        with patch('time.time', return_value=1.0):  # 1 second elapsed
            listener._after_cursor_execute(conn, cursor, statement, parameters, context, executemany)
            
            # Should log query with duration
            listener._sql_logger.log_query.assert_called_once_with(
                statement, parameters, 1000.0, executemany
            )
    
    def test_session_extension_creation(self):
        """Test that SessionExtension can be created."""
        session = MagicMock(spec=Session)
        extension = SessionExtension(session)
        
        assert extension is not None
        assert extension._session is session
    
    def test_session_patching(self):
        """Test session method patching."""
        session = MagicMock(spec=Session)
        original_commit = session.commit
        original_rollback = session.rollback
        original_flush = session.flush
        
        extension = SessionExtension(session)
        
        # Methods should be patched
        assert session.commit is not original_commit
        assert session.rollback is not original_rollback
        assert session.flush is not original_flush
    
    def test_setup_sqlalchemy_logging(self):
        """Test setup_sqlalchemy_logging function."""
        engine = MagicMock(spec=Engine)
        
        with patch('core.logging.integration.sqlalchemy.SQLAlchemyEventListener') as mock_listener_class:
            mock_listener = MagicMock()
            mock_listener_class.return_value = mock_listener
            
            setup_sqlalchemy_logging(engine)
            
            # Should create listener and register it
            mock_listener_class.assert_called_once()
            mock_listener.register.assert_called_once_with(engine)


class TestVectorDBIntegration:
    """Tests for vector database integration"""
    
    def test_qdrant_logger_mixin(self):
        """Test QdrantLoggerMixin."""
        # Create a mock class that inherits from QdrantLoggerMixin
        class MockQdrantClient(QdrantLoggerMixin):
            def __init__(self):
                self.search = MagicMock(return_value="search_result")
                super().__init__()
        
        # Create an instance
        client = MockQdrantClient()
        
        # Test that the search method is patched
        with patch.object(client, '_vector_db_logger') as mock_logger:
            result = client.search(collection_name="test", query_vector=[1, 2, 3])
            
            assert result == "search_result"
            mock_logger.log_operation.assert_called_once()
    
    def test_weaviate_logger_mixin(self):
        """Test WeaviateLoggerMixin."""
        # Create a mock class that inherits from WeaviateLoggerMixin
        class MockWeaviateClient(WeaviateLoggerMixin):
            def __init__(self):
                self.query = MagicMock(return_value="query_result")
                super().__init__()
        
        # Create an instance
        client = MockWeaviateClient()
        
        # Test that the query method is patched
        with patch.object(client, '_vector_db_logger') as mock_logger:
            result = client.query(class_name="Test", properties=["prop1", "prop2"])
            
            assert result == "query_result"
            mock_logger.log_operation.assert_called_once()
    
    def test_pinecone_logger_mixin(self):
        """Test PineconeLoggerMixin."""
        # Create a mock class that inherits from PineconeLoggerMixin
        class MockPineconeIndex(PineconeLoggerMixin):
            def __init__(self):
                self.query = MagicMock(return_value="query_result")
                super().__init__()
        
        # Create an instance
        index = MockPineconeIndex()
        
        # Test that the query method is patched
        with patch.object(index, '_vector_db_logger') as mock_logger:
            result = index.query(vector=[1, 2, 3], top_k=10)
            
            assert result == "query_result"
            mock_logger.log_operation.assert_called_once()
    
    def test_log_vector_db_operation_decorator(self):
        """Test log_vector_db_operation decorator."""
        # Create a test function
        @log_vector_db_operation(db_type="test_db", operation="test_operation")
        def test_function(arg1, arg2=None):
            return f"Result: {arg1}, {arg2}"
        
        # Test the decorated function
        with patch('core.logging.integration.vector_db.VectorDbLogger') as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger_class.return_value = mock_logger
            
            result = test_function("value1", arg2="value2")
            
            assert result == "Result: value1, value2"
            mock_logger.log_operation.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 