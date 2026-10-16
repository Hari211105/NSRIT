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
from app.models import Course, CourseCompetency, Competency, DiagnosticQuestion, User, CourseModule, Lesson, CoursePrerequisite
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
    modules_count: int = 0
    lessons_count: int = 0
    min_diagnostic_score: Optional[float] = None
    competencies: List[CompetencyItemOut] = []

    class Config:
        from_attributes = True


class TrainerLessonOut(BaseModel):
    id: int
    module_id: int
    title: str
    lesson_type: str
    body: str
    order: int
    estimated_minutes: int
    is_demo: bool = False

    class Config:
        from_attributes = True


class TrainerModuleOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    order: int
    is_demo: bool = False
    lessons_count: int = 0
    lessons: List[TrainerLessonOut] = []

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
    min_diagnostic_score: Optional[float] = None


class CourseUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    sector_id: Optional[int] = None
    level_hint: Optional[str] = None
    estimated_hours: Optional[int] = Field(None, ge=1, le=500)
    min_diagnostic_score: Optional[float] = None


class ModuleCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None


class ModuleUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    order: Optional[int] = None


class LessonCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    lesson_type: str = Field("TEXT", description="'TEXT' | 'LINK' | 'VIDEO_URL'")
    body: str = Field(..., min_length=1)
    order: Optional[int] = None
    estimated_minutes: int = Field(15, ge=1, le=600)


class LessonUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    lesson_type: Optional[str] = None
    body: Optional[str] = None
    order: Optional[int] = None
    estimated_minutes: Optional[int] = Field(None, ge=1, le=600)


class ReorderItem(BaseModel):
    id: int
    order: int


class ReorderCurriculumRequest(BaseModel):
    modules: Optional[List[ReorderItem]] = None
    lessons: Optional[List[ReorderItem]] = None


class PrerequisiteItemOut(BaseModel):
    id: int
    prerequisite_course_id: int
    course_code: str
    course_name: str


class PrerequisiteAddRequest(BaseModel):
    prerequisite_course_id: int


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
    mod_count = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course.id)
        .count()
    )
    les_count = (
        db.query(Lesson)
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(CourseModule.course_id == course.id)
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
        modules_count=mod_count,
        lessons_count=les_count,
        min_diagnostic_score=getattr(course, "min_diagnostic_score", None),
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
        min_diagnostic_score=payload.min_diagnostic_score,
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
    if payload.min_diagnostic_score is not None:
        course.min_diagnostic_score = payload.min_diagnostic_score

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


# ------------------------------------------------------------------
# Curriculum Authoring: Modules, Lessons, & Reordering
# ------------------------------------------------------------------

@router.get("/courses/{course_id}/curriculum", response_model=List[TrainerModuleOut])
def get_trainer_curriculum(
    course_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Get all modules and lessons for a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    modules = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course.id)
        .order_by(CourseModule.order.asc(), CourseModule.id.asc())
        .all()
    )
    result = []
    for m in modules:
        lessons = (
            db.query(Lesson)
            .filter(Lesson.module_id == m.id)
            .order_by(Lesson.order.asc(), Lesson.id.asc())
            .all()
        )
        lesson_outs = [
            TrainerLessonOut(
                id=l.id,
                module_id=m.id,
                title=l.title,
                lesson_type=l.lesson_type or "TEXT",
                body=l.body,
                order=l.order,
                estimated_minutes=l.estimated_minutes or 15,
                is_demo=bool(l.is_demo),
            )
            for l in lessons
        ]
        result.append(
            TrainerModuleOut(
                id=m.id,
                course_id=course.id,
                title=m.title,
                description=m.description,
                order=m.order,
                is_demo=bool(m.is_demo),
                lessons_count=len(lesson_outs),
                lessons=lesson_outs,
            )
        )
    return result


