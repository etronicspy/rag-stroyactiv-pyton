# 🧪 Unified Logging System Tests

Comprehensive test suite for the unified logging system covering all stages of implementation (0-5).

## 📁 Test Structure

```
tests/
├── unit/
│   └── test_unified_logging.py              # Unit tests for all stages
├── integration/
│   └── test_unified_logging_integration.py  # Integration tests
├── performance/
│   └── test_unified_logging_performance.py  # Performance tests
├── functional/
│   └── test_unified_logging_workflows.py    # End-to-end workflow tests
└── test_unified_logging_suite.py            # Comprehensive test runner
```

## 🚀 Quick Start

### Run All Tests
```bash
# Full test suite (includes performance tests)
python tests/test_unified_logging_suite.py

# Quick mode (skip performance tests)
python tests/test_unified_logging_suite.py --quick

# Verbose output
python tests/test_unified_logging_suite.py --verbose
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/test_unified_logging.py -v

# Integration tests only  
pytest tests/integration/test_unified_logging_integration.py -v

# Performance tests only
pytest tests/performance/test_unified_logging_performance.py -v

# Functional tests only
pytest tests/functional/test_unified_logging_workflows.py -v
```

### Run Tests by Stage
```bash
# Stage 0: Critical duplication elimination
python tests/test_unified_logging_suite.py --stage 0

# Stage 1: Mass migration tests
python tests/test_unified_logging_suite.py --stage 1

# Stage 2: UnifiedLoggingManager tests
python tests/test_unified_logging_suite.py --stage 2

# Stage 3: Correlation ID system tests
python tests/test_unified_logging_suite.py --stage 3

# Stage 4: Performance optimization tests
python tests/test_unified_logging_suite.py --stage 4

# Stage 5: Metrics integration tests
python tests/test_unified_logging_suite.py --stage 5
```

## 📊 Test Categories

### 🔬 Unit Tests (`tests/unit/test_unified_logging.py`)

**Purpose**: Test individual components in isolation with mocks.

**Coverage**:
- **Stage 0**: Critical duplication elimination
  - BaseLoggingHandler elimination
  - Single LoggingMiddleware validation
  - Unified logging configuration
  
- **Stage 1**: Mass migration validation
  - get_logger function availability
  - Logger naming conventions
  - Structured logging support
  
- **Stage 2**: UnifiedLoggingManager
  - Manager creation and components
  - Database operation logging
  - HTTP request logging
  
- **Stage 3**: Correlation ID system
  - Basic context functionality
  - Context manager behavior
  - Context nesting support

**Run Time**: ~30 seconds
**Dependencies**: Mock objects only

### 🔗 Integration Tests (`tests/integration/test_unified_logging_integration.py`)

**Purpose**: Test component interactions and integrations.

**Coverage**:
- Middleware integration with unified logging
- Service layer integration with correlation ID
- Database operations with automatic logging
- End-to-end request tracing
- System health integration

**Run Time**: ~60 seconds  
**Dependencies**: Real application components

### 🚀 Performance Tests (`tests/performance/test_unified_logging_performance.py`)

**Purpose**: Validate performance characteristics and optimizations.

**Coverage**:
- Logger caching performance (Stage 4)
- Correlation ID optimization
- Concurrent logging performance
- Memory usage patterns
- Latency measurements

**Run Time**: ~120 seconds
**Dependencies**: psutil, real system resources

### 🔄 Functional Tests (`tests/functional/test_unified_logging_workflows.py`)

**Purpose**: Test complete user workflows and business scenarios.

**Coverage**:
- Material management workflows
- API endpoint logging workflows  
- Error handling workflows
- Health monitoring workflows
- Production-like scenarios

**Run Time**: ~90 seconds
**Dependencies**: FastAPI TestClient, full application stack

## 🎯 Test Markers

Use pytest markers to run specific test types:

