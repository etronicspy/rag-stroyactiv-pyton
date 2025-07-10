"""Add materials table

Revision ID: 002_materials
Revises: 001_initial
Create Date: 2024-12-19 15:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_materials'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema.
    
    Создает таблицу materials с поддержкой векторного поиска и полнотекстового поиска.
    Включает расширенные поля для парсинга и нормализации: color, normalized_color, 
    normalized_parsed_unit, unit_coefficient.
    """
    # Create materials table
    op.create_table(
        'materials',
        # Primary key and core fields
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('use_category', sa.String(200), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('sku', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Enhanced material fields for parsing and normalization
        sa.Column('color', sa.String(100), nullable=True),
        sa.Column('normalized_color', sa.String(100), nullable=True),
        sa.Column('normalized_parsed_unit', sa.String(50), nullable=True),
        sa.Column('unit_coefficient', sa.Float(), nullable=True),
        
        # Vector embedding for semantic search
        sa.Column('embedding', postgresql.ARRAY(postgresql.REAL), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # Full-text search support
        sa.Column('search_vector', sa.Text(), nullable=True),
    )
    
    # Create indexes for performance
    # Basic indexes
    op.create_index('idx_materials_name', 'materials', ['name'])
    op.create_index('idx_materials_category', 'materials', ['use_category'])
    op.create_index('idx_materials_sku', 'materials', ['sku'], unique=True)
    op.create_index('idx_materials_category_unit', 'materials', ['use_category', 'unit'])
    
    # Enhanced search indexes
    op.create_index('idx_materials_color', 'materials', ['color'])
    op.create_index('idx_materials_normalized_color', 'materials', ['normalized_color'])
    op.create_index('idx_materials_normalized_unit', 'materials', ['normalized_parsed_unit'])
    op.create_index('idx_materials_unit_coefficient', 'materials', ['unit_coefficient'])
    
    # GIN indexes for full-text search using trigrams
    op.create_index(
        'idx_materials_name_gin', 
        'materials', 
        ['name'], 
        postgresql_using='gin',
        postgresql_ops={'name': 'gin_trgm_ops'}
    )
    
    op.create_index(
        'idx_materials_description_gin', 
        'materials', 
        ['description'], 
        postgresql_using='gin',
        postgresql_ops={'description': 'gin_trgm_ops'}
    )
    
    # GIN index for full-text search vector
    op.create_index(
        'idx_materials_search_vector',
        'materials',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Create trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER update_materials_updated_at
        BEFORE UPDATE ON materials
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create trigger for search_vector update
    op.execute("""
        CREATE OR REPLACE FUNCTION update_material_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector = to_tsvector('russian', 
                COALESCE(NEW.name, '') || ' ' || 
                COALESCE(NEW.description, '') || ' ' ||
                COALESCE(NEW.use_category, '') || ' ' ||
                COALESCE(NEW.sku, '') || ' ' ||
                COALESCE(NEW.color, '') || ' ' ||
                COALESCE(NEW.normalized_color, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER update_materials_search_vector
        BEFORE INSERT OR UPDATE ON materials
        FOR EACH ROW
        EXECUTE FUNCTION update_material_search_vector();
    """)


def downgrade() -> None:
    """Downgrade database schema.
    
    Удаляет таблицу materials и связанные функции/триггеры.
    """
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_materials_search_vector ON materials")
    op.execute("DROP TRIGGER IF EXISTS update_materials_updated_at ON materials")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_material_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop table (this will also drop all indexes)
    op.drop_table('materials') 