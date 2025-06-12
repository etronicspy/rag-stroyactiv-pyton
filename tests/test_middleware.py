"""
Tests for middleware components: Rate Limiting, Logging, and Security.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from core.middleware import RateLimitMiddleware, LoggingMiddleware, SecurityMiddleware
from core.config import settings


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
    
    @pytest.fixture
    def security_middleware(self, app):
        """Create security middleware instance."""
        return SecurityMiddleware(
            app,
            max_request_size=1024,  # 1KB for testing
            enable_security_headers=True,
            enable_input_validation=True,
        )
    
    def test_request_size_limit(self, app, security_middleware):
        """Test request size limiting."""
        app.add_middleware(SecurityMiddleware, max_request_size=1024)
        client = TestClient(app)
        
        # Test large request
        large_data = "x" * 2048  # 2KB, exceeds limit
        response = client.post("/test", content=large_data, 
                             headers={"content-length": str(len(large_data))})
        
        assert response.status_code == 413
        assert "Request too large" in response.json()["error"]
    
    def test_blocked_user_agent(self, app):
        """Test blocked user agent detection."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test with blocked user agent
        response = client.get("/test", headers={"user-agent": "sqlmap/1.0"})
        
        assert response.status_code == 403
        assert response.json()["error"] == "Forbidden"
    
    def test_path_traversal_protection(self, app):
        """Test path traversal attack protection."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test path traversal in query
        response = client.get("/test?file=../../../etc/passwd")
        assert response.status_code == 400
    
    def test_sql_injection_protection(self, app):
        """Test SQL injection protection."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test SQL injection in query
        response = client.get("/test?query='; DROP TABLE users; --")
        assert response.status_code == 400
    
    def test_xss_protection(self, app):
        """Test XSS protection."""
        app.add_middleware(SecurityMiddleware)
        client = TestClient(app)
        
        # Test XSS in query
        response = client.get("/test?name=<script>alert('xss')</script>")
        assert response.status_code == 400
    
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
    
    def test_cors_settings_development(self):
        """Test CORS settings for development."""
        middleware = SecurityMiddleware(FastAPI())
        
        with patch.object(settings, 'ENVIRONMENT', 'development'):
            cors_settings = middleware.get_cors_settings()
            
            assert cors_settings["allow_origins"] == ["*"]
            assert cors_settings["allow_methods"] == ["*"]
    
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
    
    @pytest.fixture
    def logging_middleware(self, app):
        """Create logging middleware instance."""
        return LoggingMiddleware(
            app,
            log_level="DEBUG",
            log_request_body=True,
            max_body_size=1024,
        )
    
    def test_request_logging(self, app, caplog):
        """Test request logging."""
        app.add_middleware(LoggingMiddleware, log_level="INFO")
        client = TestClient(app)
        
        with caplog.at_level("INFO"):
            response = client.get("/test")
            
        assert response.status_code == 200
        # Check for correlation ID in response
        assert "X-Correlation-ID" in response.headers
        
        # Check logs contain request info
        log_messages = [record.message for record in caplog.records]
        request_logs = [msg for msg in log_messages if "Request:" in msg]
        assert len(request_logs) > 0
    
    def test_response_logging(self, app, caplog):
        """Test response logging."""
        app.add_middleware(LoggingMiddleware, log_level="INFO")
        client = TestClient(app)
        
        with caplog.at_level("INFO"):
            response = client.get("/test")
            
        assert response.status_code == 200
        
        # Check logs contain response info
        log_messages = [record.message for record in caplog.records]
        response_logs = [msg for msg in log_messages if "Response:" in msg]
        assert len(response_logs) > 0
    
    def test_exception_logging(self, app, caplog):
        """Test exception logging."""
        app.add_middleware(LoggingMiddleware, log_level="ERROR")
        client = TestClient(app)
        
        with caplog.at_level("ERROR"):
            response = client.get("/error")
            
        # Should still have correlation ID even in error
        assert "X-Correlation-ID" in response.headers
        
        # Check error logs
        log_messages = [record.message for record in caplog.records]
        error_logs = [msg for msg in log_messages if "Exception:" in msg]
        assert len(error_logs) > 0
    
    def test_request_body_logging(self, app, caplog):
        """Test request body logging."""
        app.add_middleware(LoggingMiddleware, 
                          log_level="INFO", 
                          log_request_body=True,
                          max_body_size=1024)
        client = TestClient(app)
        
        with caplog.at_level("INFO"):
            response = client.post("/test", json={"test": "data"})
            
        assert response.status_code == 200
        
        # Check that request body was logged
        log_messages = [record.message for record in caplog.records]
        body_logs = [msg for msg in log_messages if '"test": "data"' in msg]
        assert len(body_logs) > 0
    
    def test_excluded_paths(self, app, caplog):
        """Test excluded paths from detailed logging."""
        app.add_middleware(LoggingMiddleware, log_level="DEBUG")
        client = TestClient(app)
        
        # Add health endpoint
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        with caplog.at_level("DEBUG"):
            response = client.get("/health")
            
        assert response.status_code == 200
        
        # Should have minimal logging for health checks
        log_messages = [record.message for record in caplog.records]
        detailed_logs = [msg for msg in log_messages if "Request:" in msg and "/health" in msg]
        # Health endpoint should not have detailed request logging
        assert len(detailed_logs) == 0
    
    def test_sensitive_header_masking(self):
        """Test sensitive header masking."""
        middleware = LoggingMiddleware(FastAPI())
        
        headers = {
            "authorization": "Bearer secret-token-12345",
            "x-api-key": "api-key-67890",
            "content-type": "application/json",
            "user-agent": "test-client"
        }
        
        masked = middleware._mask_sensitive_data(headers)
        
        # Sensitive headers should be masked
        assert masked["authorization"] == "Bear...2345"
        assert masked["x-api-key"] == "api-...7890"
        
        # Non-sensitive headers should be unchanged
        assert masked["content-type"] == "application/json"
        assert masked["user-agent"] == "test-client"


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
        with patch('core.middleware.rate_limiting.aioredis') as mock_aioredis:
            mock_redis = AsyncMock()
            mock_pipeline = AsyncMock()
            mock_pipeline.execute.return_value = [1, None, 1, None, 1, None]  # Simulate counters
            mock_redis.pipeline.return_value = mock_pipeline
            mock_redis.ping.return_value = True
            
            mock_pool = AsyncMock()
            mock_aioredis.ConnectionPool.from_url.return_value = mock_pool
            mock_aioredis.Redis.return_value = mock_redis
            
            yield mock_redis
    
    def test_rate_limit_initialization(self, app, mock_redis):
        """Test rate limit middleware initialization."""
        middleware = RateLimitMiddleware(
            app, 
            redis_url="redis://localhost:6379",
            default_requests_per_minute=10,
            default_requests_per_hour=100
        )
        
        assert middleware.default_rpm == 10
        assert middleware.default_rph == 100
    
    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, app, mock_redis):
        """Test requests within rate limits."""
        app.add_middleware(RateLimitMiddleware,
                          redis_url="redis://localhost:6379",
                          default_requests_per_minute=10)
        
        client = TestClient(app)
        
        # Mock Redis to return low counts (within limits)
        mock_redis.pipeline.return_value.execute.return_value = [1, None, 1, None, 1, None]
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit-RPM" in response.headers
        assert "X-RateLimit-Remaining-RPM" in response.headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, app, mock_redis):
        """Test rate limit exceeded."""
        app.add_middleware(RateLimitMiddleware,
                          redis_url="redis://localhost:6379",
                          default_requests_per_minute=5)
        
        client = TestClient(app)
        
        # Mock Redis to return high counts (exceeds limits)
        mock_redis.pipeline.return_value.execute.return_value = [10, None, 10, None, 10, None]
        
        response = client.get("/test")
        
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["error"]
        assert "Retry-After" in response.headers
    
    def test_endpoint_specific_limits(self, app, mock_redis):
        """Test endpoint-specific rate limits."""
        middleware = RateLimitMiddleware(app, redis_url="redis://localhost:6379")
        
        # Test search endpoint has different limits
        search_limits = middleware._get_endpoint_limits("/api/v1/search")
        default_limits = middleware._get_endpoint_limits("/test")
        
        assert search_limits["rpm"] == 30  # Search has stricter limit
        assert default_limits["rpm"] == 60  # Default limit
    
    def test_client_identification(self, app):
        """Test client identification methods."""
        middleware = RateLimitMiddleware(app, redis_url="redis://localhost:6379")
        
        # Mock request with API key
        request_with_key = Mock()
        request_with_key.headers = {"X-API-Key": "test-key"}
        client_id = middleware._get_client_identifier(request_with_key)
        assert client_id == "key:test-key"
        
        # Mock request with IP
        request_with_ip = Mock()
        request_with_ip.headers = {}
        request_with_ip.client.host = "192.168.1.1"
        client_id = middleware._get_client_identifier(request_with_ip)
        assert client_id == "ip:192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_redis_unavailable_fallback(self, app):
        """Test fallback when Redis is unavailable."""
        with patch('core.middleware.rate_limiting.aioredis') as mock_aioredis:
            # Mock Redis connection failure
            mock_aioredis.ConnectionPool.from_url.side_effect = Exception("Redis unavailable")
            
            app.add_middleware(RateLimitMiddleware, redis_url="redis://localhost:6379")
            client = TestClient(app)
            
            # Should still work without rate limiting
            response = client.get("/test")
            assert response.status_code == 200
    
    def test_rate_limit_headers(self, app, mock_redis):
        """Test rate limit headers in response."""
        app.add_middleware(RateLimitMiddleware, redis_url="redis://localhost:6379")
        client = TestClient(app)
        
        response = client.get("/test")
        
        # Check rate limit headers are present
        expected_headers = [
            "X-RateLimit-Limit-RPM",
            "X-RateLimit-Remaining-RPM", 
            "X-RateLimit-Reset-RPM"
        ]
        
        for header in expected_headers:
            assert header in response.headers


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
        app.add_middleware(LoggingMiddleware, log_level="INFO")
        
        return app
    
    def test_middleware_order(self, app_with_all_middleware):
        """Test middleware execution order."""
        client = TestClient(app_with_all_middleware)
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Should have correlation ID from logging middleware
        assert "X-Correlation-ID" in response.headers
        
        # Should have security headers
        assert "X-Content-Type-Options" in response.headers
    
    def test_middleware_exception_handling(self, app_with_all_middleware, caplog):
        """Test middleware handles exceptions gracefully."""
        
        @app_with_all_middleware.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        client = TestClient(app_with_all_middleware)
        
        with caplog.at_level("ERROR"):
            response = client.get("/error")
        
        # Should still have middleware headers even on error
        assert "X-Correlation-ID" in response.headers
        
        # Error should be logged
        error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
        assert len(error_logs) > 0
    
    @pytest.mark.asyncio
    async def test_middleware_performance(self, app_with_all_middleware):
        """Test middleware doesn't significantly impact performance."""
        client = TestClient(app_with_all_middleware)
        
        # Time multiple requests
        start_time = time.time()
        for _ in range(10):
            response = client.get("/test")
            assert response.status_code == 200
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # Each request should complete quickly (< 100ms)
        assert avg_time < 0.1  # 100ms


# === PYTEST CONFIGURATION ===
@pytest.fixture(autouse=True)
def configure_test_settings():
    """Configure settings for testing."""
    with patch.object(settings, 'ENVIRONMENT', 'testing'):
        with patch.object(settings, 'REDIS_URL', 'redis://localhost:6379'):
            yield 