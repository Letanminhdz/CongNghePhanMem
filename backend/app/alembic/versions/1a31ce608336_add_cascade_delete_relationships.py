"""Empty migration (Template Cleanup)

Revision ID: 1a31ce608336
Revises: d98dd8ec85a3
Create Date: 2026-05-24

"""
from alembic import op
import sqlalchemy as sa

revision = '1a31ce608336'
down_revision = 'd98dd8ec85a3'
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
