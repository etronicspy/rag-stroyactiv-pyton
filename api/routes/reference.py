from typing import List

from fastapi import APIRouter, Depends

from core.database.interfaces import IVectorDatabase
from core.dependencies.database import (
    get_ai_client_dependency,
    get_vector_db_dependency,
)
from core.schemas.colors import ColorCreate, ColorReference, ColorUpdate
from core.schemas.materials import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    Unit,
    UnitCreate,
    UnitUpdate,
)
from core.schemas.response_models import ERROR_RESPONSES
from services.materials import CategoryService, ColorService, UnitService

router = APIRouter(
    prefix="",
    tags=["reference"],
    responses=ERROR_RESPONSES
)

def get_category_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
) -> CategoryService:
    """Get CategoryService with dependency injection."""
    return CategoryService(vector_db=vector_db, ai_client=ai_client)

def get_unit_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
) -> UnitService:
    """Get UnitService with dependency injection."""
    return UnitService(vector_db=vector_db, ai_client=ai_client)

def get_color_service(
    vector_db: IVectorDatabase = Depends(get_vector_db_dependency),
    ai_client = Depends(get_ai_client_dependency)
) -> ColorService:
    """Get ColorService with dependency injection."""
    return ColorService(vector_db=vector_db, ai_client=ai_client)

@router.post(
    "/categories/",
    response_model=Category,
    summary="🏷️ Create Category – Create Material Category",
    response_description="Created material category",
    status_code=201
)
async def create_category(
    category: CategoryCreate,
    service: CategoryService = Depends(get_category_service)
):
    """
    🏷️ **Create Category** - Create new material category
    
    Creates a new material usage category for classification and filtering.
    Categories help organize materials by functional purpose.
    
    **Features:**
    - 🆔 Auto-generation of UUID for category
    - 🤖 AI embedding generation (1536 dimensions)
    - 🔍 Indexing for fast search
    - ⏰ Automatic timestamps
    - 📝 Name uniqueness validation
    - 🗄️ Storage in vector database
    
    **Required Fields:**
    - `name`: Category name (unique)
    
    **Optional Fields:**
    - `description`: Category description
    - `aliases`: Alternative names and synonyms
    
    **Request Body Example:**
    ```json
    {
        "name": "Цемент",
        "description": "Строительные цементы и вяжущие материалы",
        "aliases": ["цемент", "cement", "вяжущие"]
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Цемент",
        "description": "Строительные цементы и вяжущие материалы",
        "aliases": ["цемент", "cement", "вяжущие"],
        "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
        "created_at": "2025-06-16T17:30:15.123456Z",
        "updated_at": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **201 Created**: Category created successfully
    - **400 Bad Request**: Validation error (duplicate name)
    - **500 Internal Server Error**: Database save error
    
    **Common Categories:**
    - Cement, Brick, Reinforcement, Concrete, Sand, Crushed Stone
    - Insulation, Waterproofing, Metal Products
    - Paint and Varnish Materials, Dry Mixes
    
    **Use Cases:**
    - Creating material classification system
    - Setting up search filters
    - Organizing product catalog
    - Standardizing nomenclature
    """
    return await service.create_category(category)

@router.get(
    "/categories/",
    response_model=List[Category],
    summary="📋 List Categories – Material Categories List",
    response_description="List of material categories"
)
async def get_categories(
    service: CategoryService = Depends(get_category_service)
):
    """
    📋 **List Categories** - Get all material categories
    
    Returns complete list of all available material categories in the system.
    Used for creating dropdown lists and filters in interfaces.
    
    **Features:**
    - 📊 Complete list without pagination
    - ⚡ Fast loading (cached)
    - 📅 Sorted by creation date (oldest first)
    - 🤖 AI embeddings included (1536 dimensions)
    - 📝 Aliases and descriptions included
    - 🎯 Ready for UI use
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Reinforcement",
            "description": "Steel bars for reinforcing reinforced concrete structures",
            "aliases": ["арматура", "reinforcement", "steel bars"],
            "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Brick",
            "description": "Ceramic and silicate products for wall masonry",
            "aliases": ["кирпич", "brick", "ceramic"],
            "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "name": "Cement",
            "description": "Binding materials based on Portland cement",
            "aliases": ["цемент", "cement", "вяжущие"],
            "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: List returned successfully (may be empty)
    - **500 Internal Server Error**: Data retrieval error
    
    **Use Cases:**
    - Creating dropdown lists in forms
    - Filtering materials by categories
    - Administrative interfaces
    - API for mobile applications
    - Synchronization with external systems
    """
    return await service.get_categories()

