"""
UPSKILL AI - Authentication API (Phase 7A)

POST /api/v1/auth/register - Register a new account (returns the user, no token)
POST /api/v1/auth/login    - Verify credentials, return a JWT access token
GET  /api/v1/auth/me       - Return the currently authenticated user

Provides the reusable get_current_user() FastAPI dependency. Phase 7B will wire
the existing learner/gaps/recommendations/documents/diagnostic routes onto it;
for now only /auth/me is protected.
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Role, Sector
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Simple email regex — matches standard addresses, good enough for registration
# validation without pulling in the extra email-validator dependency.
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ------------------------------------------------------------------
# Pydantic request / response models
# ------------------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: str
    password: str = Field(..., min_length=6, max_length=200)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address format.")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address format.")
        return v


class RoleOut(BaseModel):
    id: int
    name: str


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    category: str


class UserOut(BaseModel):
    """User info as returned to clients. Never includes the password hash."""
    id: int
    name: str
    email: str
    learning_mode: str = "ROLE"
    role: Optional[RoleOut] = None
    course: Optional[CourseOut] = None
    is_demo: bool
    # Phase 8 - onboarding profile fields (None until onboarding completes).
    designation: Optional[str] = None
    department: Optional[str] = None
    assignment: Optional[str] = None
    education: Optional[str] = None
    work_experience: Optional[str] = None
    previous_training: Optional[str] = None
    profile_completed: bool = False


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ------------------------------------------------------------------
# Serialization helpers
# ------------------------------------------------------------------

def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "learning_mode": getattr(user, "learning_mode", "ROLE") or "ROLE",
        "role": {"id": user.role.id, "name": user.role.name} if user.role else None,
        "course": {
            "id": user.course.id,
            "code": user.course.code,
            "name": user.course.name,
            "category": user.course.category,
        } if getattr(user, "course", None) else None,
        "is_demo": user.is_demo,
        # Phase 8 - onboarding profile (None until completed).
        "designation": user.designation,
        "department": user.department,
        "assignment": user.assignment,
        "education": user.education,
        "work_experience": user.work_experience,
        "previous_training": user.previous_training,
        "profile_completed": bool(user.profile_completed),
    }


def serialize_token(user: User, token: str) -> dict:
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


# ------------------------------------------------------------------
# Reusable dependency (defined before the /me endpoint that uses it)
# ------------------------------------------------------------------

def _bearer_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract the Bearer token from the Authorization header.

    Raises 401 when the header is missing or not a Bearer token so protected
    routes fail fast with a clear message.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a valid access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


def get_current_user(
    token: str = Depends(_bearer_token),
    db: Session = Depends(get_db),
) -> User:
    """
    Reusable FastAPI dependency that resolves the authenticated user from the
    Authorization: Bearer <token> header. Raises 401 on a missing or invalid
    token or when the user no longer exists.
    """
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new account. Rejects duplicate emails, hashes the password,
    and never returns the password hash."""
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        is_demo=False,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Verify credentials and return a JWT access token with the user info."""
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        # Same message for unknown email and wrong password to avoid account
        # enumeration.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)
    return serialize_token(user, token)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user extracted from the JWT."""
    return serialize_user(current_user)


# ------------------------------------------------------------------
# Phase 8 & 10 - new-user onboarding (ROLE vs GOAL mode)
# ------------------------------------------------------------------

class CompleteOnboardingRequest(BaseModel):
    """Payload for POST /auth/complete-onboarding (Phases 8 & 10)."""
    learning_mode: Optional[str] = Field("ROLE", description="'ROLE' or 'GOAL'")
    role_id: Optional[int] = Field(None, description="Selected position (framework role) id.")
    course_id: Optional[int] = Field(None, description="Selected course id.")
    designation: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    assignment: Optional[str] = Field(None, max_length=2000)
    education: Optional[str] = Field(None, max_length=2000)
    work_experience: Optional[str] = Field(None, max_length=2000)
    previous_training: Optional[str] = Field(None, max_length=2000)


