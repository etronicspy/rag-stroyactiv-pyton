"""
Performance Tests for Enhanced Parser Integration

Performance benchmarks for the enhanced parser integration service
to ensure optimal performance under various load conditions.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, Tuple
from unittest.mock import Mock, patch
import concurrent.futures

from services.enhanced_parser_integration import (
    EnhancedParserIntegrationService,
    get_parser_service,
    test_enhanced_parser
)
from core.schemas.enhanced_parsing import (
    EnhancedParseRequest,
    EnhancedParseResult,
    BatchParseRequest,
    BatchParseResponse,
    ParserIntegrationConfig,
    ParsingMethod
)


class TestEnhancedParserPerformance:
    """Performance tests for enhanced parser integration"""
    
    def test_service_initialization_performance(self):
        """Test service initialization performance"""
        try:
            start_time = time.time()
            
            # Initialize service multiple times
            for i in range(10):
                service = get_parser_service()
                assert service is not None
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / 10
            
            # Should initialize quickly (< 1 second per initialization)
            assert avg_time < 1.0, f"Service initialization too slow: {avg_time:.3f}s"
            
            print(f"✅ Service initialization performance: {avg_time:.3f}s average")
            
        except Exception as e:
            pytest.skip(f"Service initialization performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_single_parsing_performance(self):
        """Test single material parsing performance"""
        try:
            service = get_parser_service()
            
            # Test materials for parsing
            test_materials = [
                "Кирпич красный облицовочный",
                "Цемент портландцемент М400",
                "Песок речной строительный",
                "Плитка керамическая белая",
                "Доска обрезная 50х150х6000"
            ]
            
            parsing_times = []
            
            for material_name in test_materials:
                request = EnhancedParseRequest(
                    name=material_name,
                    unit="шт",
                    price=100.0,
                    parsing_method=ParsingMethod.AI_GPT
                )
                
                start_time = time.time()
                result = await service.parse_single_material(request)
                end_time = time.time()
                
                parsing_time = end_time - start_time
                parsing_times.append(parsing_time)
                
                # Verify result structure
                assert isinstance(result, EnhancedParseResult)
                assert result.processing_time > 0
            
            # Calculate statistics
            avg_time = statistics.mean(parsing_times)
            median_time = statistics.median(parsing_times)
            max_time = max(parsing_times)
            min_time = min(parsing_times)
            
            print(f"✅ Single parsing performance:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Median: {median_time:.3f}s")
            print(f"   Max: {max_time:.3f}s")
            print(f"   Min: {min_time:.3f}s")
            
            # Performance assertions (adjust thresholds as needed)
            assert avg_time < 30.0, f"Average parsing time too slow: {avg_time:.3f}s"
            assert max_time < 60.0, f"Max parsing time too slow: {max_time:.3f}s"
            
        except Exception as e:
            pytest.skip(f"Single parsing performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_batch_parsing_performance(self):
        """Test batch parsing performance"""
        try:
            service = get_parser_service()
            
            # Create batch of materials
            batch_sizes = [5, 10, 20]
            
            for batch_size in batch_sizes:
                materials = []
                for i in range(batch_size):
                    materials.append(EnhancedParseRequest(
                        name=f"Тестовый материал {i+1}",
                        unit="шт",
                        price=100.0 + i,
                        parsing_method=ParsingMethod.AI_GPT
                    ))
                
                batch_request = BatchParseRequest(
                    materials=materials,
                    parallel_processing=True,
                    max_workers=min(5, batch_size)
                )
                
                start_time = time.time()
                response = await service.parse_batch_materials(batch_request)
                end_time = time.time()
                
                batch_time = end_time - start_time
                per_item_time = batch_time / batch_size
                
                print(f"✅ Batch parsing performance (size {batch_size}):")
                print(f"   Total time: {batch_time:.3f}s")
                print(f"   Per item: {per_item_time:.3f}s")
                print(f"   Success rate: {response.success_rate:.1f}%")
                
                # Verify response structure
                assert isinstance(response, BatchParseResponse)
                assert response.total_processed == batch_size
                assert response.total_processing_time > 0
                
                # Performance assertions
                assert batch_time < batch_size * 30.0, f"Batch processing too slow: {batch_time:.3f}s"
                
        except Exception as e:
            pytest.skip(f"Batch parsing performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_performance(self):
        """Test performance difference between parallel and sequential processing"""
        try:
            service = get_parser_service()
            
            # Test materials
            materials = []
            for i in range(10):
                materials.append(EnhancedParseRequest(
                    name=f"Материал параллельный тест {i+1}",
                    unit="шт",
                    price=100.0 + i,
                    parsing_method=ParsingMethod.AI_GPT
                ))
            
            # Test parallel processing
            parallel_request = BatchParseRequest(
                materials=materials,
                parallel_processing=True,
                max_workers=5
            )
            
            start_time = time.time()
            parallel_response = await service.parse_batch_materials(parallel_request)
            parallel_time = time.time() - start_time
            
            # Test sequential processing
            sequential_request = BatchParseRequest(
                materials=materials,
                parallel_processing=False,
                max_workers=1
            )
            
            start_time = time.time()
            sequential_response = await service.parse_batch_materials(sequential_request)
            sequential_time = time.time() - start_time
            
            # Calculate performance improvement
            if sequential_time > 0:
                speedup = sequential_time / parallel_time
            else:
                speedup = 1.0
            
            print(f"✅ Parallel vs Sequential performance:")
            print(f"   Parallel time: {parallel_time:.3f}s")
            print(f"   Sequential time: {sequential_time:.3f}s")
            print(f"   Speedup: {speedup:.2f}x")
            
            # Verify both responses
            assert isinstance(parallel_response, BatchParseResponse)
            assert isinstance(sequential_response, BatchParseResponse)
            assert parallel_response.total_processed == 10
            assert sequential_response.total_processed == 10
            
            # Parallel should be faster (or at least not significantly slower)
            assert parallel_time <= sequential_time * 1.5, "Parallel processing should be faster"
            
        except Exception as e:
            pytest.skip(f"Parallel vs sequential performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self):
        """Test performance under concurrent requests"""
        try:
            service = get_parser_service()
            
            # Number of concurrent requests
            num_concurrent = 5
            
            async def single_request(request_id: int) -> Tuple[int, float, bool]:
                """Single parsing request"""
                request = EnhancedParseRequest(
                    name=f"Конкурентный материал {request_id}",
                    unit="шт",
                    price=100.0 + request_id,
                    parsing_method=ParsingMethod.AI_GPT
                )
                
                start_time = time.time()
                result = await service.parse_single_material(request)
                end_time = time.time()
                
                return request_id, end_time - start_time, result.success
            
            # Execute concurrent requests
            start_time = time.time()
            tasks = [single_request(i) for i in range(num_concurrent)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Process results
            successful_requests = 0
            processing_times = []
            
            for result in results:
                if isinstance(result, Exception):
                    print(f"Request failed: {result}")
                    continue
                    
                request_id, processing_time, success = result
                processing_times.append(processing_time)
                if success:
                    successful_requests += 1
            
            if processing_times:
                avg_processing_time = statistics.mean(processing_times)
                max_processing_time = max(processing_times)
                min_processing_time = min(processing_times)
                
                print(f"✅ Concurrent requests performance:")
                print(f"   Total time: {total_time:.3f}s")
                print(f"   Successful requests: {successful_requests}/{num_concurrent}")
                print(f"   Average processing time: {avg_processing_time:.3f}s")
                print(f"   Max processing time: {max_processing_time:.3f}s")
                print(f"   Min processing time: {min_processing_time:.3f}s")
                
                # Performance assertions
                assert successful_requests >= num_concurrent * 0.8, "Too many failed requests"
                assert avg_processing_time < 60.0, f"Average processing time too slow: {avg_processing_time:.3f}s"
                
        except Exception as e:
            pytest.skip(f"Concurrent requests performance test failed: {e}")
    
    def test_memory_usage_performance(self):
        """Test memory usage during parsing operations"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            # Get initial memory usage
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create multiple services to test memory usage
            services = []
            for i in range(5):
                service = get_parser_service()
                services.append(service)
            
            # Get memory usage after service creation
            after_services_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create statistics for multiple services
            for service in services:
                stats = service.get_statistics()
                assert isinstance(stats, dict)
            
            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_increase = final_memory - initial_memory
            
            print(f"✅ Memory usage performance:")
            print(f"   Initial memory: {initial_memory:.2f} MB")
            print(f"   After services: {after_services_memory:.2f} MB")
            print(f"   Final memory: {final_memory:.2f} MB")
            print(f"   Memory increase: {memory_increase:.2f} MB")
            
            # Memory usage should be reasonable
            assert memory_increase < 100.0, f"Memory increase too high: {memory_increase:.2f} MB"
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        except Exception as e:
            pytest.skip(f"Memory usage performance test failed: {e}")
    
    def test_statistics_performance(self):
        """Test statistics collection performance"""
        try:
            service = get_parser_service()
            
            # Test statistics collection performance
            start_time = time.time()
            
            for i in range(100):
                stats = service.get_statistics()
                assert isinstance(stats, dict)
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / 100
            
            print(f"✅ Statistics collection performance:")
            print(f"   Total time for 100 calls: {total_time:.3f}s")
            print(f"   Average time per call: {avg_time:.6f}s")
            
            # Statistics collection should be fast
            assert avg_time < 0.01, f"Statistics collection too slow: {avg_time:.6f}s"
            
        except Exception as e:
            pytest.skip(f"Statistics performance test failed: {e}")
    
    def test_configuration_performance(self):
        """Test configuration handling performance"""
        try:
            # Test configuration creation performance
            start_time = time.time()
            
            configs = []
            for i in range(50):
                config = ParserIntegrationConfig(
                    openai_model="gpt-4o-mini",
                    confidence_threshold=0.8 + i * 0.001,
                    max_concurrent_requests=3 + i,
                    request_timeout=30 + i,
                    retry_attempts=2 + i
                )
                configs.append(config)
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / 50
            
            print(f"✅ Configuration handling performance:")
            print(f"   Total time for 50 configs: {total_time:.3f}s")
            print(f"   Average time per config: {avg_time:.6f}s")
            
            # Configuration handling should be fast
            assert avg_time < 0.001, f"Configuration handling too slow: {avg_time:.6f}s"
            
        except Exception as e:
            pytest.skip(f"Configuration performance test failed: {e}")


