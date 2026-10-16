"""
UPSKILL AI - Database Models (Phase 2)
Using integer primary keys for simplicity with SQLite.
"""
from sqlalchemy import Column, Float, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

# ------------------------------------------------------------------
# Competency level helpers
# ------------------------------------------------------------------

LEVEL_LABELS = {
    1: "Awareness",
    2: "Working",
    3: "Proficient",
    4: "Advanced",
}

def get_level_label(level: int) -> str:
    return LEVEL_LABELS.get(level, "Unknown")


# ------------------------------------------------------------------
# Sector (Phase 9 - Multi-Sector Expansion)
# ------------------------------------------------------------------

class Sector(Base):
    __tablename__ = "sectors"

    id            = Column(Integer, primary_key=True, index=True)
    code          = Column(String(50), unique=True, nullable=False, index=True)
    name          = Column(String(200), nullable=False)
    description   = Column(Text, nullable=True)
    icon          = Column(String(50), default="briefcase")
    display_order = Column(Integer, default=0)

    # Relationships
    roles = relationship("Role", back_populates="sector")


# ------------------------------------------------------------------
# Role
# ------------------------------------------------------------------

class Role(Base):
    __tablename__ = "roles"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_demo     = Column(Boolean, default=False)
    sector_id   = Column(Integer, ForeignKey("sectors.id"), nullable=True)

    # Relationships
    sector              = relationship("Sector", back_populates="roles")
    competency_mappings = relationship("RoleCompetency", back_populates="role")
    users               = relationship("User", back_populates="role")


# ------------------------------------------------------------------
# Competency
# ------------------------------------------------------------------

class Competency(Base):
    __tablename__ = "competencies"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_demo     = Column(Boolean, default=False)

    # Relationships
    role_mappings        = relationship("RoleCompetency", back_populates="competency")
    course_mappings      = relationship("CourseCompetency", back_populates="competency")
    learner_competencies = relationship("LearnerCompetency", back_populates="competency")
    learning_resources   = relationship("LearningResource", back_populates="competency")


# ------------------------------------------------------------------
# Role ↔ Competency mapping (required levels per role)
# ------------------------------------------------------------------

class RoleCompetency(Base):
    __tablename__ = "role_competencies"

    id             = Column(Integer, primary_key=True, index=True)
    role_id        = Column(Integer, ForeignKey("roles.id"), nullable=False)
    competency_id  = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    required_level = Column(Integer, nullable=False)  # 1–4
    priority       = Column(String(20), default="MEDIUM")  # HIGH | MEDIUM | LOW

    # Relationships
    role       = relationship("Role", back_populates="competency_mappings")
    competency = relationship("Competency", back_populates="role_mappings")


# ------------------------------------------------------------------
# Course (Phase 10 - Learning Goal Path)
# ------------------------------------------------------------------

class Course(Base):
    __tablename__ = "courses"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(50), unique=True, nullable=False, index=True)
    name        = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category    = Column(String(50), nullable=False, default="TECHNICAL")  # TECHNICAL | NON_TECHNICAL
    sector_id       = Column(Integer, ForeignKey("sectors.id"), nullable=True)
    level_hint      = Column(String(50), default="Beginner")  # Beginner | Intermediate | Advanced
    estimated_hours = Column(Integer, default=20, nullable=False)
    is_demo         = Column(Boolean, default=False)
    active          = Column(Boolean, default=True)

    # Phase 13 - Course authoring status & creator
    status          = Column(String(20), default="PUBLISHED", nullable=False)  # DRAFT | PENDING_REVIEW | PUBLISHED | ARCHIVED
    created_by      = Column(Integer, ForeignKey("users.id", use_alter=True, name="fk_courses_created_by_users"), nullable=True)
    review_note     = Column(Text, nullable=True)

    # Relationships
    sector              = relationship("Sector")
    competency_mappings = relationship("CourseCompetency", back_populates="course")
    users               = relationship("User", back_populates="course", foreign_keys="User.course_id")
    creator             = relationship("User", foreign_keys=[created_by])


