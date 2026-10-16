"""
UPSKILL AI - Admin Management Endpoints (Phase 13)
Access strictly restricted to ADMIN accounts.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Course, DiagnosticAssessment, QuizAssessment, AuditLog
from app.routes.auth import require_account_types, serialize_user, UserOut
from app.routes.trainer import TrainerCourseOut, serialize_trainer_course


router = APIRouter(prefix="/admin", tags=["Admin Console"])


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class ChangeRoleRequest(BaseModel):
    account_type: str = Field(..., description="'LEARNER' | 'TRAINER' | 'ADMIN'")


class ChangeStatusRequest(BaseModel):
    is_active: bool


class RejectCourseRequest(BaseModel):
    note: str = Field(..., min_length=2, max_length=1000)


class PlatformStatsOut(BaseModel):
    total_users: int
    learners_count: int
    trainers_count: int
    admins_count: int
    active_users: int
    total_courses: int
    published_courses: int
    pending_courses: int
    draft_courses: int
    archived_courses: int
    total_diagnostics_taken: int
    total_quizzes_taken: int


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[int] = None
    details: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UsersListResponse(BaseModel):
    total: int
    users: List[UserOut]


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------

def log_admin_action(
    db: Session,
    admin_id: int,
    action: str,
    target_type: str,
    target_id: Optional[int],
    details: str,
):
    audit = AuditLog(
        user_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(audit)
    db.commit()


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("/users", response_model=UsersListResponse)
def list_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_account_types("ADMIN")),
    db: Session = Depends(get_db),
):
    """List or search all platform users."""
    query = db.query(User)
    if account_type:
        query = query.filter(User.account_type == account_type.strip().upper())
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            func.lower(User.name).like(term) | func.lower(User.email).like(term)
        )

    total = query.count()
    users = query.order_by(User.id.asc()).offset(offset).limit(limit).all()
    return UsersListResponse(
        total=total,
        users=[serialize_user(u) for u in users],
    )


@router.patch("/users/{user_id}/role", response_model=UserOut)
def change_user_role(
    user_id: int,
    payload: ChangeRoleRequest,
    current_user: User = Depends(require_account_types("ADMIN")),
    db: Session = Depends(get_db),
):
    """Change a user's account_type ('LEARNER', 'TRAINER', 'ADMIN')."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    new_type = payload.account_type.strip().upper()
    if new_type not in ["LEARNER", "TRAINER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="account_type must be one of: 'LEARNER', 'TRAINER', 'ADMIN'.",
        )

    old_type = target.account_type or "LEARNER"
    if old_type == new_type:
        return serialize_user(target)

    target.account_type = new_type
    db.commit()
    db.refresh(target)

    log_admin_action(
        db,
        admin_id=current_user.id,
        action="ROLE_CHANGE",
        target_type="USER",
        target_id=target.id,
        details=f"Changed account type for {target.email} from {old_type} to {new_type}",
    )

    return serialize_user(target)


@router.patch("/users/{user_id}/status", response_model=UserOut)
def change_user_status(
    user_id: int,
    payload: ChangeStatusRequest,
    current_user: User = Depends(require_account_types("ADMIN")),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a user account. Admins cannot deactivate themselves."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if target.id == current_user.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own administrator account.",
        )

    old_status = bool(target.is_active)
    target.is_active = payload.is_active
    db.commit()
    db.refresh(target)

    status_str = "ACTIVE" if payload.is_active else "DEACTIVATED"
    log_admin_action(
        db,
        admin_id=current_user.id,
        action="USER_STATUS_CHANGE",
        target_type="USER",
        target_id=target.id,
        details=f"Changed user status for {target.email} to {status_str}",
    )

    return serialize_user(target)


@router.get("/courses/pending", response_model=List[TrainerCourseOut])
def list_pending_courses(
    current_user: User = Depends(require_account_types("ADMIN")),
    db: Session = Depends(get_db),
):
    """List all courses currently awaiting administrative review."""
    courses = (
        db.query(Course)
        .filter(Course.status == "PENDING_REVIEW")
        .order_by(Course.id.asc())
        .all()
    )
    return [serialize_trainer_course(c, db) for c in courses]


