"""Empty init (Template Cleanup)

Revision ID: 0001_create_users
Revises: None
Create Date: 2026-05-23

"""
from alembic import op
import sqlalchemy as sa

revision = "0001_create_users"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # This migration used to create 'users' table but is now disabled
    # to avoid conflict with the new baseline.
    pass

def downgrade() -> None:
    pass
