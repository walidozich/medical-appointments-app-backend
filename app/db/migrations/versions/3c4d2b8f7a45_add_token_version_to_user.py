"""Add token_version to users

Revision ID: 3c4d2b8f7a45
Revises: 2b7d9f0ea123
Create Date: 2025-12-03 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c4d2b8f7a45'
down_revision: Union[str, Sequence[str], None] = '2b7d9f0ea123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))
    # remove server_default if you want


def downgrade() -> None:
    op.drop_column('users', 'token_version')