class CourseCompetency(Base):
    __tablename__ = "course_competencies"

    id             = Column(Integer, primary_key=True, index=True)
    course_id      = Column(Integer, ForeignKey("courses.id"), nullable=False)
    competency_id  = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    required_level = Column(Integer, nullable=False)  # 1–4
    priority       = Column(String(20), default="MEDIUM")  # HIGH | MEDIUM | LOW

    # Relationships
    course     = relationship("Course", back_populates="competency_mappings")
    competency = relationship("Competency", back_populates="course_mappings")


# ------------------------------------------------------------------
# User (Learner)
# ------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(200), nullable=False)
    email           = Column(String(200), nullable=False, unique=True)
    role_id         = Column(Integer, ForeignKey("roles.id"), nullable=True)
    is_demo         = Column(Boolean, default=False)
    # Phase 7A - bcrypt hash of the account password. Nullable so pre-auth
    # databases (which created users without a password) still open cleanly;
    # the seeder backfills the demo learner. Never returned by any endpoint.
    hashed_password = Column(String(200), nullable=True, default=None)

    # ------------------------------------------------------------------
    # Phase 13 - Role-Based Access Control (RBAC)
    # "LEARNER" | "TRAINER" | "ADMIN"
    # ------------------------------------------------------------------
    account_type    = Column(String(20), default="LEARNER", nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)

    # ------------------------------------------------------------------
    # Phase 10 - Learning Goal / Mode
    # "ROLE" (existing role-based pathway) or "GOAL" (course-based pathway)
    # ------------------------------------------------------------------
    learning_mode   = Column(String(20), default="ROLE", nullable=False)
    course_id       = Column(Integer, ForeignKey("courses.id"), nullable=True, default=None)

    # ------------------------------------------------------------------
    # Phase 8 - learner onboarding profile (collected once, after signup,
    # before any assessment). role_id above is the selected POSITION; these
    # columns hold the rest of the professional profile. All nullable so
    # pre-onboarding accounts, upgraded databases and GOAL learners keep working.
    # ------------------------------------------------------------------
    designation        = Column(String(200), nullable=True, default=None)
    department         = Column(String(200), nullable=True, default=None)
    assignment         = Column(Text, nullable=True, default=None)
    education          = Column(Text, nullable=True, default=None)
    work_experience    = Column(Text, nullable=True, default=None)
    previous_training  = Column(Text, nullable=True, default=None)
    # False until the learner completes onboarding.
    profile_completed  = Column(Boolean, default=False)

    # Relationships
    role                 = relationship("Role", back_populates="users")
    course               = relationship("Course", back_populates="users", foreign_keys=[course_id])
    learner_competencies = relationship("LearnerCompetency", back_populates="user")


# ------------------------------------------------------------------
# Learner ↔ Competency profile (current levels per learner)
# ------------------------------------------------------------------

class LearnerCompetency(Base):
    __tablename__ = "learner_competencies"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    current_level = Column(Integer, nullable=False)  # 1–4

    # Relationships
    user       = relationship("User", back_populates="learner_competencies")
    competency = relationship("Competency", back_populates="learner_competencies")


# ------------------------------------------------------------------
# Learning Resource (Catalog)
# ------------------------------------------------------------------

class LearningResource(Base):
    __tablename__ = "learning_resources"

    id             = Column(Integer, primary_key=True, index=True)
    title          = Column(String(250), nullable=False)
    description    = Column(Text, nullable=True)
    source         = Column(String(50), nullable=False)   # IGOT_DEMO | NSSTA_TPAC_DEMO
    resource_type  = Column(String(50), default="COURSE") # COURSE | MODULE | DOCUMENT | VIDEO
    competency_id  = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    minimum_level  = Column(Integer, nullable=False, default=1)  # 1–4
    maximum_level  = Column(Integer, nullable=False, default=4)  # 1–4
    duration_hours = Column(Integer, nullable=False, default=1)
    url            = Column(String(500), nullable=True)
    is_demo        = Column(Boolean, default=True)
    active         = Column(Boolean, default=True)

    # Relationships
    competency      = relationship("Competency", back_populates="learning_resources")
    recommendations = relationship("Recommendation", back_populates="learning_resource")


