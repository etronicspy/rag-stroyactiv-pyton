"""Initial schema and PostgreSQL extensions

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-19 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema.
    
    Создает необходимые расширения PostgreSQL для полнотекстового поиска и GIN индексов.
    """
    # Enable PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")  # Trigram similarity
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")  # GIN indexes for composite searches
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")  # Remove accents for better search
    
    # Create custom types if needed
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'material_status') THEN
                CREATE TYPE material_status AS ENUM ('active', 'inactive', 'discontinued');
            END IF;
        END$$;
    """)


def downgrade() -> None:
    """Downgrade database schema.
    
    Удаляет созданные расширения и типы (осторожно в продакшене!).
    """
    # Drop custom types
    op.execute("DROP TYPE IF EXISTS material_status CASCADE")
    
    # Note: We don't drop extensions in downgrade as they might be used by other applications
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    # op.execute("DROP EXTENSION IF EXISTS btree_gin") 
    # op.execute("DROP EXTENSION IF EXISTS unaccent") 