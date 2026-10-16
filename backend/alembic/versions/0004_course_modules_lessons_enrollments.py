"""course_modules_lessons_enrollments

Revision ID: 0004_course_modules_lessons_enrollments
Revises: 0003_rbac_trainer_admin
Create Date: 2026-10-16 17:45:00.000000

Adds structured course curriculum, progress tracking, and prerequisites:
1. courses:
   - min_diagnostic_score (FLOAT, nullable)
2. learning_resources:
   - course_id (INTEGER, FK to courses.id, nullable)
3. course_modules:
   - New table for thematic modules within courses
4. lessons:
   - New table for lessons (TEXT, LINK, VIDEO_URL) within modules
5. course_enrollments:
   - New table tracking learner course enrollments, status, and progress
6. lesson_progress:
   - New table tracking individual lesson completions per learner
7. course_prerequisites:
   - New table defining prerequisite relationships between courses
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_course_modules_lessons_enrollments'
down_revision: Union[str, Sequence[str], None] = '0003_rbac_trainer_admin'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update courses table
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('min_diagnostic_score', sa.Float(), nullable=True)
        )

    # 2. Update learning_resources table
    with op.batch_alter_table('learning_resources', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('course_id', sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key('fk_learning_resources_course_id', 'courses', ['course_id'], ['id'])
        batch_op.create_index(batch_op.f('ix_learning_resources_course_id'), ['course_id'], unique=False)

    # 3. Create course_modules table
    op.create_table(
        'course_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_course_modules_id'), 'course_modules', ['id'], unique=False)
    op.create_index(op.f('ix_course_modules_course_id'), 'course_modules', ['course_id'], unique=False)

    # 4. Create lessons table
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('lesson_type', sa.String(length=20), nullable=False, server_default='TEXT'),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(['module_id'], ['course_modules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lessons_id'), 'lessons', ['id'], unique=False)
    op.create_index(op.f('ix_lessons_module_id'), 'lessons', ['module_id'], unique=False)

    # 5. Create course_enrollments table
    op.create_table(
        'course_enrollments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ENROLLED'),
        sa.Column('started_at', sa.String(length=50), nullable=True),
        sa.Column('completed_at', sa.String(length=50), nullable=True),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'course_id', name='uq_user_course_enrollment')
    )
    op.create_index(op.f('ix_course_enrollments_id'), 'course_enrollments', ['id'], unique=False)
    op.create_index(op.f('ix_course_enrollments_course_id'), 'course_enrollments', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_enrollments_user_id'), 'course_enrollments', ['user_id'], unique=False)

    # 6. Create lesson_progress table
    op.create_table(
        'lesson_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('completed_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson_progress')
    )
    op.create_index(op.f('ix_lesson_progress_id'), 'lesson_progress', ['id'], unique=False)
    op.create_index(op.f('ix_lesson_progress_lesson_id'), 'lesson_progress', ['lesson_id'], unique=False)
    op.create_index(op.f('ix_lesson_progress_user_id'), 'lesson_progress', ['user_id'], unique=False)

    # 7. Create course_prerequisites table
    op.create_table(
        'course_prerequisites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('prerequisite_course_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['prerequisite_course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'prerequisite_course_id', name='uq_course_prerequisite')
    )
    op.create_index(op.f('ix_course_prerequisites_id'), 'course_prerequisites', ['id'], unique=False)
    op.create_index(op.f('ix_course_prerequisites_course_id'), 'course_prerequisites', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_prerequisites_prerequisite_course_id'), 'course_prerequisites', ['prerequisite_course_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_course_prerequisites_prerequisite_course_id'), table_name='course_prerequisites')
    op.drop_index(op.f('ix_course_prerequisites_course_id'), table_name='course_prerequisites')
    op.drop_index(op.f('ix_course_prerequisites_id'), table_name='course_prerequisites')
    op.drop_table('course_prerequisites')

    op.drop_index(op.f('ix_lesson_progress_user_id'), table_name='lesson_progress')
    op.drop_index(op.f('ix_lesson_progress_lesson_id'), table_name='lesson_progress')
    op.drop_index(op.f('ix_lesson_progress_id'), table_name='lesson_progress')
    op.drop_table('lesson_progress')

    op.drop_index(op.f('ix_course_enrollments_user_id'), table_name='course_enrollments')
    op.drop_index(op.f('ix_course_enrollments_course_id'), table_name='course_enrollments')
    op.drop_index(op.f('ix_course_enrollments_id'), table_name='course_enrollments')
    op.drop_table('course_enrollments')

    op.drop_index(op.f('ix_lessons_module_id'), table_name='lessons')
    op.drop_index(op.f('ix_lessons_id'), table_name='lessons')
    op.drop_table('lessons')

    op.drop_index(op.f('ix_course_modules_course_id'), table_name='course_modules')
    op.drop_index(op.f('ix_course_modules_id'), table_name='course_modules')
    op.drop_table('course_modules')

    with op.batch_alter_table('learning_resources', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_resources_course_id'))
        batch_op.drop_constraint('fk_learning_resources_course_id', type_='foreignkey')
        batch_op.drop_column('course_id')

    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_column('min_diagnostic_score')