@router.delete(
    "/categories/{category_id}",
    summary="🗑️ Delete Category – Remove Material Category",
    response_description="Category deletion result",
    responses={
        200: {"description": "Category deleted successfully"},
        404: {"description": "Category not found"},
        400: {"description": "Invalid UUID"}
    }
)
async def delete_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service)
):
    """
    🗑️ **Delete Category** - Remove material category
    
    Removes category from system. Irreversible operation, requires caution.
    
    **⚠️ WARNING:** Ensure category is not used by materials!
    
    **Features:**
    - 🔥 Complete removal from vector database
    - ⚠️ Dependency check not performed
    - ⚡ Instant execution
    - 📊 Index updates
    
    **Path Parameters:**
    - `category_id`: Category UUID for deletion
    
    **Response Example:**
    ```json
    {
        "success": true,
        "message": "Category deleted successfully",
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Category deleted successfully
    - **404 Not Found**: Category with specified ID not found
    - **400 Bad Request**: Invalid UUID format
    - **500 Internal Server Error**: Deletion error
    
    **⚠️ Recommendations:**
    - Check category usage in materials
    - Create backup before deletion
    - Consider archiving instead of deletion
    
    **Use Cases:**
    - Removing obsolete categories
    - Cleaning test data
    - Reorganizing classification system
    """
    success = await service.delete_category(category_id)
    return {"success": success}

@router.patch(
    "/categories/{category_id}",
    response_model=Category,
    summary="✏️ Update Category – Update Material Category",
    response_description="Updated material category",
    status_code=200
)
async def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    service: CategoryService = Depends(get_category_service)
):
    """
    ✏️ **Update Category** - Update existing material category
    
    Updates category data and always recalculates AI embedding.
    
    **Features:**
    - Partial update (only provided fields)
    - Always recalculates embedding
    - Updates timestamps
    - Returns updated category
    
    **Request Example:**
    ```json
    {
        "name": "Обновленная категория",
        "description": "Новое описание"
    }
    ```
    """
    updated = await service.update_category(category_id, category_update)
    if not updated:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Category not found")
    return updated

@router.post(
    "/units/",
    response_model=Unit,
    summary="📏 Create Unit – Create Measurement Unit",
    response_description="Created measurement unit",
    status_code=201
)
async def create_unit(
    unit: UnitCreate,
    service: UnitService = Depends(get_unit_service)
):
    """
    📏 **Create Unit** - Create new measurement unit
    
    Creates a new measurement unit for materials with AI-generated embedding.
    Units are used for material classification and measurement standardization.
    
    **Features:**
    - 🆔 Auto-generation of UUID for unit
    - 🤖 AI embedding generation for semantic search (1536 dimensions)
    - ⏰ Automatic timestamps
    - 📝 Name uniqueness validation
    - 🗄️ Storage in vector database
    
    **Required Fields:**
    - `name`: Unit abbreviation/short name (e.g., "кг", "м³", "шт")
    
    **Optional Fields:**
    - `description`: Unit description (e.g., "Килограмм — единица массы")
    - `aliases`: Alternative names and abbreviations (e.g., ["килограмм", "kg", "кг."])
    
    **Request Body Example:**
    ```json
    {
        "name": "кг",
        "description": "Килограмм — единица массы",
        "aliases": ["килограмм", "kg", "кг."]
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "кг",
        "description": "Килограмм — единица массы",
        "aliases": ["килограмм", "kg", "кг."],
        "embedding": [0.123, 0.456, ...],  // 1536-dimensional vector
        "created_at": "2025-06-16T17:30:15.123456Z",
        "updated_at": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **201 Created**: Unit created successfully
    - **400 Bad Request**: Invalid input data
    - **422 Validation Error**: Schema validation failed
    - **500 Internal Server Error**: Creation error
    
    **Use Cases:**
    - Adding new measurement units to the system
    - Standardizing unit abbreviations
    - Supporting multiple unit variants (aliases)
    - Semantic search for unit matching
    - Material classification by units
    
    **Technical Details:**
    - Embedding model: text-embedding-3-small (1536 dimensions)
    - Vector database: Qdrant with cosine similarity
    - Text for embedding: name + description + aliases
    - Collection: units_v3
    """
    return await service.create_unit(unit)

