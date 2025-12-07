"""add chat attachment fields

Revision ID: ef12ab34cdef
Revises: abcd1234add
Create Date: 2025-12-08 07:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef12ab34cdef'
down_revision: Union[str, Sequence[str], None] = 'abcd1234add'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_messages', sa.Column('file_url', sa.String(length=1000), nullable=True))
    op.add_column('chat_messages', sa.Column('file_type', sa.String(length=50), nullable=True))
    op.alter_column('chat_messages', 'content', existing_type=sa.String(length=2000), nullable=True)


def downgrade() -> None:
    op.alter_column('chat_messages', 'content', existing_type=sa.String(length=2000), nullable=False)
    op.drop_column('chat_messages', 'file_type')
    op.drop_column('chat_messages', 'file_url')