@router.post("/courses/{course_id}/modules", response_model=TrainerModuleOut, status_code=status.HTTP_201_CREATED)
def create_course_module(
    course_id: int,
    payload: ModuleCreateRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Add a new thematic module to a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    order = payload.order
    if order is None:
        last_mod = (
            db.query(CourseModule)
            .filter(CourseModule.course_id == course.id)
            .order_by(CourseModule.order.desc())
            .first()
        )
        order = (last_mod.order + 1) if last_mod else 1

    module = CourseModule(
        course_id=course.id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        order=order,
        is_demo=False,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return TrainerModuleOut(
        id=module.id,
        course_id=course.id,
        title=module.title,
        description=module.description,
        order=module.order,
        is_demo=module.is_demo,
        lessons_count=0,
        lessons=[],
    )


@router.put("/modules/{module_id}", response_model=TrainerModuleOut)
def update_course_module(
    module_id: int,
    payload: ModuleUpdateRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Update an existing module's title, description, or order."""
    module = db.query(CourseModule).filter(CourseModule.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module with ID {module_id} not found.",
        )
    course = module.course
    if course:
        check_course_ownership(course, current_user)

    if payload.title is not None:
        module.title = payload.title.strip()
    if payload.description is not None:
        module.description = payload.description.strip() if payload.description else None
    if payload.order is not None:
        module.order = payload.order

    db.commit()
    db.refresh(module)

    lessons = (
        db.query(Lesson)
        .filter(Lesson.module_id == module.id)
        .order_by(Lesson.order.asc(), Lesson.id.asc())
        .all()
    )
    lesson_outs = [
        TrainerLessonOut(
            id=l.id,
            module_id=module.id,
            title=l.title,
            lesson_type=l.lesson_type or "TEXT",
            body=l.body,
            order=l.order,
            estimated_minutes=l.estimated_minutes or 15,
            is_demo=bool(l.is_demo),
        )
        for l in lessons
    ]
    return TrainerModuleOut(
        id=module.id,
        course_id=module.course_id,
        title=module.title,
        description=module.description,
        order=module.order,
        is_demo=module.is_demo,
        lessons_count=len(lesson_outs),
        lessons=lesson_outs,
    )


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_module(
    module_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Delete a module and all its lessons."""
    module = db.query(CourseModule).filter(CourseModule.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module with ID {module_id} not found.",
        )
    course = module.course
    if course:
        check_course_ownership(course, current_user)

    db.delete(module)
    db.commit()
    return None


@router.post("/modules/{module_id}/lessons", response_model=TrainerLessonOut, status_code=status.HTTP_201_CREATED)
def create_module_lesson(
    module_id: int,
    payload: LessonCreateRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Create a new lesson inside a module."""
    module = db.query(CourseModule).filter(CourseModule.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module with ID {module_id} not found.",
        )
    course = module.course
    if course:
        check_course_ownership(course, current_user)

    order = payload.order
    if order is None:
        last_les = (
            db.query(Lesson)
            .filter(Lesson.module_id == module.id)
            .order_by(Lesson.order.desc())
            .first()
        )
        order = (last_les.order + 1) if last_les else 1

    l_type = payload.lesson_type.strip().upper()
    if l_type not in ["TEXT", "LINK", "VIDEO_URL"]:
        l_type = "TEXT"

    lesson = Lesson(
        module_id=module.id,
        title=payload.title.strip(),
        lesson_type=l_type,
        body=payload.body.strip(),
        order=order,
        estimated_minutes=payload.estimated_minutes,
        is_demo=False,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return TrainerLessonOut(
        id=lesson.id,
        module_id=module.id,
        title=lesson.title,
        lesson_type=lesson.lesson_type,
        body=lesson.body,
        order=lesson.order,
        estimated_minutes=lesson.estimated_minutes,
        is_demo=lesson.is_demo,
    )


@router.put("/lessons/{lesson_id}", response_model=TrainerLessonOut)
def update_module_lesson(
    lesson_id: int,
    payload: LessonUpdateRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Update an existing lesson."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID {lesson_id} not found.",
        )
    course = lesson.module.course if lesson.module else None
    if course:
        check_course_ownership(course, current_user)

    if payload.title is not None:
        lesson.title = payload.title.strip()
    if payload.lesson_type is not None:
        l_type = payload.lesson_type.strip().upper()
        if l_type in ["TEXT", "LINK", "VIDEO_URL"]:
            lesson.lesson_type = l_type
    if payload.body is not None:
        lesson.body = payload.body.strip()
    if payload.order is not None:
        lesson.order = payload.order
    if payload.estimated_minutes is not None:
        lesson.estimated_minutes = payload.estimated_minutes

    db.commit()
    db.refresh(lesson)
    return TrainerLessonOut(
        id=lesson.id,
        module_id=lesson.module_id,
        title=lesson.title,
        lesson_type=lesson.lesson_type,
        body=lesson.body,
        order=lesson.order,
        estimated_minutes=lesson.estimated_minutes,
        is_demo=lesson.is_demo,
    )


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module_lesson(
    lesson_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Delete a lesson."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID {lesson_id} not found.",
        )
    course = lesson.module.course if lesson.module else None
    if course:
        check_course_ownership(course, current_user)

    db.delete(lesson)
    db.commit()
    return None


@router.post("/courses/{course_id}/reorder")
def reorder_curriculum(
    course_id: int,
    payload: ReorderCurriculumRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Bulk reorder modules and/or lessons within a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    if payload.modules:
        for item in payload.modules:
            mod = db.query(CourseModule).filter(CourseModule.id == item.id, CourseModule.course_id == course.id).first()
            if mod:
                mod.order = item.order

    if payload.lessons:
        for item in payload.lessons:
            les = (
                db.query(Lesson)
                .join(CourseModule, Lesson.module_id == CourseModule.id)
                .filter(Lesson.id == item.id, CourseModule.course_id == course.id)
                .first()
            )
            if les:
                les.order = item.order

    db.commit()
    return {"status": "success", "message": "Curriculum reordered successfully."}


# ------------------------------------------------------------------
# Course Prerequisites Management
# ------------------------------------------------------------------

@router.get("/courses/{course_id}/prerequisites", response_model=List[PrerequisiteItemOut])
def get_trainer_prerequisites(
    course_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Get all prerequisite courses configured for this course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    prereqs = db.query(CoursePrerequisite).filter(CoursePrerequisite.course_id == course.id).all()
    results = []
    for p in prereqs:
        target = p.prerequisite_course
        if target:
            results.append(
                PrerequisiteItemOut(
                    id=p.id,
                    prerequisite_course_id=target.id,
                    course_code=target.code,
                    course_name=target.name,
                )
            )
    return results


@router.post("/courses/{course_id}/prerequisites", response_model=PrerequisiteItemOut, status_code=status.HTTP_201_CREATED)
def add_course_prerequisite(
    course_id: int,
    payload: PrerequisiteAddRequest,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Add a prerequisite course dependency."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    if payload.prerequisite_course_id == course.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A course cannot be a prerequisite of itself.",
        )

    target = db.query(Course).filter(Course.id == payload.prerequisite_course_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target prerequisite course with ID {payload.prerequisite_course_id} not found.",
        )

    existing = (
        db.query(CoursePrerequisite)
        .filter(
            CoursePrerequisite.course_id == course.id,
            CoursePrerequisite.prerequisite_course_id == target.id,
        )
        .first()
    )
    if existing:
        return PrerequisiteItemOut(
            id=existing.id,
            prerequisite_course_id=target.id,
            course_code=target.code,
            course_name=target.name,
        )

    prereq = CoursePrerequisite(
        course_id=course.id,
        prerequisite_course_id=target.id,
    )
    db.add(prereq)
    db.commit()
    db.refresh(prereq)

    return PrerequisiteItemOut(
        id=prereq.id,
        prerequisite_course_id=target.id,
        course_code=target.code,
        course_name=target.name,
    )


@router.delete("/courses/{course_id}/prerequisites/{prereq_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_course_prerequisite(
    course_id: int,
    prereq_id: int,
    current_user: User = Depends(require_account_types("TRAINER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Remove a prerequisite dependency."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    check_course_ownership(course, current_user)

    prereq = (
        db.query(CoursePrerequisite)
        .filter(
            CoursePrerequisite.id == prereq_id,
            CoursePrerequisite.course_id == course.id,
        )
        .first()
    )
    if not prereq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prerequisite with ID {prereq_id} not found on this course.",
        )

    db.delete(prereq)
    db.commit()
    return None

