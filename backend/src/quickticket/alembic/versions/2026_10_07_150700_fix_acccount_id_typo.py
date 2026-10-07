"""Fix acccount_id typo

Revision ID: e9e0aab32c4f
Revises: d8f0a832401c
Create Date: 2026-10-07 15:07:00.072597+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e9e0aab32c4f"
down_revision: str | Sequence[str] | None = "d8f0a832401c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("organization_member", schema=None) as batch_op:
        batch_op.alter_column("acccount_id", new_column_name="account_id")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("organization_member", schema=None) as batch_op:
        batch_op.alter_column("account_id", new_column_name="acccount_id")
