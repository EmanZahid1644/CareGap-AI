
"""create identity and organization tables

Revision ID: 80bc2fdf2f85
Revises:
Create Date: 2026-10-20 22:57:56.492207
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "80bc2fdf2f85"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


account_type_enum = postgresql.ENUM(
    "PERSONAL",
    "HOSPITAL",
    name="account_type",
    create_type=False,
)

organization_role_enum = postgresql.ENUM(
    "OWNER",
    "ADMIN",
    "CLINICIAN",
    "REVIEWER",
    "VIEWER",
    name="organization_role",
    create_type=False,
)


def upgrade() -> None:
    """Create identity and organization tables."""

    bind = op.get_bind()

    # Create enum types only if they do not already exist.
    account_type_enum.create(bind, checkfirst=True)
    organization_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_organizations_slug",
        "organizations",
        ["slug"],
        unique=True,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("account_type", account_type_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("role", organization_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "organization_id",
            name="uq_membership_user_organization",
        ),
    )

    op.create_index(
        "ix_organization_memberships_organization_id",
        "organization_memberships",
        ["organization_id"],
        unique=False,
    )

    op.create_index(
        "ix_organization_memberships_user_id",
        "organization_memberships",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop identity and organization tables."""

    op.drop_index(
        "ix_organization_memberships_user_id",
        table_name="organization_memberships",
    )
    op.drop_index(
        "ix_organization_memberships_organization_id",
        table_name="organization_memberships",
    )
    op.drop_table("organization_memberships")

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )
    op.drop_table("users")

    op.drop_index(
        "ix_organizations_slug",
        table_name="organizations",
    )
    op.drop_table("organizations")

    # Remove enum types only after dependent tables are gone.
    organization_role_enum.drop(op.get_bind(), checkfirst=True)
    account_type_enum.drop(op.get_bind(), checkfirst=True)