@router.post("/courses/{course_id}/approve", response_model=TrainerCourseOut)
def approve_course(
    course_id: int,
    current_user: User = Depends(require_account_types("ADMIN")),
    db: Session = Depends(get_db),
):
    """Approve a course: transitions status from PENDING_REVIEW to PUBLISHED."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    if course.status != "PENDING_REVIEW":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve course with status '{course.status}'. Must be PENDING_REVIEW.",
        )

    course.status = "PUBLISHED"
    course.review_note = None
    db.commit()
    db.refresh(course)

    log_admin_action(
        db,
        admin_id=current_user.id,
        action="COURSE_APPROVE",
        target_type="COURSE",
        target_id=course.id,
        details=f"Approved course {course.code} ('{course.name}') for publication",
    )

    return serialize_trainer_course(course, db)


@router.post("/courses/{course_id}/reject", response_model=TrainerCourseOut)
def reject_course(
    course_id: int,
    payload: RejectCourseRequest,
    current_user: User = Depends(require_account_types("ADMIN")),
    db: Session = Depends(get_db),
):
    """Reject a course with a review note: transitions status from PENDING_REVIEW back to DRAFT."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    if course.status != "PENDING_REVIEW":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject course with status '{course.status}'. Must be PENDING_REVIEW.",
        )

    course.status = "DRAFT"
    course.review_note = payload.note.strip()
    db.commit()
    db.refresh(course)

    log_admin_action(
        db,
        admin_id=current_user.id,
        action="COURSE_REJECT",
        target_type="COURSE",
        target_id=course.id,
        details=f"Rejected course {course.code} with note: {payload.note.strip()}",
    )

    return serialize_trainer_course(course, db)


@router.get("/stats", response_model=PlatformStatsOut)
def get_platform_stats(
    current_user: User = Depends(require_account_types("ADMIN")),
    db: Session = Depends(get_db),
):
    """Retrieve platform statistics: user counts, course breakdown, and diagnostic metrics."""
    total_users = db.query(User).count()
    learners_count = db.query(User).filter(User.account_type == "LEARNER").count()
    trainers_count = db.query(User).filter(User.account_type == "TRAINER").count()
    admins_count = db.query(User).filter(User.account_type == "ADMIN").count()
    active_users = db.query(User).filter(User.is_active == True).count()

    total_courses = db.query(Course).count()
    published_courses = db.query(Course).filter(Course.status == "PUBLISHED").count()
    pending_courses = db.query(Course).filter(Course.status == "PENDING_REVIEW").count()
    draft_courses = db.query(Course).filter(Course.status == "DRAFT").count()
    archived_courses = db.query(Course).filter(Course.status == "ARCHIVED").count()

    total_diagnostics = db.query(DiagnosticAssessment).count()
    total_quizzes = db.query(QuizAssessment).count()

    return PlatformStatsOut(
        total_users=total_users,
        learners_count=learners_count,
        trainers_count=trainers_count,
        admins_count=admins_count,
        active_users=active_users,
        total_courses=total_courses,
        published_courses=published_courses,
        pending_courses=pending_courses,
        draft_courses=draft_courses,
        archived_courses=archived_courses,
        total_diagnostics_taken=total_diagnostics,
        total_quizzes_taken=total_quizzes,
    )


@router.get("/audit-logs", response_model=List[AuditLogOut])
def list_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_account_types("ADMIN")),
    db: Session = Depends(get_db),
):
    """List recent administrative and review audit logs."""
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    results = []
    for log in logs:
        results.append(
            AuditLogOut(
                id=log.id,
                user_id=log.user_id,
                user_email=log.user.email if log.user else None,
                user_name=log.user.name if log.user else None,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                details=log.details,
                created_at=log.created_at,
            )
        )
    return results
