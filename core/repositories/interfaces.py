"""Repository interfaces for business domain objects.

Интерфейсы репозиториев для бизнес-объектов с поддержкой мульти-БД архитектуры.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from core.schemas.materials import Material, MaterialCreate, MaterialUpdate, Category, Unit


class IMaterialsRepository(ABC):
    """Abstract interface for materials repository.
    
    Репозиторий материалов с обязательными методами: create, upsert, get_by_id, 
    update, delete, search_semantic, search_text, create_batch, batch_upsert
    """
    
    @abstractmethod
    async def create(self, material: MaterialCreate) -> Material:
        """Create a new material.
        
        Args:
            material: Material creation data
            
        Returns:
            Created material
        """
    
    @abstractmethod
    async def upsert(self, material: MaterialCreate) -> Material:
        """Insert or update a material.
        
        Args:
            material: Material data for upsert
            
        Returns:
            Created or updated material
        """
    
    @abstractmethod
    async def get_by_id(self, material_id: str) -> Optional[Material]:
        """Get material by ID.
        
        Args:
            material_id: Material identifier
            
        Returns:
            Material or None if not found
        """
    
    @abstractmethod
    async def update(self, material_id: str, material_update: MaterialUpdate) -> Optional[Material]:
        """Update material.
        
        Args:
            material_id: Material identifier
            material_update: Material update data
            
        Returns:
            Updated material or None if not found
        """
    
    @abstractmethod
    async def delete(self, material_id: str) -> bool:
        """Delete material.
        
        Args:
            material_id: Material identifier
            
        Returns:
            True if deleted successfully
        """
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100, 
                  category: Optional[str] = None) -> List[Material]:
        """List materials with optional filtering.
        
        Args:
            skip: Number of materials to skip
            limit: Maximum number of materials to return
            category: Optional category filter
            
        Returns:
            List of materials
        """
    
    @abstractmethod
    async def search_semantic(self, query: str, limit: int = 10) -> List[Material]:
        """Search materials using semantic search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching materials
        """
    
    @abstractmethod
    async def search_text(self, query: str, limit: int = 10) -> List[Material]:
        """Search materials using text search (fallback).
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching materials
        """
    
    @abstractmethod
    async def create_batch(self, materials: List[MaterialCreate], 
                          batch_size: int = 100) -> Dict[str, Any]:
        """Create multiple materials in batches.
        
        Args:
            materials: List of materials to create
            batch_size: Size of processing batches
            
        Returns:
            Batch operation results
        """

    @abstractmethod
    async def batch_upsert(self, materials: List[MaterialCreate], 
                          batch_size: int = 100) -> Dict[str, Any]:
        """Upsert multiple materials in batches (insert or update).
        
        Args:
            materials: List of materials to upsert
            batch_size: Size of processing batches
            
        Returns:
            Batch operation results with created/updated counts
        """


class ICategoriesRepository(ABC):
    """Abstract interface for categories repository."""
    
    @abstractmethod
    async def create(self, name: str, description: Optional[str] = None) -> Category:
        """Create a new category.
        
        Args:
            name: Category name
            description: Optional category description
            
        Returns:
            Created category
        """
    
    @abstractmethod
    async def list(self) -> List[Category]:
        """List all categories.
        
        Returns:
            List of categories
        """
    
    @abstractmethod
    async def delete(self, name: str) -> bool:
        """Delete category.
        
        Args:
            name: Category name
            
        Returns:
            True if deleted successfully
        """


class IUnitsRepository(ABC):
    """Abstract interface for units repository."""
    
    @abstractmethod
    async def create(self, name: str, description: Optional[str] = None) -> Unit:
        """Create a new unit.
        
        Args:
            name: Unit name
            description: Optional unit description
            
        Returns:
            Created unit
        """
    
    @abstractmethod
    async def list(self) -> List[Unit]:
        """List all units.
        
        Returns:
            List of units
        """
    
    @abstractmethod
    async def delete(self, name: str) -> bool:
        """Delete unit.
        
        Args:
            name: Unit name
            
        Returns:
            True if deleted successfully
        """


class IBatchProcessingRepository(ABC):
    """Abstract interface for batch processing repository.
    
    Universal interface for batch processing, progress tracking, and statistics.
    Should be implemented for both vector and relational DBs.
    """

    @abstractmethod
    async def create_processing_records(self, request_id: str, materials: List[Dict[str, Any]]) -> List[str]:
        """Create initial records for batch processing.
        
        Args:
            request_id: Request identifier
            materials: List of materials to process
        
        Returns:
            List of created record IDs
        """

    @abstractmethod
    async def update_processing_status(self, request_id: str, material_id: str, status: str, error: Optional[str] = None) -> bool:
        """Update processing status for a material in a batch.
        
        Args:
            request_id: Request identifier
            material_id: Material identifier
            status: New status
            error: Optional error message
        
        Returns:
            True if update successful
        """

    @abstractmethod
    async def get_processing_progress(self, request_id: str) -> Any:
        """Get processing progress for a batch request.
        
        Args:
            request_id: Request identifier
        
        Returns:
            Progress object (implementation-specific)
        """

    @abstractmethod
    async def get_processing_results(self, request_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Any]:
        """Get processing results for a batch request.
        
        Args:
            request_id: Request identifier
            limit: Optional limit
            offset: Optional offset
        
        Returns:
            List of processing results
        """

    @abstractmethod
    async def get_processing_statistics(self) -> Any:
        """Get overall processing statistics.
        
        Returns:
            Statistics object (implementation-specific)
        """

    @abstractmethod
    async def cleanup_old_records(self, days_old: int = 30) -> int:
        """Cleanup old processing records.
        
        Args:
            days_old: Number of days to keep
        
        Returns:
            Number of deleted records
        """
