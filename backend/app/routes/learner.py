"""
UPSKILL AI - Learner (Me) API (Phase 2)
GET /api/v1/me
GET /api/v1/me/competencies
GET /api/v1/me/evidence

Phase 7B: each route resolves the authenticated learner from the JWT via the
reusable get_current_user() dependency, so a user only ever sees their own
profile, competencies and evidence.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    User,
    RoleCompetency,
    get_level_label,
    QuizAssessment,
    Competency,
    Document,
)
from app.routes.auth import get_current_user

router = APIRouter(prefix="/me", tags=["Learner"])

# PROTOTYPE assessment rule - not an official government competency scale.
EVIDENCE_RULE_NOTE = (
    "Prototype assessment rule: quiz score below 40% maps to evidence level 0, "
    "40-59% to 1, 60-79% to 2 and 80-100% to 3. A single quiz can raise a "
    "competency level by at most one, and a poor score never lowers it. This is "
    "not an official MoSPI, iGOT Karmayogi, NSSTA, TPAC or Government standard."
)


@router.get("")
def get_learner_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated learner profile."""
    learner = current_user
    return {
        "id": learner.id,
        "name": learner.name,
        "email": learner.email,
        "learning_mode": getattr(learner, "learning_mode", "ROLE") or "ROLE",
        "role": {
            "id": learner.role.id,
            "name": learner.role.name,
        } if learner.role else None,
        "course": {
            "id": learner.course.id,
            "code": learner.course.code,
            "name": learner.course.name,
            "category": learner.course.category,
        } if getattr(learner, "course", None) else None,
        "is_demo": learner.is_demo,
        # Phase 8 - onboarding profile fields.
        "designation": learner.designation,
        "department": learner.department,
        "assignment": learner.assignment,
        "education": learner.education,
        "work_experience": learner.work_experience,
        "previous_training": learner.previous_training,
        "profile_completed": bool(learner.profile_completed),
    }


@router.get("/competencies")
def get_learner_competencies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated learner's current competency profile alongside
    the required levels for their assigned role or course.
    """
    learner = current_user

    # Build lookup of required levels using shared framework helper
    from app.services.learner_framework import get_learner_framework
    required_lookup, priority_lookup, target_comp_ids = get_learner_framework(db, learner)

    result = []
    for lc in learner.learner_competencies:
        comp = lc.competency
        if target_comp_ids and comp.id not in target_comp_ids:
            continue
        required = required_lookup.get(comp.id)
        priority = priority_lookup.get(comp.id)
        result.append({
            "competency_id": comp.id,
            "competency_name": comp.name,
            "competency_description": comp.description,
            "current_level": lc.current_level,
            "current_level_label": get_level_label(lc.current_level),
            "required_level": required,
            "required_level_label": get_level_label(required) if required else None,
            "priority": priority,
        })

    target_name = (
        learner.course.name if getattr(learner, "learning_mode", "ROLE") == "GOAL" and learner.course
        else (learner.role.name if learner.role else None)
    )

    return {
        "learner_id": learner.id,
        "learner_name": learner.name,
        "learning_mode": getattr(learner, "learning_mode", "ROLE") or "ROLE",
        "role": learner.role.name if learner.role else None,
        "course": learner.course.name if getattr(learner, "course", None) else None,
        "target_name": target_name,
        "competencies": result,
    }


@router.get("/evidence")
def get_learner_evidence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated learner's stored competency assessment evidence
    (Phase 6A). Only this user's quiz evidence is returned.

    One record per completed quiz that was recorded against a competency, oldest
    first, including the derived evidence level and the competency's current
    level. Documents with no competency association never produce evidence.
    """
    learner = current_user

    current_levels = {
        lc.competency_id: lc.current_level for lc in learner.learner_competencies
    }

    rows = (
        db.query(QuizAssessment, Document.filename, Competency.name)
        .outerjoin(Document, Document.id == QuizAssessment.document_id)
        .outerjoin(Competency, Competency.id == QuizAssessment.competency_id)
        .filter(QuizAssessment.learner_id == learner.id)
        .order_by(QuizAssessment.id.asc())
        .all()
    )

    evidence = [
        {
            "id": record.id,
            "document_id": record.document_id,
            "document_filename": filename,
            "competency_id": record.competency_id,
            "competency_name": competency_name,
            "score_percent": record.score_percent,
            "evidence_level": record.evidence_level,
            "current_level": current_levels.get(record.competency_id),
            "current_level_label": (
                get_level_label(current_levels[record.competency_id])
                if record.competency_id in current_levels
                else None
            ),
            "created_at": record.created_at,
        }
        for record, filename, competency_name in rows
    ]

    return {
        "learner_id": learner.id,
        "learner_name": learner.name,
        "total_evidence": len(evidence),
        "assessment_rule_note": EVIDENCE_RULE_NOTE,
        "evidence": evidence,
    }