@router.get(
    "/units/",
    response_model=List[Unit],
    summary="📐 List Units – List Measurement Units",
    response_description="List of measurement units"
)
async def get_units(
    service: UnitService = Depends(get_unit_service)
):
    """
    📋 **List Units** - Get all measurement units
    
    Returns complete list of all available measurement units in the system.
    Used for creating dropdown lists and data validation.
    
    **Features:**
    - 📊 Complete list without pagination
    - ⚡ Fast loading (cached)
    - 🔤 Sorting by popularity
    - 📈 Ready for UI use
    - 🌐 International standards support
    - 🤖 Full embedding vectors (1536 dimensions)
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "кг",
            "description": "Килограмм — единица массы",
            "aliases": ["килограмм", "kg", "кг."],
            "embedding": [0.123, 0.456, ...],  // 1536-dimensional vector
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "м³",
            "description": "Кубический метр — единица объёма",
            "aliases": ["кубометр", "куб.м", "m3"],
            "embedding": [0.789, 0.012, ...],  // 1536-dimensional vector
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: Units retrieved successfully
    - **500 Internal Server Error**: Database error
    
    **Use Cases:**
    - Populating unit selection dropdowns
    - Validating unit input in forms
    - Displaying available units in UI
    - Unit normalization and standardization
    - Semantic unit matching
    
    **Technical Details:**
    - Embedding model: text-embedding-3-small (1536 dimensions)
    - Vector database: Qdrant with cosine similarity
    - Collection: units_v3
    - Includes full embedding vectors for semantic operations
    """
    return await service.get_units()

@router.delete(
    "/units/{unit_id}",
    summary="🗑️ Delete Unit – Delete Measurement Unit",
    response_description="Unit deletion result",
    responses={
        200: {"description": "Unit deleted successfully"},
        404: {"description": "Unit not found"},
        400: {"description": "Invalid UUID"}
    }
)
async def delete_unit(
    unit_id: str,
    service: UnitService = Depends(get_unit_service)
):
    """
    ️ **Delete Unit** - Delete measurement unit
    
    Removes measurement unit from system. Irreversible operation, requires caution.
    
    **⚠️ WARNING:** Ensure unit is not used by materials!
    
    **Features:**
    - 🔥 Complete removal from vector database
    - ⚠️ Dependency check not performed
    - ⚡ Instant execution
    - 📊 Index updates
    - 🤖 AI embeddings removal
    
    **Path Parameters:**
    - `unit_id`: Unit UUID for deletion
    
    **Response Example:**
    ```json
    {
        "success": true,
        "message": "Unit deleted successfully", 
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Unit deleted successfully
    - **404 Not Found**: Unit with specified ID not found
    - **400 Bad Request**: Invalid UUID format
    - **500 Internal Server Error**: Deletion error
    
    **⚠️ Recommendations:**
    - Check unit usage in materials
    - Create backup before deletion
    - Consider archiving instead of deletion
    - Use standard SI units
    
    **Use Cases:**
    - Removing obsolete measurement units
    - Cleaning test data
    - Standardizing measurement system
    - Fixing input errors
    """
    success = await service.delete_unit(unit_id)
    return {"success": success}

