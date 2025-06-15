# Cursor Rules Structure

This directory contains modular rules for the RAG Construction Materials API project, organized by domain and responsibility. **All rules are based on the original `.cursorrules` file content - no additional requirements added**, except for extended testing rules which were preserved by request.

## Rules Files Overview

### 🐍 [python.mdc](./python.mdc)
Python-specific coding standards (from original rules):
- Python 3.9+ requirements
- FastAPI and async/await patterns
- PEP 8, type hints, docstrings
- Pydantic models and validation
- SQLAlchemy 2.0+ async patterns

### 🌐 [api-design.mdc](./api-design.mdc)
API design principles (from original rules):
- REST API versioning (/api/v1/)
- UTF-8 responses and error handling
- CSV/Excel support with required fields
- Fallback strategies for search
- Rate limiting and CORS

### 🗄️ [database.mdc](./database.mdc)
Database architecture (from original rules):
- Repository pattern implementation
- Multi-database support (PostgreSQL, Qdrant, Weaviate, Pinecone, Redis)
- Connection pooling and performance
- Vector database operations
- Database switching and configuration

### 🧪 [testing.mdc](./testing.mdc)
Testing strategies (**original rules + extended testing guidelines**):
- pytest framework and fixtures
- Mocking strategies for external APIs
- Integration vs functional tests
- API availability checks
- **Extended**: Unit testing best practices
- **Extended**: CI/CD integration guidelines
- **Extended**: Performance testing approaches
- **Extended**: Database testing specifics

### 🔒 [security.mdc](./security.mdc)
Security guidelines (from original rules):
- Environment configuration security
- Input validation and sanitization
- Attack prevention basics
- Password and key rotation

### 📊 [monitoring.mdc](./monitoring.mdc)
Monitoring and logging (from original rules):
- Health checks and diagnostics
- Database operation logging
- Debug level configuration
- External API connection logging

### 🏗️ [project-structure.mdc](./project-structure.mdc)
Project organization (from original rules):
- Folder structure (api/routes, core/config, services)
- API versioning requirements
- CSV/Excel support
- Documentation maintenance
- Embedding batching

### 🛠️ [development.mdc](./development.mdc)
Development environment (from original rules):
- .env.local configuration
- API key management
- Connection debugging
- Timeout and retry settings
- Fallback mechanisms

### 📚 [documentation.mdc](./documentation.mdc)
Documentation standards (from original rules):
- Language standards (English code, Russian/English docs)
- Architecture Decision Records (ADR)
- Inline documentation requirements
- Technical reporting guidelines

### ⚙️ [environment.mdc](./environment.mdc)
Configuration management (from original rules):
- .env file management and security
- Configuration change workflow
- Template management (env.example)
- Connection timeout settings

## Usage

These rules are automatically loaded by Cursor IDE and provide context-aware assistance during development. Each file focuses on a specific domain while **maintaining the exact same requirements as the original monolithic `.cursorrules` file**.

## Cleanup Summary

✅ **Removed 80+ new rules** that were not in the original `.cursorrules`  
✅ **Preserved 100% of original rules** from `.cursorrules`  
✅ **Kept extended testing rules** by special request  
✅ **No breaking changes** to existing development practices

## Migration from .cursorrules

This modular structure reorganizes the original `.cursorrules` content without adding new requirements:
- ✅ 100% original rule preservation
- ✅ Better organization by domain
- ✅ No additional constraints (except testing)
- ✅ Same development practices
- ✅ Context-aware IDE assistance

## Principles

- **No new requirements**: Only rules from original `.cursorrules`
- **No breaking changes**: Existing codebase remains compliant
- **Better organization**: Domain-specific rule grouping
- **Maintainable**: Easier to update specific areas
- **Testing exception**: Extended testing rules preserved for development quality

## Contributing

When adding new rules:
1. Choose the appropriate domain file
2. Follow the existing format and style
3. Update this README if adding new files
4. Ensure no duplication across files
5. Test rules with actual development scenarios 