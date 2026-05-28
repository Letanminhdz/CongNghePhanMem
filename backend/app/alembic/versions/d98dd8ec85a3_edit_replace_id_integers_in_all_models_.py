"""Empty migration (UUID Removal Cleanup)

Revision ID: d98dd8ec85a3
Revises: 9c0a54914c78
Create Date: 2024-07-19

"""
from alembic import op
import sqlalchemy as sa

revision = 'd98dd8ec85a3'
down_revision = '9c0a54914c78'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Removed all UUID conversion logic to use Integer IDs exclusively
    pass

def downgrade() -> None:
    pass
