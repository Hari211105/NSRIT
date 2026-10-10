"""
UPSKILL AI - Learner Framework Helper (Phase 10)

Extracts the required competency levels and priorities for a learner regardless
of whether they are following the:
1. "ROLE" pathway (via RoleCompetency mappings)
2. "GOAL" pathway (via CourseCompetency mappings)

This eliminates duplicate logic across:
- GET /api/v1/me/competencies
- GET /api/v1/me/gaps
- GET /api/v1/me/recommendations
- POST /api/v1/diagnostic/start
"""
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from app.models import User, RoleCompetency, CourseCompetency


def get_learner_framework(db: Session, learner: User) -> Tuple[Dict[int, int], Dict[int, str], List[int]]:
    """
    Returns:
      (required_lookup, priority_lookup, target_competency_ids)
      - required_lookup: {competency_id: required_level (1-4)}
      - priority_lookup: {competency_id: priority ("HIGH" | "MEDIUM" | "LOW")}
      - target_competency_ids: list of mapped competency IDs for this learner
    """
    required_lookup: Dict[int, int] = {}
    priority_lookup: Dict[int, str] = {}
    target_competency_ids: List[int] = []

    # Goal path: user has selected a course
    if getattr(learner, "learning_mode", "ROLE") == "GOAL" and learner.course_id:
        course_mappings = (
            db.query(CourseCompetency)
            .filter(CourseCompetency.course_id == learner.course_id)
            .all()
        )
        for cm in course_mappings:
            required_lookup[cm.competency_id] = cm.required_level
            priority_lookup[cm.competency_id] = cm.priority or "MEDIUM"
            target_competency_ids.append(cm.competency_id)

    # Role path: user has selected a role
    elif learner.role_id:
        role_mappings = (
            db.query(RoleCompetency)
            .filter(RoleCompetency.role_id == learner.role_id)
            .all()
        )
        for rm in role_mappings:
            required_lookup[rm.competency_id] = rm.required_level
            priority_lookup[rm.competency_id] = rm.priority or "MEDIUM"
            target_competency_ids.append(rm.competency_id)

    return required_lookup, priority_lookup, target_competency_ids
