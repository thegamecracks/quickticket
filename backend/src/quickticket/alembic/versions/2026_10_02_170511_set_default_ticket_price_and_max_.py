"""Set default ticket_price and max_attendees

Revision ID: 1e74e162c5ca
Revises: 42673771958f
Create Date: 2026-10-02 17:05:11.043694+00:00

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

from quickticket.models import Base

# revision identifiers, used by Alembic.
revision: str = "1e74e162c5ca"
down_revision: str | Sequence[str] | None = "42673771958f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("event", copy_from=Base.metadata.tables["event"]) as batch_op:
        batch_op.alter_column(
            "ticket_price",
            server_default=text("""'{"amount": 0, "currency": "CAD"}'"""),
        )
        batch_op.alter_column("max_attendees", server_default=text("0"))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("event", copy_from=Base.metadata.tables["event"]) as batch_op:
        batch_op.alter_column("ticket_price", server_default=None)
        batch_op.alter_column("max_attendees", server_default=None)
