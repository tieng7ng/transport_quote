"""Add user_activity_logs and security_alerts tables

Revision ID: a1b2c3d4e5f6
Revises: b343faa2a091
Create Date: 2026-02-24 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'b343faa2a091'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Table user_activity_logs ---
    op.create_table(
        'user_activity_logs',
        sa.Column('id',          UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id',     UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_login',  sa.String(100),  nullable=True),
        sa.Column('user_role',   sa.String(50),   nullable=True),
        sa.Column('action',      sa.String(100),  nullable=False),
        sa.Column('resource',    sa.String(50),   nullable=True),
        sa.Column('resource_id', sa.String(100),  nullable=True),
        sa.Column('details',     JSONB,            nullable=True, server_default='{}'),
        sa.Column('ip_address',  sa.String(45),   nullable=True),
        sa.Column('created_at',  sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_activity_user_id',    'user_activity_logs', ['user_id'])
    op.create_index('idx_activity_action',     'user_activity_logs', ['action'])
    op.create_index('idx_activity_created_at', 'user_activity_logs', [sa.text('created_at DESC')],
                    postgresql_using='btree')
    op.create_index('idx_activity_resource',   'user_activity_logs', ['resource', 'resource_id'])

    # --- Table security_alerts ---
    op.create_table(
        'security_alerts',
        sa.Column('id',          UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('type',        sa.String(50),   nullable=True),
        sa.Column('severity',    sa.String(20),   nullable=True),
        sa.Column('details',     JSONB,            nullable=True, server_default='{}'),
        sa.Column('seen_at',     sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution',  sa.String(100),  nullable=True),
        sa.Column('created_at',  sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    # --- Vues SQL ---
    op.execute("""
        CREATE VIEW daily_activity AS
        SELECT DATE(created_at) AS day, action,
               COUNT(*) AS total, COUNT(DISTINCT user_id) AS unique_users
        FROM user_activity_logs
        GROUP BY DATE(created_at), action;
    """)

    op.execute("""
        CREATE VIEW top_search_routes AS
        SELECT
            details->>'origin_city'    AS origin,
            details->>'dest_city'      AS destination,
            details->>'transport_mode' AS mode,
            COUNT(*) AS search_count,
            AVG((details->>'results_count')::int) AS avg_results
        FROM user_activity_logs
        WHERE action = 'search.performed'
        GROUP BY details->>'origin_city', details->>'dest_city', details->>'transport_mode'
        ORDER BY search_count DESC;
    """)

    op.execute("""
        CREATE VIEW quote_performance_by_user AS
        SELECT user_login, user_role,
               COUNT(*) FILTER (WHERE action = 'quote.created') AS quotes_created,
               COUNT(*) FILTER (WHERE action = 'quote.status_changed'
                   AND details->>'new_status' = 'SENT')         AS quotes_sent,
               COUNT(*) FILTER (WHERE action = 'quote.status_changed'
                   AND details->>'new_status' = 'ACCEPTED')     AS quotes_accepted
        FROM user_activity_logs
        WHERE action IN ('quote.created', 'quote.status_changed')
        GROUP BY user_login, user_role;
    """)

    op.execute("""
        CREATE VIEW login_failure_rate AS
        SELECT DATE(created_at) AS day,
               details->>'attempted_login' AS login,
               ip_address,
               COUNT(*) FILTER (WHERE action = 'auth.login_failed') AS failures,
               COUNT(*) FILTER (WHERE action = 'auth.login_success') AS successes
        FROM user_activity_logs
        WHERE action IN ('auth.login_failed', 'auth.login_success')
        GROUP BY DATE(created_at), details->>'attempted_login', ip_address;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS login_failure_rate")
    op.execute("DROP VIEW IF EXISTS quote_performance_by_user")
    op.execute("DROP VIEW IF EXISTS top_search_routes")
    op.execute("DROP VIEW IF EXISTS daily_activity")
    op.drop_table('security_alerts')
    op.drop_index('idx_activity_resource',   table_name='user_activity_logs')
    op.drop_index('idx_activity_created_at', table_name='user_activity_logs')
    op.drop_index('idx_activity_action',     table_name='user_activity_logs')
    op.drop_index('idx_activity_user_id',    table_name='user_activity_logs')
    op.drop_table('user_activity_logs')
