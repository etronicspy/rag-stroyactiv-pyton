"""
English API Documentation Configuration for RAG Construction Materials API
========================================================================

This module contains comprehensive English descriptions, summaries, and examples
for all API endpoints in the Swagger UI documentation.
"""

from typing import List, Dict, Any


def get_api_description() -> str:
    """
    Get comprehensive English API description for FastAPI documentation.
    
    Returns:
        API description string with Markdown formatting
    """
    return """
# 🏗️ RAG Construction Materials API

**AI-Powered Semantic Search & Management System for Construction Materials**

## 🚀 Overview

The RAG Construction Materials API is a comprehensive system for managing and searching construction materials using advanced AI-powered semantic search capabilities. Built with FastAPI and vector databases, it provides intelligent material discovery and catalog management for the construction industry.

## ✨ Key Features

### 🧠 AI-Powered Search
- **Semantic Search**: Find materials using natural language queries
- **Vector Embeddings**: 1536-dimensional OpenAI embeddings for precise matching
- **Hybrid Search**: Combines vector, SQL, and fuzzy search algorithms
- **Auto-complete**: Smart suggestions and search recommendations

### 📊 Multi-Database Architecture
- **Vector Databases**: Qdrant, Weaviate, Pinecone support
- **Relational Database**: PostgreSQL for structured data
- **Caching Layer**: Redis for high-performance caching
- **Fallback Strategies**: Graceful degradation when services unavailable

### 📁 Bulk Operations
- **CSV/Excel Import**: Process supplier price lists automatically
- **Batch Processing**: Handle 1000+ materials per operation
- **Data Validation**: Comprehensive input validation and error reporting
- **Progress Tracking**: Real-time processing status updates

### 🔍 Advanced Search Capabilities
- **Category Filtering**: Filter by material types and categories
- **Unit Filtering**: Search by measurement units (kg, m³, pieces)
- **Fuzzy Matching**: Handle typos and approximate matches
- **Performance Analytics**: Detailed search metrics and timing

### 📈 Production-Ready Features
- **Rate Limiting**: Prevent API abuse and ensure fair usage
- **Health Monitoring**: Comprehensive system health checks
- **SSH Tunneling**: Secure database connections
- **Error Handling**: Detailed error responses with troubleshooting info

## 🏗️ Architecture

### Vector Search Engine
- **Embedding Model**: OpenAI text-embedding-ada-002
- **Vector Dimensions**: 1536-dimensional embeddings
- **Similarity Search**: Cosine similarity for semantic matching
- **Index Management**: Automatic vector indexing and updates

### Database Layer
- **Primary Storage**: Vector database for semantic search
- **Metadata Storage**: PostgreSQL for relational data
- **Cache Layer**: Redis for frequently accessed data
- **Connection Pooling**: Optimized database connections

### Search Algorithms
1. **Vector Search**: Best for semantic similarity and concept matching
2. **SQL Search**: Perfect for exact matches and specific codes
3. **Fuzzy Search**: Handles typos and approximate matches
4. **Hybrid Search**: Combines all methods for maximum coverage

## 📚 API Structure

### 🔍 Search & Discovery (`/search`)
- **Basic Search**: Simple material search with semantic matching
- **Advanced Search**: Complex queries with filters and analytics
- **Suggestions**: Auto-complete and search recommendations
- **Categories & Units**: Available filter options

### 📦 Material Management (`/materials`)
- **CRUD Operations**: Create, read, update, delete materials
- **Batch Operations**: Bulk import and processing
- **Search Materials**: Find materials in catalog
- **Import from JSON**: Simplified import format

### 💰 Price Management (`/prices`)
- **Process Price Lists**: Import CSV/Excel files from suppliers
- **Historical Data**: Track price changes over time
- **Supplier Management**: Organize data by suppliers
- **Product Status**: Track processing status

### 📚 Reference Data (`/reference`)
- **Categories**: Manage material categories
- **Units**: Manage measurement units
- **Standardization**: Maintain consistent taxonomy

### 🩺 Health & Monitoring (`/health`)
- **System Health**: Monitor all components
- **Database Status**: Check database connectivity
- **Performance Metrics**: Track API performance
- **Diagnostic Tools**: Troubleshoot issues

### 🔌 SSH Tunnel (`/tunnel`)
- **Tunnel Management**: Control SSH tunnel connections
- **Status Monitoring**: Check tunnel health
- **Configuration**: View tunnel settings

## 🚀 Quick Start Examples

### Search for Materials
```bash
# Basic semantic search
curl -X GET "https://api.example.com/api/v1/search?q=high%20strength%20cement&limit=10"

# Advanced search with filters
curl -X POST "https://api.example.com/api/v1/search/advanced" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "waterproof membrane for foundation",
    "search_type": "hybrid",
    "categories": ["Waterproofing", "Membranes"],
    "limit": 20
  }'
```

### Material Management
```bash
# Create a new material
curl -X POST "https://api.example.com/api/v1/materials/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Portland Cement M500",
    "use_category": "Cement",
    "unit": "bag",
    "sku": "CEM500-001",
    "description": "High-strength cement for structural concrete"
  }'

# Batch import materials
curl -X POST "https://api.example.com/api/v1/materials/batch" \\
  -H "Content-Type: application/json" \\
  -d '{
    "materials": [
      {
        "name": "Steel Rebar 12mm",
        "use_category": "Steel",
        "unit": "meter",
        "description": "Reinforcement steel bar"
      }
    ]
  }'
```

### Price List Processing
```bash
# Upload supplier price list
curl -X POST "https://api.example.com/api/v1/prices/process" \\
  -F "file=@supplier_prices.csv" \\
  -F "supplier_id=supplier_001"
```

## 📊 Response Format

All API responses follow a consistent format:

### Success Responses (2xx)
```json
{
  "data": { /* Response payload */ },
  "status": "success",
  "timestamp": "2025-06-16T16:46:29.421964Z"
}
```

### Error Responses (4xx, 5xx)
```json
{
  "code": 400,
  "message": "Invalid request data",
  "details": {
    "field": "name",
    "error": "must not be empty"
  },
  "timestamp": "2025-06-16T16:46:29.421964Z"
}
```

## 🔒 Security & Rate Limiting

- **Rate Limits**: 1000 requests per hour per IP
- **Input Validation**: Comprehensive data validation
- **File Upload**: 50MB maximum file size
- **CORS**: Configured for production environments
- **Error Handling**: Secure error messages without sensitive data

## 📈 Performance Metrics

- **Search Response Time**: < 300ms average
- **Bulk Operations**: 1000+ materials per batch
- **Uptime**: 99.9% availability target
- **Throughput**: 100+ requests per second
- **Cache Hit Rate**: > 80% for frequent queries

## 🛠️ Integration Guide

### For Construction Management Systems
- Use `/search` endpoints for material discovery
- Implement `/materials/batch` for catalog synchronization
- Monitor system health with `/health` endpoints

### For E-commerce Platforms
- Integrate semantic search for product discovery
- Use price management for supplier catalogs
- Implement auto-complete with suggestions API

### For Mobile Applications
- Optimize queries with appropriate limits
- Use caching for frequently accessed data
- Implement offline fallback strategies

### For Data Analytics
- Export data using list endpoints with pagination
- Track search patterns and popular materials
- Monitor performance metrics

## 📞 Support & Documentation

- **Interactive Documentation**: Available at `/docs`
- **Alternative Documentation**: Available at `/redoc`
- **OpenAPI Schema**: Available at `/openapi.json`
- **API Support**: Contact support@example.com

---

**Version**: 1.0.0 | **Environment**: Production | **Last Updated**: 2025-06-16
    """


