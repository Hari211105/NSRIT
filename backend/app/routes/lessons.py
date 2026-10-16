"""
UPSKILL AI - Lessons API (Phase 14)

GET  /api/v1/lessons/{lesson_id}           - Retrieve lesson content, type, navigation, and completion state
POST /api/v1/lessons/{lesson_id}/complete  - Mark lesson completed, recalculate course progress & certificate
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Course,
    CourseEnrollment,
    CourseModule,
    DiagnosticAssessment,
    Lesson,
    LessonProgress,
    User,
)
from app.routes.auth import get_current_user

router = APIRouter(prefix="/lessons", tags=["Lessons"])


class LessonDetailOut(BaseModel):
    id: int
    module_id: int
    course_id: int
    course_name: str
    module_title: str
    title: str
    lesson_type: str
    body: str
    order: int
    estimated_minutes: int
    completed: bool = False
    completed_at: Optional[str] = None
    prev_lesson_id: Optional[int] = None
    next_lesson_id: Optional[int] = None

    class Config:
        from_attributes = True


class LessonCompleteOut(BaseModel):
    lesson_id: int
    completed: bool
    completed_at: str
    course_id: int
    course_name: str
    course_status: str
    progress_percent: float
    total_lessons: int
    completed_lessons: int
    is_course_completed: bool
    certificate: Optional[dict] = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/{lesson_id}", response_model=LessonDetailOut)
def get_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get lesson content and metadata. Auto-enrolls the user into the course if not enrolled.
    Returns previous/next lesson IDs for linear navigation.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID {lesson_id} not found.",
        )

    module = lesson.module
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found for this lesson.",
        )

    course = module.course
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found for this lesson.",
        )

    # Visibility check
    if course.status != "PUBLISHED":
        user_type = getattr(current_user, "account_type", "LEARNER") or "LEARNER"
        is_creator = (course.created_by == current_user.id)
        if user_type != "ADMIN" and not (user_type == "TRAINER" and is_creator):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson with ID {lesson_id} not found.",
            )

    # Ensure learner enrollment exists
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

    # Check progress for this lesson
    prog = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )
    completed = bool(prog and prog.completed)
    completed_at = prog.completed_at if prog else None

    # Determine linear previous and next lessons across all modules in this course
    all_lessons = (
        db.query(Lesson)
        .join(CourseModule, Lesson.module_id == CourseModule.id)
        .filter(CourseModule.course_id == course.id)
        .order_by(CourseModule.order.asc(), Lesson.order.asc(), Lesson.id.asc())
        .all()
    )

    lesson_ids = [l.id for l in all_lessons]
    idx = lesson_ids.index(lesson.id) if lesson.id in lesson_ids else -1
    prev_id = lesson_ids[idx - 1] if idx > 0 else None
    next_id = lesson_ids[idx + 1] if idx != -1 and idx < len(lesson_ids) - 1 else None

    return LessonDetailOut(
        id=lesson.id,
        module_id=module.id,
        course_id=course.id,
        course_name=course.name,
        module_title=module.title,
        title=lesson.title,
        lesson_type=lesson.lesson_type or "TEXT",
        body=lesson.body,
        order=lesson.order,
        estimated_minutes=lesson.estimated_minutes or 15,
        completed=completed,
        completed_at=completed_at,
        prev_lesson_id=prev_id,
        next_lesson_id=next_id,
    )


@router.post("/{lesson_id}/complete", response_model=LessonCompleteOut)
def complete_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a lesson as completed by the current user.
    Recalculates the course progress percentage and checks for course completion.
    If course completion conditions are met (all lessons completed + optional min diagnostic score),
    sets enrollment to COMPLETED and generates certificate info.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID {lesson_id} not found.",
        )

    module = lesson.module
    course = module.course if module else None
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated course not found.",
        )

    # 1. Record / update lesson progress
    prog = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )
    iso_timestamp = now_iso()
    if not prog:
        prog = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson.id,
            completed=True,
            completed_at=iso_timestamp,
        )
        db.add(prog)
    else:
        prog.completed = True
        if not prog.completed_at:
            prog.completed_at = iso_timestamp

    db.flush()

    # 2. Update CourseEnrollment
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
            status="IN_PROGRESS",
            started_at=iso_timestamp,
            progress_percent=0.0,
        )
        db.add(enrollment)
        db.flush()

    # 3. Calculate total and completed lessons for the course
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

    progress_percent = (
        round((completed_lessons / total_lessons) * 100.0, 1)
        if total_lessons > 0
        else 100.0
    )
    enrollment.progress_percent = min(progress_percent, 100.0)

    # 4. Check completion rules:
    # All lessons done + optional minimum diagnostic score set per course
    min_score = getattr(course, "min_diagnostic_score", None)
    diag_score_met = True
    if min_score is not None:
        best_diag = (
            db.query(DiagnosticAssessment)
            .filter(
                DiagnosticAssessment.learner_id == current_user.id,
                DiagnosticAssessment.score_percent >= min_score,
            )
            .first()
        )
        diag_score_met = bool(best_diag)

    is_completed = (completed_lessons >= total_lessons) and diag_score_met
    certificate_data = None

    if is_completed:
        enrollment.status = "COMPLETED"
        if not enrollment.completed_at:
            enrollment.completed_at = iso_timestamp
        db.flush()
        cert_id = f"UPSKILL-CERT-{enrollment.id:04d}-{current_user.id}-{course.id}"
        certificate_data = {
            "certificate_id": cert_id,
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.code,
            "recipient_name": current_user.name,
            "recipient_email": current_user.email,
            "issue_date": enrollment.completed_at or iso_timestamp,
            "level_hint": course.level_hint or "Intermediate",
            "estimated_hours": getattr(course, "estimated_hours", 20) or 20,
            "issuer": "UPSKILL AI Learning & Competency Intelligence Platform",
            "verification_url": f"/api/v1/courses/{course.id}/certificate",
            "status": "VERIFIED",
        }
    elif completed_lessons > 0:
        enrollment.status = "IN_PROGRESS"

    db.commit()

    return LessonCompleteOut(
        lesson_id=lesson.id,
        completed=True,
        completed_at=prog.completed_at,
        course_id=course.id,
        course_name=course.name,
        course_status=enrollment.status,
        progress_percent=enrollment.progress_percent,
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        is_course_completed=is_completed,
        certificate=certificate_data,
    )
