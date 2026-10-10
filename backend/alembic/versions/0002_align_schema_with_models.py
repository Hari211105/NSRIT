"""align_schema_with_models

Revision ID: 0002_align_schema_with_models
Revises: 0001_initial_schema
Create Date: 2026-10-11 03:00:00.000000

Aligns Alembic database schema with the current SQLAlchemy models exactly:
1. diagnostic_assessments:
   - Uses batch mode for SQLite/Postgres portability.
   - Updates 'assessment_type' (VARCHAR(30), NOT NULL) and 'status' (VARCHAR(20), NOT NULL).
   - Adds index on 'learner_id'.
2. documents:
   - Adds 'content_type' VARCHAR(100)
   - Alters 'filename' length to VARCHAR(250)
   - Drops obsolete prototype columns: 'stored_path', 'file_size_bytes',
     'sha256_hash', and 'page_count' (never mapped in app.models.Document;
     no application code or routes read or write these columns).
3. learner_competencies:
   - Drops unmapped column 'assessed_at' (not present in app.models.LearnerCompetency).
4. quiz_assessments:
   - Adds indexes on 'learner_id', 'document_id', and 'competency_id'.
   - Drops unmapped prototype columns: 'passed', 'total_questions', and 'correct_answers'
     (QuizAssessment in app.models only tracks score_percent and evidence_level).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_align_schema_with_models'
down_revision: Union[str, Sequence[str], None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. diagnostic_assessments adjustments (batch mode for SQLite alter column support)
    with op.batch_alter_table('diagnostic_assessments', schema=None) as batch_op:
        batch_op.alter_column(
            'assessment_type',
            existing_type=sa.VARCHAR(length=50),
            type_=sa.String(length=30),
            nullable=False,
        )
        batch_op.alter_column(
            'status',
            existing_type=sa.VARCHAR(length=50),
            type_=sa.String(length=20),
            nullable=False,
        )
        batch_op.create_index(
            batch_op.f('ix_diagnostic_assessments_learner_id'),
            ['learner_id'],
            unique=False,
        )

    # 2. documents adjustments
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('content_type', sa.String(length=100), nullable=True)
        )
        batch_op.alter_column(
            'filename',
            existing_type=sa.VARCHAR(length=255),
            type_=sa.String(length=250),
            existing_nullable=False,
        )
        # Note: These columns were defined in 0001 but never mapped in models.Document
        batch_op.drop_column('stored_path')
        batch_op.drop_column('file_size_bytes')
        batch_op.drop_column('sha256_hash')
        batch_op.drop_column('page_count')

    # 3. learner_competencies adjustments
    with op.batch_alter_table('learner_competencies', schema=None) as batch_op:
        batch_op.drop_column('assessed_at')

    # 4. quiz_assessments adjustments
    with op.batch_alter_table('quiz_assessments', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_quiz_assessments_competency_id'),
            ['competency_id'],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f('ix_quiz_assessments_document_id'),
            ['document_id'],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f('ix_quiz_assessments_learner_id'),
            ['learner_id'],
            unique=False,
        )
        # Note: These columns were defined in 0001 but never mapped in models.QuizAssessment
        batch_op.drop_column('correct_answers')
        batch_op.drop_column('total_questions')
        batch_op.drop_column('passed')


def downgrade() -> None:
    # 4. quiz_assessments rollback
    with op.batch_alter_table('quiz_assessments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('passed', sa.BOOLEAN(), nullable=False))
        batch_op.add_column(sa.Column('total_questions', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('correct_answers', sa.INTEGER(), nullable=False))
        batch_op.drop_index(batch_op.f('ix_quiz_assessments_learner_id'))
        batch_op.drop_index(batch_op.f('ix_quiz_assessments_document_id'))
        batch_op.drop_index(batch_op.f('ix_quiz_assessments_competency_id'))

    # 3. learner_competencies rollback
    with op.batch_alter_table('learner_competencies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assessed_at', sa.VARCHAR(length=50), nullable=True))

    # 2. documents rollback
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('page_count', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('sha256_hash', sa.VARCHAR(length=64), nullable=False))
        batch_op.add_column(sa.Column('file_size_bytes', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('stored_path', sa.VARCHAR(length=500), nullable=False))
        batch_op.alter_column(
            'filename',
            existing_type=sa.String(length=250),
            type_=sa.VARCHAR(length=255),
            existing_nullable=False,
        )
        batch_op.drop_column('content_type')

    # 1. diagnostic_assessments rollback
    with op.batch_alter_table('diagnostic_assessments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_diagnostic_assessments_learner_id'))
        batch_op.alter_column(
            'status',
            existing_type=sa.String(length=20),
            type_=sa.VARCHAR(length=50),
            nullable=True,
        )
        batch_op.alter_column(
            'assessment_type',
            existing_type=sa.String(length=30),
            type_=sa.VARCHAR(length=50),
            nullable=True,
        )