# ------------------------------------------------------------------
# Recommendation (Persisted or generated recommendation records)
# ------------------------------------------------------------------

class Recommendation(Base):
    __tablename__ = "recommendations"

    id                   = Column(Integer, primary_key=True, index=True)
    learner_id           = Column(Integer, ForeignKey("users.id"), nullable=False)
    competency_id        = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    learning_resource_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=False)
    gap                  = Column(Integer, nullable=False)
    priority             = Column(String(20), nullable=False)   # CRITICAL | HIGH | MEDIUM
    relevance_score      = Column(Integer, nullable=False)      # 0–100
    reason               = Column(Text, nullable=False)
    rank                 = Column(Integer, nullable=False)
    created_at           = Column(String(50), nullable=True)

    # Relationships
    learner           = relationship("User")
    competency        = relationship("Competency")
    learning_resource = relationship("LearningResource", back_populates="recommendations")


# ------------------------------------------------------------------
# Document (PDF Uploads & Extracted Text for Phase 5)
# ------------------------------------------------------------------

class Document(Base):
    __tablename__ = "documents"

    id              = Column(Integer, primary_key=True, index=True)
    filename        = Column(String(250), nullable=False)
    content_type    = Column(String(100), default="application/pdf")
    extracted_text  = Column(Text, nullable=False)
    # Wrapped PDF lines re-joined into paragraphs: the exact text chunks were
    # cut from. Nullable because documents uploaded before it existed have none.
    normalized_text = Column(Text, nullable=True)
    # Optional competency this document assesses (Phase 6A). Null means the
    # document is not linked to a competency, so quiz evidence cannot be
    # recorded for it - the competency is never guessed from the text.
    competency_id   = Column(Integer, ForeignKey("competencies.id"), nullable=True)
    created_at      = Column(String(50), nullable=True)

    # Relationships
    competency = relationship("Competency")
    chunks = relationship("DocumentChunk", back_populates="document", order_by="DocumentChunk.chunk_index")


# ------------------------------------------------------------------
# Document Chunk (Phase 5 Step 2 — text chunks for MCQ generation)
# ------------------------------------------------------------------

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id           = Column(Integer, primary_key=True, index=True)
    document_id  = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index  = Column(Integer, nullable=False)
    text         = Column(Text, nullable=False)
    created_at   = Column(String(50), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")


# ------------------------------------------------------------------
# Generated MCQ (Phase 5 Step 4B — validated questions persisted per chunk)
# ------------------------------------------------------------------

class GeneratedMCQ(Base):
    __tablename__ = "generated_mcqs"

    id              = Column(Integer, primary_key=True, index=True)
    document_id     = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    source_chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False)
    question        = Column(Text, nullable=False)
    # JSON-encoded array of exactly 4 option strings (SQLite has no JSON column).
    options         = Column(Text, nullable=False)
    correct_option  = Column(Integer, nullable=False)   # 0-based index into options
    explanation     = Column(Text, nullable=False)
    created_at      = Column(String(50), nullable=True)


# ------------------------------------------------------------------
# Quiz Assessment / Competency Evidence (Phase 6A)
# ------------------------------------------------------------------

