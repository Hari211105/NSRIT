"""
UPSKILL AI - Trainer Course Authoring Endpoints (Phase 13)
Access restricted to TRAINER and ADMIN accounts.
"""
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, CourseCompetency, Competency, DiagnosticQuestion, User
from app.routes.auth import get_current_user, require_account_types


router = APIRouter(prefix="/trainer", tags=["Trainer Course Studio"])


# ------------------------------------------------------------------
# Request / Response Schemas
# ------------------------------------------------------------------

class CompetencyItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    required_level: int
    priority: str

    class Config:
        from_attributes = True


class TrainerCourseOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: str
    status: str
    sector_id: Optional[int] = None
    level_hint: Optional[str] = "Beginner"
    estimated_hours: int = 20
    is_demo: bool = False
    active: bool = True
    created_by: Optional[int] = None
    review_note: Optional[str] = None
    competencies_count: int = 0
    questions_count: int = 0
    competencies: List[CompetencyItemOut] = []

    class Config:
        from_attributes = True


class CourseCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    category: str = Field("TECHNICAL", description="'TECHNICAL' or 'NON_TECHNICAL'")
    sector_id: Optional[int] = None
    level_hint: Optional[str] = "Beginner"
    estimated_hours: int = Field(20, ge=1, le=500)


class CourseUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    sector_id: Optional[int] = None
    level_hint: Optional[str] = None
    estimated_hours: Optional[int] = Field(None, ge=1, le=500)


class MapCompetencyRequest(BaseModel):
    competency_id: int
    required_level: int = Field(..., ge=1, le=4)
    priority: str = Field("MEDIUM", description="'HIGH' | 'MEDIUM' | 'LOW'")


class QuestionCreateRequest(BaseModel):
    competency_id: int
    question_type: str = Field("MCQ", description="'MCQ' or 'SCENARIO'")
    question: str = Field(..., min_length=10)
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_option: int = Field(..., ge=0, le=3)
    difficulty: str = Field("MEDIUM", description="'EASY' | 'MEDIUM' | 'HARD'")
    explanation: Optional[str] = None


class QuestionUpdateRequest(BaseModel):
    competency_id: Optional[int] = None
    question_type: Optional[str] = None
    question: Optional[str] = Field(None, min_length=10)
    options: Optional[List[str]] = Field(None, min_length=4, max_length=4)
    correct_option: Optional[int] = Field(None, ge=0, le=3)
    difficulty: Optional[str] = None
    explanation: Optional[str] = None


class QuestionOut(BaseModel):
    id: int
    course_id: Optional[int] = None
    competency_id: int
    competency_name: Optional[str] = None
    question_type: str
    question: str
    options: List[str]
    correct_option: int
    difficulty: str
    explanation: Optional[str] = None
    is_demo: bool
    active: bool

    class Config:
        from_attributes = True


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------

def serialize_trainer_course(course: Course, db: Session) -> TrainerCourseOut:
    mappings = (
        db.query(CourseCompetency)
        .filter(CourseCompetency.course_id == course.id)
        .all()
    )
    comp_list = []
    for m in mappings:
        if m.competency:
            comp_list.append(
                CompetencyItemOut(
                    id=m.competency.id,
                    name=m.competency.name,
                    description=m.competency.description,
                    required_level=m.required_level,
                    priority=m.priority or "MEDIUM",
                )
            )
    q_count = (
        db.query(DiagnosticQuestion)
        .filter(DiagnosticQuestion.course_id == course.id)
        .count()
    )
    return TrainerCourseOut(
        id=course.id,
        code=course.code,
        name=course.name,
        description=course.description,
        category=course.category,
        status=course.status or "DRAFT",
        sector_id=course.sector_id,
        level_hint=course.level_hint or "Beginner",
        estimated_hours=course.estimated_hours or 20,
        is_demo=bool(course.is_demo),
        active=bool(course.active),
        created_by=course.created_by,
        review_note=course.review_note,
        competencies_count=len(comp_list),
        questions_count=q_count,
        competencies=comp_list,
    )


