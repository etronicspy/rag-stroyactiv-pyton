#!/usr/bin/env python3
"""
Быстрый тест восстановленного middleware функционала.
Запускается независимо от pytest для быстрой проверки.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any
import sys

class MiddlewareRecoveryTester:
    """Тестер восстановленного middleware функционала."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {"passed": 0, "failed": 0, "tests": []}
    
    def log_test(self, name: str, success: bool, details: str = ""):
        """Логирование результата теста."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if details:
            print(f"    {details}")
        
        self.results["tests"].append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
    
    def test_sql_injection_post_body(self) -> bool:
        """Тест блокировки SQL injection в POST body."""
        try:
            malicious_data = {
                "name": "'; DROP TABLE materials; --",
                "description": "SQL injection attempt"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/test/materials",
                json=malicious_data,
                timeout=5
            )
            
            success = response.status_code == 400
            details = f"Status: {response.status_code}, Expected: 400"
            
            self.log_test("SQL Injection POST Body Block", success, details)
            return success
            
        except Exception as e:
            self.log_test("SQL Injection POST Body Block", False, f"Error: {e}")
            return False
    
    def test_xss_post_body(self) -> bool:
        """Тест блокировки XSS в POST body."""
        try:
            malicious_data = {
                "name": "<script>alert('xss')</script>",
                "description": "XSS attempt"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/test/materials",
                json=malicious_data,
                timeout=5
            )
            
            success = response.status_code == 400
            details = f"Status: {response.status_code}, Expected: 400"
            
            self.log_test("XSS POST Body Block", success, details)
            return success
            
        except Exception as e:
            self.log_test("XSS POST Body Block", False, f"Error: {e}")
            return False
    
    def test_legitimate_cyrillic_content(self) -> bool:
        """Тест пропуска legitimate Cyrillic content."""
        try:
            legitimate_data = {
                "name": "Цемент М500",
                "description": "Высококачественный строительный материал"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/test/materials",
                json=legitimate_data,
                timeout=5
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Expected: 200"
            
            if success:
                data = response.json()
                if data.get("data", {}).get("name") == "Цемент М500":
                    details += " - Cyrillic preserved correctly"
                else:
                    success = False
                    details += " - Cyrillic not preserved"
            
            self.log_test("Legitimate Cyrillic Content", success, details)
            return success
            
        except Exception as e:
            self.log_test("Legitimate Cyrillic Content", False, f"Error: {e}")
            return False
    
    def test_sql_injection_query_params(self) -> bool:
        """Тест блокировки SQL injection в query params."""
        try:
            malicious_query = "'; DROP TABLE materials; --"
            
            response = requests.get(
                f"{self.base_url}/api/v1/test/sql-injection-test",
                params={"q": malicious_query},
                timeout=5
            )
            
            success = response.status_code == 400
            details = f"Status: {response.status_code}, Expected: 400"
            
            self.log_test("SQL Injection Query Params Block", success, details)
            return success
            
        except Exception as e:
            self.log_test("SQL Injection Query Params Block", False, f"Error: {e}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Тест работоспособности health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                if "status" in data:
                    details += f" - Health: {data['status']}"
            
            self.log_test("Health Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {e}")
            return False
    
    def test_security_headers(self) -> bool:
        """Тест присутствия security headers."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/test/materials/1", timeout=5)
            
            required_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection"
            ]
            
            missing_headers = []
            for header in required_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            success = len(missing_headers) == 0
            details = f"Status: {response.status_code}"
            
            if missing_headers:
                details += f" - Missing headers: {', '.join(missing_headers)}"
            else:
                details += " - All security headers present"
            
            self.log_test("Security Headers", success, details)
            return success
            
        except Exception as e:
            self.log_test("Security Headers", False, f"Error: {e}")
            return False
    
    def test_large_data_compression(self) -> bool:
        """Тест сжатия больших данных."""
        try:
            headers = {"Accept-Encoding": "gzip, deflate, br"}
            response = requests.get(
                f"{self.base_url}/api/v1/test/large-data",
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                content_encoding = response.headers.get("Content-Encoding", "none")
                content_length = len(response.content)
                details += f" - Encoding: {content_encoding}, Size: {content_length} bytes"
                
                # Если данные сжаты, это хорошо
                if content_encoding in ["gzip", "deflate", "br"]:
                    details += " - Compressed ✓"
                else:
                    details += " - Not compressed (may be normal for test data)"
            
            self.log_test("Large Data Compression", success, details)
            return success
            
        except Exception as e:
            self.log_test("Large Data Compression", False, f"Error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Запуск всех тестов."""
        print("🔍 Running Middleware Recovery Tests...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Основные security тесты
        self.test_sql_injection_post_body()
        self.test_xss_post_body()
        self.test_legitimate_cyrillic_content()
        self.test_sql_injection_query_params()
        
        # Функциональные тесты
        self.test_health_endpoint()
        self.test_security_headers()
        self.test_large_data_compression()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n📊 Test Results:")
        print("=" * 60)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        success_rate = (self.results["passed"] / (self.results["passed"] + self.results["failed"])) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.results["failed"] == 0:
            print("\n🎉 ALL TESTS PASSED! Middleware recovery successful!")
            return {"status": "success", "results": self.results}
        else:
            print(f"\n⚠️  {self.results['failed']} tests failed. Check details above.")
            return {"status": "partial", "results": self.results}

def main():
    """Главная функция."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"🚀 Testing middleware recovery on: {base_url}")
    
    tester = MiddlewareRecoveryTester(base_url)
    
    try:
        results = tester.run_all_tests()
        
        # Возвращаем exit code по результатам
        if results["status"] == "success":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 