class QuizAssessment(Base):
    """
    Evidence that a learner completed a quiz for a competency (Phase 6A).

    One row per successful quiz submission. score_percent is the server-side
    quiz percentage and evidence_level the prototype evidence level derived from
    it (0-3, see app.services.competency_evidence_service). competency_id is
    required: evidence is only ever recorded for a competency the document is
    explicitly linked to, never one guessed from the text.

    PROTOTYPE assessment rule - not an official MoSPI / iGOT Karmayogi / NSSTA /
    TPAC / Government competency scale.
    """
    __tablename__ = "quiz_assessments"

    id             = Column(Integer, primary_key=True, index=True)
    learner_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id    = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    competency_id  = Column(Integer, ForeignKey("competencies.id"), nullable=False, index=True)
    score_percent  = Column(Float, nullable=False)    # 0-100
    evidence_level = Column(Integer, nullable=False)  # 0-3
    created_at     = Column(String(50), nullable=True)

    # Relationships
    learner    = relationship("User")
    document   = relationship("Document")
    competency = relationship("Competency")


# ------------------------------------------------------------------
# Diagnostic Assessment Question (Phase 2 — competency-mapped questions)
# ------------------------------------------------------------------

class DiagnosticQuestion(Base):
    """
    A question used in diagnostic assessments, mapped to a specific competency.

    Each question has a difficulty level (EASY, MEDIUM, HARD) used for
    difficulty-weighted scoring. Questions are pre-seeded per competency for
    the demo, or can be generated by AI and validated.

    PROTOTYPE — not an official MoSPI / iGOT Karmayogi assessment instrument.
    """
    __tablename__ = "diagnostic_questions"

    id              = Column(Integer, primary_key=True, index=True)
    competency_id   = Column(Integer, ForeignKey("competencies.id"), nullable=False, index=True)
    course_id       = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    question_type   = Column(String(20), nullable=False, default="MCQ")  # MCQ | SCENARIO
    question        = Column(Text, nullable=False)
    options         = Column(Text, nullable=False)   # JSON-encoded array of 4 option strings
    correct_option  = Column(Integer, nullable=False) # 0-based index into options
    difficulty      = Column(String(20), nullable=False, default="MEDIUM")  # EASY | MEDIUM | HARD
    explanation     = Column(Text, nullable=True)
    is_demo         = Column(Boolean, default=False)
    active          = Column(Boolean, default=True)
    created_at      = Column(String(50), nullable=True)

    # Relationships
    competency = relationship("Competency")
    course     = relationship("Course")


# ------------------------------------------------------------------
# Diagnostic Assessment Result (Phase 2 — per-session results)
# ------------------------------------------------------------------

class DiagnosticAssessment(Base):
    """
    A completed diagnostic assessment session.

    Stores the overall result and per-competency breakdown as JSON. Evidence
    is per-competency within this record; the quiz_assessments table is not
    used for diagnostics because its rows are document-scoped (one document,
    one competency), which cannot represent a multi-competency diagnostic.

    PROTOTYPE — not an official MoSPI / iGOT Karmayogi assessment instrument.
    """
    __tablename__ = "diagnostic_assessments"

    id              = Column(Integer, primary_key=True, index=True)
    learner_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_type = Column(String(30), nullable=False, default="diagnostic")
    total_questions = Column(Integer, nullable=False)
    total_correct   = Column(Integer, nullable=False)
    score_percent   = Column(Float, nullable=False)   # difficulty-weighted percentage 0-100
    passed          = Column(Boolean, nullable=False)
    status          = Column(String(20), nullable=False)  # PASSED | FAILED
    # JSON-encoded per-competency breakdown
    competency_results = Column(Text, nullable=True)
    created_at      = Column(String(50), nullable=True)

    # Relationships
    learner = relationship("User")


# ------------------------------------------------------------------
# Audit Log (Phase 13 — RBAC role changes & course approvals)
# ------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action      = Column(String(50), nullable=False)   # ROLE_CHANGE | USER_STATUS_CHANGE | COURSE_APPROVE | COURSE_REJECT
    target_type = Column(String(50), nullable=False)   # USER | COURSE
    target_id   = Column(Integer, nullable=True)
    details     = Column(Text, nullable=True)
    created_at  = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User")

