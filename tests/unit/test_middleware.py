"""
Unit tests for middleware components
Unit тесты для компонентов middleware

Объединяет тесты из:
- test_middleware.py (Security, Logging, Rate Limiting)
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from core.middleware import RateLimitMiddleware, LoggingMiddleware, SecurityMiddleware
from core.config import settings, get_settings


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.post("/api/v1/prices/upload") 
        async def upload_endpoint():
            return {"message": "upload"}
        
        return app
    
    @pytest.mark.unit
    def test_request_size_limit(self, app):
        """Test request size limiting."""
        app.add_middleware(SecurityMiddleware, max_request_size=1024)
        client = TestClient(app)
        
        # Test large request
        large_data = "x" * 2048  # 2KB, exceeds limit
        response = client.post("/test", content=large_data,
                             headers={"content-length": str(len(large_data))})
        
        assert response.status_code == 413
        assert "Request too large" in response.json()["error"]
    
    @pytest.mark.unit
    def test_blocked_user_agent(self, app):
        """Test blocked user agent detection."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test with blocked user agent
        response = client.get("/test", headers={"user-agent": "sqlmap/1.0"})
        
        assert response.status_code == 403
        assert response.json()["error"] == "Forbidden"
    
    @pytest.mark.unit
    def test_path_traversal_protection(self, app):
        """Test path traversal attack protection."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test path traversal in query
        response = client.get("/test?file=../../../etc/passwd")
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_sql_injection_protection(self, app):
        """Test SQL injection protection."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test SQL injection in query
        response = client.get("/test?query='; DROP TABLE users; --")
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_xss_protection(self, app):
        """Test XSS protection."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test XSS in query
        response = client.get("/test?name=<script>alert('xss')</script>")
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_file_extension_check(self, app):
        """Test file extension validation for uploads."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test valid content type
        response = client.post("/api/v1/prices/upload",
                             headers={"content-type": "text/csv"},
                             content="test,data")
        # Should not be blocked (endpoint doesn't exist but passes security)
        assert response.status_code != 400
        
        # Test invalid content type
        response = client.post("/api/v1/prices/upload",
                             headers={"content-type": "application/x-executable"},
                             content="test")
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_security_headers(self, app):
        """Test security headers addition."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    @pytest.mark.unit
    def test_cors_settings_development(self):
        """Test CORS settings for development."""
        middleware = SecurityMiddleware(FastAPI())
        
        with patch.object(settings, 'ENVIRONMENT', 'development'):
            cors_settings = middleware.get_cors_settings()
            
            assert cors_settings["allow_origins"] == ["*"]
            assert cors_settings["allow_methods"] == ["*"]
    
    @pytest.mark.unit
    def test_cors_settings_production(self):
        """Test CORS settings for production."""
        middleware = SecurityMiddleware(FastAPI())
        
        with patch.object(settings, 'ENVIRONMENT', 'production'):
            cors_settings = middleware.get_cors_settings()
            
            assert "*" not in cors_settings["allow_origins"]
            assert "https://yourdomain.com" in cors_settings["allow_origins"]
            assert cors_settings["max_age"] == 600


class TestLoggingMiddleware:
    """Test logging middleware functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.post("/test")
        async def test_post():
            return {"message": "posted"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        return app
    
    @pytest.mark.unit
    def test_request_logging(self, app, caplog):
        """Test request logging."""
        settings = get_settings()
        app.add_middleware(LoggingMiddleware)
        client = TestClient(app)
        
        with caplog.at_level("INFO"):
            response = client.get("/test")
        
        assert response.status_code == 200
        # Check for correlation ID in response
        assert "X-Correlation-ID" in response.headers
        
        # Check logs contain request info
        log_messages = [record.message for record in caplog.records]
        request_logs = [msg for msg in log_messages if "Incoming" in msg]
        assert len(request_logs) > 0
    
    @pytest.mark.unit
    def test_response_logging(self, app, caplog):
        """Test response logging."""
        settings = get_settings()
        app.add_middleware(LoggingMiddleware)
        client = TestClient(app)
        
        with caplog.at_level("INFO"):
            response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check logs contain response info
        log_messages = [record.message for record in caplog.records]
        response_logs = [msg for msg in log_messages if "Response" in msg]
        assert len(response_logs) > 0
    
    @pytest.mark.unit
    def test_exception_logging(self, app, caplog):
        """Test exception logging."""
        settings = get_settings()
        app.add_middleware(LoggingMiddleware)
        client = TestClient(app)
        
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                client.get("/error")
    
    @pytest.mark.unit
    def test_request_body_logging(self, app, caplog):
        """Test request body logging."""
        app.add_middleware(LoggingMiddleware, log_request_body=True)
        client = TestClient(app)
        
        with caplog.at_level("DEBUG"):
            response = client.post("/test", json={"test": "data"})
        
        assert response.status_code == 200
        
        # Check body is logged
        log_messages = [record.message for record in caplog.records]
        body_logs = [msg for msg in log_messages if "incoming post" in msg.lower()]
        assert len(body_logs) > 0
    
    @pytest.mark.unit
    def test_excluded_paths(self, app, caplog):
        """Test excluded paths logging."""
        app.add_middleware(LoggingMiddleware, exclude_paths=["/health"])
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        client = TestClient(app)
        
        with caplog.at_level("INFO"):
            response = client.get("/health")
        
        assert response.status_code == 200
        
        # Health endpoint should not be logged
        log_messages = [record.message for record in caplog.records]
        health_logs = [msg for msg in log_messages if "Incoming" in msg and "/health" in msg]
        assert len(health_logs) == 0
    
    @pytest.mark.unit
    def test_sensitive_header_masking(self):
        """Test sensitive header masking."""
        middleware = LoggingMiddleware(FastAPI())
        
        headers = {
            "Authorization": "Bearer secret-token",
            "X-API-Key": "api-key-123",
            "Content-Type": "application/json"
        }
        
        masked_headers = middleware.mask_sensitive_data(headers)
        
        assert masked_headers["Authorization"] == "Bearer ***"
        assert masked_headers["X-API-Key"] == "***"
        assert masked_headers["Content-Type"] == "application/json"  # Not sensitive


class TestRateLimitMiddleware:
    """Test rate limiting middleware functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/api/v1/search")
        async def search_endpoint():
            return {"results": []}
        
        return app
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        mock_redis = AsyncMock()
        
        async def _async_noop(*args, **kwargs):
            return True

        # Simple pipeline mock
        class _Pipe:
            def __init__(self):
                self.cmds = []
            def incr(self, *args, **kwargs):
                self.cmds.append("incr")
            def expire(self, *args, **kwargs):
                self.cmds.append("expire")
            async def execute(self):
                # Return counts mimicking [minute_count, expire1, hour_count, expire2, burst_count]
                return [1, True, 1, True, 1]

        mock_redis.pipeline = lambda *args, **kwargs: _Pipe()
        mock_redis.ping = AsyncMock(return_value=True)

        # For completeness if used elsewhere
        mock_redis.get = AsyncMock(side_effect=_async_noop)

        # Provide other attrs used
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.ttl.return_value = 60
        
        with patch('redis.asyncio.ConnectionPool.from_url', return_value=AsyncMock()):
            # Patch Redis constructor so no real connection is attempted
            with patch('redis.asyncio.Redis', side_effect=lambda *args, **kwargs: mock_redis):
                yield mock_redis
    
    @pytest.mark.unit
    def test_rate_limit_initialization(self, app, mock_redis):
        """Test rate limit middleware initialization."""
        middleware = RateLimitMiddleware(
            app,
            default_requests_per_minute=10,
            redis_url="redis://localhost:6379"
        )
        
        assert middleware.default_rpm == 10
        assert middleware.redis_url == "redis://localhost:6379"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, app, mock_redis):
        """Test allowed request within rate limit."""
        app.add_middleware(RateLimitMiddleware, 
                         default_requests_per_minute=10,
                         redis_url="redis://localhost:6379")
        
        # Mock Redis to show request is allowed
        mock_redis.get.return_value = "3"  # 3 requests so far
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit-RPM" in response.headers
        assert "X-RateLimit-Remaining-RPM" in response.headers
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, app, mock_redis):
        """Test rate limit exceeded."""
        app.add_middleware(RateLimitMiddleware,
                         default_requests_per_minute=5,
                         redis_url="redis://localhost:6379")
        
        # Mock Redis pipeline to exceed limits
        class _PipeExceed:
            def incr(self, *args, **kwargs):
                pass
            def expire(self, *args, **kwargs):
                pass
            async def execute(self):
                # minute_count=6, hour_count=6, burst_count=6
                return [6, True, 6, True, 6]
        mock_redis.pipeline = lambda *args, **kwargs: _PipeExceed()
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.text
    
    @pytest.mark.unit
    def test_endpoint_specific_limits(self, app, mock_redis):
        """Test endpoint-specific rate limits."""
        middleware = RateLimitMiddleware(
            app,
            default_requests_per_minute=10,
        )
        # Override endpoint limits for testing purposes
        middleware.endpoint_limits = {"/api/v1/search": {"rpm": 20, "rph": 1000, "burst": 5}}
        
        # Test search endpoint has higher limit
        assert middleware._get_endpoint_limits("/api/v1/search")["rpm"] == 20
        assert middleware._get_endpoint_limits("/test")["rpm"] == 10
    
    @pytest.mark.unit
    def test_client_identification(self, app):
        """Test client identification for rate limiting."""
        middleware = RateLimitMiddleware(app)
        
        # Test IP-based identification
        request = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        client_id = middleware._get_client_identifier(request)
        assert client_id == "ip:127.0.0.1"
        
        # Test API key identification
        request.headers = {"X-API-Key": "test-key"}
        client_id = middleware._get_client_identifier(request)
        assert client_id == "key:test-key"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_redis_unavailable_fallback(self, app):
        """Test fallback when Redis is unavailable."""
        with patch('redis.asyncio.ConnectionPool.from_url', side_effect=Exception("Redis unavailable")):
            app.add_middleware(RateLimitMiddleware)
            
            client = TestClient(app)
            response = client.get("/test")
            
            # Should still work but without rate limiting
            assert response.status_code == 200
    
    @pytest.mark.unit
    def test_rate_limit_headers(self, app, mock_redis):
        """Test rate limit headers in response."""
        app.add_middleware(RateLimitMiddleware,
                         default_requests_per_minute=10)
        
        mock_redis.get.return_value = "3"
        mock_redis.ttl.return_value = 45
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit-RPM" in response.headers
        assert "X-RateLimit-Remaining-RPM" in response.headers
        assert "X-RateLimit-Reset-RPM" in response.headers


class TestMiddlewareIntegration:
    """Test middleware integration and interaction."""
    
    @pytest.fixture
    def app_with_all_middleware(self):
        """Create app with all middleware."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        # Add all middleware
        app.add_middleware(SecurityMiddleware)
        from core.config import get_settings
        settings = get_settings()
        app.add_middleware(LoggingMiddleware)
        app.add_middleware(RateLimitMiddleware, default_requests_per_minute=100)
        
        return app
    
    @pytest.mark.unit
    def test_middleware_order(self, app_with_all_middleware):
        """Test middleware execution order."""
        client = TestClient(app_with_all_middleware)
        response = client.get("/test")
        
        # All middleware should process successfully
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
        
        # Should have security headers
        assert "X-Content-Type-Options" in response.headers
        # Should have correlation ID from logging
        assert "X-Correlation-ID" in response.headers
    
    @pytest.mark.unit
    def test_middleware_exception_handling(self, app_with_all_middleware, caplog):
        """Test middleware exception handling."""
        
        @app_with_all_middleware.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        client = TestClient(app_with_all_middleware)
        
        with caplog.at_level("ERROR"):
            response = client.get("/error")
        
        # Should handle error gracefully
        assert response.status_code == 500
        
        # Error should be logged
        log_messages = [record.message for record in caplog.records]
        error_logs = [msg for msg in log_messages if "test error" in msg.lower() or "500" in msg]
        assert len(error_logs) > 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_middleware_performance(self, app_with_all_middleware):
        """Test middleware performance impact."""
        client = TestClient(app_with_all_middleware)
        
        # Measure response time with all middleware
        start_time = asyncio.get_event_loop().time()
        response = client.get("/test")
        end_time = asyncio.get_event_loop().time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        # With mock dependencies, should be fast
        assert response_time < 1.0  # Less than 1 second


@pytest.fixture(autouse=True)
def configure_test_settings():
    """Configure settings for testing."""
    with patch.object(settings, 'ENVIRONMENT', 'test'):
        with patch.object(settings, 'ENABLE_RATE_LIMITING', True):
            with patch.object(settings, 'ENABLE_REQUEST_LOGGING', True):
                yield 