"""
UPSKILL AI - Courses API (Phase 10 & 14)

GET  /api/v1/courses                    - List published active courses with search & filters
GET  /api/v1/courses/my                 - List current learner's enrolled courses with progress
GET  /api/v1/courses/{id}               - Get single course with mapped competencies & prerequisites
POST /api/v1/courses/{id}/enroll        - Enroll learner in course (prerequisites warning, non-blocking)
GET  /api/v1/courses/{id}/modules       - Curriculum with modules, lessons, and completion state
GET  /api/v1/courses/{id}/progress      - Detailed course progress and completion status
GET  /api/v1/courses/{id}/certificate   - Course completion certificate
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Course,
    CourseCompetency,
    CourseEnrollment,
    CourseModule,
    CoursePrerequisite,
    DiagnosticAssessment,
    Lesson,
    LessonProgress,
    User,
)
from app.routes.auth import get_current_user

router = APIRouter(prefix="/courses", tags=["Courses"])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------------

class CompetencyBrief(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    required_level: int
    priority: str

    class Config:
        from_attributes = True


class PrerequisiteBrief(BaseModel):
    course_id: int
    code: str
    name: str
    is_completed: bool = False


class CourseBrief(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: str
    status: str = "PUBLISHED"
    sector_id: Optional[int] = None
    level_hint: Optional[str] = "Beginner"
    estimated_hours: int = 20
    is_demo: bool
    competency_count: int = 0
    min_diagnostic_score: Optional[float] = None
    has_prerequisites: bool = False
    unmet_prerequisites: List[str] = []

    class Config:
        from_attributes = True


class CourseDetail(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: str
    status: str = "PUBLISHED"
    sector_id: Optional[int] = None
    level_hint: Optional[str] = "Beginner"
    estimated_hours: int = 20
    is_demo: bool
    competencies: List[CompetencyBrief]
    min_diagnostic_score: Optional[float] = None
    prerequisites: List[PrerequisiteBrief] = []
    unmet_prerequisites: List[str] = []
    is_enrolled: bool = False
    progress_percent: float = 0.0

    class Config:
        from_attributes = True


class EnrolledCourseOut(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    category: str
    level_hint: Optional[str] = "Beginner"
    estimated_hours: int = 20
    status: str
    progress_percent: float
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_lessons: int = 0
    completed_lessons: int = 0
    has_certificate: bool = False
    certificate_id: Optional[str] = None
    unmet_prerequisites: List[str] = []


class EnrollmentOut(BaseModel):
    enrollment_id: int
    user_id: int
    course_id: int
    course_name: str
    status: str
    started_at: Optional[str] = None
    progress_percent: float = 0.0
    unmet_prerequisites: List[str] = []
    warning: Optional[str] = None


class LessonBrief(BaseModel):
    id: int
    module_id: int
    title: str
    lesson_type: str
    order: int
    estimated_minutes: int
    completed: bool = False
    completed_at: Optional[str] = None


class ModuleDetail(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    order: int
    lessons: List[LessonBrief] = []


class CourseCurriculumOut(BaseModel):
    course_id: int
    course_name: str
    total_modules: int
    total_lessons: int
    completed_lessons: int
    progress_percent: float
    status: str
    modules: List[ModuleDetail]
    prerequisites: List[PrerequisiteBrief] = []
    unmet_prerequisites: List[str] = []
    warning: Optional[str] = None


class CourseProgressOut(BaseModel):
    course_id: int
    course_name: str
    status: str
    progress_percent: float
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_modules: int
    total_lessons: int
    completed_lessons: int
    min_diagnostic_score: Optional[float] = None
    diagnostic_score_met: bool = True
    user_diagnostic_score: Optional[float] = None
    certificate: Optional[dict] = None
    unmet_prerequisites: List[str] = []
    warning: Optional[str] = None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def check_course_prerequisites(db: Session, course_id: int, user_id: int):
    """
    Returns (all_prereqs_list, unmet_names_list)
    """
    prereqs = (
        db.query(CoursePrerequisite)
        .filter(CoursePrerequisite.course_id == course_id)
        .all()
    )
    if not prereqs:
        return [], []

    all_prereqs = []
    unmet = []
    for p in prereqs:
        prereq_course = p.prerequisite_course
        if not prereq_course:
            continue
        enr = (
            db.query(CourseEnrollment)
            .filter(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == prereq_course.id,
                CourseEnrollment.status == "COMPLETED",
            )
            .first()
        )
        is_done = bool(enr)
        all_prereqs.append(
            PrerequisiteBrief(
                course_id=prereq_course.id,
                code=prereq_course.code,
                name=prereq_course.name,
                is_completed=is_done,
            )
        )
        if not is_done:
            unmet.append(prereq_course.name)

    return all_prereqs, unmet


def build_certificate_dict(enrollment: CourseEnrollment, user: User, course: Course) -> dict:
    cert_id = f"UPSKILL-CERT-{enrollment.id:04d}-{user.id}-{course.id}"
    return {
        "certificate_id": cert_id,
        "course_id": course.id,
        "course_name": course.name,
        "course_code": course.code,
        "recipient_name": user.name,
        "recipient_email": user.email,
        "issue_date": enrollment.completed_at or now_iso(),
        "level_hint": course.level_hint or "Intermediate",
        "estimated_hours": getattr(course, "estimated_hours", 20) or 20,
        "issuer": "UPSKILL AI Learning & Competency Intelligence Platform",
        "verification_url": f"/api/v1/courses/{course.id}/certificate",
        "status": "VERIFIED",
    }


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("", response_model=List[CourseBrief])
def list_courses(
    category: Optional[str] = Query(None, description="Filter by 'TECHNICAL' or 'NON_TECHNICAL'"),
    search: Optional[str] = Query(None, description="Search query matching course name or description"),
    sector_id: Optional[int] = Query(None, description="Filter by sector id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all published active courses.
    Includes prerequisite status warning if any unmet prerequisites exist for current learner.
    """
    query = db.query(Course).filter(Course.active == True, Course.status == "PUBLISHED")
    if category:
        query = query.filter(Course.category == category.upper())
    if sector_id:
        query = query.filter(Course.sector_id == sector_id)
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        from sqlalchemy import func
        query = query.filter(
            func.lower(Course.name).like(term) | func.lower(Course.description).like(term)
        )

    courses = query.order_by(Course.id.asc()).all()
    results = []
    for c in courses:
        comp_count = (
            db.query(CourseCompetency)
            .filter(CourseCompetency.course_id == c.id)
            .count()
        )
        all_prereqs, unmet = check_course_prerequisites(db, c.id, current_user.id)
        results.append(
            CourseBrief(
                id=c.id,
                code=c.code,
                name=c.name,
                description=c.description,
                category=c.category,
                status=c.status or "PUBLISHED",
                sector_id=c.sector_id,
                level_hint=c.level_hint or "Beginner",
                estimated_hours=getattr(c, "estimated_hours", 20) or 20,
                is_demo=bool(c.is_demo),
                competency_count=comp_count,
                min_diagnostic_score=getattr(c, "min_diagnostic_score", None),
                has_prerequisites=len(all_prereqs) > 0,
                unmet_prerequisites=unmet,
            )
        )
    return results


