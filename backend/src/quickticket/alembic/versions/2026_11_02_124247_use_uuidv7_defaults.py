"""Use uuidv7 defaults

Revision ID: 42b681b50585
Revises: e17db4e9cdbb
Create Date: 2026-11-02 12:42:47.314797+00:00

"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision: str = "42b681b50585"
down_revision: str | Sequence[str] | None = "e17db4e9cdbb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.alter_column("account", "account_id", server_default=func.uuidv7())
    op.alter_column("address", "address_id", server_default=func.uuidv7())
    op.alter_column("notification", "notification_id", server_default=func.uuidv7())
    op.alter_column("event", "event_id", server_default=func.uuidv7())
    op.alter_column("organization", "organization_id", server_default=func.uuidv7())
    op.alter_column("storage_provider", "storage_provider_id", server_default=func.uuidv7())
    op.alter_column("storage_object", "storage_object_id", server_default=func.uuidv7())
    op.alter_column("ticket", "ticket_id", server_default=func.uuidv7())
    op.alter_column("venue", "venue_id", server_default=func.uuidv7())


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.alter_column("account", "account_id", server_default=func.uuidv4())
    op.alter_column("address", "address_id", server_default=func.uuidv4())
    op.alter_column("notification", "notification_id", server_default=func.uuidv4())
    op.alter_column("event", "event_id", server_default=func.uuidv4())
    op.alter_column("organization", "organization_id", server_default=func.uuidv4())
    op.alter_column("storage_provider", "storage_provider_id", server_default=func.uuidv4())
    op.alter_column("storage_object", "storage_object_id", server_default=func.uuidv4())
    op.alter_column("ticket", "ticket_id", server_default=func.uuidv4())
    op.alter_column("venue", "venue_id", server_default=func.uuidv4())
