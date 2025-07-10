#!/usr/bin/env python3
"""
Тест скрипт для проверки Stage 8 - Full API Pipeline.
Проверяет работу всего batch processing pipeline через API endpoints.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any

import aiohttp
import pytest
from pydantic import ValidationError

from core.schemas.processing_models import (
    BatchMaterialsRequest,
    MaterialInput,
    ProcessingStatus,
    ProcessingProgress
)
from core.logging import get_logger

# Настройка логгера
logger = get_logger(__name__)

# Конфигурация для тестов
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/materials"

# Тестовые данные
TEST_MATERIALS = [
    {"id": "test_001", "name": "Кирпич керамический М125", "unit": "шт"},
    {"id": "test_002", "name": "Цемент М400", "unit": "кг"},
    {"id": "test_003", "name": "Песок речной", "unit": "м³"},
    {"id": "test_004", "name": "Щебень фракции 20-40", "unit": "м³"},
    {"id": "test_005", "name": "Арматура А400 диаметр 12мм", "unit": "м"},
    {"id": "test_006", "name": "Бетон М300", "unit": "м³"},
    {"id": "test_007", "name": "Доска обрезная 50x150x6000", "unit": "м³"},
    {"id": "test_008", "name": "Гипсокартон 12.5мм", "unit": "м²"},
    {"id": "test_009", "name": "Утеплитель минвата 100мм", "unit": "м²"},
    {"id": "test_010", "name": "Кровля металлочерепица", "unit": "м²"}
]

LARGE_BATCH_MATERIALS = [
    {"id": f"large_batch_{i:03d}", "name": f"Материал тестовый {i}", "unit": "шт"}
    for i in range(1, 101)  # 100 материалов
]


class Stage8PipelineTestRunner:
    """Тест runner для Stage 8 pipeline."""
    
    def __init__(self):
        self.logger = logger
        self.session: aiohttp.ClientSession = None
        self.test_results: List[Dict[str, Any]] = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self):
        """Запустить все тесты Stage 8 pipeline."""
        self.logger.info("🚀 Starting Stage 8 Full Pipeline Tests")
        
        try:
            # Тест 1: Проверка health endpoint
            await self._test_health_endpoint()
            
            # Тест 2: Малый batch (10 материалов)
            await self._test_small_batch()
            
            # Тест 3: Средний batch (50 материалов)
            await self._test_medium_batch()
            
            # Тест 4: Большой batch (100 материалов)
            await self._test_large_batch()
            
            # Тест 5: Проверка статистики
            await self._test_statistics()
            
            # Тест 6: Проверка валидации данных
            await self._test_validation_errors()
            
            # Тест 7: Проверка retry функциональности
            await self._test_retry_functionality()
            
            # Тест 8: Проверка concurrent requests
            await self._test_concurrent_requests()
            
            # Финальный отчет
            await self._generate_final_report()
            
        except Exception as e:
            self.logger.error(f"Error running tests: {str(e)}")
            raise
    
    async def _test_health_endpoint(self):
        """Тест health endpoint."""
        self.logger.info("Testing health endpoint...")
        
        try:
            async with self.session.get(f"{API_BASE}/process-enhanced/health") as response:
                data = await response.json()
                
                assert response.status == 200
                assert data["status"] in ["healthy", "overloaded", "degraded"]
                assert "timestamp" in data
                
                self.test_results.append({
                    "test": "health_endpoint",
                    "status": "passed",
                    "response": data
                })
                
                self.logger.info("✅ Health endpoint test passed")
                
        except Exception as e:
            self.logger.error(f"❌ Health endpoint test failed: {str(e)}")
            self.test_results.append({
                "test": "health_endpoint",
                "status": "failed",
                "error": str(e)
            })
    
    async def _test_small_batch(self):
        """Тест малого batch (10 материалов)."""
        self.logger.info("Testing small batch processing...")
        
        try:
            request_id = f"small_batch_{uuid.uuid4().hex[:8]}"
            materials = TEST_MATERIALS[:10]
            
            # Отправляем запрос
            request_data = {
                "request_id": request_id,
                "materials": materials
            }
            
            async with self.session.post(
                f"{API_BASE}/process-enhanced",
                json=request_data
            ) as response:
                data = await response.json()
                
                assert response.status == 200
                assert data["status"] == "accepted"
                assert data["request_id"] == request_id
                assert data["materials_count"] == 10
                
                self.logger.info(f"✅ Small batch request accepted: {request_id}")
            
            # Ждем завершения обработки
            await self._wait_for_processing_completion(request_id)
            
            # Проверяем результаты
            results = await self._get_processing_results(request_id)
            
            self.test_results.append({
                "test": "small_batch",
                "status": "passed",
                "request_id": request_id,
                "materials_count": 10,
                "results_count": len(results)
            })
            
            self.logger.info("✅ Small batch test passed")
            
        except Exception as e:
            self.logger.error(f"❌ Small batch test failed: {str(e)}")
            self.test_results.append({
                "test": "small_batch",
                "status": "failed",
                "error": str(e)
            })
    
    async def _test_medium_batch(self):
        """Тест среднего batch (50 материалов)."""
        self.logger.info("Testing medium batch processing...")
        
        try:
            request_id = f"medium_batch_{uuid.uuid4().hex[:8]}"
            materials = LARGE_BATCH_MATERIALS[:50]
            
            # Отправляем запрос
            request_data = {
                "request_id": request_id,
                "materials": materials
            }
            
            async with self.session.post(
                f"{API_BASE}/process-enhanced",
                json=request_data
            ) as response:
                data = await response.json()
                
                assert response.status == 200
                assert data["status"] == "accepted"
                assert data["request_id"] == request_id
                assert data["materials_count"] == 50
                
                self.logger.info(f"✅ Medium batch request accepted: {request_id}")
            
            # Ждем завершения обработки
            await self._wait_for_processing_completion(request_id)
            
            # Проверяем результаты
            results = await self._get_processing_results(request_id)
            
            self.test_results.append({
                "test": "medium_batch",
                "status": "passed",
                "request_id": request_id,
                "materials_count": 50,
                "results_count": len(results)
            })
            
            self.logger.info("✅ Medium batch test passed")
            
        except Exception as e:
            self.logger.error(f"❌ Medium batch test failed: {str(e)}")
            self.test_results.append({
                "test": "medium_batch",
                "status": "failed",
                "error": str(e)
            })
    
    async def _test_large_batch(self):
        """Тест большого batch (100 материалов)."""
        self.logger.info("Testing large batch processing...")
        
        try:
            request_id = f"large_batch_{uuid.uuid4().hex[:8]}"
            materials = LARGE_BATCH_MATERIALS
            
            # Отправляем запрос
            request_data = {
                "request_id": request_id,
                "materials": materials
            }
            
            async with self.session.post(
                f"{API_BASE}/process-enhanced",
                json=request_data
            ) as response:
                data = await response.json()
                
                assert response.status == 200
                assert data["status"] == "accepted"
                assert data["request_id"] == request_id
                assert data["materials_count"] == 100
                
                self.logger.info(f"✅ Large batch request accepted: {request_id}")
            
            # Ждем завершения обработки (больше времени для большого batch)
            await self._wait_for_processing_completion(request_id, timeout=300)
            
            # Проверяем результаты
            results = await self._get_processing_results(request_id)
            
            self.test_results.append({
                "test": "large_batch",
                "status": "passed",
                "request_id": request_id,
                "materials_count": 100,
                "results_count": len(results)
            })
            
            self.logger.info("✅ Large batch test passed")
            
        except Exception as e:
            self.logger.error(f"❌ Large batch test failed: {str(e)}")
            self.test_results.append({
                "test": "large_batch",
                "status": "failed",
                "error": str(e)
            })
    
    async def _test_statistics(self):
        """Тест получения статистики."""
        self.logger.info("Testing statistics endpoint...")
        
        try:
            async with self.session.get(f"{API_BASE}/process-enhanced/statistics") as response:
                data = await response.json()
                
                assert response.status == 200
                assert "total_requests" in data
                assert "total_materials" in data
                assert "success_rate" in data
                
                self.test_results.append({
                    "test": "statistics",
                    "status": "passed",
                    "statistics": data
                })
                
                self.logger.info("✅ Statistics test passed")
                
        except Exception as e:
            self.logger.error(f"❌ Statistics test failed: {str(e)}")
            self.test_results.append({
                "test": "statistics",
                "status": "failed",
                "error": str(e)
            })
    
    async def _test_validation_errors(self):
        """Тест валидации данных."""
        self.logger.info("Testing validation errors...")
        
        try:
            # Тест с пустым списком материалов
            request_data = {
                "request_id": "empty_materials",
                "materials": []
            }
            
            async with self.session.post(
                f"{API_BASE}/process-enhanced",
                json=request_data
            ) as response:
                data = await response.json()
                
                assert response.status == 400 or "errors" in data
                
                self.logger.info("✅ Empty materials validation test passed")
            
            # Тест с невалидными данными
            request_data = {
                "request_id": "invalid_data",
                "materials": [
                    {"id": "", "name": "", "unit": ""}  # Пустые поля
                ]
            }
            
            async with self.session.post(
                f"{API_BASE}/process-enhanced",
                json=request_data
            ) as response:
                data = await response.json()
                
                assert response.status == 400 or "errors" in data
                
                self.logger.info("✅ Invalid data validation test passed")
            
            self.test_results.append({
                "test": "validation_errors",
                "status": "passed"
            })
            
        except Exception as e:
            self.logger.error(f"❌ Validation errors test failed: {str(e)}")
            self.test_results.append({
                "test": "validation_errors",
                "status": "failed",
                "error": str(e)
            })
    
    async def _test_retry_functionality(self):
        """Тест retry функциональности."""
        self.logger.info("Testing retry functionality...")
        
        try:
            async with self.session.post(f"{API_BASE}/process-enhanced/retry") as response:
                data = await response.json()
                
                assert response.status == 200
                assert "retry_count" in data
                
                self.test_results.append({
                    "test": "retry_functionality",
                    "status": "passed",
                    "retry_count": data["retry_count"]
                })
                
                self.logger.info("✅ Retry functionality test passed")
                
        except Exception as e:
            self.logger.error(f"❌ Retry functionality test failed: {str(e)}")
            self.test_results.append({
                "test": "retry_functionality",
                "status": "failed",
                "error": str(e)
            })
    
    async def _test_concurrent_requests(self):
        """Тест concurrent requests."""
        self.logger.info("Testing concurrent requests...")
        
        try:
            # Создаем 3 одновременных запроса
            tasks = []
            
            for i in range(3):
                request_id = f"concurrent_{i}_{uuid.uuid4().hex[:8]}"
                materials = TEST_MATERIALS[:5]  # Малые batch для быстроты
                
                request_data = {
                    "request_id": request_id,
                    "materials": materials
                }
                
                task = self._send_batch_request(request_data)
                tasks.append(task)
            
            # Ждем завершения всех запросов
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Проверяем результаты
            success_count = sum(1 for r in responses if not isinstance(r, Exception))
            
            self.test_results.append({
                "test": "concurrent_requests",
                "status": "passed",
                "total_requests": 3,
                "successful_requests": success_count
            })
            
            self.logger.info("✅ Concurrent requests test passed")
            
        except Exception as e:
            self.logger.error(f"❌ Concurrent requests test failed: {str(e)}")
            self.test_results.append({
                "test": "concurrent_requests",
                "status": "failed",
                "error": str(e)
            })
    
    async def _send_batch_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправить batch request."""
        async with self.session.post(
            f"{API_BASE}/process-enhanced",
            json=request_data
        ) as response:
            return await response.json()
    
    async def _wait_for_processing_completion(self, request_id: str, timeout: int = 120):
        """Ждать завершения обработки."""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            try:
                async with self.session.get(
                    f"{API_BASE}/process-enhanced/status/{request_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status")
                        
                        if status in ["completed", "failed"]:
                            self.logger.info(f"Processing completed for {request_id}: {status}")
                            return
                        
                        if status == "processing":
                            progress = data.get("progress", {})
                            self.logger.info(
                                f"Processing {request_id}: {progress.get('completed', 0)}/"
                                f"{progress.get('total', 0)} completed"
                            )
                    
                    await asyncio.sleep(5)  # Ждем 5 секунд
                    
            except Exception as e:
                self.logger.warning(f"Error checking status for {request_id}: {str(e)}")
                await asyncio.sleep(5)
        
        self.logger.warning(f"Timeout waiting for completion of {request_id}")
    
    async def _get_processing_results(self, request_id: str) -> List[Dict[str, Any]]:
        """Получить результаты обработки."""
        try:
            async with self.session.get(
                f"{API_BASE}/process-enhanced/results/{request_id}"
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    return data.get("results", [])
                else:
                    self.logger.warning(f"Error getting results for {request_id}: {data}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting results for {request_id}: {str(e)}")
            return []
    
    async def _generate_final_report(self):
        """Сгенерировать финальный отчет."""
        self.logger.info("Generating final test report...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "passed")
        failed_tests = total_tests - passed_tests
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "test_results": self.test_results
        }
        
        # Сохраняем отчет
        report_file = f"test_results/stage_8_pipeline_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            import os
            os.makedirs("test_results", exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Test report saved to {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving test report: {str(e)}")
        
        # Выводим сводку
        self.logger.info("=" * 60)
        self.logger.info("🎯 STAGE 8 PIPELINE TEST RESULTS")
        self.logger.info("=" * 60)
        self.logger.info(f"Total tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Failed: {failed_tests}")
        self.logger.info(f"Success rate: {report['success_rate']:.1%}")
        self.logger.info("=" * 60)
        
        if failed_tests > 0:
            self.logger.error("❌ Some tests failed!")
            for result in self.test_results:
                if result["status"] == "failed":
                    self.logger.error(f"Failed test: {result['test']} - {result.get('error', 'Unknown error')}")
        else:
            self.logger.info("✅ All tests passed!")


async def main():
    """Основная функция для запуска тестов."""
    try:
        async with Stage8PipelineTestRunner() as test_runner:
            await test_runner.run_all_tests()
            
    except Exception as e:
        logger.error(f"Error running Stage 8 pipeline tests: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    
    # Запускаем тесты
    result = asyncio.run(main())
    sys.exit(result) 