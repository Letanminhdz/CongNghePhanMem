"""baseline

Revision ID: 0001
Revises: fix_user_v1
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = 'fix_user_v1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. User table
    if "user" not in tables:
        op.create_table(
            "user",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("full_name", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
            sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
        op.create_index(op.f("ix_user_id"), "user", ["id"], unique=False)

    # 2. FavoriteDrug table
    if "favoritedrug" not in tables:
        op.create_table(
            "favoritedrug",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
            sa.Column("drug_name", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index(op.f("ix_favoritedrug_id"), "favoritedrug", ["id"], unique=False)

    # 3. ChatHistory table
    if "chathistory" not in tables:
        op.create_table(
            "chathistory",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("response", sa.Text(), nullable=False),
            sa.Column("intent", sa.String(), nullable=True),
            sa.Column("entities", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id")
        )
        op.create_index(op.f("ix_chathistory_id"), "chathistory", ["id"], unique=False)
        op.create_index(op.f("ix_chathistory_intent"), "chathistory", ["intent"], unique=False)


def downgrade() -> None:
    op.drop_table("chathistory")
    op.drop_table("favoritedrug")
    op.drop_table("user")