```bash
# Run only correlation ID tests
pytest -m correlation_id

# Run only performance tests
pytest -m logging_performance

# Run only unified logging tests
pytest -m unified_logging

# Exclude slow tests
pytest -m "not slow"
```

## 📈 Expected Results

### ✅ Success Criteria

**Unit Tests**: 100% pass rate
- All stages (0-3) should pass completely
- No import errors or missing components
- All mocked interactions work correctly

**Integration Tests**: ≥95% pass rate
- Component integrations work seamlessly
- Correlation ID propagates correctly
- Database operations log automatically

**Performance Tests**: ≥90% pass rate
- Logger caching shows improvement
- Correlation context handles 10K+ ops/second
- Concurrent logging supports multiple threads
- Memory usage remains stable

**Functional Tests**: ≥85% pass rate
- End-to-end workflows complete successfully
- Error handling works gracefully
- Health monitoring responds correctly

### 📊 Performance Benchmarks

**Logger Caching**: 
- Expected: 50%+ performance improvement
- Target: 1000+ logger requests in <1 second

**Correlation Context**:
- Expected: 10,000+ operations/second
- Target: <1ms average latency

**Concurrent Logging**:
- Expected: 1000+ operations/second overall
- Target: 10+ operations/second per thread

**Memory Usage**:
- Expected: <100MB growth for extended operations
- Target: Stable memory usage over time

## 🔧 Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure you're in the project root
cd /path/to/rag-stroyactiv-pyton

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

**Test Failures**:
```bash
# Run with verbose output for debugging
pytest tests/unit/test_unified_logging.py -v -s

# Run specific test
pytest tests/unit/test_unified_logging.py::TestUnifiedLoggingSystemStage0::test_base_logging_handler_eliminated -v
```

**Performance Test Issues**:
```bash
# Skip performance tests if system is under load
python tests/test_unified_logging_suite.py --quick

# Run performance tests with more lenient thresholds
pytest tests/performance/test_unified_logging_performance.py -v --tb=short
```

### Environment Requirements

**Python**: 3.9+
**Memory**: 4GB+ recommended for performance tests
**CPU**: Multi-core recommended for concurrent tests
**Dependencies**: All packages from requirements-dev.txt

## 📋 Test Maintenance

### Adding New Tests

1. **Unit Tests**: Add to appropriate stage class in `test_unified_logging.py`
2. **Integration Tests**: Add to relevant category in `test_unified_logging_integration.py`
3. **Performance Tests**: Add to appropriate performance class
4. **Functional Tests**: Add to relevant workflow class

### Updating Benchmarks

Performance benchmarks should be updated when:
- Hardware changes significantly
- Major optimizations are implemented
- System requirements change

### Test Data

Tests use:
- **Mock data**: For unit and integration tests
- **Generated data**: For performance tests
- **Real API responses**: For functional tests (when available)

## 🎉 Success Indicators

When all tests pass:

```
🎉 ALL TESTS PASSED! Unified Logging System is ready for production!

📊 UNIFIED LOGGING SYSTEM TEST SUITE SUMMARY
================================================================================
📈 Overall Results:
   Total Categories: 4
   ✅ Passed: 4
   ❌ Failed: 0
   ⏭️  Skipped: 0
   💥 Crashed: 0
   ⏱️  Total Duration: X.XXs

🎯 Success Rate: 100.0%
```

This indicates that:
- ✅ All stages (0-5) are fully implemented and working
- ✅ Performance optimizations are effective
- ✅ System is production-ready
- ✅ Full traceability with correlation IDs
- ✅ Comprehensive error handling
- ✅ Metrics integration is functional

## 📞 Support

For test-related issues:
1. Check this README for common solutions
2. Review test output for specific error messages  
3. Run individual test categories to isolate issues
4. Use `--verbose` flag for detailed debugging information

---

**Last Updated**: 2024
**Maintained By**: AI Assistant
**Test Coverage**: Stages 0-5 of Unified Logging System Implementation 