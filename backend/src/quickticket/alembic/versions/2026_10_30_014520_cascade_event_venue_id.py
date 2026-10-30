"""Cascade event.venue_id

Revision ID: 24794a619d1b
Revises: aaa598e616f8
Create Date: 2026-10-30 01:45:20.197648+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "24794a619d1b"
down_revision: str | Sequence[str] | None = "aaa598e616f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_event_venue_id_venue"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_event_venue_id_venue"),
            "venue",
            ["venue_id"],
            ["venue_id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_event_venue_id_venue"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_event_venue_id_venue"), "venue", ["venue_id"], ["venue_id"]
        )
