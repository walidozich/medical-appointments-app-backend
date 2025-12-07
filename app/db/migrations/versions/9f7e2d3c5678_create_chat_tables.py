"""create chat threads and messages

Revision ID: 9f7e2d3c5678
Revises: 8f3c6c2f1234
Create Date: 2025-12-08 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '9f7e2d3c5678'
down_revision: Union[str, Sequence[str], None] = '8f3c6c2f1234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chat_threads',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column('patient_id', sa.UUID(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', sa.UUID(), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_chat_threads_patient_id'), 'chat_threads', ['patient_id'], unique=False)
    op.create_index(op.f('ix_chat_threads_doctor_id'), 'chat_threads', ['doctor_id'], unique=False)
    op.create_unique_constraint('uq_chat_thread_patient_doctor', 'chat_threads', ['patient_id', 'doctor_id'])

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column('thread_id', sa.UUID(), sa.ForeignKey('chat_threads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.String(length=2000), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_system_message', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_index(op.f('ix_chat_messages_thread_id'), 'chat_messages', ['thread_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_sender_id'), 'chat_messages', ['sender_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chat_messages_sender_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_thread_id'), table_name='chat_messages')
    op.drop_table('chat_messages')

    op.drop_constraint('uq_chat_thread_patient_doctor', 'chat_threads', type_='unique')
    op.drop_index(op.f('ix_chat_threads_doctor_id'), table_name='chat_threads')
    op.drop_index(op.f('ix_chat_threads_patient_id'), table_name='chat_threads')
    op.drop_table('chat_threads')
