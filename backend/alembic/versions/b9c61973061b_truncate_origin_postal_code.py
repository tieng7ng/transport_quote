"""truncate origin_postal_code

Revision ID: b9c61973061b
Revises: 38a0786708da
Create Date: 2026-01-29 19:21:11.616000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9c61973061b'
down_revision: Union[str, None] = '38a0786708da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update existing data: truncate to 2 characters
    op.execute("UPDATE partner_quotes SET origin_postal_code = SUBSTRING(origin_postal_code, 1, 2) WHERE LENGTH(origin_postal_code) > 2")
    
    # 2. Alter column to VARCHAR(2)
    op.alter_column('partner_quotes', 'origin_postal_code',
               existing_type=sa.VARCHAR(),
               type_=sa.String(length=2),
               existing_nullable=True)


def downgrade() -> None:
    # Revert column to VARCHAR (unspecified length)
    op.alter_column('partner_quotes', 'origin_postal_code',
               existing_type=sa.String(length=2),
               type_=sa.VARCHAR(),
               existing_nullable=True)
