"""create medical_records table

Revision ID: 1f4d7a6b9b3c
Revises: 9c1a0b3f9f0e
Create Date: 2025-12-04 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f4d7a6b9b3c'
down_revision: Union[str, Sequence[str], None] = '9c1a0b3f9f0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'medical_records',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.UUID(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', sa.UUID(), sa.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True),
        sa.Column('diagnosis', sa.String(length=500), nullable=False),
        sa.Column('treatment_plan', sa.String(length=1000), nullable=True),
        sa.Column('prescription', sa.String(length=1000), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_medical_records_patient_id'), 'medical_records', ['patient_id'], unique=False)
    op.create_index(op.f('ix_medical_records_doctor_id'), 'medical_records', ['doctor_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_medical_records_doctor_id'), table_name='medical_records')
    op.drop_index(op.f('ix_medical_records_patient_id'), table_name='medical_records')
    op.drop_table('medical_records')
