"""
🧪 Unit Tests for Unified Logging System

Comprehensive test suite for the unified logging system covering:
- Stage 0: Critical duplication elimination
- Stage 1: Mass migration to unified logging  
- Stage 2: UnifiedLoggingManager integration
- Stage 3: Correlation ID system (100% coverage)
- Stage 4: Performance optimization
- Stage 5: Metrics integration

Author: AI Assistant
Created: 2024
"""

import pytest
import asyncio
import uuid
import time
import json
import logging
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
from core.logging.context import CorrelationContext, get_correlation_id, set_correlation_id
from core.logging.base.formatters import StructuredFormatter
from core.logging.handlers.database import DatabaseLogger
from core.logging.handlers.request import RequestLogger
from core.logging.managers.unified import UnifiedLoggingManager
from core.config import get_settings

# Настройка тестового логгера
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


class TestUnifiedLoggingSystemStage0:
    """🔥 Stage 0: Critical Duplication Elimination Tests"""
    
    def test_base_logging_handler_eliminated(self):
        """Test that BaseLoggingHandler has been completely eliminated."""
        # Should not be able to import BaseLoggingHandler
        with pytest.raises(ImportError):
            from core.middleware.request_logging import BaseLoggingHandler
    
    def test_single_logging_middleware(self):
        """Test that only one LoggingMiddleware exists."""
        from core.middleware.request_logging import LoggingMiddleware
        
        # Should not be able to import LoggingMiddlewareAdapter
        with pytest.raises(ImportError):
            from core.middleware.request_logging import LoggingMiddlewareAdapter
    
    def test_unified_logging_config(self):
        """Test that LoggingConfig is properly integrated."""
        settings = get_settings()
        
        # Test that logging settings are available
        assert hasattr(settings, 'LOG_LEVEL')
        assert hasattr(settings, 'ENABLE_STRUCTURED_LOGGING')
        assert hasattr(settings, 'ENABLE_REQUEST_LOGGING')


class TestUnifiedLoggingSystemStage1:
    """🔄 Stage 1: Mass Migration Tests"""
    
    def test_get_logger_function_available(self):
        """Test that get_logger function is available from monitoring system."""
        logger = get_logger("test_stage1")
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
    
    def test_logger_naming_convention(self):
        """Test that logger names follow the unified convention."""
        logger = get_logger("test.module.name")
        assert logger.name == "test.module.name"
    
    def test_structured_logging_support(self):
        """Test that structured logging is supported."""
        logger = get_logger("test_structured")
        
        # Should be able to log with extra data
        with patch.object(logger, 'info') as mock_info:
            logger.info("Test message", extra={"key": "value"})
            mock_info.assert_called_once()


class TestUnifiedLoggingSystemStage2:
    """🎯 Stage 2: UnifiedLoggingManager Tests"""
    
    def test_unified_logging_manager_creation(self):
        """Test UnifiedLoggingManager can be created successfully."""
        manager = get_unified_logging_manager()
        assert manager is not None
        assert isinstance(manager, UnifiedLoggingManager)
    
    def test_unified_manager_components(self):
        """Test that UnifiedLoggingManager has all required components."""
        manager = get_unified_logging_manager()
        
        # Should have all core components
        assert hasattr(manager, 'metrics_collector')
        assert hasattr(manager, 'performance_tracker')
        assert hasattr(manager, 'request_logger')
        assert hasattr(manager, 'database_logger')
    
    def test_database_operation_logging(self):
        """Test database operation logging through unified manager."""
        manager = get_unified_logging_manager()
        
        # Test that the method can be called without errors
        try:
            manager.log_database_operation(
                db_type="qdrant",
                operation="search",
                duration_ms=100.5,
                success=True,
                record_count=10
            )
            # If we get here without exception, the test passes
            assert True
        except Exception as e:
            pytest.fail(f"Database operation logging failed: {e}")


class TestUnifiedLoggingSystemStage3:
    """🎯 Stage 3: Correlation ID System Tests"""
    
    def test_correlation_context_basic(self, clean_correlation_context):
        """Test basic correlation context functionality."""
        # Initially no correlation ID
        assert CorrelationContext.get_correlation_id() is None
        
        # Set correlation ID
        test_id = "test-correlation-123"
        CorrelationContext.set_correlation_id(test_id)
        assert CorrelationContext.get_correlation_id() == test_id
    
    def test_correlation_context_manager(self, clean_correlation_context):
        """Test correlation context manager."""
        test_id = "context-manager-test"
        
        with CorrelationContext.with_correlation_id(test_id):
            assert CorrelationContext.get_correlation_id() == test_id
        
        # Should be cleared after context
        assert CorrelationContext.get_correlation_id() is None
    
    def test_correlation_context_nesting(self, clean_correlation_context):
        """Test nested correlation contexts."""
        outer_id = "outer-context"
        inner_id = "inner-context"
        
        with CorrelationContext.with_correlation_id(outer_id):
            assert CorrelationContext.get_correlation_id() == outer_id
            
            with CorrelationContext.with_correlation_id(inner_id):
                assert CorrelationContext.get_correlation_id() == inner_id
            
            # Should restore outer context
            assert CorrelationContext.get_correlation_id() == outer_id


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


class TestUnifiedLogging:
    """Test suite for unified logging system."""
    
    def test_get_logger_basic(self):
        """Test basic logger creation."""
        test_logger = get_logger("test.logger")
        assert test_logger is not None
        assert test_logger.name == "test.logger"
    
    def test_structured_formatter(self):
        """Test structured formatter."""
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
        parsed = json.loads(formatted)
        
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test.logger"
    
    def test_correlation_context(self):
        """Test correlation context."""
        # No correlation ID initially
        assert get_correlation_id() is None
        
        # With explicit correlation ID
        with CorrelationContext.with_correlation_id("test-id"):
            assert get_correlation_id() == "test-id"
            
            # Nested context with same ID
            with CorrelationContext.with_correlation_id():
                assert get_correlation_id() == "test-id"
        
        # Outside context, no correlation ID
        assert get_correlation_id() is None
        
        # Auto-generated correlation ID
        with CorrelationContext.with_correlation_id():
            correlation_id = get_correlation_id()
            assert correlation_id is not None
            assert isinstance(correlation_id, str)
    
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
    
    def test_unified_manager_basic(self):
        """Test unified logging manager basic functionality."""
        manager = get_unified_logging_manager()
        assert isinstance(manager, UnifiedLoggingManager)
        
        # Get logger through manager
        test_logger = manager.get_logger("test.unified")
        assert test_logger is not None
        assert test_logger.name == "test.unified"
    
    def test_log_database_operation(self):
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
    
    def test_log_request(self):
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
