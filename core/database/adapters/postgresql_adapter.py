"""PostgreSQL database adapter implementation.

Адаптер для работы с PostgreSQL БД.
"""

from typing import List, Dict, Any, Optional
from core.logging import get_logger
from datetime import datetime
import uuid
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, DateTime, Text, Integer, Numeric, Boolean, Index, func, or_
from sqlalchemy.dialects.postgresql import UUID, ARRAY, REAL
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from core.database.interfaces import IRelationalDatabase
from core.database.exceptions import ConnectionError, QueryError, DatabaseError, TransactionError
from core.config import Settings
from services.ssh_tunnel_service import get_tunnel_service


logger = get_logger(__name__)

# SQLAlchemy Base
Base = declarative_base()


class MaterialModel(Base):
    """SQLAlchemy model for materials table.
    
    Модель материалов с поддержкой полнотекстового поиска и векторных эмбеддингов.
    """
    __tablename__ = "materials"
    
    # Primary fields
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    use_category: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Vector embedding for semantic search (pgvector support)
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(REAL), nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Full-text search support
    search_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Will use PostgreSQL tsvector
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_materials_name_gin', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('idx_materials_description_gin', 'description', postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'}),
        Index('idx_materials_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_materials_category_unit', 'use_category', 'unit'),
    )


class RawProductModel(Base):
    """SQLAlchemy model for raw products from supplier price lists.
    
    Модель сырых продуктов из прайс-листов поставщиков.
    """
    __tablename__ = "raw_products"
    
    # Primary fields
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    use_category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    
    # Supplier information
    supplier_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    pricelistid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Pricing information
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    unit_price_currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    unit_calc_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    unit_calc_price_currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    buy_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    buy_price_currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    sale_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    sale_price_currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    
    # Units and quantities
    calc_unit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Vector embedding
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(REAL), nullable=True)
    
    # Timestamps
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    modified: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    upload_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    date_price_change: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_raw_products_supplier_pricelist', 'supplier_id', 'pricelistid'),
        Index('idx_raw_products_name_gin', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('idx_raw_products_processed', 'is_processed'),
    )


