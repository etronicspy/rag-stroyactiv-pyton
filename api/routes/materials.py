"""Refactored Materials API routes using new multi-database architecture.

Рефакторенные API роуты материалов с новой мульти-БД архитектурой.
"""

from typing import List, Optional
import logging
from fastapi import APIRouter, HTTPException, Depends

from core.schemas.materials import (
    MaterialCreate, MaterialUpdate, Material, MaterialSearchQuery, 
    MaterialBatchCreate, MaterialBatchResponse, MaterialImportRequest
)
from core.database.interfaces import IVectorDatabase
from core.dependencies.database import get_vector_db_dependency, get_ai_client_dependency
from core.database.exceptions import DatabaseError, ConnectionError, QueryError
from services.materials import MaterialsService


logger = logging.getLogger(__name__)
router = APIRouter()


def get_materials_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
) -> MaterialsService:
    """Get MaterialsService with dependency injection (Qdrant-only mode).
    
    Args:
        vector_db: Vector database client (injected)
        ai_client: AI client for embeddings (injected)
        
    Returns:
        Configured MaterialsService instance
    """
    try:
        return MaterialsService(vector_db=vector_db, ai_client=ai_client)
    except Exception as e:
        logger.error(f"Failed to initialize MaterialsService: {e}")
        # For now, return None to trigger fallback behavior
        return None


@router.get("/health")
async def health_check(
    service: MaterialsService = Depends(get_materials_service)
):
    """Check health of materials service and database connections (Qdrant-only mode).
    
    Args:
        service: Materials service (injected, optional)
        
    Returns:
        Health status information with Qdrant connection status
    """
    health_status = {
        "status": "healthy",
        "service": "MaterialsService",
        "mode": "qdrant-only",
        "available_endpoints": {
            "search": "POST /api/v1/materials/search",
            "batch": "POST /api/v1/materials/batch", 
            "import": "POST /api/v1/materials/import",
            "list": "GET /api/v1/materials/",
            "get_by_id": "GET /api/v1/materials/{id}",
            "create": "POST /api/v1/materials/",
            "update": "PUT /api/v1/materials/{id}",
            "delete": "DELETE /api/v1/materials/{id}"
        }
    }
    
    # Try to check service health
    if service is None:
        health_status.update({
            "status": "degraded",
            "service_status": "initialization_failed",
            "message": "MaterialsService failed to initialize, running in fallback mode"
        })
    else:
        try:
            # Try to check vector database health
            vector_health = await service.vector_db.health_check()
            health_status.update({
                "vector_database": vector_health,
                "service_status": "operational"
            })
        except Exception as e:
            health_status.update({
                "status": "degraded",
                "service_status": "vector_db_error",
                "vector_db_error": str(e),
                "message": "Vector database connection issues detected"
            })
    
    return health_status