def get_contact_info() -> Dict[str, str]:
    """
    Get API contact information.
    
    Returns:
        Contact information dictionary
    """
    return {
        "name": "RAG Construction Materials API Support",
        "url": "https://github.com/your-repo/rag-construction-materials",
        "email": "support@example.com"
    }


def get_license_info() -> Dict[str, str]:
    """
    Get API license information.
    
    Returns:
        License information dictionary
    """
    return {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }


def get_servers_config() -> List[Dict[str, str]]:
    """
    Get API servers configuration.
    
    Returns:
        List of server configurations
    """
    return [
        {
            "url": "http://localhost:8000",
            "description": "🔧 Development server - Local development environment"
        },
        {
            "url": "https://api-staging.construction-materials.com",
            "description": "🧪 Staging server - Testing environment"
        },
        {
            "url": "https://api.construction-materials.com",
            "description": "🚀 Production server - Live environment"
        }
    ]


def get_tags_metadata() -> List[Dict[str, str]]:
    """
    Get API tags metadata for English documentation.
    
    Returns:
        List of tag metadata dictionaries
    """
    return [
        {
            "name": "search",
            "description": "🔍 **Material Search & Discovery** - AI-powered semantic search for construction materials with natural language processing"
        },
        {
            "name": "materials", 
            "description": "📦 **Material Management** - Complete CRUD operations for construction materials catalog with batch processing and validation"
        },
        {
            "name": "prices",
            "description": "💰 **Price Management** - Import and process supplier price lists from CSV/Excel files with comprehensive analytics"
        },
        {
            "name": "reference",
            "description": "📚 **Reference Data** - Manage categories, units, and other reference information for material classification"
        },
        {
            "name": "advanced-search",
            "description": "🚀 **Advanced Search** - Complex search operations with filters, algorithm selection, and detailed analytics"
        },
        {
            "name": "health",
            "description": "🩺 **Health & Monitoring** - Comprehensive system health checks, database monitoring, and performance metrics"
        },
        {
            "name": "tunnel",
            "description": "🔌 **SSH Tunnel Management** - Secure database connection management with status monitoring and configuration"
        }
    ]