@router.patch(
    "/units/{unit_id}",
    response_model=Unit,
    summary="✏️ Update Unit – Update Measurement Unit",
    response_description="Updated measurement unit",
    status_code=200
)
async def update_unit(
    unit_id: str,
    unit_update: UnitUpdate,
    service: UnitService = Depends(get_unit_service)
):
    """
    ✏️ **Update Unit** - Update existing measurement unit
    
    Updates unit data and always recalculates AI embedding.
    
    **Features:**
    - Partial update (only provided fields)
    - Always recalculates embedding
    - Updates timestamps
    - Returns updated unit
    
    **Request Example:**
    ```json
    {
        "name": "кг",
        "description": "Обновленное описание"
    }
    ```
    """
    updated = await service.update_unit(unit_id, unit_update)
    if not updated:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unit not found")
    return updated

@router.post(
    "/colors/",
    response_model=ColorReference,
    summary="🎨 Create Color – Create Color",
    response_description="Created color",
    status_code=201
)
async def create_color(
    color: ColorCreate,
    service: ColorService = Depends(get_color_service)
):
    """
    🎨 **Create Color** - Create new reference color
    
    Creates a new color in the reference for material classification.
    Colors are used for visual search and filtering of construction materials.
    
    **Features:**
    - 🆔 Auto-generation of UUID for color
    - 🤖 AI embedding generation for semantic search
    - 🌈 HEX and RGB format support
    - 🏷️ Synonym system for precise search
    - ⏰ Automatic timestamps
    - 🗄️ Storage in vector database
    
    **Required Fields:**
    - `name`: Color name in English
    
    **Optional Fields:**
    - `hex_code`: HEX color code (e.g., "#FFFFFF")
    - `rgb_values`: RGB values [R, G, B] (0-255)
    - `aliases`: Synonyms and alternative names
    
    **Request Body Example:**
    ```json
    {
        "name": "white",
        "hex_code": "#FFFFFF",
        "rgb_values": [255, 255, 255],
        "aliases": ["light", "milk", "snow", "cream"]
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "white",
        "hex_code": "#FFFFFF",
        "rgb_values": [255, 255, 255],
        "aliases": ["light", "milk", "snow", "cream"],
        "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
        "created_at": "2025-06-16T17:30:15.123456Z",
        "updated_at": "2025-06-16T17:30:15.123456Z"
    }
    ```
    
    **Response Status Codes:**
    - **201 Created**: Color created successfully
    - **400 Bad Request**: Validation error (invalid HEX/RGB)
    - **500 Internal Server Error**: Database save error
    
    **Common Colors:**
    - **Basic**: white, black, gray, brown
    - **Primary**: red, blue, green, yellow
    - **Natural**: beige, sand, terracotta, ochre
    - **Metallic**: silver, gold, copper
    - **Special**: transparent, matte, glossy
    
    **Use Cases:**
    - Creating material color reference
    - Filtering by colors in catalogs
    - Visual search for construction materials
    - Standardizing color nomenclature
    - RAG normalization of color descriptions
    """
    return await service.create_color(color)

