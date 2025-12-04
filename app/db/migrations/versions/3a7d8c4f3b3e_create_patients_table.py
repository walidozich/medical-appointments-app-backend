"""create patients table

Revision ID: 3a7d8c4f3b3e
Revises: b8b2cb064d5d
Create Date: 2025-12-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a7d8c4f3b3e'
down_revision: Union[str, Sequence[str], None] = 'b8b2cb064d5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'patients',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('blood_type', sa.String(length=5), nullable=True),
        sa.Column('allergies', sa.String(length=500), nullable=True),
        sa.Column('chronic_conditions', sa.String(length=500), nullable=True),
        sa.Column('medications', sa.String(length=500), nullable=True),
        sa.Column('emergency_contact_name', sa.String(length=100), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='uq_patients_user_id'),
    )
    op.create_index(op.f('ix_patients_user_id'), 'patients', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_patients_user_id'), table_name='patients')
    op.drop_table('patients')
