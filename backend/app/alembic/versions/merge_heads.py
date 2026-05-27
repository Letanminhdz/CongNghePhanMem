"""Merge multiple heads into single lineage

Revision ID: merge_001
Revises: 0001_create_users, fe56fa70289e
Create Date: 2026-05-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "merge_001"
down_revision = ("0001_create_users", "fe56fa70289e")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration that reconciles the two separate branches
    # No schema changes needed, just declares the merge
    pass


def downgrade() -> None:
    pass
