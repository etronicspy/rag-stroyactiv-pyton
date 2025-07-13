"""Refactored Materials API routes using new multi-database architecture.

Refactored materials API routes with new multi-database architecture.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from datetime import datetime

from core.logging import get_logger
from core.schemas.materials import (
    MaterialCreate, MaterialUpdate, Material, MaterialSearchQuery, 
    MaterialBatchCreate, MaterialBatchResponse, MaterialImportRequest
)
from core.schemas.response_models import ERROR_RESPONSES
from core.database.interfaces import IVectorDatabase
from core.dependencies.database import get_vector_db_dependency, get_ai_client_dependency
from core.database.exceptions import DatabaseError
from services.materials import MaterialsService


logger = get_logger(__name__)
router = APIRouter(
    prefix="",
    tags=["materials"],
    responses=ERROR_RESPONSES
)


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


@router.get(
    "/health",
    summary="🩺 Materials Health – Materials Service Status",
    response_description="Materials service health information"
)
async def health_check(
    service: MaterialsService = Depends(get_materials_service)
):
    """
    🔍 **Materials Service Health Check** - Materials service status verification
    
    Checks the status of the materials service and vector database connectivity.
    Operates in Qdrant-only mode for semantic search of construction materials.
    
    **Features:**
    - 🗄️ Qdrant connection verification
    - 📋 Available endpoints list
    - ⚡ Quick service diagnostics
    - 🎯 Initialization status
    
    **Response Status Codes:**
    - **200 OK**: Service is running normally
    - **206 Partial Content**: Service is running with limitations
    - **503 Service Unavailable**: Service is unavailable
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "service": "MaterialsService",
        "mode": "qdrant-only",
        "service_status": "operational",
        "vector_database": {
            "status": "healthy",
            "database_type": "Qdrant",
            "collections_count": 3,
            "total_vectors": 15420,
            "response_time_ms": 156.3
        },
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
    ```
    
    **Use Cases:**
    - Materials service health verification
    - Vector database diagnostics
    - Endpoints availability monitoring
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


@router.post(
    "/",
    response_model=Material,
    responses=ERROR_RESPONSES,
    summary="➕ Create Material – Create New Material",
    response_description="Created material with embedding"
)
async def create_material(
    material: MaterialCreate,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    ➕ **Create Material** - Create new construction material
    
    Creates a new material with automatic generation of semantic embedding
    for search. Material is saved to vector database for subsequent search.
    
    **Features:**
    - 🧠 Auto-generation of 1536-dimensional embedding (OpenAI)
    - 🔍 Indexing for semantic search
    - ✨ Automatic UUID creation
    - 📝 Required fields validation
    - ⏰ Automatic timestamps
    
    **Required Fields:**
    - `name`: Material name (2-200 characters)
    - `use_category`: Usage category
    - `unit`: Measurement unit
    
    **Optional Fields:**
    - `sku`: Material code/part number (3-50 characters)
    - `description`: Material description
    
    **Request Body Example:**
    ```json
    {
        "name": "Portland Cement M500 D0",
        "use_category": "Cement",
        "unit": "bag",
        "sku": "CEM500-001",
        "description": "High-strength cement for structural concrete without mineral additives"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Portland Cement M500 D0",
        "use_category": "Cement",
        "unit": "bag",
        "sku": "CEM500-001",
        "description": "High-strength cement for structural concrete without mineral additives",
        "embedding": [0.023, -0.156, 0.789, ...], // 1536 dimensions
        "created_at": "2025-06-16T16:46:29.421964Z",
        "updated_at": "2025-06-16T16:46:29.421964Z"
    }
    ```
    
    **Response Status Codes:**
    - **201 Created**: Material successfully created
    - **400 Bad Request**: Data validation error
    - **500 Internal Server Error**: Embedding creation or database error
    
    **Use Cases:**
    - Adding new materials to catalog
    - Importing data from price lists
    - Creating material reference books
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


@router.get(
    "/{material_id}",
    response_model=Material,
    responses=ERROR_RESPONSES,
    summary="🔍 Get Material – Get Material by ID",
    response_description="Material data with embedding"
)
async def get_material(
    material_id: str,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    🔍 **Get Material by ID** - Retrieve material by identifier
    
    Returns complete material information including embedding for analysis.
    Search is performed by UUID in vector database.
    
    **Path Parameters:**
    - `material_id`: Material UUID in UUID4 format
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Portland Cement M500 D0",
        "use_category": "Cement",
        "unit": "bag",
        "sku": "CEM500-001",
        "description": "High-strength cement for structural concrete",
        "embedding": [0.023, -0.156, 0.789, ...], // 1536 dimensions
        "created_at": "2025-06-16T16:46:29.421964Z",
        "updated_at": "2025-06-16T16:46:29.421964Z"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Material found and returned
    - **404 Not Found**: Material with specified ID not found
    - **400 Bad Request**: Invalid UUID format
    - **500 Internal Server Error**: Database operation error
    
    **Use Cases:**
    - Getting complete material information
    - Analyzing embedding for search debugging
    - Checking material existence
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


# 🛈 Deprecated: material-level search endpoint removed. See unified search router.


@router.get(
    "/",
    response_model=List[Material],
    summary="📋 List Materials – List Materials with Pagination",
    response_description="List of materials with filtering support"
)
async def get_materials(
    skip: int = 0, 
    limit: int = 10, 
    category: Optional[str] = None,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    📋 **List Materials** - Get materials list with pagination
    
    Returns a list of all materials with pagination and filtering support.
    Useful for creating catalogs and administrative interfaces.
    
    **Query Parameters:**
    - `skip`: Number of records to skip (offset) - default: 0
    - `limit`: Maximum number of records - default: 10, max: 100
    - `category`: Filter by usage category (optional)
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Portland Cement M500 D0",
            "use_category": "Cement",
            "unit": "bag",
            "sku": "CEM500-001",
            "description": "High-strength cement for structural concrete",
            "embedding": null, // Hidden in list view
            "created_at": "2025-06-16T16:46:29.421964Z",
            "updated_at": "2025-06-16T16:46:29.421964Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: List returned successfully (may be empty)
    - **400 Bad Request**: Invalid pagination parameters
    - **500 Internal Server Error**: Data retrieval error
    
    **Pagination Examples:**
    - `GET /materials/?limit=20` → first 20 materials
    - `GET /materials/?skip=20&limit=20` → materials 21-40
    - `GET /materials/?category=Cement&limit=50` → cements (up to 50 items)
    
    **Use Cases:**
    - Display materials catalog
    - Administrative interfaces
    - Data export
    - Report generation
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


@router.put(
    "/{material_id}",
    response_model=Material,
    summary="✏️ Update Material – Update Material",
    response_description="Updated material"
)
async def update_material(
    material_id: str,
    material: MaterialUpdate,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    ✏️ **Update Material** - Update existing material
    
    Updates material data with recalculation of semantic embedding when critical
    fields (name, description) are changed. Supports partial updates.
    
    **Features:**
    - 🔄 Recalculation of embedding when key fields change
    - 📝 Partial updates (only specified fields)
    - ⏰ Automatic updated_at timestamp update
    - ✅ Validation of changed data
    - 🔍 Material existence verification
    
    **Path Parameters:**
    - `material_id`: Material UUID for update
    
    **Updateable Fields:**
    - `name`: Material name (triggers embedding recalculation)
    - `use_category`: Usage category 
    - `unit`: Measurement unit
    - `sku`: Stock keeping unit/material code
    - `description`: Description (triggers embedding recalculation)
    
    **Request Body Example:**
    ```json
    {
        "name": "Portland Cement M500 D0 (Enhanced)",
        "description": "High-strength cement for structural concrete with improved characteristics",
        "sku": "CEM500-001-V2"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Portland Cement M500 D0 (Enhanced)",
        "use_category": "Cement",
        "unit": "bag",
        "sku": "CEM500-001-V2",
        "description": "High-strength cement for structural concrete with improved characteristics",
        "embedding": [0.021, -0.134, 0.756, ...], // Updated embedding
        "created_at": "2025-06-16T16:46:29.421964Z",
        "updated_at": "2025-06-16T17:30:15.123456Z" // Updated timestamp
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Material successfully updated
    - **404 Not Found**: Material with specified ID not found
    - **400 Bad Request**: Data validation error
    - **500 Internal Server Error**: Update or embedding recalculation error
    
    **Use Cases:**
    - Fixing material data
    - Updating technical specifications
    - Changing categorization
    - Updating SKU codes
    """
    try:
        logger.info(f"Updating material: {material_id}")
        result = await service.update_material(material_id, material)
        if not result:
            logger.warning(f"Material not found for update: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        logger.info(f"Material updated successfully: {material_id}")
        return result
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except DatabaseError as e:
        logger.error(f"Database error updating material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error updating material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{material_id}",
    summary="🗑️ Delete Material – Delete Material",
    response_description="Deletion result"
)
async def delete_material(
    material_id: str,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    🗑️ **Delete Material** - Delete material
    
    Deletes material from vector database by UUID. Operation is irreversible,
    recovery is only possible from backups.
    
    **⚠️ WARNING: Operation is irreversible!**
    
    **Features:**
    - 🔥 Complete removal from vector database
    - 🔍 Existence verification before deletion
    - 📊 Search index updates
    - ⚡ Fast execution
    - 🛡️ Protection against accidental deletion
    
    **Path Parameters:**
    - `material_id`: Material UUID for deletion
    
    **Response Example:**
    ```json
    {
        "success": true,
        "message": "Material deleted successfully",
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Material successfully deleted
    - **404 Not Found**: Material with specified ID not found
    - **400 Bad Request**: Invalid UUID format
    - **500 Internal Server Error**: Database deletion error
    
    **Use Cases:**
    - Removing obsolete materials
    - Cleaning test data
    - Removing duplicates
    - Archiving outdated records
    
    **⚠️ Recommendations:**
    - Create backups before bulk deletion
    - Check dependencies in related systems
    - Use batch operations for multiple deletions
    """
    try:
        logger.info(f"Deleting material: {material_id}")
        success = await service.delete_material(material_id)
        if not success:
            logger.warning(f"Material not found for deletion: {material_id}")
            raise HTTPException(status_code=404, detail="Material not found")
        logger.info(f"Material deleted successfully: {material_id}")
        return {
            "success": True,
            "message": "Material deleted successfully",
            "deleted_id": material_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except DatabaseError as e:
        logger.error(f"Database error deleting material: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error deleting material: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/batch",
    response_model=MaterialBatchResponse,
    summary="📦 Batch Create Materials – Batch Create Materials",
    response_description="Batch material creation results"
)
async def create_materials_batch(
    batch_data: MaterialBatchCreate,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    📦 **Batch Create Materials** - Batch create materials
    
    Creates multiple materials in a single request with optimized processing.
    Supports partial success - some materials may be created successfully.
    
    **Features:**
    - ⚡ Parallel embedding processing
    - 📊 Statistics of successful/failed operations
    - 🔄 Batch processing in vector database
    - 🛡️ Graceful error handling
    - 📈 Progress tracking
    
    **Limits:**
    - **Minimum**: 1 material
    - **Maximum**: 1000 materials per request
    - **Batch size**: 100 materials (configurable)
    - **Timeout**: 5 minutes for entire request
    
    **Request Body Example:**
    ```json
    {
        "materials": [
            {
                "name": "Portland Cement M500",
                "use_category": "Cement",
                "unit": "bag",
                "sku": "CEM500-001",
                "description": "High-strength cement"
            },
            {
                "name": "Ceramic Brick",
                "use_category": "Brick",
                "unit": "piece",
                "sku": "BRICK-001",
                "description": "Solid brick"
            }
        ],
        "batch_size": 100
    }
    ```
    
    **Response Example:**
    ```json
    {
        "success": true,
        "total_processed": 2,
        "successful_materials": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Portland Cement M500",
                "use_category": "Cement",
                "unit": "bag",
                "sku": "CEM500-001",
                "description": "High-strength cement",
                "embedding": [...],
                "created_at": "2025-06-16T17:30:15.123456Z",
                "updated_at": "2025-06-16T17:30:15.123456Z"
            }
        ],
        "failed_materials": [
            {
                "index": 1,
                "material": {...},
                "error": "Duplicate SKU: BRICK-001"
            }
        ],
        "processing_time_seconds": 45.6,
        "successful_count": 1,
        "failed_count": 1,
        "success_rate": 50.0,
        "errors": []
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Batch processed (check success_rate)
    - **400 Bad Request**: Invalid batch data
    - **413 Payload Too Large**: Material limit exceeded
    - **500 Internal Server Error**: Critical processing error
    
    **Use Cases:**
    - Import material catalogs
    - Data migration between systems
    - Bulk creation of test data
    - Synchronization with ERP systems
    """
    try:
        logger.info(f"Processing batch create: {len(batch_data.materials)} materials")
        result = await service.create_materials_batch(batch_data.materials, batch_data.batch_size)
        logger.info(f"Batch create completed: {result.successful_count}/{result.total_processed} successful")
        return result
    except ValueError as e:
        logger.error(f"Invalid batch data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid batch data: {str(e)}")
    except DatabaseError as e:
        logger.error(f"Database error in batch create: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error in batch create: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/import",
    response_model=MaterialBatchResponse,
    summary="📥 Import Materials – Import Materials from JSON/CSV",
    response_description="Material import results"
)
async def import_materials_from_json(
    import_data: MaterialImportRequest,
    service: MaterialsService = Depends(get_materials_service)
):
    """
    📥 **Import Materials from JSON** - Import materials from JSON file
    
    Imports materials from structured JSON format with automatic
    default value filling. Optimized for price list imports.
    
    **Features:**
    - 📄 Simplified import format (only SKU + name)
    - 🔧 Automatic default values
    - 📊 Detailed import statistics
    - 🛡️ Validation and deduplication
    - ⚡ Optimized processing
    
    **Automatic Defaults:**
    - `use_category`: "Construction Materials" (configurable)
    - `unit`: "piece" (configurable)
    - `description`: Generated from name
    - `embedding`: Automatic calculation
    
    **Request Body Example:**
    ```json
    {
        "materials": [
            {
                "sku": "CEM500-001",
                "name": "Portland Cement M500 D0"
            },
            {
                "sku": "BRICK-001", 
                "name": "Ceramic Solid Brick"
            }
        ],
        "default_use_category": "Construction Materials",
        "default_unit": "unit",
        "batch_size": 100
    }
    ```
    
    **Response Example:**
    ```json
    {
        "success": true,
        "total_processed": 2,
        "successful_materials": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Portland Cement M500 D0",
                "use_category": "Construction Materials",
                "unit": "unit",
                "sku": "CEM500-001",
                "description": "Portland Cement M500 D0",
                "embedding": [...],
                "created_at": "2025-06-16T17:30:15.123456Z",
                "updated_at": "2025-06-16T17:30:15.123456Z"
            }
        ],
        "failed_materials": [],
        "processing_time_seconds": 32.1,
        "successful_count": 2,
        "failed_count": 0,
        "success_rate": 100.0,
        "errors": []
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Import completed (check success_rate)
    - **400 Bad Request**: Invalid data format
    - **413 Payload Too Large**: Import limit exceeded
    - **500 Internal Server Error**: Import processing error
    
    **Supported Formats:**
    - Simple JSON with minimal fields
    - Bulk import from suppliers
    - Export/Import between systems
    - Price lists in JSON format
    
    **Use Cases:**
    - Import supplier price lists
    - Migration from old systems
    - Loading material catalogs
    - Synchronization with external APIs
    """
    try:
        logger.info(f"Importing materials from JSON: {len(import_data.materials)} items")
        
        # Convert import format to standard MaterialCreate format
        materials = []
        for item in import_data.materials:
            material = MaterialCreate(
                name=item.name,
                use_category=import_data.default_use_category,
                unit=import_data.default_unit,
                sku=item.sku,
                description=item.name  # Use name as description by default
            )
            materials.append(material)
        
        result = await service.create_materials_batch(materials, import_data.batch_size)
        logger.info(f"JSON import completed: {result.successful_count}/{result.total_processed} successful")
        return result
        
    except ValueError as e:
        logger.error(f"Invalid import data: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid import data: {str(e)}")
    except DatabaseError as e:
        logger.error(f"Database error in import: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error in import: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/upload",
    response_model=MaterialBatchResponse,
    summary="📤 Upload Materials – File-based Material Upload",
    response_description="File processing and material upload results"
)
async def upload_materials(
    file: UploadFile = File(..., description="CSV/Excel file with materials"),
):
    """
    📤 **Upload Materials** - Bulk material upload from file
    
    Uploads and processes files containing construction material data. Supports
    CSV and Excel formats with automatic structure detection and data validation.
    
    **Supported Formats:**
    - 📊 **CSV**: Delimiters (,;|), encodings (UTF-8, Windows-1251)
    - 📋 **Excel**: .xlsx, .xls files with multiple sheets
    - 🔍 **Auto-detection**: Automatic format and structure detection
    
    **Required Fields:**
    - `name`: Material name (1-500 characters)
    - `description`: Material description (optional)
    - `use_category`: Usage category
    - `unit`: Measurement unit
    - `sku`: Stock keeping unit (optional, unique)
    
    **Processing Features:**
    - 🧠 AI-powered data analysis and enrichment
    - 🔍 Automatic category and unit detection
    - 📊 Data validation and cleaning
    - ⚡ Batch processing for large files
    - 🔄 Deduplication by name and SKU
    - 📈 Embedding generation for search
     
    **Request Example:**
    ```bash
    curl -X POST -F "file=@materials.csv" http://localhost:8000/api/v1/materials/upload
    ```
    
    **Response Status Codes:**
    - **200 OK**: File processed successfully (may have warnings)
    - **400 Bad Request**: Unsupported format or empty file
    - **413 Request Entity Too Large**: File size exceeded (50MB)
    - **422 Unprocessable Entity**: Data validation errors
    - **500 Internal Server Error**: File processing error
    
    **File Requirements:**
    - **Size**: Maximum 50MB
    - **Encoding**: UTF-8 (recommended), Windows-1251
    - **Structure**: First row contains column headers
    - **Data**: Minimum 1 data row required
    
    **Processing Statistics:**
    - `total_processed`: Total number of processed records
    - `successful`: Successfully uploaded materials
    - `failed`: Number of errors
    - `duplicates`: Found duplicates
    - `enriched`: AI-enriched records
    
    **Use Cases:**
    - Supplier catalog import
    - Data migration from other systems
    - Bulk material updates
    - ERP system synchronization
    - Initial database population
    """

# Duplicate endpoints, keeping the first definitions. The below endpoints are redundant and will be removed.
# @router.get(
#     "",
#     response_model=List[Material],
#     summary="📋 List Materials – Complete Materials Catalog",
#     response_description="Complete materials list with pagination and filtering"
# )
# async def list_materials(
#     skip: int = Query(0, ge=0, description="Number of records to skip"),
#     limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
#     category: Optional[str] = Query(None, description="Filter by material category"),
#     unit: Optional[str] = Query(None, description="Filter by measurement unit"),
# ):
#     pass # Implementation for this endpoint is already above (get_materials)

# @router.get(
#     "/{material_id}",
#     response_model=Material,
#     summary="🔍 Get Material – Retrieve Material by ID",
#     response_description="Detailed information about specific material"
# )
# async def get_material(material_id: str):
#     pass # Implementation for this endpoint is already above (get_material)

# @router.put(
#     "/{material_id}",
#     response_model=Material,
#     summary="✏️ Update Material – Material Update Operation",
#     response_description="Updated material information"
# )
# async def update_material(
#     material_id: str,
#     material_data: MaterialCreate
# ):
#     pass # Implementation for this endpoint is already above (update_material)

# @router.delete(
#     "/{material_id}",
#     summary="🗑️ Delete Material – Material Deletion Operation",
#     response_description="Material deletion confirmation"
# )
# async def delete_material(material_id: str):
#     pass # Implementation for this endpoint is already above (delete_material)

 