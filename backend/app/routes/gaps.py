"""
UPSKILL AI - Gap Analysis API (Phase 3)
GET /api/v1/me/gaps

Returns the authenticated learner's competency gap analysis:
- gap per competency (required_level - current_level)
- gap status (MAJOR_GAP / MODERATE_GAP / MEETS_TARGET / ABOVE_TARGET)
- gap priority (CRITICAL / HIGH / MEDIUM / NONE)
- summary counts
- results sorted by priority then gap size

Gap logic lives in app/services/gap_service.py (pure, testable).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, get_level_label
from app.services.gap_service import compute_learner_gaps
from app.services.learner_framework import get_learner_framework
from app.routes.auth import get_current_user

router = APIRouter(prefix="/me/gaps", tags=["Gap Analysis"])


@router.get("")
def get_learner_gaps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the full gap analysis for the authenticated learner.
    Gap = required_level - current_level for each competency.
    Works for both ROLE and GOAL modes.
    """
    learner = current_user

    # Build required-level and priority lookup from framework helper
    required_lookup, priority_lookup, target_comp_ids = get_learner_framework(db, learner)

    # Build the input list for the gap service
    raw_records = []
    for lc in learner.learner_competencies:
        comp = lc.competency
        # If user has a framework, only consider competencies in their framework
        # (or all if not filtered, but matching role/goal competencies)
        if target_comp_ids and comp.id not in target_comp_ids:
            continue

        raw_records.append({
            "competency_id":          comp.id,
            "competency_name":        comp.name,
            "competency_description": comp.description,
            "current_level":          lc.current_level,
            "required_level":         required_lookup.get(comp.id),
            "priority":               priority_lookup.get(comp.id, "MEDIUM"),
        })

    # Delegate all gap logic to the service
    result = compute_learner_gaps(raw_records)

    return {
        "learner": {
            "id":   learner.id,
            "name": learner.name,
        },
        "summary": result["summary"],
        "gaps":    result["gaps"],
    }