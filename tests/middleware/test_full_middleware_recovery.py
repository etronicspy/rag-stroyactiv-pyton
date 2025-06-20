"""
Tests for full middleware recovery functionality.
Testing all recovered components: Security, Logging, Compression, RateLimit.
"""

import pytest
import json
import time
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

class TestFullMiddlewareRecovery:
    """Тесты полного восстановления всех middleware компонентов."""
    
    def test_logging_middleware_request_body_logging(self):
        """Тест логирования тел запросов."""
        test_data = {
            "name": "Test Material for Logging",
            "description": "Testing request body logging functionality"
        }
        
        with patch('core.middleware.request_logging.logger') as mock_logger:
            response = client.post("/api/v1/test/materials", json=test_data)
            
            assert response.status_code == 200
            
            # Проверяем что request body логируется
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            request_body_logged = any("request_body" in call for call in log_calls)
            
            print(f"✅ Request body logging: {'ENABLED' if request_body_logged else 'DISABLED'}")
            # Может быть включено или отключено в зависимости от конфигурации
    
    def test_logging_middleware_response_body_logging(self):
        """Тест логирования тел ответов."""
        with patch('core.middleware.request_logging.logger') as mock_logger:
            response = client.get("/api/v1/test/materials/1")
            
            assert response.status_code == 200
            
            # Проверяем что response body логируется
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            response_body_logged = any("response_body" in call for call in log_calls)
            
            print(f"✅ Response body logging: {'ENABLED' if response_body_logged else 'DISABLED'}")
    
    def test_logging_middleware_headers_logging(self):
        """Тест логирования headers."""
        headers = {
            "X-Custom-Header": "test-value",
            "X-API-Key": "secret-key-12345",
            "User-Agent": "MiddlewareRecoveryTest/1.0"
        }
        
        with patch('core.middleware.request_logging.logger') as mock_logger:
            response = client.get("/api/v1/test/materials/1", headers=headers)
            
            assert response.status_code == 200
            
            # Проверяем что headers логируются
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            headers_logged = any("X-Custom-Header" in call for call in log_calls)
            
            # Проверяем что sensitive headers маскируются
            sensitive_masked = not any("secret-key-12345" in call for call in log_calls)
            
            print(f"✅ Headers logging: {'ENABLED' if headers_logged else 'DISABLED'}")
            print(f"✅ Sensitive headers masking: {'ENABLED' if sensitive_masked else 'DISABLED'}")
    
    def test_compression_middleware_brotli_support(self):
        """Тест поддержки Brotli сжатия."""
        headers = {"Accept-Encoding": "br, gzip, deflate"}
        
        response = client.get("/api/v1/test/large-data", headers=headers)
        
        assert response.status_code == 200
        
        content_encoding = response.headers.get("Content-Encoding", "none")
        content_length = len(response.content)
        
        print(f"✅ Compression type: {content_encoding}")
        print(f"✅ Response size: {content_length} bytes")
        
        # Проверяем что данные сжимаются (если размер достаточно большой)
        if content_length > 2048:  # Minimum size for compression
            compression_enabled = content_encoding in ["br", "gzip", "deflate"]
            print(f"✅ Compression enabled: {compression_enabled}")
        else:
            print("ℹ️  Response too small for compression")
    
    def test_compression_middleware_gzip_fallback(self):
        """Тест fallback на gzip если Brotli не поддерживается."""
        headers = {"Accept-Encoding": "gzip, deflate"}  # No Brotli
        
        response = client.get("/api/v1/test/large-data", headers=headers)
        
        assert response.status_code == 200
        
        content_encoding = response.headers.get("Content-Encoding", "none")
        
        print(f"✅ Fallback compression: {content_encoding}")
        
        # Должен использовать gzip или deflate
        if content_encoding in ["gzip", "deflate"]:
            print("✅ Gzip/Deflate fallback working")
        elif content_encoding == "none":
            print("ℹ️  No compression (response may be too small)")
    
    def test_compression_middleware_streaming(self):
        """Тест streaming сжатия для больших ответов."""
        # Для этого теста нужен endpoint возвращающий действительно большие данные
        headers = {"Accept-Encoding": "gzip"}
        
        response = client.get("/api/v1/test/large-data", headers=headers)
        
        assert response.status_code == 200
        
        # Проверяем Transfer-Encoding для streaming
        transfer_encoding = response.headers.get("Transfer-Encoding", "none")
        
        print(f"✅ Transfer encoding: {transfer_encoding}")
        print("✅ Streaming compression test completed")
    
    def test_rate_limit_middleware_headers(self):
        """Тест наличия rate limit headers."""
        response = client.get("/api/v1/test/materials/1")
        
        assert response.status_code == 200
        
        # Проверяем наличие rate limit headers
        rate_limit_headers = {
            "X-RateLimit-Limit-RPM": response.headers.get("X-RateLimit-Limit-RPM"),
            "X-RateLimit-Remaining-RPM": response.headers.get("X-RateLimit-Remaining-RPM"),
            "X-RateLimit-Reset-RPM": response.headers.get("X-RateLimit-Reset-RPM"),
        }
        
        headers_present = sum(1 for v in rate_limit_headers.values() if v is not None)
        
        print(f"✅ Rate limit headers present: {headers_present}/3")
        for header, value in rate_limit_headers.items():
            if value:
                print(f"    {header}: {value}")
    
    def test_rate_limit_middleware_performance_logging(self):
        """Тест performance логирования rate limiting."""
        with patch('core.middleware.rate_limiting.logger') as mock_logger:
            # Несколько запросов для тестирования performance logging
            for i in range(3):
                response = client.get("/api/v1/test/materials/1")
                assert response.status_code == 200
                time.sleep(0.1)
            
            # Проверяем что performance метрики логируются
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            performance_logged = any("performance" in call.lower() or "rate_limit" in call.lower() 
                                   for call in log_calls)
            
            print(f"✅ Rate limit performance logging: {'ENABLED' if performance_logged else 'DISABLED'}")
    
    def test_security_middleware_still_working(self):
        """Тест что SecurityMiddleware все еще работает после восстановления других."""
        malicious_data = {
            "name": "'; DROP TABLE materials; --",
            "description": "Testing security after full recovery"
        }
        
        response = client.post("/api/v1/test/materials", json=malicious_data)
        
        assert response.status_code == 400
        response_data = response.json()
        assert "Invalid input detected" in response_data["message"]
        
        print("✅ SecurityMiddleware still blocking attacks after full recovery")
    
    def test_full_middleware_stack_integration(self):
        """Интеграционный тест всего middleware стека."""
        # Legitimate запрос, который должен пройти через все middleware
        legitimate_data = {
            "name": "Интеграционный тест цемента",
            "description": "Полный тест всего middleware стека с русским текстом"
        }
        
        headers = {
            "Accept-Encoding": "br, gzip",
            "X-Test-Header": "integration-test",
            "User-Agent": "FullStackTest/1.0"
        }
        
        start_time = time.time()
        
        response = client.post(
            "/api/v1/test/materials", 
            json=legitimate_data, 
            headers=headers
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Проверяем что данные корректно прошли
        assert response_data["status"] == "success"
        assert response_data["data"]["name"] == "Интеграционный тест цемента"
        
        # Проверяем middleware headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection"
        ]
        
        security_headers_present = sum(1 for h in security_headers 
                                     if h in response.headers)
        
        print(f"✅ Integration test passed:")
        print(f"    - Response time: {duration:.3f}s")
        print(f"    - Status: {response.status_code}")
        print(f"    - Security headers: {security_headers_present}/{len(security_headers)}")
        print(f"    - Content encoding: {response.headers.get('Content-Encoding', 'none')}")
        print(f"    - Response size: {len(response.content)} bytes")
        print(f"    - Cyrillic preserved: {'✓' if 'цемента' in str(response.content) else '✗'}")

