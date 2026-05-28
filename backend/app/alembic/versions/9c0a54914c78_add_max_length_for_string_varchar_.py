"""Empty migration (Template Cleanup)

Revision ID: 9c0a54914c78
Revises: e2412789c190
Create Date: 2026-05-24

"""
from alembic import op
import sqlalchemy as sa

revision = '9c0a54914c78'
down_revision = 'e2412789c190'
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
