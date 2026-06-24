"""Empty migration (Template Cleanup)

Revision ID: fe56fa70289e
Revises: 1a31ce608336
Create Date: 2026-05-24

"""
from alembic import op
import sqlalchemy as sa

revision = 'fe56fa70289e'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
