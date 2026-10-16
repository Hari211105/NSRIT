"""rbac_trainer_admin

Revision ID: 0003_rbac_trainer_admin
Revises: 0002_align_schema_with_models
Create Date: 2026-10-16 17:00:00.000000

Adds Role-Based Access Control (RBAC), course authoring workflow, and audit logs:
1. users:
   - account_type (VARCHAR(20), NOT NULL, default 'LEARNER')
   - is_active (BOOLEAN, NOT NULL, default TRUE)
2. courses:
   - status (VARCHAR(20), NOT NULL, default 'PUBLISHED')
   - created_by (INTEGER, FK to users.id, nullable)
   - review_note (TEXT, nullable)
3. audit_logs:
   - New table to track administrative and course workflow actions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_rbac_trainer_admin'
down_revision: Union[str, Sequence[str], None] = '0002_align_schema_with_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update users table with account_type and is_active
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('account_type', sa.String(length=20), nullable=False, server_default='LEARNER')
        )
        batch_op.add_column(
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true())
        )

    # 2. Update courses table with status, created_by, and review_note
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('status', sa.String(length=20), nullable=False, server_default='PUBLISHED')
        )
        batch_op.add_column(
            sa.Column('created_by', sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('review_note', sa.Text(), nullable=True)
        )
        batch_op.create_foreign_key('fk_courses_created_by_users', 'users', ['created_by'], ['id'])

    # 3. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    # 3. Drop audit_logs table
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    # 2. Revert courses table
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_courses_created_by_users', type_='foreignkey')
        batch_op.drop_column('review_note')
        batch_op.drop_column('created_by')
        batch_op.drop_column('status')

    # 1. Revert users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_active')
        batch_op.drop_column('account_type')
