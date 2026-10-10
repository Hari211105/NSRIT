"""
UPSKILL AI - Diagnostic Assessment API (Phase 2)

POST /api/v1/diagnostic/start     - Start a new diagnostic assessment
GET  /api/v1/diagnostic/{id}      - Get diagnostic questions (no answer key)
POST /api/v1/diagnostic/{id}/submit - Submit answers and get results
GET  /api/v1/diagnostic/history    - Get assessment history
"""

import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StrictInt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Competency,
    DiagnosticAssessment,
    DiagnosticQuestion,
    LearnerCompetency,
    RoleCompetency,
    User,
)
from app.routes.auth import get_current_user
from app.models import get_level_label
from app.services import diagnostic_service

router = APIRouter(prefix="/diagnostic", tags=["Diagnostic Assessment"])

ALLOWED_ASSESSMENT_TYPES = ("diagnostic", "standard", "post-learning")


# ------------------------------------------------------------------
# Request/Response models
# ------------------------------------------------------------------

class DiagnosticAnswer(BaseModel):
    """One answer in a diagnostic submission."""
    question_id: StrictInt
    selected_option: StrictInt


class DiagnosticSubmission(BaseModel):
    answers: List[DiagnosticAnswer]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get_assessment_or_404(assessment_id: int, db: Session) -> DiagnosticAssessment:
    assessment = (
        db.query(DiagnosticAssessment)
        .filter(DiagnosticAssessment.id == assessment_id)
        .first()
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic assessment with ID {assessment_id} not found.",
        )
    return assessment


def _serialize_question(q: DiagnosticQuestion) -> dict:
    """Serialize a diagnostic question for storage/retrieval."""
    return {
        "id": q.id,
        "competency_id": q.competency_id,
        "question": q.question,
        "options": json.loads(q.options),
        "correct_option": q.correct_option,
        "difficulty": q.difficulty,
        "explanation": q.explanation,
    }


def _serialize_question_for_learner(q: DiagnosticQuestion, competency_name: str = None) -> dict:
    """
    Serialize a diagnostic question for the learner (no answer key).

    competency_name is included so the learner can see which competency each
    question assesses; it is display data only and is never used for scoring.
    """
    payload = {
        "question_id": q.id,
        "competency_id": q.competency_id,
        "question": q.question,
        "options": json.loads(q.options),
        "difficulty": q.difficulty,
    }
    if competency_name is not None:
        payload["competency_name"] = competency_name
    return payload


# ------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------

