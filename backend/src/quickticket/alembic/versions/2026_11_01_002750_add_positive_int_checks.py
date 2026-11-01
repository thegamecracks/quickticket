"""Add positive int checks

Revision ID: e17db4e9cdbb
Revises: fdfc0b2c57f5
Create Date: 2026-11-01 00:27:50.076664+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e17db4e9cdbb"
down_revision: str | Sequence[str] | None = "fdfc0b2c57f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("event") as batch_op:
        batch_op.create_check_constraint("max_attendees_positive", "max_attendees >= 0")
    with op.batch_alter_table("storage_object") as batch_op:
        batch_op.create_check_constraint("filesize_positive", "filesize >= 0")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("event") as batch_op:
        batch_op.drop_constraint("max_attendees_positive", type_="check")
    with op.batch_alter_table("storage_object") as batch_op:
        batch_op.drop_constraint("filesize_positive", type_="check")