class PostgreSQLAdapter(IRelationalDatabase):
    """PostgreSQL adapter with SSH tunnel integration."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = None
        self.session_factory = None
        self._connection_string = None
        self._tunnel_service = None
        
    async def connect(self) -> bool:
        """Connect to PostgreSQL with automatic SSH tunnel detection."""
        try:
            # Check if SSH tunnel is available and active
            self._tunnel_service = get_tunnel_service()
            if self._tunnel_service and self._tunnel_service.is_tunnel_active():
                logger.info("Using active SSH tunnel for PostgreSQL connection")
                # Use tunnel local port for connection
                tunnel_config = self._tunnel_service.config
                connection_string = (
                    f"postgresql+asyncpg://{self.settings.POSTGRESQL_USER}:"
                    f"{self.settings.POSTGRESQL_PASSWORD}@localhost:"
                    f"{tunnel_config.local_port}/{self.settings.POSTGRESQL_DATABASE}"
                )
            else:
                logger.info("No active SSH tunnel found, using direct PostgreSQL connection")
                # Use direct connection
                connection_string = (
                    f"postgresql+asyncpg://{self.settings.POSTGRESQL_USER}:"
                    f"{self.settings.POSTGRESQL_PASSWORD}@{self.settings.POSTGRESQL_HOST}:"
                    f"{self.settings.POSTGRESQL_PORT}/{self.settings.POSTGRESQL_DATABASE}"
                )
            
            self._connection_string = connection_string
            
            # Create engine with connection pooling
            self.engine = create_async_engine(
                connection_string,
                pool_size=getattr(self.settings, 'POSTGRESQL_POOL_SIZE', 10),
                max_overflow=getattr(self.settings, 'POSTGRESQL_MAX_OVERFLOW', 20),
                pool_timeout=getattr(self.settings, 'POSTGRESQL_POOL_TIMEOUT', 30),
                pool_recycle=getattr(self.settings, 'POSTGRESQL_POOL_RECYCLE', 3600),
                echo=self.settings.LOG_LEVEL == "DEBUG",
                future=True
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            logger.info("PostgreSQL connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            await self.disconnect()
            raise ConnectionError("postgresql", f"PostgreSQL connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            logger.info("PostgreSQL connection closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        if not self.engine:
            return {
                "status": "error",
                "message": "No database connection",
                "tunnel_status": "unknown"
            }
        
        try:
            # Check database connection
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT version(), current_database(), current_user"))
                version_info = result.fetchone()
            
            # Check tunnel status
            tunnel_status = "not_used"
            if self._tunnel_service:
                if self._tunnel_service.is_tunnel_active():
                    tunnel_status = "active"
                else:
                    tunnel_status = "inactive"
            
            return {
                "status": "healthy",
                "database": version_info[1] if version_info else None,
                "user": version_info[2] if version_info else None,
                "version": version_info[0] if version_info else None,
                "tunnel_status": tunnel_status,
                "connection_type": "tunneled" if tunnel_status == "active" else "direct"
            }
            
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "tunnel_status": "unknown"
            }
    
    async def create_tables(self) -> None:
        """Create all database tables.
        
        Создает все таблицы БД и необходимые расширения PostgreSQL.
        
        Raises:
            DatabaseError: If table creation fails
        """
        try:
            async with self.engine.begin() as conn:
                # Enable required PostgreSQL extensions
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))  # Trigram similarity
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gin"))  # GIN indexes
                
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("PostgreSQL tables created successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create PostgreSQL tables: {e}")
            raise DatabaseError(
                message="Failed to create database tables",
                details=str(e)
            )
    
    async def drop_tables(self) -> None:
        """Drop all database tables.
        
        Удаляет все таблицы БД (используется для тестирования).
        
        Raises:
            DatabaseError: If table dropping fails
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                
            logger.info("PostgreSQL tables dropped successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop PostgreSQL tables: {e}")
            raise DatabaseError(
                message="Failed to drop database tables",
                details=str(e)
            )
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session with automatic cleanup.
        
        Контекстный менеджер для работы с сессией БД.
        
        Yields:
            AsyncSession: Database session
            
        Raises:
            ConnectionError: If session creation fails
        """
        try:
            async with self.session_factory() as session:
                yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}")
            raise ConnectionError(
                database_type="PostgreSQL",
                message="Database session error",
                details=str(e)
            )
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query results as list of dictionaries
            
        Raises:
            QueryError: If query execution fails
        """
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                
                # Convert result to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryError(
                message="Failed to execute query",
                details=str(e),
                query=query
            )
    
    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute SQL command (INSERT, UPDATE, DELETE).
        
        Args:
            command: SQL command
            params: Command parameters
            
        Returns:
            Number of affected rows
            
        Raises:
            QueryError: If command execution fails
        """
        try:
            async with self.get_session() as session:
                result = await session.execute(text(command), params or {})
                await session.commit()
                
                return result.rowcount
                
        except SQLAlchemyError as e:
            logger.error(f"Command execution failed: {e}")
            raise QueryError(
                message="Failed to execute command",
                details=str(e),
                query=command
            )
    
    @asynccontextmanager
    async def begin_transaction(self):
        """Begin database transaction as async context manager.
        
        Yields:
            AsyncSession: Transaction session
            
        Raises:
            TransactionError: If transaction start fails
        """
        session = None
        try:
            session = self.session_factory()
            # Транзакция начинается автоматически при создании сессии
            yield session
            await session.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Transaction failed: {e}")
            if session:
                await session.rollback()
            raise TransactionError(
                message="Transaction failed",
                details=str(e)
            )
        finally:
            if session:
                await session.close()
    

    
    # === Material-specific methods ===
    
    async def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new material in PostgreSQL.
        
        Args:
            material_data: Material data dictionary
            
        Returns:
            Created material data
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            async with self.get_session() as session:
                # Prepare search vector for full-text search
                search_text = f"{material_data.get('name', '')} {material_data.get('description', '')} {material_data.get('use_category', '')}"
                
                material = MaterialModel(
                    id=material_data.get('id', str(uuid.uuid4())),
                    name=material_data['name'],
                    use_category=material_data['use_category'],
                    unit=material_data['unit'],
                    sku=material_data.get('sku'),
                    description=material_data.get('description'),
                    embedding=material_data.get('embedding'),
                    search_vector=search_text,
                    created_at=material_data.get('created_at', datetime.utcnow()),
                    updated_at=material_data.get('updated_at', datetime.utcnow())
                )
                
                session.add(material)
                await session.commit()
                await session.refresh(material)
                
                logger.info(f"Material created in PostgreSQL: {material.name} (ID: {material.id})")
                
                return {
                    'id': material.id,
                    'name': material.name,
                    'use_category': material.use_category,
                    'unit': material.unit,
                    'sku': material.sku,
                    'description': material.description,
                    'embedding': material.embedding,
                    'created_at': material.created_at,
                    'updated_at': material.updated_at
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create material in PostgreSQL: {e}")
            raise DatabaseError(
                message="Failed to create material",
                details=str(e)
            )
    
    async def search_materials_hybrid(
        self, 
        query: str, 
        limit: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Hybrid search: full-text + trigram similarity.
        
        Гибридный поиск материалов с использованием полнотекстового поиска и триграммного сходства.
        
        Args:
            query: Search query
            limit: Maximum results
            similarity_threshold: Minimum similarity threshold (0.0-1.0)
            
        Returns:
            List of matching materials with similarity scores
            
        Raises:
            QueryError: If search fails
        """
        try:
            async with self.get_session() as session:
                # Hybrid search query combining multiple approaches
                search_query = select(
                    MaterialModel,
                    # Trigram similarity scores
                    func.similarity(MaterialModel.name, query).label('name_similarity'),
                    func.similarity(MaterialModel.description, query).label('desc_similarity'),
                    # Combined similarity score
                    (
                        func.similarity(MaterialModel.name, query) * 0.6 +
                        func.similarity(MaterialModel.description, query) * 0.3 +
                        func.similarity(MaterialModel.use_category, query) * 0.1
                    ).label('total_similarity')
                ).where(
                    or_(
                        # Trigram similarity
                        func.similarity(MaterialModel.name, query) > similarity_threshold,
                        func.similarity(MaterialModel.description, query) > similarity_threshold,
                        # ILIKE for partial matches
                        MaterialModel.name.ilike(f'%{query}%'),
                        MaterialModel.description.ilike(f'%{query}%'),
                        MaterialModel.use_category.ilike(f'%{query}%'),
                        MaterialModel.sku.ilike(f'%{query}%')
                    )
                ).order_by(
                    text('total_similarity DESC')
                ).limit(limit)
                
                result = await session.execute(search_query)
                rows = result.fetchall()
                
                materials = []
                for row in rows:
                    material = row[0]  # MaterialModel instance
                    name_sim = row[1]
                    desc_sim = row[2]
                    total_sim = row[3]
                    
                    materials.append({
                        'id': material.id,
                        'name': material.name,
                        'use_category': material.use_category,
                        'unit': material.unit,
                        'sku': material.sku,
                        'description': material.description,
                        'embedding': material.embedding,
                        'created_at': material.created_at,
                        'updated_at': material.updated_at,
                        'similarity_score': float(total_sim) if total_sim else 0.0,
                        'name_similarity': float(name_sim) if name_sim else 0.0,
                        'description_similarity': float(desc_sim) if desc_sim else 0.0
                    })
                
                logger.info(f"Hybrid search found {len(materials)} materials for query: '{query}'")
                return materials
                
        except SQLAlchemyError as e:
            logger.error(f"Hybrid search failed: {e}")
            raise QueryError(
                message="Hybrid search failed",
                details=str(e),
                query=query
            )
    
    async def get_materials(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get materials with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            category: Filter by category
            
        Returns:
            List of materials
            
        Raises:
            QueryError: If query fails
        """
        try:
            async with self.get_session() as session:
                query = select(MaterialModel)
                
                if category:
                    query = query.where(MaterialModel.use_category.ilike(f'%{category}%'))
                
                query = query.offset(skip).limit(limit).order_by(MaterialModel.created_at.desc())
                
                result = await session.execute(query)
                materials = result.scalars().all()
                
                return [
                    {
                        'id': material.id,
                        'name': material.name,
                        'use_category': material.use_category,
                        'unit': material.unit,
                        'sku': material.sku,
                        'description': material.description,
                        'embedding': material.embedding,
                        'created_at': material.created_at,
                        'updated_at': material.updated_at
                    }
                    for material in materials
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get materials: {e}")
            raise QueryError(
                message="Failed to get materials",
                details=str(e)
            )
    
    async def close(self) -> None:
        """Close database connections.
        
        Закрывает все соединения с БД.
        """
        try:
            await self.engine.dispose()
            logger.info("PostgreSQL connections closed")
            
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connections: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close() 