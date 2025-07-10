"""005_processing_results_table

Revision ID: 005_processing_results_table
Revises: 002_add_materials_table
Create Date: 2025-01-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_processing_results_table'
down_revision = '002_add_materials_table'
branch_labels = None
depends_on = None


def upgrade():
    """
    Создание таблицы processing_results для batch обработки материалов.
    Этап 8.2: Database schema для асинхронной обработки.
    """
    # Создаем таблицу processing_results
    op.create_table(
        'processing_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=255), nullable=False),
        sa.Column('material_id', sa.String(length=255), nullable=False),
        sa.Column('original_name', sa.String(length=500), nullable=False),
        sa.Column('original_unit', sa.String(length=100), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Дополнительные поля для анализа
        sa.Column('normalized_color', sa.String(length=100), nullable=True),
        sa.Column('normalized_unit', sa.String(length=50), nullable=True),
        sa.Column('unit_coefficient', sa.Float(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('retry_after', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создаем индексы для производительности
    op.create_index(
        'idx_processing_results_request_id',
        'processing_results',
        ['request_id']
    )
    
    op.create_index(
        'idx_processing_results_status',
        'processing_results',
        ['processing_status']
    )
    
    op.create_index(
        'idx_processing_results_material_id',
        'processing_results',
        ['material_id']
    )
    
    # Композитный индекс для поиска по request_id + status
    op.create_index(
        'idx_processing_results_request_status',
        'processing_results',
        ['request_id', 'processing_status']
    )
    
    # Индекс для поиска заданий для retry
    op.create_index(
        'idx_processing_results_retry',
        'processing_results',
        ['processing_status', 'retry_after']
    )
    
    # Индекс для временных запросов
    op.create_index(
        'idx_processing_results_created_at',
        'processing_results',
        ['created_at']
    )
    
    # Создаем триггер для автоматического обновления updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_processing_results_updated_at
        BEFORE UPDATE ON processing_results
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Создаем enum для processing_status (опционально)
    op.execute("""
        CREATE TYPE processing_status_enum AS ENUM ('pending', 'processing', 'completed', 'failed');
    """)
    
    # Создаем constraint для валидации статуса
    op.execute("""
        ALTER TABLE processing_results 
        ADD CONSTRAINT chk_processing_status 
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'));
    """)
    
    # Создаем constraint для валидации similarity_score
    op.execute("""
        ALTER TABLE processing_results 
        ADD CONSTRAINT chk_similarity_score 
        CHECK (similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1));
    """)
    
    # Создаем constraint для валидации retry_count
    op.execute("""
        ALTER TABLE processing_results 
        ADD CONSTRAINT chk_retry_count 
        CHECK (retry_count >= 0 AND retry_count <= 10);
    """)


def downgrade():
    """Удаление таблицы processing_results и связанных объектов."""
    
    # Удаляем триггер
    op.execute("DROP TRIGGER IF EXISTS update_processing_results_updated_at ON processing_results;")
    
    # Удаляем функцию
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Удаляем enum
    op.execute("DROP TYPE IF EXISTS processing_status_enum;")
    
    # Удаляем индексы (они удалятся автоматически с таблицей)
    op.drop_index('idx_processing_results_created_at', table_name='processing_results')
    op.drop_index('idx_processing_results_retry', table_name='processing_results')
    op.drop_index('idx_processing_results_request_status', table_name='processing_results')
    op.drop_index('idx_processing_results_material_id', table_name='processing_results')
    op.drop_index('idx_processing_results_status', table_name='processing_results')
    op.drop_index('idx_processing_results_request_id', table_name='processing_results')
    
    # Удаляем таблицу
    op.drop_table('processing_results') 