@router.get(
    "/colors/",
    response_model=List[ColorReference],
    summary="🌈 List Colors – List Colors",
    response_description="List of material colors"
)
async def get_colors(
    service: ColorService = Depends(get_color_service)
):
    """
    🌈 **List Colors** - Get all colors from reference
    
    Returns complete list of all available colors in the system.
    Used for creating color palettes and filters in interfaces.
    
    **Features:**
    - 🎨 Complete color list with embeddings
    - 🌈 HEX and RGB format support
    - 🏷️ Synonyms for each color
    - ⚡ Fast loading (cached)
    - 🔤 Sorting by popularity
    - 📈 Ready for UI use
    
    **Response Example:**
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "white",
            "hex_code": "#FFFFFF",
            "rgb_values": [255, 255, 255],
            "aliases": ["light", "milk", "snow"],
            "embedding": [0.1, 0.2, 0.3, "...", "(1536 dimensions)"],
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "red",
            "hex_code": "#FF0000",
            "rgb_values": [255, 0, 0],
            "aliases": ["scarlet", "brick", "crimson"],
            "embedding": [0.4, 0.5, 0.6, "...", "(1536 dimensions)"],
            "created_at": "2025-06-16T17:30:15.123456Z",
            "updated_at": "2025-06-16T17:30:15.123456Z"
        }
    ]
    ```
    
    **Response Status Codes:**
    - **200 OK**: List returned successfully (may be empty)
    - **500 Internal Server Error**: Data retrieval error
    
    **Color Categories:**
    - **Neutral**: white, black, gray
    - **Warm**: red, orange, yellow
    - **Cool**: blue, green, purple
    - **Natural**: brown, beige, terracotta
    - **Metallic**: silver, gold, copper
    
    **Use Cases:**
    - Creating color palettes in UI
    - Filtering materials by colors
    - RAG normalization of color descriptions
    - API for mobile applications
    - Integration with supplier catalogs
    """
    return await service.get_colors()

@router.delete(
    "/colors/{color_id}",
    summary="🗑️ Delete Color – Delete Color",
    response_description="Color deletion result",
    responses={
        200: {"description": "Color deleted successfully"},
        404: {"description": "Color not found"},
        400: {"description": "Invalid UUID"}
    }
)
async def delete_color(
    color_id: str,
    service: ColorService = Depends(get_color_service)
):
    """
    🗑️ **Delete Color** - Delete color from reference
    
    Removes color from system. Irreversible operation, requires caution.
    
    **⚠️ WARNING:** Ensure color is not used in materials!
    
    **Features:**
    - 🔥 Complete removal from vector database
    - ⚠️ Dependency check not performed
    - ⚡ Instant execution
    - 📊 Index updates
    - 🤖 AI embeddings removal
    
    **Path Parameters:**
    - `color_id`: Color UUID for deletion
    
    **Response Example:**
    ```json
    {
        "success": true,
        "message": "Color deleted successfully",
        "deleted_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    
    **Response Status Codes:**
    - **200 OK**: Color deleted successfully
    - **404 Not Found**: Color with specified ID not found
    - **400 Bad Request**: Invalid UUID format
    - **500 Internal Server Error**: Deletion error
    
    **⚠️ Recommendations:**
    - Check color usage in materials
    - Create backup before deletion
    - Consider archiving instead of deletion
    - Use standard colors from palette
    
    **Use Cases:**
    - Removing obsolete colors
    - Cleaning test data
    - Standardizing color palette
    - Fixing input errors
    - Reorganizing color reference
    """
    success = await service.delete_color(color_id)
    return {"success": success}

@router.patch(
    "/colors/{color_id}",
    response_model=ColorReference,
    summary="✏️ Update Color – Update Reference Color",
    response_description="Updated color",
    status_code=200
)
async def update_color(
    color_id: str,
    color_update: ColorUpdate,
    service: ColorService = Depends(get_color_service)
):
    """
    ✏️ **Update Color** - Update existing reference color
    
    Updates color data and always recalculates AI embedding.
    
    **Features:**
    - Partial update (only provided fields)
    - Always recalculates embedding
    - Updates timestamps
    - Returns updated color
    
    **Request Example:**
    ```json
    {
        "name": "Обновленный цвет",
        "hex_code": "#00FF00"
    }
    ```
    """
    updated = await service.update_color(color_id, color_update)
    if not updated:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Color not found")
    return updated

 