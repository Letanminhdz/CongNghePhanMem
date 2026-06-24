"""cleanup and new tables

Revision ID: cleanup_v1
Revises: 0001
Create Date: 2026-06-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cleanup_v1'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop favoritedrug
    op.drop_table("favoritedrug")

    # 2. Create search_history
    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("item_type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_search_history_id"), "search_history", ["id"], unique=False)

    # 3. Create bookmark
    op.create_table(
        "bookmark",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", sa.String(), nullable=False),
        sa.Column("item_neo4j_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_bookmark_id"), "bookmark", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("bookmark")
    op.drop_table("search_history")
    
    # Re-create favoritedrug
    op.create_table(
        "favoritedrug",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("drug_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