@router.get("/my", response_model=List[EnrolledCourseOut])
def get_my_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all courses the authenticated learner is enrolled in with live progress.
    """
    enrollments = (
        db.query(CourseEnrollment)
        .filter(CourseEnrollment.user_id == current_user.id)
        .order_by(CourseEnrollment.id.desc())
        .all()
    )

    results = []
    for enr in enrollments:
        course = enr.course
        if not course:
            continue

        total_lessons = (
            db.query(Lesson)
            .join(CourseModule, Lesson.module_id == CourseModule.id)
            .filter(CourseModule.course_id == course.id)
            .count()
        )

        completed_lessons = (
            db.query(LessonProgress)
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .join(CourseModule, Lesson.module_id == CourseModule.id)
            .filter(
                CourseModule.course_id == course.id,
                LessonProgress.user_id == current_user.id,
                LessonProgress.completed == True,
            )
            .count()
        )

        cert_id = (
            f"UPSKILL-CERT-{enr.id:04d}-{current_user.id}-{course.id}"
            if enr.status == "COMPLETED"
            else None
        )

        _, unmet = check_course_prerequisites(db, course.id, current_user.id)

        results.append(
            EnrolledCourseOut(
                course_id=course.id,
                course_code=course.code,
                course_name=course.name,
                category=course.category,
                level_hint=course.level_hint or "Beginner",
                estimated_hours=getattr(course, "estimated_hours", 20) or 20,
                status=enr.status,
                progress_percent=enr.progress_percent,
                started_at=enr.started_at,
                completed_at=enr.completed_at,
                total_lessons=total_lessons,
                completed_lessons=completed_lessons,
                has_certificate=(enr.status == "COMPLETED"),
                certificate_id=cert_id,
                unmet_prerequisites=unmet,
            )
        )
    return results


@router.get("/{course_id}", response_model=CourseDetail)
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get course details including mapped competencies and prerequisites.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.active == True).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    # Visibility check
    if course.status != "PUBLISHED":
        user_type = getattr(current_user, "account_type", "LEARNER") or "LEARNER"
        is_creator = (course.created_by == current_user.id)
        if user_type != "ADMIN" and not (user_type == "TRAINER" and is_creator):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

    mappings = (
        db.query(CourseCompetency)
        .filter(CourseCompetency.course_id == course.id)
        .all()
    )
    comp_list = [
        CompetencyBrief(
            id=m.competency.id,
            name=m.competency.name,
            description=m.competency.description,
            required_level=m.required_level,
            priority=m.priority or "MEDIUM",
        )
        for m in mappings
    ]

    all_prereqs, unmet = check_course_prerequisites(db, course.id, current_user.id)

    enr = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id,
        )
        .first()
    )

    return CourseDetail(
        id=course.id,
        code=course.code,
        name=course.name,
        description=course.description,
        category=course.category,
        status=course.status or "PUBLISHED",
        sector_id=course.sector_id,
        level_hint=course.level_hint or "Beginner",
        estimated_hours=getattr(course, "estimated_hours", 20) or 20,
        is_demo=bool(course.is_demo),
        competencies=comp_list,
        min_diagnostic_score=getattr(course, "min_diagnostic_score", None),
        prerequisites=all_prereqs,
        unmet_prerequisites=unmet,
        is_enrolled=bool(enr),
        progress_percent=enr.progress_percent if enr else 0.0,
    )


@router.post("/{course_id}/enroll", response_model=EnrollmentOut)
def enroll_in_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enroll the authenticated learner in a course.
    If prerequisites are unmet, returns a warning message but does NOT block enrollment.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.active == True).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    # Visibility check
    if course.status != "PUBLISHED":
        user_type = getattr(current_user, "account_type", "LEARNER") or "LEARNER"
        is_creator = (course.created_by == current_user.id)
        if user_type != "ADMIN" and not (user_type == "TRAINER" and is_creator):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

    # Check prerequisites
    _, unmet = check_course_prerequisites(db, course.id, current_user.id)
    warning = None
    if unmet:
        warning = f"Prerequisite recommended: {', '.join(unmet)}. You can still proceed with enrollment."

    enrollment = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id,
        )
        .first()
    )

    if not enrollment:
        enrollment = CourseEnrollment(
            user_id=current_user.id,
            course_id=course.id,
            status="ENROLLED",
            started_at=now_iso(),
            progress_percent=0.0,
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

    return EnrollmentOut(
        enrollment_id=enrollment.id,
        user_id=current_user.id,
        course_id=course.id,
        course_name=course.name,
        status=enrollment.status,
        started_at=enrollment.started_at,
        progress_percent=enrollment.progress_percent,
        unmet_prerequisites=unmet,
        warning=warning,
    )


@router.get("/{course_id}/modules", response_model=CourseCurriculumOut)
def get_course_curriculum(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get full course curriculum (modules and lessons) with learner completion status.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.active == True).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    # Visibility check
    if course.status != "PUBLISHED":
        user_type = getattr(current_user, "account_type", "LEARNER") or "LEARNER"
        is_creator = (course.created_by == current_user.id)
        if user_type != "ADMIN" and not (user_type == "TRAINER" and is_creator):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )

    # Fetch learner's completed lesson IDs
    completed_rows = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.completed == True,
        )
        .all()
    )
    completed_map = {r.lesson_id: r.completed_at for r in completed_rows}

    modules = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course.id)
        .order_by(CourseModule.order.asc(), CourseModule.id.asc())
        .all()
    )

    module_details = []
    total_lessons = 0
    completed_count = 0

    for m in modules:
        lessons = (
            db.query(Lesson)
            .filter(Lesson.module_id == m.id)
            .order_by(Lesson.order.asc(), Lesson.id.asc())
            .all()
        )
        lesson_briefs = []
        for l in lessons:
            total_lessons += 1
            is_done = l.id in completed_map
            if is_done:
                completed_count += 1
            lesson_briefs.append(
                LessonBrief(
                    id=l.id,
                    module_id=m.id,
                    title=l.title,
                    lesson_type=l.lesson_type or "TEXT",
                    order=l.order,
                    estimated_minutes=l.estimated_minutes or 15,
                    completed=is_done,
                    completed_at=completed_map.get(l.id),
                )
            )
        module_details.append(
            ModuleDetail(
                id=m.id,
                course_id=course.id,
                title=m.title,
                description=m.description,
                order=m.order,
                lessons=lesson_briefs,
            )
        )

    enr = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id,
        )
        .first()
    )
    status_str = enr.status if enr else "NOT_ENROLLED"
    prog_pct = enr.progress_percent if enr else (
        round((completed_count / total_lessons) * 100.0, 1) if total_lessons > 0 else 0.0
    )

    all_prereqs, unmet = check_course_prerequisites(db, course.id, current_user.id)
    warning = (
        f"Prerequisite recommended: {', '.join(unmet)}" if unmet else None
    )

    return CourseCurriculumOut(
        course_id=course.id,
        course_name=course.name,
        total_modules=len(module_details),
        total_lessons=total_lessons,
        completed_lessons=completed_count,
        progress_percent=prog_pct,
        status=status_str,
        modules=module_details,
        prerequisites=all_prereqs,
        unmet_prerequisites=unmet,
        warning=warning,
    )


@router.get("/{course_id}/progress", response_model=CourseProgressOut)
def get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed progress for a course, checking lesson counts, diagnostic score thresholds,
    and certificate eligibility.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.active == True).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    enr = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id,
        )
        .first()
    )

    total_modules = (
        db.query(CourseModule)
        .filter(CourseModule.course_id == course.id)
        .count()
    )

    total_lessons = (
        db.query(Lesson)
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(CourseModule.course_id == course.id)
        .count()
    )

    completed_lessons = (
        db.query(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(
            CourseModule.course_id == course.id,
            LessonProgress.user_id == current_user.id,
            LessonProgress.completed == True,
        )
        .count()
    )

    min_score = getattr(course, "min_diagnostic_score", None)
    diag_score_met = True
    user_score = None
    if min_score is not None:
        best_diag = (
            db.query(DiagnosticAssessment)
            .filter(DiagnosticAssessment.learner_id == current_user.id)
            .order_by(DiagnosticAssessment.score_percent.desc())
            .first()
        )
        if best_diag:
            user_score = best_diag.score_percent
            diag_score_met = (best_diag.score_percent >= min_score)
        else:
            diag_score_met = False

    cert_data = None
    if enr and enr.status == "COMPLETED":
        cert_data = build_certificate_dict(enr, current_user, course)

    _, unmet = check_course_prerequisites(db, course.id, current_user.id)

    return CourseProgressOut(
        course_id=course.id,
        course_name=course.name,
        status=enr.status if enr else "NOT_ENROLLED",
        progress_percent=enr.progress_percent if enr else 0.0,
        started_at=enr.started_at if enr else None,
        completed_at=enr.completed_at if enr else None,
        total_modules=total_modules,
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        min_diagnostic_score=min_score,
        diagnostic_score_met=diag_score_met,
        user_diagnostic_score=user_score,
        certificate=cert_data,
        unmet_prerequisites=unmet,
        warning=f"Prerequisite recommended: {', '.join(unmet)}" if unmet else None,
    )


@router.get("/{course_id}/certificate")
def get_course_certificate(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve certificate for a completed course.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.active == True).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    enr = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id,
        )
        .first()
    )

    if not enr or enr.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course has not been completed yet.",
        )

    return build_certificate_dict(enr, current_user, course)
