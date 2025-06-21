"""
Unit tests for the unified logging system.
"""
import pytest
import logging
import json
import asyncio
import time
import os
import io
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Generator, AsyncGenerator

# Core imports
from core.logging import (
    get_logger, 
    get_unified_logging_manager, 
    get_metrics_collector,
    get_performance_optimizer
)
from core.logging.context.correlation import get_correlation_id, set_correlation_id, CorrelationContext
from core.logging.base.formatters import StructuredFormatter
from core.logging.handlers.database import DatabaseLogger
from core.logging.handlers.request import RequestLogger
from core.logging.managers.unified import UnifiedLoggingManager
from core.config import get_settings, logging_config

# Настройка тестового логгера
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


class TestUnifiedLoggingSystem:
    """Tests for the unified logging system."""
    
    def test_get_logger_function_available(self):
        """Test get_logger function is available."""
        logger = get_logger("test.logger")
        assert logger is not None
        assert logger.name == "test.logger"
        
        # Test basic logging functionality
        with patch.object(logger, 'info') as mock_info:
            logger.info("Test message")
            mock_info.assert_called_once_with("Test message")
    
    def test_logger_naming_convention(self):
        """Test logger naming convention."""
        logger = get_logger("api.routes.materials")
        assert logger.name == "api.routes.materials"
    
    def test_structured_logging_support(self):
        """Test structured logging support."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert "timestamp" in parsed
    
    def test_unified_logging_manager_creation(self):
        """Test unified logging manager creation."""
        manager = get_unified_logging_manager()
        assert manager is not None
        assert isinstance(manager, UnifiedLoggingManager)
    
    def test_unified_manager_components(self):
        """Test unified manager components."""
        manager = get_unified_logging_manager()
        
        # Should have these components
        assert hasattr(manager, "get_logger")
        assert hasattr(manager, "log_database_operation")
        assert hasattr(manager, "log_request")
        assert hasattr(manager, "metrics_collector")
        
        # Test logger creation
        logger = manager.get_logger("test.unified")
        assert logger is not None
        assert logger.name == "test.unified"
    
    def test_database_operation_logging(self):
        """Test database operation logging."""
        manager = get_unified_logging_manager()
        
        with patch.object(manager, "_log_db_operation") as mock_log:
            manager.log_database_operation(
                db_type="postgresql",
                operation="select",
                duration_ms=100.5,
                success=True,
                record_count=10
            )
            
            mock_log.assert_called_once()
    
    def test_correlation_context_basic(self, clean_correlation_context):
        """Test basic correlation context functionality."""
        # Initially no correlation ID
        assert get_correlation_id() is None
        
        # Set correlation ID
        test_id = "test-correlation-123"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id
    
    def test_correlation_context_manager(self, clean_correlation_context):
        """Test correlation context manager."""
        test_id = "context-manager-test"
        
        with CorrelationContext.with_correlation_id(test_id):
            assert get_correlation_id() == test_id
        
        # Should be cleared after context
        assert get_correlation_id() is None
    
    def test_correlation_context_nesting(self, clean_correlation_context):
        """Test nested correlation contexts."""
        outer_id = "outer-context"
        inner_id = "inner-context"
        
        with CorrelationContext.with_correlation_id(outer_id):
            assert get_correlation_id() == outer_id
            
            with CorrelationContext.with_correlation_id(inner_id):
                assert get_correlation_id() == inner_id
            
            # Should restore outer context
            assert get_correlation_id() == outer_id
    
    def test_database_logger(self):
        """Test database logger."""
        db_logger = DatabaseLogger("test-db")
        
        # Test basic logging
        with patch.object(db_logger, "_log") as mock_log:
            db_logger.log_operation(
                operation="test-operation",
                duration_ms=100.5,
                success=True,
                record_count=5
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert kwargs["level"] == "INFO"
            assert "test-operation" in kwargs["message"]
            assert kwargs["extra"]["db_type"] == "test-db"
            assert kwargs["extra"]["duration_ms"] == 100.5
            assert kwargs["extra"]["success"] is True
            assert kwargs["extra"]["record_count"] == 5
    
    def test_request_logger(self):
        """Test request logger."""
        req_logger = RequestLogger()
        
        # Test request logging
        with patch.object(req_logger, "_log") as mock_log:
            req_logger.log_request(
                method="GET",
                path="/api/test",
                status_code=200,
                duration_ms=50.5,
                request_id="test-req-id"
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert kwargs["level"] == "INFO"
            assert "GET /api/test" in kwargs["message"]
            assert kwargs["extra"]["method"] == "GET"
            assert kwargs["extra"]["path"] == "/api/test"
            assert kwargs["extra"]["status_code"] == 200
            assert kwargs["extra"]["duration_ms"] == 50.5
            assert kwargs["extra"]["request_id"] == "test-req-id"
    
    def test_log_database_operation_manager(self):
        """Test database operation logging through unified manager."""
        manager = get_unified_logging_manager()
        
        with patch.object(manager, "_log_db_operation") as mock_log:
            manager.log_database_operation(
                db_type="postgresql",
                operation="select",
                duration_ms=75.5,
                success=True,
                record_count=10
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert kwargs["db_type"] == "postgresql"
            assert kwargs["operation"] == "select"
            assert kwargs["duration_ms"] == 75.5
            assert kwargs["success"] is True
            assert kwargs["record_count"] == 10
    
    def test_log_request_manager(self):
        """Test request logging through unified manager."""
        manager = get_unified_logging_manager()
        
        with patch.object(manager, "_log_request") as mock_log:
            manager.log_request(
                method="POST",
                path="/api/resource",
                status_code=201,
                duration_ms=120.5,
                request_id="test-post-id"
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert kwargs["method"] == "POST"
            assert kwargs["path"] == "/api/resource"
            assert kwargs["status_code"] == 201
            assert kwargs["duration_ms"] == 120.5
            assert kwargs["request_id"] == "test-post-id"
    
    def test_metrics_collector(self):
        """Test metrics collector."""
        metrics = get_metrics_collector()
        
        with patch.object(metrics, "_increment_counter") as mock_increment:
            metrics.increment_counter("test_counter", labels={"test": "value"})
            mock_increment.assert_called_once_with("test_counter", 1, {"test": "value"})
        
        with patch.object(metrics, "_record_histogram") as mock_record:
            metrics.record_histogram("test_histogram", 42.5, labels={"test": "value"})
            mock_record.assert_called_once_with("test_histogram", 42.5, {"test": "value"})
    
    @pytest.mark.asyncio
    async def test_performance_optimizer(self):
        """Test performance optimizer."""
        optimizer = get_performance_optimizer()
        
        # Mock the async processing
        with patch.object(optimizer, "_process_log_async") as mock_process:
            mock_process.return_value = asyncio.Future()
            mock_process.return_value.set_result(None)
            
            await optimizer.log_optimized(
                logger_name="test.perf",
                level="INFO",
                message="Optimized log message",
                extra_data={"test": "value"}
            )
            
            mock_process.assert_called_once()
            args, kwargs = mock_process.call_args
            assert args[0]["logger_name"] == "test.perf"
            assert args[0]["level"] == "INFO"
            assert args[0]["message"] == "Optimized log message"
            assert args[0]["extra_data"] == {"test": "value"}


# Fixtures for testing
@pytest.fixture
def clean_correlation_context():
    """Fixture to ensure clean correlation context for each test."""
    from core.logging import force_clear_correlation_id
    # Force clear any existing correlation ID
    force_clear_correlation_id()
    yield
    # Clean up after test
    force_clear_correlation_id()


@pytest.fixture
def unified_manager():
    """Fixture providing UnifiedLoggingManager instance."""
    return get_unified_logging_manager()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
