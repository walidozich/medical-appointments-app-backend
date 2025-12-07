"""add thread status and preferences

Revision ID: 1234abcd5678
Revises: ef12ab34cdef
Create Date: 2025-12-08 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '1234abcd5678'
down_revision: Union[str, Sequence[str], None] = 'ef12ab34cdef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_threads', sa.Column('status', sa.String(length=20), nullable=False, server_default='open'))
    op.create_table(
        'chat_thread_preferences',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('thread_id', sa.UUID(), sa.ForeignKey('chat_threads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_chat_thread_preferences_user_id'), 'chat_thread_preferences', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_thread_preferences_thread_id'), 'chat_thread_preferences', ['thread_id'], unique=False)
    op.create_unique_constraint('uq_thread_pref_user_thread', 'chat_thread_preferences', ['user_id', 'thread_id'])


def downgrade() -> None:
    op.drop_constraint('uq_thread_pref_user_thread', 'chat_thread_preferences', type_='unique')
    op.drop_index(op.f('ix_chat_thread_preferences_thread_id'), table_name='chat_thread_preferences')
    op.drop_index(op.f('ix_chat_thread_preferences_user_id'), table_name='chat_thread_preferences')
    op.drop_table('chat_thread_preferences')
    op.drop_column('chat_threads', 'status')
