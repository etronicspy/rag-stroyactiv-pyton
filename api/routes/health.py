"""
Comprehensive health check endpoints for RAG Construction Materials API.

Provides detailed health monitoring for all database types, services, and system components.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import httpx
import logging

from core.config import get_settings, DatabaseType, AIProvider, get_vector_db_client
from core.monitoring import get_metrics_collector
from core.monitoring.logger import get_logger
from core.database.factories import DatabaseFactory

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


class HealthChecker:
    """Comprehensive health checking system for all services."""
    
    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self.logger = get_logger("health_checker")
        self._startup_time = time.time()
    
    async def check_basic_health(self) -> Dict[str, Any]:
        """Basic application health check."""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - getattr(self, '_startup_time', time.time())
        }
    
    async def check_vector_database(self) -> Dict[str, Any]:
        """Check vector database health with detailed diagnostics."""
        db_type = settings.DATABASE_TYPE
        health_info = {
            "type": db_type.value,
            "status": "unknown",
            "details": {},
            "response_time_ms": 0,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            if db_type == DatabaseType.QDRANT_CLOUD or db_type == DatabaseType.QDRANT_LOCAL:
                health_info.update(await self._check_qdrant())
            elif db_type == DatabaseType.WEAVIATE:
                health_info.update(await self._check_weaviate())
            elif db_type == DatabaseType.PINECONE:
                health_info.update(await self._check_pinecone())
            else:
                health_info["status"] = "unsupported"
                health_info["error"] = f"Unsupported database type: {db_type.value}"
                
            health_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            
        except Exception as e:
            health_info["status"] = "error"
            health_info["error"] = str(e)
            health_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"Vector database health check failed: {e}", exc_info=True)
        
        return health_info
    
    async def _check_qdrant(self) -> Dict[str, Any]:
        """Check Qdrant health."""
        try:
            # Use adapter health check method
            vector_db = DatabaseFactory.create_vector_database()
            health_result = await vector_db.health_check()
            
            return {
                "status": "healthy" if health_result.get("status") == "healthy" else "error",
                "details": health_result.get("details", {}),
                "error": health_result.get("error")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_weaviate(self) -> Dict[str, Any]:
        """Check Weaviate health."""
        try:
            client = get_vector_db_client()
            
            # Check if client is ready
            is_ready = await asyncio.to_thread(client.is_ready)
            
            if not is_ready:
                return {
                    "status": "unhealthy",
                    "error": "Weaviate client not ready"
                }
            
            # Get schema
            schema = await asyncio.to_thread(client.schema.get)
            
            # Check if Materials class exists
            materials_class = None
            if 'classes' in schema:
                materials_class = next(
                    (cls for cls in schema['classes'] if cls['class'] == 'Materials'),
                    None
                )
            
            return {
                "status": "healthy",
                "details": {
                    "ready": is_ready,
                    "classes_count": len(schema.get('classes', [])),
                    "materials_class_exists": materials_class is not None,
                    "materials_properties": len(materials_class.get('properties', [])) if materials_class else 0
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_pinecone(self) -> Dict[str, Any]:
        """Check Pinecone health."""
        try:
            client = get_vector_db_client()
            
            # List indexes
            indexes = await asyncio.to_thread(client.list_indexes)
            
            # Check if materials index exists
            index_exists = settings.get_vector_db_config()['index_name'] in indexes
            
            index_stats = None
            if index_exists:
                index = client.Index(settings.get_vector_db_config()['index_name'])
                index_stats = await asyncio.to_thread(index.describe_index_stats)
            
            return {
                "status": "healthy",
                "details": {
                    "indexes_count": len(indexes),
                    "index_exists": index_exists,
                    "vector_count": index_stats.total_vector_count if index_stats else 0,
                    "dimension": index_stats.dimension if index_stats else 0
                }
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    async def check_postgresql(self) -> Dict[str, Any]:
        """Check PostgreSQL health."""
        health_info = {
            "type": "postgresql",
            "status": "unknown",
            "details": {},
            "response_time_ms": 0,
            "error": None
        }
        
        if not settings.POSTGRESQL_URL:
            return {
                **health_info,
                "status": "not_configured",
                "error": "PostgreSQL not configured"
            }
        
        start_time = time.time()
        
        try:
            from sqlalchemy import text
            
            # Get database connection
            db_client = DatabaseFactory.create_relational_database()
            
            # Check if it's a mock adapter
            if hasattr(db_client, 'mock_db'):
                health_info.update({
                    "status": "mock",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "details": {
                        "type": "mock_postgresql",
                        "message": "Using mock PostgreSQL adapter (fallback mode)",
                        "connectivity": True,
                        "version": "Mock PostgreSQL v1.0",
                        "tables_count": 0,
                        "materials_count": 0,
                        "required_tables": {
                            "materials": True,
                            "categories": True,
                            "units": True
                        }
                    }
                })
                return health_info
            
            async with db_client() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1 as health_check"))
                health_check = result.scalar()
                
                # Get database info
                version_result = await session.execute(text("SELECT version()"))
                db_version = version_result.scalar()
                
                # Check table existence
                tables_result = await session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in tables_result.fetchall()]
                
                # Get materials count if table exists
                materials_count = 0
                if 'materials' in tables:
                    count_result = await session.execute(text("SELECT COUNT(*) FROM materials"))
                    materials_count = count_result.scalar()
            
            health_info.update({
                "status": "healthy",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "details": {
                    "connectivity": health_check == 1,
                    "version": db_version[:50] + "..." if len(db_version) > 50 else db_version,
                    "tables_count": len(tables),
                    "materials_count": materials_count,
                    "required_tables": {
                        "materials": "materials" in tables,
                        "categories": "categories" in tables,
                        "units": "units" in tables
                    }
                }
            })
            
        except Exception as e:
            health_info.update({
                "status": "error",
                "error": str(e),
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            })
            self.logger.error(f"PostgreSQL health check failed: {e}", exc_info=True)
        
        return health_info
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis health."""
        health_info = {
            "type": "redis",
            "status": "unknown",
            "details": {},
            "response_time_ms": 0,
            "error": None
        }
        
        if not settings.REDIS_URL:
            return {
                **health_info,
                "status": "not_configured",
                "error": "Redis not configured"
            }
        
        start_time = time.time()
        
        try:
            redis_client = DatabaseFactory.create_cache_database()
            
            # Check if it's a mock adapter
            if hasattr(redis_client, 'mock_redis'):
                health_info.update({
                    "status": "mock",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "details": {
                        "type": "mock_redis",
                        "message": "Using mock Redis adapter (fallback mode)",
                        "ping": True,
                        "version": "Mock Redis v1.0",
                        "memory_usage": "1KB",
                        "connected_clients": 1,
                        "operations_per_sec": 0,
                        "keyspace": {},
                        "test_operation": True
                    }
                })
                return health_info
            
            # Test basic connectivity
            ping_result = await redis_client.ping()
            
            # Get Redis info
            info = await redis_client.info()
            
            # Test set/get operation
            test_key = "health_check_test"
            await redis_client.set(test_key, "test_value", ex=60)
            test_value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            health_info.update({
                "status": "healthy",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "details": {
                    "ping": ping_result,
                    "version": info.get('redis_version', 'unknown'),
                    "memory_usage": info.get('used_memory_human', 'unknown'),
                    "connected_clients": info.get('connected_clients', 0),
                    "operations_per_sec": info.get('instantaneous_ops_per_sec', 0),
                    "keyspace": {
                        db: info.get(f'db{db}', {}) 
                        for db in range(16) 
                        if f'db{db}' in info
                    },
                    "test_operation": test_value == "test_value"
                }
            })
            
        except Exception as e:
            health_info.update({
                "status": "error",
                "error": str(e),
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            })
            self.logger.error(f"Redis health check failed: {e}", exc_info=True)
        
        return health_info
    
    async def check_ai_service(self) -> Dict[str, Any]:
        """Check AI service health."""
        ai_provider = settings.AI_PROVIDER
        health_info = {
            "type": ai_provider.value,
            "status": "unknown",
            "details": {},
            "response_time_ms": 0,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            if ai_provider == AIProvider.OPENAI:
                health_info.update(await self._check_openai())
            elif ai_provider == AIProvider.AZURE_OPENAI:
                health_info.update(await self._check_azure_openai())
            elif ai_provider == AIProvider.HUGGINGFACE:
                health_info.update(await self._check_huggingface())
            elif ai_provider == AIProvider.OLLAMA:
                health_info.update(await self._check_ollama())
            else:
                health_info["status"] = "unsupported"
                health_info["error"] = f"Unsupported AI provider: {ai_provider.value}"
                
            health_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            
        except Exception as e:
            health_info.update({
                "status": "error",
                "error": str(e),
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            })
            self.logger.error(f"AI service health check failed: {e}", exc_info=True)
        
        return health_info
    
    async def _check_openai(self) -> Dict[str, Any]:
        """Check OpenAI API health."""
        try:
            async with httpx.AsyncClient() as client:
                ai_config = settings.get_ai_config()
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {ai_config['api_key']}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    models_data = response.json()
                    model_exists = any(
                        model['id'] == ai_config['model'] 
                        for model in models_data.get('data', [])
                    )
                    
                    return {
                        "status": "healthy",
                        "details": {
                            "api_accessible": True,
                            "model": ai_config['model'],
                            "model_exists": model_exists,
                            "available_models_count": len(models_data.get('data', []))
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_azure_openai(self) -> Dict[str, Any]:
        """Check Azure OpenAI health."""
        # Implementation for Azure OpenAI health check
        return {
            "status": "not_implemented",
            "details": {"message": "Azure OpenAI health check not yet implemented"}
        }
    
    async def _check_huggingface(self) -> Dict[str, Any]:
        """Check HuggingFace model health."""
        try:
            # For HuggingFace, we just verify model configuration
            ai_config = settings.get_ai_config()
            
            return {
                "status": "configured",
                "details": {
                    "model": ai_config['model'],
                    "device": ai_config.get('device', 'cpu'),
                    "local_model": True
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_ollama(self) -> Dict[str, Any]:
        """Check Ollama health."""
        # Implementation for Ollama health check
        return {
            "status": "not_implemented",
            "details": {"message": "Ollama health check not yet implemented"}
        }


# Initialize health checker
health_checker = HealthChecker()


@router.get("/")
async def basic_health_check():
    """
    Basic health check endpoint.
    
    Parameters:
    - Returns: Basic service status and uptime information
    """
    return await health_checker.check_basic_health()


@router.get("/detailed")
async def detailed_health_check():
    """
    Comprehensive health check for all services.
    
    Parameters:
    - Returns: Detailed health status of all system components (databases, AI services, metrics)
    """
    start_time = time.time()
    
    # Run all health checks concurrently
    health_checks = await asyncio.gather(
        health_checker.check_basic_health(),
        health_checker.check_vector_database(),
        health_checker.check_postgresql(),
        health_checker.check_redis(),
        health_checker.check_ai_service(),
        return_exceptions=True
    )
    
    basic_health, vector_db, postgresql, redis, ai_service = health_checks
    
    # Collect results
    health_status = {
        "overall_status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "total_check_time_ms": round((time.time() - start_time) * 1000, 2),
        "service_info": basic_health if not isinstance(basic_health, Exception) else {"error": str(basic_health)},
        "databases": {
            "vector_db": vector_db if not isinstance(vector_db, Exception) else {"status": "error", "error": str(vector_db)},
            "postgresql": postgresql if not isinstance(postgresql, Exception) else {"status": "error", "error": str(postgresql)},
            "redis": redis if not isinstance(redis, Exception) else {"status": "error", "error": str(redis)}
        },
        "ai_service": ai_service if not isinstance(ai_service, Exception) else {"status": "error", "error": str(ai_service)},
        "metrics": health_checker.metrics_collector.get_health_metrics()
    }
    
    # Determine overall status
    service_statuses = []
    
    # Check vector database
    if isinstance(vector_db, dict) and vector_db.get('status') in ['error', 'unhealthy']:
        service_statuses.append('unhealthy')
    
    # Check PostgreSQL (optional)
    if isinstance(postgresql, dict) and postgresql.get('status') == 'error':
        service_statuses.append('degraded')
        
    # Check Redis (optional)
    if isinstance(redis, dict) and redis.get('status') == 'error':
        service_statuses.append('degraded')
        
    # Check AI service
    if isinstance(ai_service, dict) and ai_service.get('status') in ['error', 'unhealthy']:
        service_statuses.append('unhealthy')
    
    # Set overall status
    if 'unhealthy' in service_statuses:
        health_status['overall_status'] = 'unhealthy'
    elif 'degraded' in service_statuses:
        health_status['overall_status'] = 'degraded'
    
    return health_status


@router.get("/databases")
async def database_health_check():
    """
    Database-specific health checks.
    
    Parameters:
    - Returns: Health status of all database connections (vector DB, PostgreSQL, Redis)
    """
    checks = await asyncio.gather(
        health_checker.check_vector_database(),
        health_checker.check_postgresql(),
        health_checker.check_redis(),
        return_exceptions=True
    )
    
    vector_db, postgresql, redis = checks
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "databases": {
            "vector_db": vector_db if not isinstance(vector_db, Exception) else {"status": "error", "error": str(vector_db)},
            "postgresql": postgresql if not isinstance(postgresql, Exception) else {"status": "error", "error": str(postgresql)},
            "redis": redis if not isinstance(redis, Exception) else {"status": "error", "error": str(redis)}
        }
    }


 