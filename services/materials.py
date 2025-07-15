"""Consolidated Materials Service - Best of all versions.

Консолидированный сервис материалов - лучшее из всех версий.
"""

from typing import List, Optional, Dict, Any
from core.logging import get_logger, with_correlation_context, get_correlation_id
from core.logging.managers.unified import get_unified_logging_manager
from core.logging import log_database_operation_decorator  # Новый декоратор для логирования операций с БД
from core.logging.metrics.integration import (  # 🎯 ЭТАП 5.4: Metrics Integration
    get_metrics_integrated_logger,
)
import uuid
from datetime import datetime

from core.schemas.materials import (
    Material, MaterialCreate, MaterialUpdate, MaterialBatchResponse, MaterialImportItem,
    Category, CategoryCreate, Unit
)
from core.schemas.colors import ColorReference, ColorCreate
from core.database.interfaces import IVectorDatabase
from core.database.exceptions import DatabaseError
from core.repositories.base import BaseRepository
from core.logging.metrics import get_metrics_collector


logger = get_logger(__name__)
unified_manager = get_unified_logging_manager()


class MaterialsService(BaseRepository):
    """Consolidated Materials Service with best features from all versions.
    
    Консолидированный сервис материалов с лучшими функциями из всех версий.
    
    Features:
    - New multi-database architecture with dependency injection
    - Fallback search strategy (vector → SQL)
    - Comprehensive error handling and logging
    - Batch operations with performance optimization
    - Category and unit inference
    - JSON import functionality
    - Performance tracking and metrics collection
    """
    
    def __init__(self, vector_db: IVectorDatabase = None, ai_client = None):
        """Initialize Materials Service with dependency injection.
        
        Args:
            vector_db: Vector database client (injected)
            ai_client: AI client for embeddings (injected)
        """
        # Use factory defaults if not provided
        if vector_db is None:
            try:
                from core.database.factories import DatabaseFactory
                vector_db = DatabaseFactory.create_vector_database()
            except Exception as e:
                logger.warning(f"Failed to get vector DB client: {e}")
                vector_db = None
        
        if ai_client is None:
            try:
                from core.database.factories import AIClientFactory
                ai_client = AIClientFactory.create_ai_client()
                logger.info("✅ AI client successfully created")
            except Exception as e:
                logger.error(f"❌ CRITICAL: Failed to create AI client: {e}")
                # NO FALLBACK - AI client is required for embeddings
                raise DatabaseError(
                    message="Failed to initialize AI client for embeddings",
                    details=f"Cannot proceed without OpenAI API access: {str(e)}"
                )
        
        super().__init__(vector_db=vector_db, ai_client=ai_client)
        self.collection_name = "materials"
        
        # Initialize performance tracking
        self.metrics_collector = get_metrics_collector()
        self.performance_tracker = self.metrics_collector.get_performance_tracker()
        
        # 🎯 ЭТАП 5.4: Initialize metrics-integrated logger
        self.metrics_logger = get_metrics_integrated_logger("materials_service")
        
        logger.info("MaterialsService initialized with consolidated architecture, performance tracking, and metrics integration")
    
    async def initialize(self) -> None:
        """Initialize service and ensure collection exists.
        
        Raises:
            DatabaseError: If initialization fails
        """
        try:
            await self._ensure_collection_exists()
            logger.info("MaterialsService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MaterialsService: {e}")
            raise DatabaseError(
                message="Failed to initialize MaterialsService",
                details=str(e)
            )
    
    async def _ensure_collection_exists(self) -> None:
        """Ensure materials collection exists with proper configuration."""
        try:
            # Check if vector_db is available
            if self.vector_db is None:
                logger.warning("Vector DB not available, skipping collection creation")
                return
                
            # Check if collection exists (using adapter method)
            if not await self.vector_db.collection_exists(self.collection_name):
                logger.info(f"Creating collection: {self.collection_name}")
                # Create collection using adapter
                await self.vector_db.create_collection(
                    name=self.collection_name,
                    vector_size=1536,
                    distance_metric="cosine"
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.debug(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise DatabaseError(
                message=f"Failed to create collection {self.collection_name}",
                details=str(e)
            )
    
    # === CRUD Operations ===
    
    @with_correlation_context
    @log_database_operation_decorator("qdrant", "create_material")  # Используем новый декоратор
    async def create_material(self, material: MaterialCreate) -> Material:
        """Create a new material with semantic embedding.
        
        Args:
            material: Material data to create
            
        Returns:
            Created material with ID and embedding
            
        Raises:
            DatabaseError: If creation fails
        """
        get_correlation_id()
        logger.info(f"Creating material: {material.name}")
        
        with self.performance_tracker.time_operation("materials_service", "create_material", 1):
            try:
                await self._ensure_collection_exists()
                
                # Duplicate validation (name + unit must be unique)
                if await self._is_duplicate(material.name, material.unit):
                    raise ValueError(f"Duplicate material (name + unit) already exists: {material.name} / {material.unit}")
                
                # Generate embedding for semantic search
                text_for_embedding = self._prepare_text_for_embedding(material)
                embedding = await self.get_embedding(text_for_embedding)
                
                # Create material ID and timestamps
                material_id = str(uuid.uuid4())
                current_time = datetime.utcnow()
                
                # Prepare vector data
                vector_data = {
                    "id": material_id,
                    "vector": embedding,
                    "payload": {
                        "name": material.name,
                        "use_category": material.use_category,
                        "unit": material.unit,
                        "sku": material.sku,
                        "description": material.description,
                        # Enhanced fields for parsing and normalization
                        "color": material.color,
                        "normalized_color": material.normalized_color,
                        "normalized_parsed_unit": material.normalized_parsed_unit,
                        "unit_coefficient": material.unit_coefficient,
                        "created_at": current_time.isoformat(),
                        "updated_at": current_time.isoformat()
                    }
                }
                
                # Store in vector database (using adapter)
                await self.vector_db.upsert(
                    collection_name=self.collection_name,
                    vectors=[vector_data]
                )
                
                logger.info(f"Material created successfully: {material.name} (ID: {material_id})")
                
                return Material(
                    id=material_id,
                    name=material.name,
                    use_category=material.use_category,
                    unit=material.unit,
                    sku=material.sku,
                    description=material.description,
                    # Enhanced fields
                    color=material.color,
                    normalized_color=material.normalized_color,
                    normalized_parsed_unit=material.normalized_parsed_unit,
                    unit_coefficient=material.unit_coefficient,
                    embedding=embedding,  # Full embedding, will be formatted by field_serializer
                    created_at=current_time,
                    updated_at=current_time
                )
                
            except Exception as e:
                logger.error(f"Failed to create material '{material.name}': {e}")
                await self._handle_database_error("create_material", e)
    
    @with_correlation_context
    async def get_material(self, material_id: str) -> Optional[Material]:
        """Get material by ID.
        
        Args:
            material_id: Material identifier
            
        Returns:
            Material if found, None otherwise
            
        Raises:
            DatabaseError: If retrieval fails
        """
        get_correlation_id()
        logger.debug(f"Retrieving material: {material_id}")
        
        try:
            await self._ensure_collection_exists()
            
            result = await self.vector_db.get_by_id(
                collection_name=self.collection_name,
                vector_id=material_id
            )
            
            if not result:
                logger.debug(f"Material not found: {material_id}")
                return None
            
            return self._convert_vector_result_to_material(result)
            
        except Exception as e:
            logger.error(f"Failed to get material {material_id}: {e}")
            await self._handle_database_error("get_material", e)
    
    async def update_material(self, material_id: str, material_update: MaterialUpdate) -> Optional[Material]:
        """Update existing material.
        
        Args:
            material_id: Material identifier
            material_update: Updated material data
            
        Returns:
            Updated material if found, None otherwise
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            # Get existing material
            existing = await self.get_material(material_id)
            if not existing:
                logger.debug(f"Material not found for update: {material_id}")
                return None
            
            # Update fields
            updated_data = existing.model_dump()
            for field, value in material_update.model_dump(exclude_unset=True).items():
                updated_data[field] = value
            
            # Generate new embedding if content changed
            material_create = MaterialCreate(**{
                k: v for k, v in updated_data.items() 
                if k in MaterialCreate.model_fields
            })
            text_for_embedding = self._prepare_text_for_embedding(material_create)
            embedding = await self.get_embedding(text_for_embedding)
            
            # Update timestamps
            current_time = datetime.utcnow()
            updated_data["updated_at"] = current_time
            
            # Prepare updated vector data
            vector_data = {
                "id": material_id,
                "vector": embedding,
                "payload": {
                    "name": updated_data["name"],
                    "use_category": updated_data["use_category"],
                    "unit": updated_data["unit"],
                    "sku": updated_data.get("sku"),
                    "description": updated_data.get("description"),
                    "created_at": updated_data["created_at"].isoformat(),
                    "updated_at": current_time.isoformat()
                }
            }
            
            # Update in vector database
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[vector_data]
            )
            
            logger.info(f"Material updated successfully: {material_id}")
            
            # Return updated material
            updated_data["embedding"] = embedding[:10]  # Truncate for response
            return Material(**updated_data)
            
        except Exception as e:
            logger.error(f"Failed to update material {material_id}: {e}")
            await self._handle_database_error("update_material", e)
    
    async def delete_material(self, material_id: str) -> bool:
        """Delete a material.
        
        Args:
            material_id: Material identifier
            
        Returns:
            True if deleted successfully, False if material not found
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            # Check if material exists directly via vector DB (more efficient)
            existing_data = await self.vector_db.get_by_id(
                collection_name=self.collection_name,
                vector_id=material_id
            )
            
            if not existing_data:
                logger.warning(f"Material not found for deletion: {material_id}")
                return False
            
            # Delete the material
            await self.vector_db.delete(
                collection_name=self.collection_name,
                vector_id=material_id
            )
            
            logger.info(f"Material deleted successfully: {material_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete material {material_id}: {e}")
            await self._handle_database_error("delete_material", e)
    
    # === Search Operations ===
    
    @with_correlation_context
    @log_database_operation_decorator("qdrant", "search_materials")
    async def search_materials(self, query: str, limit: int = 10) -> List[Material]:
        """Search materials using centralized fallback manager (vector → SQL LIKE)."""
        from core.database.factories import get_fallback_manager, AllDatabasesUnavailableError
        get_correlation_id()
        with self.performance_tracker.time_operation("materials_service", "search_materials", limit):
            fallback_manager = get_fallback_manager()
            try:
                results = await fallback_manager.search_materials(query, limit)
                return results
            except AllDatabasesUnavailableError as e:
                logger.error(f"All databases unavailable for search_materials: {e.errors}")
                raise
    
    async def _search_vector(self, query: str, limit: int) -> List[Material]:
        """Perform vector semantic search."""
        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Search in vector database (using adapter)
            results = await self.vector_db.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Convert results to Material objects (adapter already returns proper format)
            materials = []
            for result in results:
                material = self._convert_vector_result_to_material(result)
                if material:
                    materials.append(material)
            
            return materials
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise DatabaseError(
                message="Vector search failed",
                details=str(e)
            )
    
    async def get_materials(self, skip: int = 0, limit: int = 100, category: Optional[str] = None) -> List[Material]:
        """Get all materials with optional category filter.
        
        Args:
            skip: Number of materials to skip
            limit: Maximum number of materials to return
            category: Optional category filter
            
        Returns:
            List of materials
            
        Raises:
            DatabaseError: If retrieval fails
        """
        with self.performance_tracker.time_operation("materials_service", "get_materials", limit):
            try:
                await self._ensure_collection_exists()
                
                # Build filter conditions
                filter_conditions = None
                if category:
                    filter_conditions = {"use_category": category}
                
                # Get materials from vector database
                # Note: This is a simplified implementation
                # In production, you might want to use scroll/pagination
                all_results = await self.vector_db.search(
                    collection_name=self.collection_name,
                    query_vector=[0.0] * 1536,  # Dummy vector for getting all
                    limit=limit + skip,
                    filter_conditions=filter_conditions
                )
                
                # Apply skip and convert to Material objects
                materials = []
                for i, result in enumerate(all_results):
                    if i < skip:
                        continue
                    if len(materials) >= limit:
                        break
                        
                    material = self._convert_vector_result_to_material(result)
                    if material:
                        materials.append(material)
                
                logger.info(f"Retrieved {len(materials)} materials (skip={skip}, limit={limit})")
                return materials
                
            except Exception as e:
                logger.error(f"Failed to get materials: {e}")
                await self._handle_database_error("get_materials", e)
    
    # === Batch Operations ===
    
    @with_correlation_context
    @log_database_operation_decorator("qdrant", "create_materials_batch")  # Используем новый декоратор
    async def create_materials_batch(self, materials: List[MaterialCreate], batch_size: int = 100) -> MaterialBatchResponse:
        """Create multiple materials in batches with optimized performance.
        
        Args:
            materials: List of materials to create
            batch_size: Size of processing batches
            
        Returns:
            Batch operation results
            
        Raises:
            DatabaseError: If batch creation fails
        """
        import time
        
        get_correlation_id()
        logger.info(f"Starting batch creation of {len(materials)} materials")
        
        start_time = time.time()
        successful_creates = 0
        failed_creates = 0
        errors = []
        created_materials = []
        failed_materials_list = []
        seen_keys = set()
        
        try:
            await self._ensure_collection_exists()
            
            logger.info(f"Starting batch creation of {len(materials)} materials")
            
            # Process materials in batches
            for i in range(0, len(materials), batch_size):
                chunk = materials[i:i + batch_size]
                current_time = datetime.utcnow()
                
                logger.debug(f"Processing batch {i//batch_size + 1}: {len(chunk)} materials")
                
                # Generate embeddings for the batch
                texts_for_embedding = [
                    self._prepare_text_for_embedding(material) 
                    for material in chunk
                ]
                
                try:
                    embeddings = await self.get_embeddings_batch(texts_for_embedding)
                except Exception as e:
                    logger.error(f"Failed to generate embeddings for batch: {e}")
                    failed_creates += len(chunk)
                    error_msg = f"Batch {i//batch_size + 1}: Failed to generate embeddings - {str(e)}"
                    errors.append(error_msg)
                    # Add failed materials to failed_materials_list
                    for material in chunk:
                        failed_materials_list.append({
                            "error": f"Failed to generate embeddings: {str(e)}",
                            "material": material.dict()
                        })
                    continue
                
                # Prepare vector data for batch upsert
                vectors = []
                
                for j, (material, embedding) in enumerate(zip(chunk, embeddings)):
                    try:
                        # Check duplicates inside DB and within the same batch
                        key = (material.name.lower(), material.unit.lower())
                        if key in seen_keys or await self._is_duplicate(material.name, material.unit):
                            raise ValueError("Duplicate material (name + unit) detected")
                        seen_keys.add(key)

                        material_id = str(uuid.uuid4())
                        
                        vector_data = {
                            "id": material_id,
                            "vector": embedding,
                            "payload": {
                                "name": material.name,
                                "use_category": material.use_category,
                                "unit": material.unit,
                                "sku": material.sku,
                                "description": material.description,
                                # Enhanced fields
                                "color": material.color,
                                "normalized_color": material.normalized_color,
                                "normalized_parsed_unit": material.normalized_parsed_unit,
                                "unit_coefficient": material.unit_coefficient,
                                "created_at": current_time.isoformat(),
                                "updated_at": current_time.isoformat()
                            }
                        }
                        vectors.append(vector_data)
                        
                        # Create Material object for response
                        created_material = Material(
                            id=material_id,
                            name=material.name,
                            use_category=material.use_category,
                            unit=material.unit,
                            sku=material.sku,
                            description=material.description,
                            # Enhanced fields
                            color=material.color,
                            normalized_color=material.normalized_color,
                            normalized_parsed_unit=material.normalized_parsed_unit,
                            unit_coefficient=material.unit_coefficient,
                            embedding=embedding,  # Full embedding, will be formatted by field_serializer
                            created_at=current_time,
                            updated_at=current_time
                        )
                        created_materials.append(created_material)
                        
                    except Exception as e:
                        failed_creates += 1
                        error_msg = f"Material '{material.name}': {str(e)}"
                        errors.append(error_msg)
                        failed_materials_list.append({
                            "error": str(e),
                            "material": material.dict()
                        })
                        continue
                
                # Batch upsert to vector database
                if vectors:
                    try:
                        await self.vector_db.upsert(
                            collection_name=self.collection_name,
                            vectors=vectors
                        )
                        successful_creates += len(vectors)
                        logger.debug(f"Successfully created batch of {len(vectors)} materials")
                    except Exception as e:
                        failed_creates += len(vectors)
                        error_msg = f"Batch {i//batch_size + 1}: Database upsert failed - {str(e)}"
                        errors.append(error_msg)
                        # Add failed materials to failed_materials_list and remove from created_materials
                        for j, material in enumerate(chunk):
                            if j < len(vectors):  # Only for materials that had vectors created
                                failed_materials_list.append({
                                    "error": f"Database upsert failed: {str(e)}",
                                    "material": material.dict()
                                })
                        created_materials = created_materials[:-len(vectors)]
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            logger.info(f"Batch creation completed: {successful_creates} successful, {failed_creates} failed, {processing_time:.2f}s")
            
            return MaterialBatchResponse(
                success=failed_creates == 0,
                total_processed=len(materials),
                successful_materials=created_materials,
                failed_materials=failed_materials_list,
                processing_time_seconds=processing_time,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Failed to create materials batch: {e}")
            await self._handle_database_error("create_materials_batch", e)
    
    async def import_materials_from_json(self, 
                                       import_items: List[MaterialImportItem], 
                                       default_category: str = "Стройматериалы",
                                       default_unit: str = "шт",
                                       batch_size: int = 100) -> MaterialBatchResponse:
        """Import materials from JSON format with sku and name.
        
        Args:
            import_items: List of import items with name and sku
            default_category: Default category for materials
            default_unit: Default unit for materials
            batch_size: Batch size for processing
            
        Returns:
            Batch operation results
            
        Raises:
            DatabaseError: If import fails
        """
        try:
            # Convert import items to MaterialCreate objects
            materials_to_create = []
            category_map = self._get_category_mapping()
            unit_map = self._get_unit_mapping()
            
            for item in import_items:
                # Try to infer category from name or use default
                category = self._infer_category(item.name, category_map) or default_category
                
                # Try to infer unit from name or use default  
                unit = self._infer_unit(item.name, unit_map) or default_unit
                
                material = MaterialCreate(
                    name=item.name,
                    use_category=category,
                    unit=unit,
                    sku=item.sku,
                    description=None
                )
                materials_to_create.append(material)
            
            logger.info(f"Importing {len(materials_to_create)} materials from JSON")
            
            # Use existing batch create method
            return await self.create_materials_batch(materials_to_create, batch_size)
            
        except Exception as e:
            logger.error(f"Failed to import materials from JSON: {e}")
            await self._handle_database_error("import_materials_from_json", e)
    
    # === Helper Methods ===
    
    def _prepare_text_for_embedding(self, material: MaterialCreate) -> str:
        """Prepare text for embedding generation using name, unit, color and optional description.
        
        The embedding input is constructed as:
            "<name> <normalized_parsed_unit or unit> <normalized_color or color> <description?>"
        where description is included only if provided. This intentionally omits
        use_category and sku as requested.
        """
        # Use normalized fields if available, otherwise fallback to original
        unit_text = material.normalized_parsed_unit or material.unit
        color_text = material.normalized_color or material.color or ""
        
        return f"{material.name} {unit_text} {color_text} {material.description or ''}".strip()
    
    def _convert_vector_result_to_material(self, result: Dict[str, Any]) -> Optional[Material]:
        """Convert vector database result to Material object."""
        try:
            payload = result.get("payload", {})
            
            # Parse timestamps
            created_at = self._parse_timestamp(payload.get("created_at"))
            updated_at = self._parse_timestamp(payload.get("updated_at"))
            
            # Handle embedding - always provide some data instead of None
            embedding_data = result.get("vector", [])
            if embedding_data:
                # Keep full embedding data for the Material object
                # The formatting will be handled by the model_dump method
                formatted_embedding = embedding_data
            else:
                # Even if no embedding data, we'll let the model_dump handle the display
                formatted_embedding = None
            
            return Material(
                id=str(result.get("id")),
                name=payload.get("name"),
                use_category=payload.get("use_category", ""),
                unit=payload.get("unit"),
                sku=payload.get("sku"),
                description=payload.get("description"),
                # Enhanced fields
                color=payload.get("color"),
                normalized_color=payload.get("normalized_color"),
                normalized_parsed_unit=payload.get("normalized_parsed_unit"),
                unit_coefficient=payload.get("unit_coefficient"),
                embedding=formatted_embedding,
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            logger.error(f"Failed to convert vector result to material: {e}")
            return None
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string or return current time."""
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str)
            except:
                pass
        return datetime.utcnow()
    
    def _get_category_mapping(self) -> Dict[str, str]:
        """Get category mapping for inference."""
        return {
            "цемент": "Цемент",
            "бетон": "Бетон",
            "кирпич": "Кирпич",
            "блок": "Блоки",
            "газобетон": "Газобетон",
            "пеноблок": "Пеноблоки",
            "арматура": "Арматура",
            "металл": "Металлопрокат",
            "труба": "Трубы",
            "профиль": "Профили",
            "лист": "Листовые материалы",
            "утеплитель": "Утеплители",
            "изоляция": "Изоляционные материалы",
            "кровля": "Кровельные материалы",
            "черепица": "Черепица",
            "профнастил": "Профнастил",
            "сайдинг": "Сайдинг",
            "гипсокартон": "Гипсокартон",
            "фанера": "Фанера",
            "доска": "Пиломатериалы",
            "брус": "Пиломатериалы",
            "краска": "Лакокрасочные материалы",
            "грунт": "Грунтовки",
            "клей": "Клеи",
            "герметик": "Герметики",
            "смесь": "Сухие смеси",
            "раствор": "Растворы",
            "штукатурка": "Штукатурки",
            "шпатлевка": "Шпатлевки",
            "плитка": "Плитка",
            "керамогранит": "Керамогранит",
            "ламинат": "Ламинат",
            "линолеум": "Линолеум",
            "паркет": "Паркет"
        }
    
    def _get_unit_mapping(self) -> Dict[str, str]:
        """Get unit mapping for inference."""
        return {
            "мешок": "мешок",
            "кг": "кг",
            "тонна": "т",
            "куб": "м³",
            "кубометр": "м³",
            "м3": "м³",
            "квадрат": "м²",
            "м2": "м²",
            "метр": "м",
            "штука": "шт",
            "упаковка": "упак",
            "пачка": "пачка",
            "рулон": "рулон",
            "лист": "лист",
            "погонный": "пог.м",
            "литр": "л",
            "ведро": "ведро",
            "банка": "банка",
            "тюбик": "тюбик"
        }
    
    def _infer_category(self, name: str, category_map: Dict[str, str]) -> Optional[str]:
        """Infer category from material name."""
        name_lower = name.lower()
        for keyword, category in category_map.items():
            if keyword in name_lower:
                return category
        return None
    
    def _infer_unit(self, name: str, unit_map: Dict[str, str]) -> Optional[str]:
        """Infer unit from material name."""
        name_lower = name.lower()
        for keyword, unit in unit_map.items():
            if keyword in name_lower:
                return unit
        return None

    async def _is_duplicate(self, name: str, unit: str) -> bool:
        """Check if a material with the same (name, unit) already exists.

        Args:
            name: Material name
            unit: Measurement unit

        Returns:
            True if duplicate exists, False otherwise.
        """
        try:
            # Build case-insensitive filter; store original but compare lower-cased
            filter_conditions = {
                "name": name,
                "unit": unit
            }
            results = await self.vector_db.search(
                collection_name=self.collection_name,
                query_vector=[0.0] * 1536,  # dummy
                limit=1,
                filter_conditions=filter_conditions
            )
            return bool(results)
        except Exception as exc:
            # On failure we prefer to err on safe side – treat as duplicate to avoid collision
            logger.error(f"Duplicate-check failed, assuming duplicate for '{name} / {unit}': {exc}")
            return True


# === Separate Services for Categories and Units ===

class CategoryService(BaseRepository):
    """Service for managing material categories with Qdrant persistence and AI embedding."""
    
    def __init__(self, vector_db: IVectorDatabase = None, ai_client=None):
        super().__init__(vector_db=vector_db, ai_client=ai_client)
        self.collection_name = "categories_v3"  # Новая коллекция с 1536
        logger.info("CategoryService initialized with Qdrant persistence and AI embedding support")
    
    async def _ensure_collection_exists(self) -> None:
        """Ensure categories collection exists in Qdrant."""
        try:
            if self.vector_db:
                # Check if collection exists
                exists = await self.vector_db.collection_exists(self.collection_name)
                
                if not exists:
                    # Create collection if it doesn't exist
                    await self.vector_db.create_collection(
                        name=self.collection_name,
                        vector_size=1536,  # OpenAI text-embedding-3-small
                        distance_metric="cosine"
                    )
                    logger.debug(f"Categories collection '{self.collection_name}' created")
        except Exception as e:
            logger.error(f"Failed to ensure categories collection: {e}")
    
    async def create_category(self, category_data: CategoryCreate) -> Category:
        """Create a new category and save to Qdrant. Supports description and aliases.
        
        Args:
            category_data: CategoryCreate object with name, description, and aliases
            
        Returns:
            Category: Created category with AI embedding and metadata
            
        Raises:
            Exception: If vector database or AI client not available
        """
        try:
            if not self.vector_db:
                raise Exception("Vector database not available")
            
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            # Generate UUID for Qdrant ID
            import uuid
            category_id = str(uuid.uuid4())
            
            if not self.ai_client:
                raise Exception("AI client not available for embedding generation")
            
            # Формируем текст для embedding: name + description + aliases
            embedding_text = category_data.name
            if category_data.description:
                embedding_text += f" {category_data.description}"
            if category_data.aliases:
                embedding_text += " " + " ".join(category_data.aliases)
            
            # Generate AI embedding using BaseRepository method
            embedding = await self.get_embedding(embedding_text)
            
            if not embedding or not isinstance(embedding, list) or len(embedding) == 0:
                raise Exception("Failed to generate embedding for category")
            
            category = Category(
                id=category_id,
                name=category_data.name,
                description=category_data.description,
                aliases=category_data.aliases,
                embedding=embedding
            )
            
            # Save to Qdrant
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": category_id,
                    "vector": embedding,
                    "payload": {
                        "name": category_data.name,
                        "description": category_data.description,
                        "aliases": category_data.aliases,
                        "type": "category",
                        "created_at": category.created_at.isoformat(),
                        "updated_at": category.updated_at.isoformat()
                    }
                }]
            )
            
            logger.info(f"Category '{category_data.name}' created and saved to Qdrant with ID {category_id}")
            return category
        except Exception as e:
            logger.error(f"Failed to create category {getattr(category_data, 'name', None)}: {e}")
            raise e
    
    async def get_categories(self) -> List[Category]:
        """Get all categories from Qdrant, including description, aliases, and embedding."""
        try:
            if not self.vector_db:
                logger.warning("Vector DB not available, returning empty categories list")
                return []
            
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            # Get all categories from Qdrant using scroll_all
            results = await self.vector_db.scroll_all(
                collection_name=self.collection_name,
                with_payload=True,
                with_vectors=True
            )
            
            categories = []
            for result in results:
                payload = result.get("payload", {})
                if payload.get("type") == "category":
                    category = Category(
                        id=result.get("id"),
                        name=payload.get("name"),
                        description=payload.get("description"),
                        aliases=payload.get("aliases", []),
                        embedding=result.get("vector"),
                        created_at=datetime.fromisoformat(payload.get("created_at", datetime.utcnow().isoformat())),
                        updated_at=datetime.fromisoformat(payload.get("updated_at", datetime.utcnow().isoformat()))
                    )
                    categories.append(category)
            
            # Сортируем по дате создания (старые сначала, новые в конце)
            categories.sort(key=lambda x: x.created_at)
            
            return categories
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            # Return empty list instead of raising error
            return []
    
    async def update_category(self, category_id: str, category_update) -> Optional["Category"]:
        """Update existing category and embedding.
        
        Args:
            category_id: Category UUID
            category_update: CategoryUpdate object
        Returns:
            Updated Category or None if not found
        """
        try:
            # Получить текущую категорию
            existing = await self.vector_db.get_by_id(self.collection_name, category_id)
            if not existing:
                logger.info(f"Category not found for update: {category_id}")
                return None
            payload = existing.get("payload", {})
            # Обновить поля
            updated_data = {
                "name": category_update.name if category_update.name is not None else payload.get("name"),
                "description": category_update.description if category_update.description is not None else payload.get("description"),
                "aliases": category_update.aliases if category_update.aliases is not None else payload.get("aliases", []),
            }
            # Пересчитать embedding
            embedding_text = updated_data["name"]
            if updated_data["description"]:
                embedding_text += f" {updated_data['description']}"
            if updated_data["aliases"]:
                embedding_text += " " + " ".join(updated_data["aliases"])
            embedding = await self.get_embedding(embedding_text)
            # Обновить timestamps
            from datetime import datetime
            updated_at = datetime.utcnow().isoformat()
            # Upsert вектор
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": category_id,
                    "vector": embedding,
                    "payload": {
                        **updated_data,
                        "type": "category",
                        "created_at": payload.get("created_at"),
                        "updated_at": updated_at
                    }
                }]
            )
            logger.info(f"Category updated successfully: {category_id}")
            from core.schemas.materials import Category
            return Category(
                id=category_id,
                name=updated_data["name"],
                description=updated_data["description"],
                aliases=updated_data["aliases"],
                embedding=embedding,
                created_at=payload.get("created_at"),
                updated_at=updated_at
            )
        except Exception as e:
            logger.error(f"Failed to update category {category_id}: {e}")
            return None

    async def delete_category(self, category_id: str) -> bool:
        """Delete a category from Qdrant by ID."""
        try:
            if not self.vector_db:
                logger.warning("Vector DB not available")
                return False
            
            # Delete from Qdrant using the provided ID
            deleted = await self.vector_db.delete(
                collection_name=self.collection_name,
                vector_id=category_id
            )
            
            if deleted:
                logger.info(f"Category with ID '{category_id}' deleted from Qdrant")
                return True
            else:
                logger.warning(f"Failed to delete category with ID '{category_id}' from Qdrant")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete category {category_id}: {e}")
            return False




class UnitService(BaseRepository):
    """Service for managing material units with Qdrant persistence and AI embedding."""
    def __init__(self, vector_db: IVectorDatabase = None, ai_client=None):
        super().__init__(vector_db=vector_db, ai_client=ai_client)
        self.collection_name = "units_v3"  # Изменено: новая коллекция с 1536
        logger.info("UnitService initialized with Qdrant persistence and AI embedding support")

    async def _ensure_collection_exists(self) -> None:
        try:
            if self.vector_db:
                exists = await self.vector_db.collection_exists(self.collection_name)
                if not exists:
                    await self.vector_db.create_collection(
                        name=self.collection_name,
                        vector_size=1536,  # Исправлено: теперь 1536
                        distance_metric="cosine"
                    )
                    logger.debug(f"Units collection '{self.collection_name}' created")
        except Exception as e:
            logger.error(f"Failed to ensure units collection: {e}")

    async def create_unit(self, unit_data: Unit) -> Unit:
        """Create a new unit and save to Qdrant. Supports description and aliases."""
        try:
            await self._ensure_collection_exists()
            import uuid
            unit_id = str(uuid.uuid4())
            if not self.ai_client:
                raise Exception("AI client not available for embedding generation")
            # Формируем текст для embedding: name + description + aliases
            embedding_text = unit_data.name
            if unit_data.description:
                embedding_text += f" {unit_data.description}"
            if unit_data.aliases:
                embedding_text += " " + " ".join(unit_data.aliases)
            
            # Generate AI embedding using BaseRepository method
            embedding = await self.get_embedding(embedding_text)
            
            if not embedding or not isinstance(embedding, list) or len(embedding) == 0:
                raise Exception("Failed to generate embedding for unit")
            unit = Unit(
                id=unit_id,
                name=unit_data.name,
                description=unit_data.description,
                aliases=unit_data.aliases,
                embedding=embedding
            )
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": unit_id,
                    "vector": embedding,
                    "payload": {
                        "name": unit_data.name,
                        "description": unit_data.description,
                        "aliases": unit_data.aliases,
                        "type": "unit",
                        "created_at": unit.created_at.isoformat(),
                        "updated_at": unit.updated_at.isoformat()
                    }
                }]
            )
            return unit
        except Exception as e:
            logger.error(f"Failed to create unit {getattr(unit_data, 'name', None)}: {e}")
            raise e

    async def update_unit(self, unit_id: str, unit_update) -> Optional["Unit"]:
        """Update existing unit and embedding.
        
        Args:
            unit_id: Unit UUID
            unit_update: UnitUpdate object
        Returns:
            Updated Unit or None if not found
        """
        try:
            # Получить текущую единицу
            existing = await self.vector_db.get_by_id(self.collection_name, unit_id)
            if not existing:
                logger.info(f"Unit not found for update: {unit_id}")
                return None
            payload = existing.get("payload", {})
            # Обновить поля
            updated_data = {
                "name": unit_update.name if unit_update.name is not None else payload.get("name"),
                "description": unit_update.description if unit_update.description is not None else payload.get("description"),
                "aliases": unit_update.aliases if unit_update.aliases is not None else payload.get("aliases", []),
            }
            # Пересчитать embedding
            embedding_text = updated_data["name"]
            if updated_data["description"]:
                embedding_text += f" {updated_data['description']}"
            if updated_data["aliases"]:
                embedding_text += " " + " ".join(updated_data["aliases"])
            embedding = await self.get_embedding(embedding_text)
            # Обновить timestamps
            from datetime import datetime
            updated_at = datetime.utcnow().isoformat()
            # Upsert вектор
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": unit_id,
                    "vector": embedding,
                    "payload": {
                        **updated_data,
                        "type": "unit",
                        "created_at": payload.get("created_at"),
                        "updated_at": updated_at
                    }
                }]
            )
            logger.info(f"Unit updated successfully: {unit_id}")
            from core.schemas.materials import Unit
            return Unit(
                id=unit_id,
                name=updated_data["name"],
                description=updated_data["description"],
                aliases=updated_data["aliases"],
                embedding=embedding,
                created_at=payload.get("created_at"),
                updated_at=updated_at
            )
        except Exception as e:
            logger.error(f"Failed to update unit {unit_id}: {e}")
            return None

    async def get_units(self) -> List[Unit]:
        """Get all units from Qdrant, including description, aliases, and embedding."""
        try:
            if not self.vector_db:
                logger.warning("Vector DB not available, returning empty units list")
                return []
            await self._ensure_collection_exists()
            results = await self.vector_db.scroll_all(
                collection_name=self.collection_name,
                with_payload=True,
                with_vectors=True  # Теперь получаем embedding
            )
            units = []
            for result in results:
                payload = result.get("payload", {})
                if payload.get("type") == "unit":
                    unit = Unit(
                        id=result.get("id"),
                        name=payload.get("name"),
                        description=payload.get("description"),
                        aliases=payload.get("aliases", []),
                        embedding=result.get("vector"),
                        created_at=datetime.fromisoformat(payload.get("created_at", datetime.utcnow().isoformat())),
                        updated_at=datetime.fromisoformat(payload.get("updated_at", datetime.utcnow().isoformat()))
                    )
                    units.append(unit)
            
            # Сортируем по дате создания (старые сначала, новые в конце)
            units.sort(key=lambda x: x.created_at)
            return units
        except Exception as e:
            logger.error(f"Failed to get units: {e}")
            return []

    async def delete_unit(self, unit_id: str) -> bool:
        try:
            if not self.vector_db:
                logger.warning("Vector DB not available")
                return False
            deleted = await self.vector_db.delete(
                collection_name=self.collection_name,
                vector_id=unit_id
            )
            if deleted:
                logger.info(f"Unit with ID '{unit_id}' deleted from Qdrant")
                return True
            else:
                logger.warning(f"Failed to delete unit with ID '{unit_id}' from Qdrant")
                return False
        except Exception as e:
            logger.error(f"Failed to delete unit {unit_id}: {e}")
            return False


class ColorService(BaseRepository):
    """Service for managing color references with Qdrant persistence."""
    
    def __init__(self, vector_db: IVectorDatabase = None, ai_client = None):
        # Use factory defaults if not provided
        if vector_db is None:
            try:
                from core.database.factories import DatabaseFactory
                vector_db = DatabaseFactory.create_vector_database()
            except Exception as e:
                logger.warning(f"Failed to get vector DB client: {e}")
                vector_db = None
        
        if ai_client is None:
            try:
                from core.database.factories import AIClientFactory
                ai_client = AIClientFactory.create_ai_client()
            except Exception as e:
                logger.error(f"Failed to create AI client for ColorService: {e}")
                ai_client = None
        
        super().__init__(vector_db=vector_db, ai_client=ai_client)
        self.collection_name = "construction_colors"
        logger.info("ColorService initialized with Qdrant persistence")
    
    async def _ensure_collection_exists(self) -> None:
        """Ensure colors collection exists in Qdrant."""
        try:
            if self.vector_db:
                # Check if collection exists
                exists = await self.vector_db.collection_exists(self.collection_name)
                
                if not exists:
                    # Create collection if it doesn't exist
                    await self.vector_db.create_collection(
                        name=self.collection_name,
                        vector_size=1536,  # OpenAI text-embedding-3-small
                        distance_metric="cosine"
                    )
                    logger.debug(f"Colors collection '{self.collection_name}' created")
        except Exception as e:
            logger.error(f"Failed to ensure colors collection: {e}")
    
    async def create_color(self, color_data: ColorCreate) -> ColorReference:
        """Create a new color reference and save to Qdrant."""
        try:
            if not self.vector_db:
                raise Exception("Vector database not available")
            
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            # Generate UUID for color ID
            import uuid
            color_id = str(uuid.uuid4())
            
            # Формируем текст для embedding: name + aliases
            embedding_text = color_data.name
            if color_data.aliases:
                embedding_text += " " + " ".join(color_data.aliases)
            
            # Use AI client to generate embedding (inherited from BaseRepository)
            try:
                embedding = await self.get_embedding(embedding_text)
            except Exception as e:
                logger.error(f"Failed to generate embedding for color '{color_data.name}': {e}")
                # Use fallback hash-based vector
                import hashlib
                hash_obj = hashlib.md5(color_data.name.encode())
                hash_hex = hash_obj.hexdigest()
                embedding = []
                for i in range(1536):
                    byte_index = i % len(hash_hex)
                    value = int(hash_hex[byte_index], 16) / 15.0 - 0.5
                    embedding.append(value)
                logger.warning(f"Using fallback embedding for color '{color_data.name}'")
            
            # Create ColorReference
            color_ref = ColorReference(
                id=color_id,
                name=color_data.name,
                hex_code=color_data.hex_code,
                rgb_values=color_data.rgb_values,
                aliases=color_data.aliases,
                embedding=embedding
            )
            
            # Save to Qdrant
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": color_id,
                    "vector": embedding,
                    "payload": {
                        "name": color_data.name,
                        "hex_code": color_data.hex_code,
                        "rgb_values": color_data.rgb_values,
                        "aliases": color_data.aliases,
                        "type": "color",
                        "created_at": color_ref.created_at.isoformat(),
                        "updated_at": color_ref.updated_at.isoformat()
                    }
                }]
            )
            
            logger.info(f"Color '{color_data.name}' created and saved to Qdrant with ID {color_id}")
            return color_ref
            
        except Exception as e:
            logger.error(f"Failed to create color {color_data.name}: {e}")
            raise e
    
    async def get_colors(self) -> List[ColorReference]:
        """Get all colors from Qdrant."""
        try:
            if not self.vector_db:
                logger.warning("Vector DB not available, returning empty colors list")
                return []
            
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            # Get all colors from Qdrant using scroll_all
            results = await self.vector_db.scroll_all(
                collection_name=self.collection_name,
                with_payload=True,
                with_vectors=True
            )
            
            colors = []
            for result in results:
                payload = result.get("payload", {})
                if payload.get("type") == "color":
                    color_ref = ColorReference(
                        id=result.get("id"),
                        name=payload.get("name"),
                        hex_code=payload.get("hex_code"),
                        rgb_values=payload.get("rgb_values"),
                        aliases=payload.get("aliases", []),
                        embedding=result.get("vector", []),
                        created_at=datetime.fromisoformat(payload.get("created_at", datetime.utcnow().isoformat())),
                        updated_at=datetime.fromisoformat(payload.get("updated_at", datetime.utcnow().isoformat()))
                    )
                    colors.append(color_ref)
            
            # Сортируем по дате создания (старые сначала, новые в конце)
            colors.sort(key=lambda x: x.created_at)
            
            logger.info(f"Retrieved {len(colors)} colors from Qdrant")
            return colors
            
        except Exception as e:
            logger.error(f"Failed to get colors: {e}")
            # Return empty list instead of raising error
            return []
    
    async def update_color(self, color_id: str, color_update) -> Optional["ColorReference"]:
        """Update existing color and embedding.
        
        Args:
            color_id: Color UUID
            color_update: ColorUpdate object
        Returns:
            Updated ColorReference or None if not found
        """
        try:
            # Получить текущий цвет
            existing = await self.vector_db.get_by_id(self.collection_name, color_id)
            if not existing:
                logger.info(f"Color not found for update: {color_id}")
                return None
            payload = existing.get("payload", {})
            # Обновить поля
            updated_data = {
                "name": color_update.name if color_update.name is not None else payload.get("name"),
                "hex_code": color_update.hex_code if color_update.hex_code is not None else payload.get("hex_code"),
                "rgb_values": color_update.rgb_values if color_update.rgb_values is not None else payload.get("rgb_values"),
                "aliases": color_update.aliases if color_update.aliases is not None else payload.get("aliases", []),
            }
            # Пересчитать embedding
            embedding_text = updated_data["name"]
            if updated_data["aliases"]:
                embedding_text += " " + " ".join(updated_data["aliases"])
            embedding = await self.get_embedding(embedding_text)
            # Обновить timestamps
            from datetime import datetime
            updated_at = datetime.utcnow().isoformat()
            # Upsert вектор
            await self.vector_db.upsert(
                collection_name=self.collection_name,
                vectors=[{
                    "id": color_id,
                    "vector": embedding,
                    "payload": {
                        **updated_data,
                        "type": "color",
                        "created_at": payload.get("created_at"),
                        "updated_at": updated_at
                    }
                }]
            )
            logger.info(f"Color updated successfully: {color_id}")
            from core.schemas.colors import ColorReference
            return ColorReference(
                id=color_id,
                name=updated_data["name"],
                hex_code=updated_data["hex_code"],
                rgb_values=updated_data["rgb_values"],
                aliases=updated_data["aliases"],
                embedding=embedding,
                created_at=payload.get("created_at"),
                updated_at=updated_at
            )
        except Exception as e:
            logger.error(f"Failed to update color {color_id}: {e}")
            return None
    
    async def delete_color(self, color_id: str) -> bool:
        """Delete a color from Qdrant by ID."""
        try:
            if not self.vector_db:
                logger.warning("Vector DB not available")
                return False
            
            # Delete from Qdrant using the provided ID
            deleted = await self.vector_db.delete(
                collection_name=self.collection_name,
                vector_id=color_id
            )
            
            if deleted:
                logger.info(f"Color with ID '{color_id}' deleted from Qdrant")
                return True
            else:
                logger.warning(f"Failed to delete color with ID '{color_id}' from Qdrant")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete color {color_id}: {e}")
            return False


# --- Backward compatibility -------------------------------------------------
# Older tests patch private method ``_search_in_vector_db``. During the
# refactor it was renamed to ``_search_vector``.  Provide an alias so that
# legacy tests continue to work without modifications.
MaterialsService._search_in_vector_db = MaterialsService._search_vector  # type: ignore[attr-defined]

 