@router.post("/", response_model=Material)
async def create_material(
    material: MaterialCreate,
    service: MaterialsService = Depends(get_materials_service)
):
    """Create a new material with semantic embedding.
    
    Args:
        material: Material data to create
        service: Materials service (injected)
        
    Returns:
        Created material with ID and embedding
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(f"Creating material: {material.name}")
        result = await service.create_material(material)
        logger.info(f"Material created successfully: {result.id}")
        return result
    except DatabaseError as e:
        logger.error(f"Database error creating material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error creating material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{material_id}", response_model=Material)
async def get_material(
    material_id: str,
    service: MaterialsService = Depends(get_materials_service)
):
    """Get a specific material by ID.
    
    Args:
        material_id: Material identifier
        service: Materials service (injected)
        
    Returns:
        Material if found
        
    Raises:
        HTTPException: If material not found or retrieval fails
    """
    try:
        logger.debug(f"Getting material: {material_id}")
        material = await service.get_material(material_id)
        if not material:
            logger.warning(f"Material not found: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        return material
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except DatabaseError as e:
        logger.error(f"Database error getting material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error getting material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/search", response_model=List[Material])
async def search_materials(
    query: MaterialSearchQuery,
    service: MaterialsService = Depends(get_materials_service)
):
    """Search materials using semantic search with fallback (Qdrant-only mode).
    
    Implements fallback strategy: vector search → SQL LIKE search if 0 results
    
    Args:
        query: Search query parameters
        service: Materials service (injected)
        
    Returns:
        List of matching materials or fallback mock response
        
    Raises:
        HTTPException: If search fails critically
    """
    try:
        # Check if service initialization failed
        if service is None:
            logger.warning("MaterialsService initialization failed, returning mock response")
            return [{
                "id": "fallback-1",
                "name": f"Fallback result for '{query.query}'",
                "sku": "FB-001",
                "description": f"Fallback search result for query: {query.query} (service unavailable)",
                "use_category": "Fallback",
                "unit": "шт",
                "embedding": None,
                "created_at": None,
                "updated_at": None
            }]
        
        logger.info(f"Searching materials: '{query.query}' (limit: {query.limit})")
        results = await service.search_materials(query.query, query.limit)
        logger.info(f"Search returned {len(results)} results")
        return results
        
    except DatabaseError as e:
        logger.error(f"Database error searching materials: {e}")
        # Return fallback instead of HTTP error
        return [{
            "id": "error-fallback-1",
            "name": f"Search temporarily unavailable for '{query.query}'",
            "sku": "ERR-001", 
            "description": f"Database error occurred, please try again later",
            "use_category": "System",
            "unit": "шт",
            "embedding": None,
            "created_at": None,
            "updated_at": None
        }]
    except Exception as e:
        logger.error(f"Unexpected error searching materials: {e}")
        # Return fallback instead of HTTP error for better UX
        return [{
            "id": "exception-fallback-1",
            "name": f"Search error for '{query.query}'",
            "sku": "EXC-001",
            "description": f"An error occurred during search, please try again",
            "use_category": "System", 
            "unit": "шт",
            "embedding": None,
            "created_at": None,
            "updated_at": None
        }]


@router.get("/", response_model=List[Material])
async def get_materials(
    skip: int = 0, 
    limit: int = 10, 
    category: Optional[str] = None,
    service: MaterialsService = Depends(get_materials_service)
):
    """Get all materials with optional filtering.
    
    Args:
        skip: Number of materials to skip
        limit: Maximum number of materials to return
        category: Optional category filter
        service: Materials service (injected)
        
    Returns:
        List of materials
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.debug(f"Getting materials: skip={skip}, limit={limit}, category={category}")
        results = await service.get_materials(skip=skip, limit=limit, category=category)
        logger.info(f"Retrieved {len(results)} materials")
        return results
    except DatabaseError as e:
        logger.error(f"Database error getting materials: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error getting materials: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{material_id}", response_model=Material)