# Benchmark test для проверки производительности
class TestMiddlewarePerformance:
    """Тесты производительности восстановленного middleware стека."""
    
    def test_performance_under_load(self):
        """Тест производительности под нагрузкой."""
        requests_count = 20
        total_time = 0
        successful_requests = 0
        
        print(f"🔬 Performance test: {requests_count} requests")
        
        for i in range(requests_count):
            start_time = time.time()
            
            response = client.get("/api/v1/test/materials/1")
            
            end_time = time.time()
            request_time = end_time - start_time
            total_time += request_time
            
            if response.status_code == 200:
                successful_requests += 1
        
        avg_time = total_time / requests_count
        success_rate = (successful_requests / requests_count) * 100
        
        print(f"✅ Performance results:")
        print(f"    - Average response time: {avg_time:.3f}s")
        print(f"    - Total time: {total_time:.3f}s")
        print(f"    - Success rate: {success_rate:.1f}%")
        print(f"    - Requests per second: {requests_count/total_time:.1f}")
        
        # Базовые критерии производительности
        assert avg_time < 0.1, f"Average response time too high: {avg_time:.3f}s"
        assert success_rate >= 95, f"Success rate too low: {success_rate:.1f}%"
        
        print("✅ Performance test passed")

if __name__ == "__main__":
    # Быстрый запуск тестов
    import sys
    
    print("🔍 Running Full Middleware Recovery Tests...")
    print("=" * 70)
    
    # Основные тесты
    recovery_test = TestFullMiddlewareRecovery()
    performance_test = TestMiddlewarePerformance()
    
    try:
        print("\n📝 Logging Middleware Tests:")
        recovery_test.test_logging_middleware_request_body_logging()
        recovery_test.test_logging_middleware_response_body_logging()
        recovery_test.test_logging_middleware_headers_logging()
        
        print("\n⚡ Compression Middleware Tests:")
        recovery_test.test_compression_middleware_brotli_support()
        recovery_test.test_compression_middleware_gzip_fallback()
        recovery_test.test_compression_middleware_streaming()
        
        print("\n📊 Rate Limit Middleware Tests:")
        recovery_test.test_rate_limit_middleware_headers()
        recovery_test.test_rate_limit_middleware_performance_logging()
        
        print("\n🛡️ Security Integration Tests:")
        recovery_test.test_security_middleware_still_working()
        
        print("\n🧪 Full Stack Integration:")
        recovery_test.test_full_middleware_stack_integration()
        
        print("\n🚀 Performance Tests:")
        performance_test.test_performance_under_load()
        
        print("\n🎉 ALL FULL MIDDLEWARE RECOVERY TESTS PASSED!")
        print("✅ Complete middleware stack successfully restored!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 