def get_fastapi_config(settings) -> Dict[str, Any]:
    """
    Get complete FastAPI configuration with English documentation.
    
    Args:
        settings: Application settings
        
    Returns:
        FastAPI configuration dictionary
    """
    return {
        "title": "RAG Construction Materials API",
        "version": "1.0.0",
        "description": get_api_description(),
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/api/v1/openapi.json",
        "contact": get_contact_info(),
        "license_info": get_license_info(),
        "servers": get_servers_config(),
        "tags_metadata": get_tags_metadata(),
        "openapi_tags": get_tags_metadata()
    }


# Standard Error Responses for English Documentation
ERROR_RESPONSES = {
    "400": {
        "description": "Bad Request - Invalid input data or malformed request",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "code": 400,
                    "message": "Invalid request data",
                    "details": {"field": "name", "error": "must not be empty"}
                }
            }
        }
    },
    "404": {
        "description": "Resource Not Found - The requested resource does not exist",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "code": 404,
                    "message": "Material not found",
                    "details": {"resource_id": "550e8400-e29b-41d4-a716-446655440000"}
                }
            }
        }
    },
    "422": {
        "description": "Validation Error - Request data failed validation",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/HTTPValidationError"},
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "name"],
                            "msg": "ensure this value has at least 2 characters",
                            "type": "value_error.any_str.min_length"
                        }
                    ]
                }
            }
        }
    },
    "429": {
        "description": "Too Many Requests - Rate limit exceeded",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "code": 429,
                    "message": "Rate limit exceeded",
                    "details": {"retry_after": 60, "limit": "1000 requests per hour"}
                }
            }
        }
    },
    "500": {
        "description": "Internal Server Error - Unexpected server error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                "example": {
                    "code": 500,
                    "message": "Internal server error",
                    "details": {"error_id": "err_123456", "support": "Contact support@example.com"}
                }
            }
        }
    }
} 