async def update_material(
    material_id: str,
    material: MaterialUpdate,
    service: MaterialsService = Depends(get_materials_service)
):
    """Update a material with new semantic embedding.
    
    Args:
        material_id: Material identifier
        material: Updated material data
        service: Materials service (injected)
        
    Returns:
        Updated material
        
    Raises:
        HTTPException: If material not found or update fails
    """
    try:
        logger.info(f"Updating material: {material_id}")
        updated = await service.update_material(material_id, material)
        if not updated:
            logger.warning(f"Material not found for update: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        logger.info(f"Material updated successfully: {material_id}")
        return updated
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except DatabaseError as e:
        logger.error(f"Database error updating material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error updating material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    service: MaterialsService = Depends(get_materials_service)
):
    """Delete a material.
    
    Args:
        material_id: Material identifier
        service: Materials service (injected)
        
    Returns:
        Success status
        
    Raises:
        HTTPException: If material not found or deletion fails
    """
    try:
        logger.info(f"Deleting material: {material_id}")
        success = await service.delete_material(material_id)
        if not success:
            logger.warning(f"Material not found for deletion: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        logger.info(f"Material deleted successfully: {material_id}")
        return {"success": success}
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except DatabaseError as e:
        logger.error(f"Database error deleting material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error deleting material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=MaterialBatchResponse)
async def create_materials_batch(
    batch_data: MaterialBatchCreate,
    service: MaterialsService = Depends(get_materials_service)
):
    """Batch create materials with optimized performance (Qdrant-only mode).
    
    Args:
        batch_data: Batch creation parameters
        service: Materials service (injected)
        
    Returns:
        Batch operation results or fallback response
        
    Raises:
        HTTPException: If batch creation fails critically
    """
    try:
        # Check if service initialization failed
        if service is None:
            logger.warning("MaterialsService initialization failed, returning fallback response")
            return MaterialBatchResponse(
                success=False,
                total_processed=len(batch_data.materials),
                successful_materials=[],
                failed_materials=[{"error": "Service unavailable", "material": mat.dict()} for mat in batch_data.materials],
                processing_time_seconds=0.001,
                errors=["MaterialsService initialization failed"]
            )
        
        logger.info(f"Starting batch creation of {len(batch_data.materials)} materials")
        result = await service.create_materials_batch(
            batch_data.materials, 
            batch_data.batch_size
        )
        logger.info(f"Batch creation completed: {result.successful_count} success, {result.failed_count} failed")
        return result
        
    except DatabaseError as e:
        logger.error(f"Database error in batch creation: {e}")
        return MaterialBatchResponse(
            success=False,
            total_processed=len(batch_data.materials),
            successful_materials=[],
            failed_materials=[{"error": f"Database error: {e.message}", "material": mat.dict()} for mat in batch_data.materials],
            processing_time_seconds=0.001,
            errors=[f"Database error: {e.message}"]
        )
    except Exception as e:
        logger.error(f"Unexpected error in batch creation: {e}")
        return MaterialBatchResponse(
            success=False,
            total_processed=len(batch_data.materials),
            successful_materials=[],
            failed_materials=[{"error": f"Unexpected error: {str(e)}", "material": mat.dict()} for mat in batch_data.materials],
            processing_time_seconds=0.001,
            errors=[f"Batch creation failed: {str(e)}"]
        )


@router.post("/import", response_model=MaterialBatchResponse)
async def import_materials_from_json(
    import_data: MaterialImportRequest,
    service: MaterialsService = Depends(get_materials_service)
):
    """Import materials from JSON format (sku + name) - Qdrant-only mode.
    
    Args:
        import_data: Import parameters
        service: Materials service (injected)
        
    Returns:
        Import operation results or fallback response
        
    Raises:
        HTTPException: If import fails critically
    """
    try:
        # Check if service initialization failed
        if service is None:
            logger.warning("MaterialsService initialization failed, returning fallback response")
            return MaterialBatchResponse(
                success=False,
                total_processed=len(import_data.materials),
                successful_materials=[],
                failed_materials=[{"error": "Service unavailable", "material": mat.dict()} for mat in import_data.materials],
                processing_time_seconds=0.001,
                errors=["MaterialsService initialization failed"]
            )
        
        logger.info(f"Starting import of {len(import_data.materials)} materials")
        result = await service.import_materials_from_json(
            import_data.materials,
            import_data.default_use_category,
            import_data.default_unit,
            import_data.batch_size
        )
        logger.info(f"Import completed: {result.successful_count} success, {result.failed_count} failed")
        return result
        
    except DatabaseError as e:
        logger.error(f"Database error in import: {e}")
        return MaterialBatchResponse(
            success=False,
            total_processed=len(import_data.materials),
            successful_materials=[],
            failed_materials=[{"error": f"Database error: {e.message}", "material": mat.dict()} for mat in import_data.materials],
            processing_time_seconds=0.001,
            errors=[f"Database error: {e.message}"]
        )
    except Exception as e:
        logger.error(f"Unexpected error in import: {e}")
        return MaterialBatchResponse(
            success=False,
            total_processed=len(import_data.materials),
            successful_materials=[],
            failed_materials=[{"error": f"Unexpected error: {str(e)}", "material": mat.dict()} for mat in import_data.materials],
            processing_time_seconds=0.001,
            errors=[f"Import failed: {str(e)}"]
        )

 