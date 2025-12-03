"""Create revoked_tokens table

Revision ID: 2b7d9f0ea123
Revises: 1d99d7e99b69
Create Date: 2025-12-02 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b7d9f0ea123'
down_revision: Union[str, Sequence[str], None] = '1d99d7e99b69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'revoked_tokens',
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('token')
    )


def downgrade() -> None:
    op.drop_table('revoked_tokens')
