"""add doctor favorites and reviews

Revision ID: 8f3c6c2f1234
Revises: d3f1a9c8f0b4
Create Date: 2025-12-08 04:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '8f3c6c2f1234'
down_revision: Union[str, Sequence[str], None] = 'd3f1a9c8f0b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'favorite_doctors',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column('patient_id', sa.UUID(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', sa.UUID(), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_favorite_doctors_patient_id'), 'favorite_doctors', ['patient_id'], unique=False)
    op.create_index(op.f('ix_favorite_doctors_doctor_id'), 'favorite_doctors', ['doctor_id'], unique=False)
    op.create_unique_constraint('uq_favorite_doctor_patient_doctor', 'favorite_doctors', ['patient_id', 'doctor_id'])

    op.create_table(
        'doctor_reviews',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False, default=uuid.uuid4),
        sa.Column('patient_id', sa.UUID(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', sa.UUID(), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_doctor_reviews_patient_id'), 'doctor_reviews', ['patient_id'], unique=False)
    op.create_index(op.f('ix_doctor_reviews_doctor_id'), 'doctor_reviews', ['doctor_id'], unique=False)
    op.create_unique_constraint('uq_doctor_review_patient_doctor', 'doctor_reviews', ['patient_id', 'doctor_id'])


def downgrade() -> None:
    op.drop_constraint('uq_doctor_review_patient_doctor', 'doctor_reviews', type_='unique')
    op.drop_index(op.f('ix_doctor_reviews_doctor_id'), table_name='doctor_reviews')
    op.drop_index(op.f('ix_doctor_reviews_patient_id'), table_name='doctor_reviews')
    op.drop_table('doctor_reviews')

    op.drop_constraint('uq_favorite_doctor_patient_doctor', 'favorite_doctors', type_='unique')
    op.drop_index(op.f('ix_favorite_doctors_doctor_id'), table_name='favorite_doctors')
    op.drop_index(op.f('ix_favorite_doctors_patient_id'), table_name='favorite_doctors')
    op.drop_table('favorite_doctors')
