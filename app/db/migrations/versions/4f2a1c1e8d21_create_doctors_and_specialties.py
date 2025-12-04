"""create doctors, specialties, availability

Revision ID: 4f2a1c1e8d21
Revises: 3a7d8c4f3b3e
Create Date: 2025-12-04 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '4f2a1c1e8d21'
down_revision: Union[str, Sequence[str], None] = '3a7d8c4f3b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'specialties',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.String(length=500), nullable=True),
    )

    op.create_table(
        'doctors',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('bio', sa.String(length=1000), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('clinic_address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('avg_rating', sa.Float(), server_default='0'),
        sa.Column('rating_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='uq_doctors_user_id'),
    )
    op.create_index(op.f('ix_doctors_user_id'), 'doctors', ['user_id'], unique=False)

    op.create_table(
        'doctor_specialties',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('doctor_id', sa.UUID(), sa.ForeignKey('doctors.id', ondelete='CASCADE')),
        sa.Column('specialty_id', sa.Integer(), sa.ForeignKey('specialties.id', ondelete='CASCADE')),
    )

    op.create_table(
        'doctor_availability',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('doctor_id', sa.UUID(), sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('weekday', sa.String(length=10), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_doctor_availability_doctor_id'), 'doctor_availability', ['doctor_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_doctor_availability_doctor_id'), table_name='doctor_availability')
    op.drop_table('doctor_availability')
    op.drop_table('doctor_specialties')
    op.drop_index(op.f('ix_doctors_user_id'), table_name='doctors')
    op.drop_table('doctors')
    op.drop_table('specialties')
