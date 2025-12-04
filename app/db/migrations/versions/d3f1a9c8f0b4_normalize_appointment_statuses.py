"""normalize appointment statuses to Scheduled/Completed/Cancelled

Revision ID: d3f1a9c8f0b4
Revises: 5c3d4e8f1a2b
Create Date: 2025-12-04 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3f1a9c8f0b4'
down_revision: Union[str, Sequence[str], None] = '5c3d4e8f1a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing statuses
    op.execute(
        """
        UPDATE appointments
        SET status = 'SCHEDULED'
        WHERE status IN ('PENDING','CONFIRMED')
        """
    )
    # Ensure default is SCHEDULED
    op.alter_column(
        'appointments',
        'status',
        existing_type=sa.String(length=20),
        server_default='SCHEDULED',
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'appointments',
        'status',
        existing_type=sa.String(length=20),
        server_default='PENDING',
        nullable=False,
    )
