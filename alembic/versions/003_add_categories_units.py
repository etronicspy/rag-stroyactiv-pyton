"""Add categories, units and raw_products tables

Revision ID: 003_reference_tables
Revises: 002_materials
Create Date: 2024-12-19 15:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_reference_tables'
down_revision: Union[str, None] = '002_materials'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema.
    
    Создает справочные таблицы categories, units и таблицу raw_products.
    """
    # Create categories reference table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # Foreign key for hierarchical structure
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
    )
    
    # Create units reference table
    op.create_table(
        'units',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit_type', sa.String(50), nullable=False),  # weight, volume, length, etc.
        sa.Column('base_unit_id', sa.Integer(), nullable=True),  # For unit conversions
        sa.Column('conversion_factor', sa.Numeric(15, 6), nullable=True),  # To base unit
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        # Foreign key for base unit relationship
        sa.ForeignKeyConstraint(['base_unit_id'], ['units.id'], ondelete='SET NULL'),
    )
    
    # Create raw_products table
    op.create_table(
        'raw_products',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, nullable=False),
        
        # Core product information
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('use_category', sa.String(200), nullable=True),
        
        # Supplier information
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('pricelistid', sa.Integer(), nullable=False),
        
        # Pricing information
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('unit_price_currency', sa.String(3), nullable=False, default='RUB'),
        sa.Column('unit_calc_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('unit_calc_price_currency', sa.String(3), nullable=False, default='RUB'),
        sa.Column('buy_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('buy_price_currency', sa.String(3), nullable=False, default='RUB'),
        sa.Column('sale_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('sale_price_currency', sa.String(3), nullable=False, default='RUB'),
        
        # Units and quantities
        sa.Column('calc_unit', sa.String(100), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        
        # Processing status
        sa.Column('is_processed', sa.Boolean(), nullable=False, default=False),
        
        # Vector embedding for semantic search
        sa.Column('embedding', postgresql.ARRAY(postgresql.REAL), nullable=True),
        
        # Timestamps
        sa.Column('created', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('modified', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('upload_date', sa.DateTime(), nullable=True),
        sa.Column('date_price_change', sa.DateTime(), nullable=True),
    )
    
    # Create indexes for categories
    op.create_index('idx_categories_name', 'categories', ['name'])
    op.create_index('idx_categories_parent', 'categories', ['parent_id'])
    op.create_index('idx_categories_active', 'categories', ['is_active'])
    
    # Create indexes for units
    op.create_index('idx_units_name', 'units', ['name'])
    op.create_index('idx_units_symbol', 'units', ['symbol'])
    op.create_index('idx_units_type', 'units', ['unit_type'])
    op.create_index('idx_units_active', 'units', ['is_active'])
    
    # Create indexes for raw_products
    op.create_index('idx_raw_products_name', 'raw_products', ['name'])
    op.create_index('idx_raw_products_sku', 'raw_products', ['sku'])
    op.create_index('idx_raw_products_category', 'raw_products', ['use_category'])
    op.create_index('idx_raw_products_supplier_pricelist', 'raw_products', ['supplier_id', 'pricelistid'])
    op.create_index('idx_raw_products_processed', 'raw_products', ['is_processed'])
    
    # GIN index for product name search
    op.create_index(
        'idx_raw_products_name_gin',
        'raw_products',
        ['name'],
        postgresql_using='gin',
        postgresql_ops={'name': 'gin_trgm_ops'}
    )
    
    # Create triggers for updated_at columns
    op.execute("""
        CREATE TRIGGER update_categories_updated_at
        BEFORE UPDATE ON categories
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_units_updated_at
        BEFORE UPDATE ON units
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create trigger for raw_products modified column
    op.execute("""
        CREATE OR REPLACE FUNCTION update_modified_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.modified = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER update_raw_products_modified
        BEFORE UPDATE ON raw_products
        FOR EACH ROW
        EXECUTE FUNCTION update_modified_column();
    """)


def downgrade() -> None:
    """Downgrade database schema.
    
    Удаляет справочные таблицы и таблицу raw_products.
    """
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_raw_products_modified ON raw_products")
    op.execute("DROP TRIGGER IF EXISTS update_units_updated_at ON units")
    op.execute("DROP TRIGGER IF EXISTS update_categories_updated_at ON categories")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_modified_column()")
    
    # Drop tables (order matters due to foreign keys)
    op.drop_table('raw_products')
    op.drop_table('units')
    op.drop_table('categories') 