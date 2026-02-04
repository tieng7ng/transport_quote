"""make_partner_email_nullable

Revision ID: e4a7f2c31d85
Revises: b9c61973061b
Create Date: 2026-02-03 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4a7f2c31d85'
down_revision: Union[str, None] = 'b9c61973061b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('partners', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade() -> None:
    # Set NULL emails to empty string before making NOT NULL
    op.execute("UPDATE partners SET email = '' WHERE email IS NULL")
    op.alter_column('partners', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
