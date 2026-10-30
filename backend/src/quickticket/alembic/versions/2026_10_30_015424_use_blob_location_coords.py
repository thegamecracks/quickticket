"""Use BLOB location_coords

Revision ID: fa34b8ca35c5
Revises: 24794a619d1b
Create Date: 2026-10-30 01:54:24.540811+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fa34b8ca35c5"
down_revision: str | Sequence[str] | None = "24794a619d1b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("venue", schema=None) as batch_op:
        batch_op.drop_column("location_coords")
        batch_op.add_column(sa.Column("location_coords", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("venue", schema=None) as batch_op:
        batch_op.drop_column("location_coords")
        batch_op.add_column(sa.Column("location_coords", sa.JSON(), nullable=True))
