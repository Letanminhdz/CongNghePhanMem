"""Empty migration (Template Cleanup)

Revision ID: e2412789c190
Revises: 0001_create_users
Create Date: 2026-05-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'e2412789c190'
down_revision = '0001_create_users'
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
