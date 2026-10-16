"""
UPSKILL AI - Courses API (Phase 10)

GET /api/v1/courses            - List active courses (optionally filtered by ?category=TECHNICAL|NON_TECHNICAL)
GET /api/v1/courses/{id}       - Get single course with mapped competencies
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, CourseCompetency, User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/courses", tags=["Courses"])


class CompetencyBrief(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    required_level: int
    priority: str

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


@router.get("", response_model=List[CourseBrief])
def list_courses(
    category: Optional[str] = Query(None, description="Filter by 'TECHNICAL' or 'NON_TECHNICAL'"),
    search: Optional[str] = Query(None, description="Search query matching course name or description"),
    sector_id: Optional[int] = Query(None, description="Filter by sector id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all published active courses. Protected by JWT authentication.
    Supports filtering by category, sector_id, and free-text search.
    Learners and default catalog listings only ever see PUBLISHED courses.
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
    Get course details including mapped competencies.
    Non-published courses (DRAFT, PENDING_REVIEW, ARCHIVED) can only be viewed
    by their trainer creator or by administrators.
    """
    course = db.query(Course).filter(Course.id == course_id, Course.active == True).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    # Visibility check: if course is not PUBLISHED, only creator or admin can view
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

    comp_list = []
    for m in mappings:
        comp_list.append(
            CompetencyBrief(
                id=m.competency.id,
                name=m.competency.name,
                description=m.competency.description,
                required_level=m.required_level,
                priority=m.priority or "MEDIUM",
            )
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
    )