def serialize_question(q: DiagnosticQuestion) -> QuestionOut:
    opts = []
    if q.options:
        try:
            opts = json.loads(q.options)
        except Exception:
            opts = [q.options]
    return QuestionOut(
        id=q.id,
        course_id=q.course_id,
        competency_id=q.competency_id,
        competency_name=q.competency.name if q.competency else None,
        question_type=q.question_type or "MCQ",
        question=q.question,
        options=opts,
        correct_option=q.correct_option,
        difficulty=q.difficulty or "MEDIUM",
        explanation=q.explanation,
        is_demo=bool(q.is_demo),
        active=bool(q.active),
    )


def check_course_ownership(course: Course, current_user: User):
    user_type = getattr(current_user, "account_type", "LEARNER") or "LEARNER"
    if user_type == "ADMIN":
        return
    if course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this course.",
        )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("/courses", response_model=List[TrainerCourseOut])
def list_trainer_courses(
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """List all courses created by the current trainer (or all if admin)."""
    user_type = getattr(current_user, "account_type", "LEARNER") or "LEARNER"
    query = db.query(Course)
    if user_type != "ADMIN":
        query = query.filter(Course.created_by == current_user.id)
    courses = query.order_by(Course.id.desc()).all()
    return [serialize_trainer_course(c, db) for c in courses]


@router.post("/courses", response_model=TrainerCourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreateRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Create a new course authored by the authenticated trainer in DRAFT status."""
    clean_code = payload.code.strip().upper()
    existing = db.query(Course).filter(Course.code == clean_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course code '{clean_code}' is already in use.",
        )

    cat = payload.category.strip().upper()
    if cat not in ["TECHNICAL", "NON_TECHNICAL"]:
        cat = "TECHNICAL"

    course = Course(
        code=clean_code,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        category=cat,
        sector_id=payload.sector_id,
        level_hint=payload.level_hint or "Beginner",
        estimated_hours=payload.estimated_hours,
        status="DRAFT",
        created_by=current_user.id,
        is_demo=False,
        active=True,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return serialize_trainer_course(course, db)


@router.get("/courses/{course_id}", response_model=TrainerCourseOut)
def get_trainer_course(
    course_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Retrieve full course authoring details including mapped competencies."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)
    return serialize_trainer_course(course, db)


@router.put("/courses/{course_id}", response_model=TrainerCourseOut)
def update_course(
    course_id: int,
    payload: CourseUpdateRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Edit course metadata. Allowed only while course is in DRAFT or ARCHIVED status."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    if course.status in ["PENDING_REVIEW", "PUBLISHED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit course with status '{course.status}'. Withdraw or reject to DRAFT first.",
        )

    if payload.name is not None:
        course.name = payload.name.strip()
    if payload.description is not None:
        course.description = payload.description.strip() if payload.description else None
    if payload.category is not None:
        cat = payload.category.strip().upper()
        if cat in ["TECHNICAL", "NON_TECHNICAL"]:
            course.category = cat
    if payload.sector_id is not None:
        course.sector_id = payload.sector_id
    if payload.level_hint is not None:
        course.level_hint = payload.level_hint
    if payload.estimated_hours is not None:
        course.estimated_hours = payload.estimated_hours

    db.commit()
    db.refresh(course)
    return serialize_trainer_course(course, db)


@router.post("/courses/{course_id}/competencies", response_model=TrainerCourseOut)
def map_course_competency(
    course_id: int,
    payload: MapCompetencyRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Map a competency to the course with required level and priority."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    competency = db.query(Competency).filter(Competency.id == payload.competency_id).first()
    if not competency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competency with ID {payload.competency_id} not found.",
        )

    mapping = (
        db.query(CourseCompetency)
        .filter(
            CourseCompetency.course_id == course.id,
            CourseCompetency.competency_id == competency.id,
        )
        .first()
    )
    prio = payload.priority.strip().upper()
    if prio not in ["HIGH", "MEDIUM", "LOW"]:
        prio = "MEDIUM"

    if mapping:
        mapping.required_level = payload.required_level
        mapping.priority = prio
    else:
        mapping = CourseCompetency(
            course_id=course.id,
            competency_id=competency.id,
            required_level=payload.required_level,
            priority=prio,
        )
        db.add(mapping)

    db.commit()
    db.refresh(course)
    return serialize_trainer_course(course, db)


@router.delete("/courses/{course_id}/competencies/{competency_id}", response_model=TrainerCourseOut)
def unmap_course_competency(
    course_id: int,
    competency_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Unmap a competency from the course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    mapping = (
        db.query(CourseCompetency)
        .filter(
            CourseCompetency.course_id == course.id,
            CourseCompetency.competency_id == competency_id,
        )
        .first()
    )
    if mapping:
        db.delete(mapping)
        db.commit()

    db.refresh(course)
    return serialize_trainer_course(course, db)


@router.get("/courses/{course_id}/questions", response_model=List[QuestionOut])
def list_course_questions(
    course_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """List all diagnostic questions mapped to this course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    questions = (
        db.query(DiagnosticQuestion)
        .filter(DiagnosticQuestion.course_id == course.id)
        .order_by(DiagnosticQuestion.id.asc())
        .all()
    )
    return [serialize_question(q) for q in questions]


@router.post("/courses/{course_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_course_question(
    course_id: int,
    payload: QuestionCreateRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Add a diagnostic question (MCQ or SCENARIO) for this course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    comp = db.query(Competency).filter(Competency.id == payload.competency_id).first()
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competency with ID {payload.competency_id} not found.",
        )

    q_type = payload.question_type.strip().upper()
    if q_type not in ["MCQ", "SCENARIO"]:
        q_type = "MCQ"

    diff = payload.difficulty.strip().upper()
    if diff not in ["EASY", "MEDIUM", "HARD"]:
        diff = "MEDIUM"

    q = DiagnosticQuestion(
        course_id=course.id,
        competency_id=comp.id,
        question_type=q_type,
        question=payload.question.strip(),
        options=json.dumps([opt.strip() for opt in payload.options]),
        correct_option=payload.correct_option,
        difficulty=diff,
        explanation=payload.explanation.strip() if payload.explanation else None,
        is_demo=False,
        active=True,
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return serialize_question(q)


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    payload: QuestionUpdateRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Edit an existing diagnostic question."""
    q = db.query(DiagnosticQuestion).filter(DiagnosticQuestion.id == question_id).first()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} not found.",
        )

    if q.course_id:
        course = db.query(Course).filter(Course.id == q.course_id).first()
        if course:
            check_course_ownership(course, current_user)

    if payload.competency_id is not None:
        comp = db.query(Competency).filter(Competency.id == payload.competency_id).first()
        if not comp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Competency with ID {payload.competency_id} not found.",
            )
        q.competency_id = comp.id

    if payload.question_type is not None:
        q_type = payload.question_type.strip().upper()
        if q_type in ["MCQ", "SCENARIO"]:
            q.question_type = q_type
    if payload.question is not None:
        q.question = payload.question.strip()
    if payload.options is not None:
        q.options = json.dumps([opt.strip() for opt in payload.options])
    if payload.correct_option is not None:
        q.correct_option = payload.correct_option
    if payload.difficulty is not None:
        diff = payload.difficulty.strip().upper()
        if diff in ["EASY", "MEDIUM", "HARD"]:
            q.difficulty = diff
    if payload.explanation is not None:
        q.explanation = payload.explanation.strip() if payload.explanation else None

    db.commit()
    db.refresh(q)
    return serialize_question(q)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Delete a diagnostic question."""
    q = db.query(DiagnosticQuestion).filter(DiagnosticQuestion.id == question_id).first()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} not found.",
        )

    if q.course_id:
        course = db.query(Course).filter(Course.id == q.course_id).first()
        if course:
            check_course_ownership(course, current_user)

    db.delete(q)
    db.commit()
    return None


@router.post("/courses/{course_id}/submit", response_model=TrainerCourseOut)
def submit_course_for_review(
    course_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Submit course for review: transitions status from DRAFT/ARCHIVED to PENDING_REVIEW."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    if course.status not in ["DRAFT", "ARCHIVED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit course in status '{course.status}'. Must be DRAFT or ARCHIVED.",
        )

    # Validate that at least one competency is mapped
    comp_count = db.query(CourseCompetency).filter(CourseCompetency.course_id == course.id).count()
    if comp_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course must have at least one competency mapped before submission.",
        )

    course.status = "PENDING_REVIEW"
    db.commit()
    db.refresh(course)
    return serialize_trainer_course(course, db)


@router.post("/courses/{course_id}/archive", response_model=TrainerCourseOut)
def archive_course(
    course_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Archive an authored course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    course.status = "ARCHIVED"
    db.commit()
    db.refresh(course)
    return serialize_trainer_course(course, db)
