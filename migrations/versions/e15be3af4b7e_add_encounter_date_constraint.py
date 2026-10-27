
"""add encounter date constraint

Revision ID: e15be3af4b7e
Revises: 1decfa8bf45e
Create Date: 2026-10-22 21:40:36.960251
"""

from typing import Sequence, Union

from alembic import op


# Revision identifiers used by Alembic.
revision: str = "e15be3af4b7e"
down_revision: Union[str, Sequence[str], None] = "1decfa8bf45e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Prevent discharge dates earlier than admission dates."""

    op.create_check_constraint(
        "ck_encounters_discharge_not_before_admission",
        "encounters",
        "discharge_date IS NULL OR admission_date IS NULL "
        "OR discharge_date >= admission_date",
    )


def downgrade() -> None:
    """Remove encounter date consistency constraint."""

    op.drop_constraint(
        "ck_encounters_discharge_not_before_admission",
        "encounters",
        type_="check",
    )
