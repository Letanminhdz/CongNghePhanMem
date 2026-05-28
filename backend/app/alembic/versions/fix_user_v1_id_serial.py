"""Neutralized fix_user_v1

Revision ID: fix_user_v1
Revises: merge_001
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa

revision = 'fix_user_v1'
down_revision = 'merge_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Logic has been moved to baseline
    pass

def downgrade() -> None:
    pass