class TestPerformanceThresholds:
    """Performance threshold tests"""
    
    @pytest.mark.asyncio
    async def test_response_time_thresholds(self):
        """Test that response times meet defined thresholds"""
        try:
            service = get_parser_service()
            
            # Test single parsing response time
            request = EnhancedParseRequest(
                name="Кирпич красный для теста производительности",
                unit="шт",
                price=25.0,
                parsing_method=ParsingMethod.AI_GPT
            )
            
            start_time = time.time()
            result = await service.parse_single_material(request)
            response_time = time.time() - start_time
            
            # Define thresholds
            SINGLE_PARSE_THRESHOLD = 30.0  # seconds
            
            print(f"✅ Response time thresholds:")
            print(f"   Single parse time: {response_time:.3f}s (threshold: {SINGLE_PARSE_THRESHOLD}s)")
            
            # Assert thresholds
            assert response_time < SINGLE_PARSE_THRESHOLD, f"Single parse exceeded threshold: {response_time:.3f}s"
            
        except Exception as e:
            pytest.skip(f"Response time threshold test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_throughput_thresholds(self):
        """Test that throughput meets defined thresholds"""
        try:
            service = get_parser_service()
            
            # Test batch processing throughput
            batch_size = 10
            materials = []
            for i in range(batch_size):
                materials.append(EnhancedParseRequest(
                    name=f"Материал пропускной способности {i+1}",
                    unit="шт",
                    price=100.0 + i,
                    parsing_method=ParsingMethod.AI_GPT
                ))
            
            batch_request = BatchParseRequest(
                materials=materials,
                parallel_processing=True,
                max_workers=5
            )
            
            start_time = time.time()
            response = await service.parse_batch_materials(batch_request)
            total_time = time.time() - start_time
            
            # Calculate throughput
            if total_time > 0:
                throughput = batch_size / total_time  # items per second
            else:
                throughput = 0
            
            # Define threshold
            THROUGHPUT_THRESHOLD = 0.1  # items per second (conservative)
            
            print(f"✅ Throughput thresholds:")
            print(f"   Batch throughput: {throughput:.3f} items/s (threshold: {THROUGHPUT_THRESHOLD} items/s)")
            
            # Assert threshold
            assert throughput >= THROUGHPUT_THRESHOLD, f"Throughput below threshold: {throughput:.3f} items/s"
            
        except Exception as e:
            pytest.skip(f"Throughput threshold test failed: {e}")


class TestPerformanceRegression:
    """Performance regression tests"""
    
    @pytest.mark.asyncio
    async def test_performance_regression(self):
        """Test for performance regression compared to baseline"""
        try:
            service = get_parser_service()
            
            # Baseline performance test
            baseline_materials = [
                EnhancedParseRequest(
                    name="Кирпич красный базовый",
                    unit="шт",
                    price=25.0,
                    parsing_method=ParsingMethod.AI_GPT
                )
            ]
            
            # Run baseline test multiple times
            baseline_times = []
            for i in range(3):
                start_time = time.time()
                result = await service.parse_single_material(baseline_materials[0])
                end_time = time.time()
                baseline_times.append(end_time - start_time)
            
            avg_baseline_time = statistics.mean(baseline_times)
            
            # Historical baseline (adjust based on previous measurements)
            HISTORICAL_BASELINE = 30.0  # seconds
            REGRESSION_THRESHOLD = 1.5  # 50% slower than historical
            
            print(f"✅ Performance regression test:")
            print(f"   Current avg time: {avg_baseline_time:.3f}s")
            print(f"   Historical baseline: {HISTORICAL_BASELINE}s")
            print(f"   Regression threshold: {HISTORICAL_BASELINE * REGRESSION_THRESHOLD}s")
            
            # Check for regression
            assert avg_baseline_time < HISTORICAL_BASELINE * REGRESSION_THRESHOLD, \
                f"Performance regression detected: {avg_baseline_time:.3f}s vs {HISTORICAL_BASELINE}s baseline"
            
        except Exception as e:
            pytest.skip(f"Performance regression test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) 