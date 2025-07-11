# Core Parsers Module

AI-powered parsing system for construction materials and text processing with comprehensive type safety and configuration management.

## 🏗️ Architecture Overview

The Core Parsers Module provides a modern, type-safe architecture for AI-powered parsing operations:

```
core/parsers/
├── interfaces/          # ABC interfaces and type definitions
├── services/           # Parser service implementations  
├── config/             # Configuration managers
└── README.md           # This documentation
```

## 📋 Components

### Interfaces (`interfaces/`)

Type-safe contracts for all parser implementations:

- **`IBaseParser`** - Base interface for all parsers
- **`IAIParser`** - AI-enhanced parser interface  
- **`IMaterialParser`** - Material-specific parsing
- **`ITextParser`** - Text analysis and extraction

### Services (`services/`) 

Parser service implementations:

- **`AIParserService`** - Core AI parsing with OpenAI integration
- **`MaterialParserService`** - Construction materials parsing
- **`BatchParserService`** - Batch processing operations

### Configuration (`config/`)

Configuration managers for parser operations:

- **`ParserConfigManager`** - Parser settings and parameters
- **`SystemPromptsManager`** - AI prompts management
- **`UnitsConfigManager`** - Units and conversions

## 🚀 Quick Start

### Basic Usage

```python
from core.parsers import (
    get_material_parser_service,
    MaterialParseData,
    AIParseRequest
)

# Get parser service
parser = get_material_parser_service()

# Parse material text
request = AIParseRequest(
    input_data="Кирпич красный облицовочный 250x120x65 мм, цена 25 руб/шт",
    options={"enable_embeddings": True}
)

result = await parser.parse_material("Кирпич красный облицовочный 250x120x65 мм")
print(f"Material: {result.data.name}")
print(f"Unit: {result.data.unit}")
print(f"Color: {result.data.color}")
```

### Batch Processing

```python
from core.parsers import get_batch_parser_service, BatchParseRequest

batch_parser = get_batch_parser_service()

materials = [
    "Цемент М400, 50 кг мешок",
    "Песок строительный, 1 тонна", 
    "Кирпич силикатный белый, 1000 шт"
]

requests = [AIParseRequest(input_data=material) for material in materials]
batch_request = BatchParseRequest(
    requests=requests,
    parallel_processing=True,
    max_workers=3
)

results = await batch_parser.parse_batch(batch_request)
print(f"Processed {results.total_processed} items")
print(f"Success rate: {results.success_rate:.1f}%")
```

### Configuration

```python
from core.parsers import get_parser_config_manager

config = get_parser_config_manager()

# Get current configuration
current_config = config.get_config()
print(f"Model: {current_config['models']['openai_model']}")
print(f"Confidence threshold: {current_config['validation']['confidence_threshold']}")

# Update configuration
config.update_config({
    "validation": {
        "confidence_threshold": 0.9,
        "enable_strict_validation": True
    }
})
```

## 🔧 Configuration

### Environment Variables

Key configuration variables (see `env.example` for full list):

```bash
# AI Model Settings
PARSER_MODELS_OPENAI_MODEL=gpt-4o-mini
PARSER_MODELS_EMBEDDING_MODEL=text-embedding-3-small
PARSER_MODELS_TEMPERATURE=0.1

# Performance Settings  
PARSER_PERFORMANCE_BATCH_SIZE=10
PARSER_PERFORMANCE_TIMEOUT=30
PARSER_PERFORMANCE_RETRY_ATTEMPTS=3

# Validation Settings
PARSER_VALIDATION_CONFIDENCE_THRESHOLD=0.85
PARSER_VALIDATION_ENABLE_VALIDATION=true
```

### Configuration Files

Configuration is managed through:

- **`core/config/parsers.py`** - Main parser configuration
- **`core/config/constants.py`** - Parser constants  
- **`core/config/factories.py`** - Client factories

## 🧪 Testing

### Unit Tests

```bash
# Run parser unit tests
pytest tests/unit/parsers/ -v

# Run specific test
pytest tests/unit/parsers/test_ai_parser_service.py -v
```

### Integration Tests

```bash
# Run integration tests (requires API keys)
pytest tests/integration/test_parser_integration.py -v
```