@router.get("/onboarding-status")
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tell the frontend whether this user must complete onboarding, plus the list
    of selectable positions, sectors, and courses.
    """
    from app.models import Course
    sectors = db.query(Sector).order_by(Sector.display_order.asc(), Sector.id.asc()).all()
    roles = db.query(Role).order_by(Role.id.asc()).all()
    courses = db.query(Course).filter(Course.active == True).order_by(Course.id.asc()).all()

    has_target = (
        (getattr(current_user, "learning_mode", "ROLE") == "GOAL" and current_user.course_id is not None)
        or (current_user.role_id is not None)
    )

    return {
        "profile_completed": bool(current_user.profile_completed) and has_target,
        "learning_mode": getattr(current_user, "learning_mode", "ROLE") or "ROLE",
        "has_role": current_user.role_id is not None,
        "has_course": current_user.course_id is not None,
        "role_id": current_user.role_id,
        "course_id": current_user.course_id,
        "designation": current_user.designation,
        "sectors": [
            {
                "id": s.id,
                "code": s.code,
                "name": s.name,
                "description": s.description,
                "icon": s.icon or "briefcase",
            }
            for s in sectors
        ],
        "roles": [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "is_demo": r.is_demo,
                "sector_id": r.sector_id,
            }
            for r in roles
        ],
        "courses": [
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "description": c.description,
                "category": c.category,
                "level_hint": c.level_hint or "Beginner",
                "is_demo": bool(c.is_demo),
            }
            for c in courses
        ],
    }


@router.post("/complete-onboarding", response_model=UserOut)
def complete_onboarding(
    payload: CompleteOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Complete onboarding in either ROLE or GOAL mode:
    - Rejects requests that provide NEITHER or BOTH role_id and course_id.
    - For ROLE mode: requires designation and department.
    - For GOAL mode: skips employee-only fields.
    """
    from app.models import Course

    has_role = payload.role_id is not None
    has_course = payload.course_id is not None

    # Validation: reject if neither or both are provided
    if not has_role and not has_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either role_id or course_id for onboarding.",
        )
    if has_role and has_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provide both role_id and course_id. Choose either role or course.",
        )

    mode = "ROLE" if has_role else "GOAL"

    if has_role:
        # Validate role exists
        role = db.query(Role).filter(Role.id == payload.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with ID {payload.role_id} not found.",
            )
        # Designation and department required in role mode
        if not payload.designation or len(payload.designation.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Designation is required for role-based onboarding.",
            )
        if not payload.department or len(payload.department.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department / Office is required for role-based onboarding.",
            )

        role_changed = current_user.role_id is not None and current_user.role_id != role.id
        current_user.learning_mode = "ROLE"
        current_user.role_id = role.id
        current_user.course_id = None
        current_user.designation = payload.designation.strip()
        current_user.department = payload.department.strip()
        current_user.assignment = (payload.assignment or "").strip() or None
        current_user.education = (payload.education or "").strip() or None
        current_user.work_experience = (payload.work_experience or "").strip() or None
        current_user.previous_training = (payload.previous_training or "").strip() or None

        if role_changed:
            current_user.profile_completed = False
        else:
            current_user.profile_completed = True

    else:
        # GOAL mode (course-based)
        course = db.query(Course).filter(Course.id == payload.course_id, Course.active == True).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Course with ID {payload.course_id} not found.",
            )

        course_changed = current_user.course_id is not None and current_user.course_id != course.id
        current_user.learning_mode = "GOAL"
        current_user.course_id = course.id
        current_user.role_id = None
        # Optional profile fields
        current_user.designation = (payload.designation or "").strip() or None
        current_user.department = (payload.department or "").strip() or None
        current_user.assignment = (payload.assignment or "").strip() or None
        current_user.education = (payload.education or "").strip() or None
        current_user.work_experience = (payload.work_experience or "").strip() or None
        current_user.previous_training = (payload.previous_training or "").strip() or None

        if course_changed:
            current_user.profile_completed = False
        else:
            current_user.profile_completed = True

    db.commit()
    db.refresh(current_user)
    return serialize_user(current_user)