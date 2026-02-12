"""add_login_column_and_enum_role

Revision ID: b343faa2a091
Revises: 5ec4c3702320
Create Date: 2026-02-11 07:53:50.220957

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b343faa2a091'
down_revision: Union[str, None] = '5ec4c3702320'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add login column as nullable first to allow data migration
    op.add_column('users', sa.Column('login', sa.String(), nullable=True))
    
    # 2. Populate login from email (take the part before @)
    op.execute("UPDATE users SET login = split_part(email, '@', 1)")
    
    # 2b. Handle duplicates: append suffix for colliding logins
    op.execute("""
        UPDATE users u1 
        SET login = u1.login || '_' || substr(u1.id::text, 1, 4) 
        WHERE u1.id IN (
            SELECT id FROM users WHERE login IN (
                SELECT login FROM users GROUP BY login HAVING count(*) > 1
            )
        )
    """)
    
    # 3. Alter login to be not nullable
    op.alter_column('users', 'login', nullable=False)
    
    # 4. Create index
    op.create_index(op.f('ix_users_login'), 'users', ['login'], unique=True)

    # 5. Handle Enum for role
    # Create the enum type explicitly in PostgreSQL
    user_role_enum = sa.Enum('SUPER_ADMIN', 'ADMIN', 'COMMERCIAL', 'OPERATOR', 'VIEWER', name='userrole')
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # Alter column to use the new Enum type
    op.alter_column('users', 'role',
               existing_type=sa.VARCHAR(),
               type_=user_role_enum,
               existing_nullable=False,
               postgresql_using="role::userrole")


def downgrade() -> None:
    # 1. Revert role to String
    op.alter_column('users', 'role',
               existing_type=sa.Enum('SUPER_ADMIN', 'ADMIN', 'COMMERCIAL', 'OPERATOR', 'VIEWER', name='userrole'),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    
    # 2. Drop Enum type
    user_role_enum = sa.Enum('SUPER_ADMIN', 'ADMIN', 'COMMERCIAL', 'OPERATOR', 'VIEWER', name='userrole')
    user_role_enum.drop(op.get_bind(), checkfirst=True)

    # 3. Drop login index and column
    op.drop_index(op.f('ix_users_login'), table_name='users')
    op.drop_column('users', 'login')
