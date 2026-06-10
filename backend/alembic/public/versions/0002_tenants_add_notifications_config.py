"""tenants: add notifications_config column

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "notifications_config",
            JSONB(),
            nullable=False,
            server_default='{"email": false, "webhook": false, "sms": false}',
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "notifications_config")
