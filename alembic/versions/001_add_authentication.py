"""
Alembic migration: Add authentication tables

Create this file as: alembic/versions/001_add_authentication.py
Run with: alembic upgrade head
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.String(30), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])

    # Create api_tokens table
    op.create_table(
        'api_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_api_tokens_user_id', 'api_tokens', ['user_id'])
    op.create_index('idx_api_tokens_token_hash', 'api_tokens', ['token_hash'])

    # Delete all existing sessions (clean start)
    op.execute('DELETE FROM sessions')

    # Drop the old user_id column (String type)
    op.drop_column('sessions', 'user_id')

    # Add new user_id column with UUID type
    op.add_column('sessions', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.create_foreign_key('fk_sessions_user_id', 'sessions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])


def downgrade():
    # Remove user_id from sessions
    op.drop_index('idx_sessions_user_id', 'sessions')
    op.drop_constraint('fk_sessions_user_id', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'user_id')

    # Restore old user_id column
    op.add_column('sessions', sa.Column('user_id', sa.String(100), nullable=False))
    op.create_index('idx_sessions_user_id_old', 'sessions', ['user_id'])

    # Drop api_tokens table
    op.drop_index('idx_api_tokens_token_hash', 'api_tokens')
    op.drop_index('idx_api_tokens_user_id', 'api_tokens')
    op.drop_table('api_tokens')

    # Drop users table
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_username', 'users')
    op.drop_table('users')