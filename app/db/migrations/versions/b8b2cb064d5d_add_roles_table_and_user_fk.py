"""Add roles table and user.role_id foreign key

Revision ID: b8b2cb064d5d
Revises: 3c4d2b8f7a45, 7a10c5830524
Create Date: 2025-12-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8b2cb064d5d'
down_revision: Union[str, Sequence[str], None] = ('3c4d2b8f7a45', '7a10c5830524')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
    )

    roles_table = sa.table('roles', sa.column('id', sa.Integer), sa.column('name', sa.String))
    op.bulk_insert(
        roles_table,
        [
            {"name": "ADMIN"},
            {"name": "DOCTOR"},
            {"name": "PATIENT"},
            {"name": "STAFF"},
        ],
    )

    op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_role_id_roles', 'users', 'roles', ['role_id'], ['id'])

    conn = op.get_bind()
    patient_id = conn.execute(sa.select(roles_table.c.id).where(roles_table.c.name == 'PATIENT')).scalar()
    conn.execute(sa.text("""
        UPDATE users
        SET role_id = roles.id
        FROM roles
        WHERE users.role = roles.name
    """))
    if patient_id is not None:
        conn.execute(sa.text("UPDATE users SET role_id = :patient WHERE role_id IS NULL"), {"patient": patient_id})

    op.alter_column('users', 'role_id', nullable=False)

    inspector = sa.inspect(conn)
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "role" in user_columns:
        op.drop_column('users', 'role')


def downgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE users
        SET role = roles.name
        FROM roles
        WHERE users.role_id = roles.id
    """))
    op.alter_column('users', 'role', nullable=False, server_default='PATIENT')
    op.drop_constraint('fk_users_role_id_roles', 'users', type_='foreignkey')
    op.drop_column('users', 'role_id')
    op.drop_table('roles')