@router.post("/start", status_code=status.HTTP_201_CREATED)
def start_diagnostic(
    assessment_type: str = "diagnostic",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a new diagnostic assessment for the authenticated learner.

    Selects questions mapped to the learner's role competencies, covering
    all required competencies with a balanced mix of difficulty levels.
    assessment_type (optional) labels the session - 'diagnostic' (default),
    'standard' or 'post-learning'. Scoring is identical for all types.

    Returns the assessment ID and learner-safe questions (no answer key).
    """
    if assessment_type not in ALLOWED_ASSESSMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unknown assessment_type {assessment_type!r}. Must be one of: "
                f"{', '.join(ALLOWED_ASSESSMENT_TYPES)}."
            ),
        )

    learner = current_user

    # Get competencies required for the learner's role
    if not learner.role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Learner has no assigned role. Cannot start diagnostic assessment.",
        )

    role_mappings = (
        db.query(RoleCompetency)
        .filter(RoleCompetency.role_id == learner.role_id)
        .all()
    )

    if not role_mappings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No competencies mapped to the learner's role.",
        )

    competency_ids = [rm.competency_id for rm in role_mappings]

    # Load available diagnostic questions for these competencies
    questions = (
        db.query(DiagnosticQuestion)
        .filter(
            DiagnosticQuestion.competency_id.in_(competency_ids),
            DiagnosticQuestion.active == True,
        )
        .order_by(DiagnosticQuestion.competency_id, DiagnosticQuestion.difficulty)
        .all()
    )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No diagnostic questions available for this role's competencies.",
        )

    # Competency names for display (never used for scoring).
    competencies = (
        db.query(Competency).filter(Competency.id.in_(competency_ids)).all()
    )
    competency_name_by_id = {c.id: c.name for c in competencies}

    # Create assessment record
    now_iso = datetime.utcnow().isoformat()
    assessment = DiagnosticAssessment(
        learner_id=learner.id,
        assessment_type=assessment_type,
        total_questions=len(questions),
        total_correct=0,
        score_percent=0.0,
        passed=False,
        status="IN_PROGRESS",
        competency_results=None,
        created_at=now_iso,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # Serialize questions for storage in the assessment record
    # (so we can retrieve them later without re-querying)
    stored_questions = [_serialize_question(q) for q in questions]

    # Store the questions JSON in the assessment for later retrieval
    assessment.competency_results = json.dumps({
        "questions": stored_questions,
        "learner_competencies": {
            str(q.competency_id): _get_learner_comp_info(q.competency_id, learner, db)
            for q in questions
        },
    })
    db.commit()

    return {
        "assessment_id": assessment.id,
        "assessment_type": assessment.assessment_type,
        "total_questions": len(questions),
        "questions": [
            _serialize_question_for_learner(
                q, competency_name_by_id.get(q.competency_id)
            )
            for q in questions
        ],
    }


def _get_learner_comp_info(competency_id: int, learner: User, db: Session) -> dict:
    """Get learner's current level and role requirement for a competency."""
    # Current level
    lc = (
        db.query(LearnerCompetency)
        .filter(
            LearnerCompetency.user_id == learner.id,
            LearnerCompetency.competency_id == competency_id,
        )
        .first()
    )
    current_level = lc.current_level if lc else 1

    # Required level and priority
    mapping = (
        db.query(RoleCompetency)
        .filter(
            RoleCompetency.role_id == learner.role_id,
            RoleCompetency.competency_id == competency_id,
        )
        .first()
    )
    required_level = mapping.required_level if mapping else None
    priority = mapping.priority if mapping else "MEDIUM"

    return {
        "current_level": current_level,
        "required_level": required_level,
        "priority": priority,
    }


@router.get("/history")
def get_diagnostic_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated learner's diagnostic assessment history."""
    learner = current_user

    assessments = (
        db.query(DiagnosticAssessment)
        .filter(DiagnosticAssessment.learner_id == learner.id)
        .order_by(DiagnosticAssessment.id.desc())
        .all()
    )

    return {
        "learner_id": learner.id,
        "learner_name": learner.name,
        "total_assessments": len(assessments),
        "assessments": [
            {
                "id": a.id,
                "assessment_type": a.assessment_type,
                "total_questions": a.total_questions,
                "score_percent": a.score_percent,
                "passed": a.passed,
                "status": a.status,
                "created_at": a.created_at,
            }
            for a in assessments
        ],
    }


@router.get("/{assessment_id}")
def get_diagnostic(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get diagnostic assessment details.

    If the assessment is IN_PROGRESS, returns learner-safe questions (no answer key).
    If COMPLETED, returns the full result.
    Only the owning learner may view the assessment.
    """
    assessment = _get_assessment_or_404(assessment_id, db)

    # Check ownership
    learner = current_user
    if assessment.learner_id != learner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This assessment belongs to a different learner.",
        )

    stored_data = json.loads(assessment.competency_results) if assessment.competency_results else {}

    if assessment.status == "IN_PROGRESS":
        questions = stored_data.get("questions", [])
        return {
            "assessment_id": assessment.id,
            "status": assessment.status,
            "total_questions": assessment.total_questions,
            "questions": [
                {
                    "question_id": q["id"],
                    "competency_id": q["competency_id"],
                    "question": q["question"],
                    "options": q["options"],
                    "difficulty": q["difficulty"],
                }
                for q in questions
            ],
        }
    else:
        # COMPLETED - return full result. Level labels come from the shared
        # model helper so every screen shows the same scale wording.
        competencies = stored_data.get("competencies", {})
        for comp in competencies.values():
            for key in ("previous_level", "new_level", "required_level"):
                level = comp.get(key)
                if level is not None:
                    comp[f"{key}_label"] = get_level_label(level)

        return {
            "assessment_id": assessment.id,
            "status": assessment.status,
            "overall": {
                "total_questions": assessment.total_questions,
                "total_correct": assessment.total_correct,
                "score_percent": assessment.score_percent,
                "passed": assessment.passed,
                "pass_threshold_percent": diagnostic_service.PASS_THRESHOLD_PERCENT,
                "status": assessment.status,
            },
            "competencies": competencies,
            "created_at": assessment.created_at,
        }


@router.post("/{assessment_id}/submit")
def submit_diagnostic(
    assessment_id: int,
    submission: DiagnosticSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit answers for a diagnostic assessment.

    Scores answers with difficulty weighting, calculates per-competency
    evidence, and updates competency levels using the existing deterministic
    competency engine. Evidence is stored against the authenticated learner,
    and only the owning learner may submit.

    Returns the full result with per-competency breakdown and competency updates.
    """
    assessment = _get_assessment_or_404(assessment_id, db)

    # Check ownership
    learner = current_user
    if assessment.learner_id != learner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This assessment belongs to a different learner.",
        )

    if assessment.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assessment is already {assessment.status}. Cannot resubmit.",
        )

    if not submission.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission must contain at least one answer.",
        )

    # Load stored questions
    stored_data = json.loads(assessment.competency_results) if assessment.competency_results else {}
    stored_questions = stored_data.get("questions", [])
    learner_comp_info = stored_data.get("learner_competencies", {})

    if not stored_questions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assessment questions data is missing or corrupted.",
        )

    # Validate answers
    questions_by_id = {q["id"]: q for q in stored_questions}
    answers_dict = {}
    seen_ids = set()

    for answer in submission.answers:
        q_id = answer.question_id
        if q_id in seen_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate answer for question_id {q_id}.",
            )
        seen_ids.add(q_id)

        if q_id not in questions_by_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"question_id {q_id} does not belong to this assessment.",
            )

        if not 0 <= answer.selected_option <= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"selected_option must be between 0 and 3, got {answer.selected_option}.",
            )

        answers_dict[q_id] = answer.selected_option

    # Build competency info dicts for the scoring engine
    existing_levels = {}
    required_levels = {}
    priorities = {}
    for comp_id_str, info in learner_comp_info.items():
        comp_id = int(comp_id_str)
        existing_levels[comp_id] = info["current_level"]
        required_levels[comp_id] = info["required_level"]
        priorities[comp_id] = info["priority"]

    # Score and calculate competency updates
    result = diagnostic_service.build_diagnostic_result(
        stored_questions, answers_dict, existing_levels, required_levels, priorities
    )

    # Apply competency level updates. The engine guarantees new >= existing,
    # so no level can ever drop; the guard below keeps that promise explicit.
    # Phase 8: a learner with no prior competency rows gets their FULL assessed
    # profile persisted (including unchanged competencies), so the dashboard
    # shows all assessed areas rather than only the ones that levelled up.
    existing_lc_rows = (
        db.query(LearnerCompetency)
        .filter(LearnerCompetency.user_id == learner.id)
        .all()
    )
    has_prior_profile = len(existing_lc_rows) > 0

    for comp_id_str, comp_result in result["competencies"].items():
        comp_id = int(comp_id_str) if isinstance(comp_id_str, str) else comp_id_str
        if comp_result["level_changed"] or not has_prior_profile:
            if comp_result["new_level"] < comp_result["previous_level"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Computed competency level would decrease, which the "
                        "prototype rule forbids. Submission aborted."
                    ),
                )
            lc = (
                db.query(LearnerCompetency)
                .filter(
                    LearnerCompetency.user_id == learner.id,
                    LearnerCompetency.competency_id == comp_id,
                )
                .first()
            )
            if lc:
                lc.current_level = comp_result["new_level"]
            else:
                db.add(LearnerCompetency(
                    user_id=learner.id,
                    competency_id=comp_id,
                    current_level=comp_result["new_level"],
                ))

    # Update assessment record
    now_iso = datetime.utcnow().isoformat()
    assessment.total_correct = result["overall"]["total_correct"]
    assessment.score_percent = result["overall"]["weighted_percent"]
    assessment.passed = result["overall"]["passed"]
    assessment.status = result["overall"]["status"]

    # Store full result including competency_results in the JSON field
    result_with_questions = {
        **result,
        "questions": stored_questions,
        "learner_competencies": learner_comp_info,
    }
    assessment.competency_results = json.dumps(result_with_questions)

    db.commit()

    # Build the competency name lookup for the response
    comp_ids = [int(cid) for cid in result["competencies"].keys()]
    competencies = db.query(Competency).filter(Competency.id.in_(comp_ids)).all()
    comp_name_map = {c.id: c.name for c in competencies}

    # Format response
    response_competencies = {}
    for comp_id_str, comp_result in result["competencies"].items():
        comp_id = int(comp_id_str) if isinstance(comp_id_str, str) else comp_id_str
        response_competencies[comp_id] = {
            **comp_result,
            "competency_name": comp_name_map.get(comp_id, f"Competency {comp_id}"),
        }

    return {
        "assessment_id": assessment.id,
        "status": assessment.status,
        "overall": result["overall"],
        "competencies": response_competencies,
        "created_at": assessment.created_at,
    }