### Performance Tests

```bash
# Run performance benchmarks
pytest tests/performance/test_parser_performance.py -v
```

## 📊 Monitoring & Logging

### Specialized Logging

The parser module includes specialized loggers:

```python
from core.logging.specialized.parsers import get_ai_parser_logger

logger = get_ai_parser_logger()

# Log AI operation
logger.log_ai_request(
    operation_id="parse_001",
    model_name="gpt-4o-mini",
    prompt="Parse this material...",
    temperature=0.1,
    max_tokens=1000
)
```

### Metrics Collection

```python
from core.logging.specialized.parsers import get_ai_parser_metrics

metrics = get_ai_parser_metrics()

# Get performance metrics
stats = metrics.get_ai_metrics()
print(f"Total tokens used: {stats['total_tokens_used']}")
print(f"Average confidence: {stats['average_confidence']:.2f}")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

## 🔍 Health Checks

### Service Health

```python
from core.parsers.services import check_services_health

health = check_services_health()
for service, status in health.items():
    print(f"{service}: {'✅' if status else '❌'}")
```

### Configuration Validation

```python
from core.parsers.config import validate_all_configurations

validation = validate_all_configurations()
for config, valid in validation.items():
    print(f"{config}: {'✅' if valid else '❌'}")
```

## 🔄 Migration Status

Check migration progress:

```python
from core.parsers import get_migration_status, is_migration_complete

print(f"Migration status: {get_migration_status()}")
print(f"Complete: {is_migration_complete()}")
```

## 🏷️ Types & Interfaces

### Core Types

```python
from core.parsers import (
    ParseRequest,      # Generic parse request
    ParseResult,       # Generic parse result  
    AIParseRequest,    # AI-specific request
    AIParseResult,     # AI-specific result
    MaterialParseData, # Material data structure
    TextParseData      # Text data structure
)
```

### Interface Validation

```python
from core.parsers import validate_interface_implementation

# Validate custom parser implementation
is_valid = validate_interface_implementation(MyParser, 'IMaterialParser')
print(f"Implementation valid: {is_valid}")
```

## 🚨 Error Handling

### Common Errors

- **`ImportError`** - Service not available (migration incomplete)
- **`ValueError`** - Invalid configuration or parameters
- **`TimeoutError`** - AI API timeout
- **`ValidationError`** - Pydantic validation failure

### Error Recovery

```python
from core.parsers import get_material_parser_service

try:
    parser = get_material_parser_service()
    result = await parser.parse_material("Invalid input")
except ImportError:
    print("Parser service not available - migration incomplete")
except TimeoutError:
    print("AI API timeout - retry with increased timeout")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 📚 Advanced Usage

### Custom Parser Implementation

```python
from core.parsers.interfaces import IMaterialParser, MaterialParseData

class CustomMaterialParser(IMaterialParser):
    async def parse_material(self, material_text: str) -> AIParseResult[MaterialParseData]:
        # Custom implementation
        pass
    
    async def extract_unit(self, text: str) -> Optional[str]:
        # Custom unit extraction
        pass
```

### Prompt Optimization

```python
from core.parsers import get_system_prompts_manager

prompts = get_system_prompts_manager()

# Get optimized prompt
optimized = await prompts.optimize_prompt(
    base_prompt="Extract material information",
    context={"language": "russian", "domain": "construction"}
)
```

## 🔧 Troubleshooting

### Migration Issues

1. **Import errors**: Check migration status with `get_migration_status()`
2. **Service unavailable**: Ensure migration is complete
3. **Configuration errors**: Validate with `validate_all_configurations()`

### Performance Issues

1. **Slow parsing**: Check batch size and parallel processing
2. **High token usage**: Optimize prompts and temperature
3. **Memory issues**: Monitor metrics and reduce batch sizes

### API Issues

1. **OpenAI errors**: Check API key and quotas
2. **Timeout errors**: Increase timeout settings
3. **Rate limiting**: Implement exponential backoff

## 📄 License

Part of the RAG Construction Materials API project.

---

**Version**: 2.0.0  
**Last Updated**: December 2024  
**Maintainer**: RAG Construction Materials Team 