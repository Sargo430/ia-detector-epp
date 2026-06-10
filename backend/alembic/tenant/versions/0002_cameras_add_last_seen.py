"""cameras: add last_seen_at column

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cameras",
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cameras",
        sa.Column(
            "stream_status",
            sa.String(20),
            nullable=False,
            server_default="unknown",
        ),
    )
    op.create_index("idx_cameras_stream_status", "cameras", ["stream_status"])


def downgrade() -> None:
    op.drop_index("idx_cameras_stream_status", "cameras")
    op.drop_column("cameras", "stream_status")
    op.drop_column("cameras", "last_seen_at")
