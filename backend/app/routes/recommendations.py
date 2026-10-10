"""
UPSKILL AI - Personalized Recommendations API (Phase 4)
GET /api/v1/me/recommendations

Returns personalized learning recommendations for the authenticated learner.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.services.recommendation_service import generate_recommendations_for_learner
from app.services.learner_framework import get_learner_framework
from app.routes.auth import get_current_user

router = APIRouter(prefix="/me/recommendations", tags=["Recommendations"])


@router.get("")
def get_learner_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return personalized learning recommendations for the authenticated learner
    based on their competency gaps (supports both ROLE and GOAL modes).
    """
    learner = current_user

    # Build required-level and priority lookup from framework helper
    required_lookup, priority_lookup, target_comp_ids = get_learner_framework(db, learner)

    # Build input list for recommendation service
    raw_records = []
    for lc in learner.learner_competencies:
        comp = lc.competency
        if target_comp_ids and comp.id not in target_comp_ids:
            continue
        raw_records.append({
            "competency_id": comp.id,
            "competency_name": comp.name,
            "competency_description": comp.description,
            "current_level": lc.current_level,
            "required_level": required_lookup.get(comp.id),
            "priority": priority_lookup.get(comp.id, "MEDIUM"),
        })

    # Generate recommendations via service
    result = generate_recommendations_for_learner(db, learner, raw_records)

    return result