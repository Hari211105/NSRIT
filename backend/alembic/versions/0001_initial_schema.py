"""Initial baseline schema for UPSKILL AI platform

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-11 02:15:00.000000

Creates all tables for sectors, roles, competencies, role_competencies,
courses, course_competencies, users, learner_competencies,
learning_resources, recommendations, documents, document_chunks,
generated_mcqs, quiz_assessments, and diagnostic_questions.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Sectors
    op.create_table(
        'sectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sectors_id'), 'sectors', ['id'], unique=False)
    op.create_index(op.f('ix_sectors_code'), 'sectors', ['code'], unique=True)

    # 2. Roles
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=True),
        sa.Column('sector_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['sector_id'], ['sectors.id'], name='fk_roles_sector_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)

    # 3. Competencies
    op.create_table(
        'competencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_competencies_id'), 'competencies', ['id'], unique=False)

    # 4. Role Competencies
    op.create_table(
        'role_competencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('required_level', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], name='fk_role_comp_comp_id'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='fk_role_comp_role_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_role_competencies_id'), 'role_competencies', ['id'], unique=False)

    # 5. Courses (Phase 10 & 11)
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('sector_id', sa.Integer(), nullable=True),
        sa.Column('level_hint', sa.String(length=50), nullable=True),
        sa.Column('estimated_hours', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('is_demo', sa.Boolean(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['sector_id'], ['sectors.id'], name='fk_courses_sector_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_courses_id'), 'courses', ['id'], unique=False)
    op.create_index(op.f('ix_courses_code'), 'courses', ['code'], unique=True)

    # 6. Course Competencies
    op.create_table(
        'course_competencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('required_level', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], name='fk_course_comp_comp_id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_course_comp_course_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_course_competencies_id'), 'course_competencies', ['id'], unique=False)

    # 7. Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=True),
        sa.Column('hashed_password', sa.String(length=200), nullable=True),
        sa.Column('learning_mode', sa.String(length=20), nullable=False, server_default='ROLE'),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('designation', sa.String(length=200), nullable=True),
        sa.Column('department', sa.String(length=200), nullable=True),
        sa.Column('assignment', sa.Text(), nullable=True),
        sa.Column('education', sa.Text(), nullable=True),
        sa.Column('work_experience', sa.Text(), nullable=True),
        sa.Column('previous_training', sa.Text(), nullable=True),
        sa.Column('profile_completed', sa.Boolean(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_users_course_id'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='fk_users_role_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 8. Learner Competencies
    op.create_table(
        'learner_competencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('current_level', sa.Integer(), nullable=False),
        sa.Column('assessed_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], name='fk_learner_comp_comp_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_learner_comp_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_learner_competencies_id'), 'learner_competencies', ['id'], unique=False)

    # 9. Learning Resources
    op.create_table(
        'learning_resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=250), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('minimum_level', sa.Integer(), nullable=False),
        sa.Column('maximum_level', sa.Integer(), nullable=False),
        sa.Column('duration_hours', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], name='fk_learning_res_comp_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_learning_resources_id'), 'learning_resources', ['id'], unique=False)

    # 10. Recommendations
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learner_id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('learning_resource_id', sa.Integer(), nullable=False),
        sa.Column('gap', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('relevance_score', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], name='fk_rec_comp_id'),
        sa.ForeignKeyConstraint(['learner_id'], ['users.id'], name='fk_rec_learner_id'),
        sa.ForeignKeyConstraint(['learning_resource_id'], ['learning_resources.id'], name='fk_rec_resource_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_recommendations_id'), 'recommendations', ['id'], unique=False)

    # 11. Documents
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('stored_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('normalized_text', sa.Text(), nullable=True),
        sa.Column('competency_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], name='fk_docs_comp_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)

    # 12. Document Chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name='fk_chunks_doc_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)

    # 13. Generated MCQs
    op.create_table(
        'generated_mcqs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('source_chunk_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('options', sa.Text(), nullable=False),
        sa.Column('correct_option', sa.Integer(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name='fk_mcqs_doc_id'),
        sa.ForeignKeyConstraint(['source_chunk_id'], ['document_chunks.id'], name='fk_mcqs_chunk_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_generated_mcqs_id'), 'generated_mcqs', ['id'], unique=False)
    op.create_index(op.f('ix_generated_mcqs_document_id'), 'generated_mcqs', ['document_id'], unique=False)

    # 14. Quiz Assessments
    op.create_table(
        'quiz_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learner_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('score_percent', sa.Float(), nullable=False),
        sa.Column('evidence_level', sa.Integer(), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('correct_answers', sa.Integer(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], name='fk_quiz_comp_id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name='fk_quiz_doc_id'),
        sa.ForeignKeyConstraint(['learner_id'], ['users.id'], name='fk_quiz_learner_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_quiz_assessments_id'), 'quiz_assessments', ['id'], unique=False)

    # 15. Diagnostic Questions
    op.create_table(
        'diagnostic_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('question_type', sa.String(length=20), nullable=False, server_default='MCQ'),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('options', sa.Text(), nullable=False),
        sa.Column('correct_option', sa.Integer(), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], name='fk_diag_q_comp_id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_diag_q_course_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_diagnostic_questions_id'), 'diagnostic_questions', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_questions_competency_id'), 'diagnostic_questions', ['competency_id'], unique=False)
    op.create_index(op.f('ix_diagnostic_questions_course_id'), 'diagnostic_questions', ['course_id'], unique=False)

    # 16. Diagnostic Assessments
    op.create_table(
        'diagnostic_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learner_id', sa.Integer(), nullable=False),
        sa.Column('assessment_type', sa.String(length=50), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('total_correct', sa.Integer(), nullable=False),
        sa.Column('score_percent', sa.Float(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('competency_results', sa.Text(), nullable=True),
        sa.Column('created_at', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['learner_id'], ['users.id'], name='fk_diag_a_learner_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_diagnostic_assessments_id'), 'diagnostic_assessments', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('diagnostic_assessments')
    op.drop_table('diagnostic_questions')
    op.drop_table('quiz_assessments')
    op.drop_table('generated_mcqs')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('recommendations')
    op.drop_table('learning_resources')
    op.drop_table('learner_competencies')
    op.drop_table('users')
    op.drop_table('course_competencies')
    op.drop_table('courses')
    op.drop_table('role_competencies')
    op.drop_table('competencies')
    op.drop_table('roles')
    op.drop_table('sectors')
