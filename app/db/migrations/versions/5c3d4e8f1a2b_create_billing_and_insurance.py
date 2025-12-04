"""create billing and insurance tables

Revision ID: 5c3d4e8f1a2b
Revises: 1f4d7a6b9b3c
Create Date: 2025-12-04 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c3d4e8f1a2b'
down_revision: Union[str, Sequence[str], None] = '1f4d7a6b9b3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'insurance_policies',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.UUID(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_name', sa.String(length=255), nullable=False),
        sa.Column('policy_number', sa.String(length=100), nullable=False),
        sa.Column('coverage_details', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_insurance_policies_patient_id'), 'insurance_policies', ['patient_id'], unique=False)

    op.create_table(
        'billings',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('patient_id', sa.UUID(), sa.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True),
        sa.Column('appointment_id', sa.UUID(), sa.ForeignKey('appointments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_billings_patient_id'), 'billings', ['patient_id'], unique=False)
    op.create_index(op.f('ix_billings_appointment_id'), 'billings', ['appointment_id'], unique=False)

    op.create_table(
        'insurance_claims',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('policy_id', sa.UUID(), sa.ForeignKey('insurance_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('billing_id', sa.UUID(), sa.ForeignKey('billings.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_insurance_claims_policy_id'), 'insurance_claims', ['policy_id'], unique=False)
    op.create_index(op.f('ix_insurance_claims_billing_id'), 'insurance_claims', ['billing_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_insurance_claims_billing_id'), table_name='insurance_claims')
    op.drop_index(op.f('ix_insurance_claims_policy_id'), table_name='insurance_claims')
    op.drop_table('insurance_claims')
    op.drop_index(op.f('ix_billings_appointment_id'), table_name='billings')
    op.drop_index(op.f('ix_billings_patient_id'), table_name='billings')
    op.drop_table('billings')
    op.drop_index(op.f('ix_insurance_policies_patient_id'), table_name='insurance_policies')
    op.drop_table('insurance_policies')
