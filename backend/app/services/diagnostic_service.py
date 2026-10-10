"""
UPSKILL AI - Diagnostic Assessment Service (Phase 2)

Deterministic scoring and per-competency evidence derivation for the
diagnostic assessment. No AI calls — the LLM may generate questions, but
scoring and competency evidence are always deterministic.

Difficulty weighting:
  EASY   = 1.0
  MEDIUM = 2.0
  HARD   = 3.0

Weighted performance formula:
  weighted_score = sum(weight_i * is_correct_i) for all answered questions
  weighted_total = sum(weight_i) for all answered questions
  weighted_percent = (weighted_score / weighted_total) * 100

The weighted_percent is then mapped to evidence levels using the existing
competency_evidence_service.evidence_level_from_percent() function, and
competency level updates use the existing next_competency_level() safety rule.

This ensures diagnostic evidence flows through the same deterministic engine
as quiz evidence — no parallel scoring system.

Gap severity and the recommended action are NOT judged by an LLM either: they
reuse the existing gap_service.calculate_gap_status / calculate_gap_priority
rules and a fixed lookup table, so the same evidence always produces the same
result.
"""

from typing import Any, Dict, List, Optional
from app.services.competency_evidence_service import (
    CompetencyEvidenceError,
    evidence_level_from_percent,
    next_competency_level,
)
from app.services import gap_service


# ------------------------------------------------------------------
# Difficulty weights
# ------------------------------------------------------------------

DIFFICULTY_WEIGHTS = {
    "EASY": 1.0,
    "MEDIUM": 2.0,
    "HARD": 3.0,
}

DEFAULT_DIFFICULTY_WEIGHT = 2.0  # fallback for unknown difficulty

PASS_THRESHOLD_PERCENT = 60  # prototype threshold, same as quiz


def get_difficulty_weight(difficulty: str) -> float:
    """Return the weight for a difficulty level string."""
    if not isinstance(difficulty, str):
        return DEFAULT_DIFFICULTY_WEIGHT
    return DIFFICULTY_WEIGHTS.get(difficulty.upper().strip(), DEFAULT_DIFFICULTY_WEIGHT)


# ------------------------------------------------------------------
# Weighted scoring (pure, deterministic, unit-testable)
# ------------------------------------------------------------------

def calculate_weighted_score(
    questions: List[Dict[str, Any]],
    answers: Dict[int, int],
) -> Dict[str, Any]:
    """
    Calculate difficulty-weighted score for answered questions.

    `questions` is a list of dicts with at least: id, correct_option, difficulty.
    `answers` is a dict mapping question_id -> selected_option (0-based index).

    Returns a dict with:
      weighted_score  - sum of weights for correctly answered questions
      weighted_total  - sum of weights for all answered questions
      weighted_percent - (weighted_score / weighted_total) * 100, rounded to 2 decimals
      total_correct   - count of correct answers
      total_answered  - count of answered questions
      per_question    - list of per-question results
    """
    weighted_score = 0.0
    weighted_total = 0.0
    total_correct = 0
    per_question = []

    for q in questions:
        q_id = q["id"]
        difficulty = q.get("difficulty", "MEDIUM")
        weight = get_difficulty_weight(difficulty)
        correct_option = q["correct_option"]

        if q_id in answers:
            selected = answers[q_id]
            is_correct = selected == correct_option
            weighted_total += weight
            if is_correct:
                weighted_score += weight
                total_correct += 1
            per_question.append({
                "question_id": q_id,
                "selected_option": selected,
                "is_correct": is_correct,
                "difficulty": difficulty,
                "weight": weight,
                "explanation": q.get("explanation", ""),
            })
        else:
            per_question.append({
                "question_id": q_id,
                "selected_option": None,
                "is_correct": False,
                "difficulty": difficulty,
                "weight": weight,
                "explanation": q.get("explanation", ""),
            })

    if weighted_total == 0:
        weighted_percent = 0.0
    else:
        weighted_percent = round((weighted_score / weighted_total) * 100, 2)

    return {
        "weighted_score": weighted_score,
        "weighted_total": weighted_total,
        "weighted_percent": weighted_percent,
        "total_correct": total_correct,
        "total_answered": sum(1 for q in questions if q["id"] in answers),
        "per_question": per_question,
    }


# ------------------------------------------------------------------
# Per-competency evidence calculation
# ------------------------------------------------------------------

def calculate_competency_evidence(
    questions: List[Dict[str, Any]],
    answers: Dict[int, int],
) -> Dict[int, Dict[str, Any]]:
    """
    Group questions by competency and calculate per-competency evidence.

    Each competency gets:
      - total_questions
      - total_correct
      - weighted_percent (difficulty-weighted)
      - evidence_level (0-3, via existing evidence_level_from_percent)
      - difficulty breakdown (count by difficulty)

    Returns a dict keyed by competency_id.
    """
    # Group questions by competency
    competency_groups: Dict[int, List[Dict[str, Any]]] = {}
    for q in questions:
        comp_id = q["competency_id"]
        if comp_id not in competency_groups:
            competency_groups[comp_id] = []
        competency_groups[comp_id].append(q)

    results = {}
    for comp_id, comp_questions in competency_groups.items():
        scoring = calculate_weighted_score(comp_questions, answers)

        # Difficulty breakdown
        difficulty_counts = {}
        for q in comp_questions:
            d = q.get("difficulty", "MEDIUM")
            difficulty_counts[d] = difficulty_counts.get(d, 0) + 1

        # Map to evidence level using the existing function
        evidence_level = evidence_level_from_percent(scoring["weighted_percent"])

        results[comp_id] = {
            "competency_id": comp_id,
            "total_questions": len(comp_questions),
            "total_correct": scoring["total_correct"],
            "total_answered": scoring["total_answered"],
            "weighted_percent": scoring["weighted_percent"],
            "evidence_level": evidence_level,
            "difficulty_breakdown": difficulty_counts,
        }

    return results


# ------------------------------------------------------------------
# Deterministic recommended action (no AI)
# ------------------------------------------------------------------

# Fixed, deterministic next step per remaining gap size. The LLM never picks
# or words these - the same gap always yields the same action.
RECOMMENDED_ACTIONS = {
    0: (
        "Meets the role requirement. Maintain the level with a short quiz or "
        "refresher resource."
    ),
    1: (
        "Complete one targeted learning module for this competency to close "
        "the remaining one-level gap."
    ),
    2: (
        "Start with the highest-priority learning resource for this competency - "
        "the remaining gap is large, so learning comes before assessment."
    ),
    3: (
        "Start with the highest-priority learning resource for this competency - "
        "the remaining gap is large, so learning comes before assessment."
    ),
}


def recommended_action(gap_after) -> str:
    """
    Return the fixed next-step text for a post-assessment gap.

    gap_after None means the role does not require this competency, so there is
    no learning action tied to it.
    """
    if gap_after is None:
        return (
            "No role requirement is mapped for this competency, so it is not "
            "part of your learning plan."
        )
    return RECOMMENDED_ACTIONS.get(
        gap_after,
        "Start with the highest-priority learning resource for this competency.",
    )


# ------------------------------------------------------------------
# Build full diagnostic result
# ------------------------------------------------------------------

def build_diagnostic_result(
    questions: List[Dict[str, Any]],
    answers: Dict[int, int],
    existing_levels: Dict[int, int],
    required_levels: Dict[int, Optional[int]],
    priorities: Dict[int, str],
) -> Dict[str, Any]:
    """
    Build the complete diagnostic result with per-competency competency updates.

    Args:
        questions: list of diagnostic question dicts (id, competency_id, correct_option, difficulty, etc.)
        answers: dict mapping question_id -> selected_option
        existing_levels: dict mapping competency_id -> current_level (1-4)
        required_levels: dict mapping competency_id -> required_level (1-4 or None)
        priorities: dict mapping competency_id -> role priority string

    Returns a dict with:
        overall - overall scoring summary
        competencies - per-competency results with competency updates
    """
    # Overall scoring
    overall = calculate_weighted_score(questions, answers)
    overall_passed = overall["weighted_percent"] >= PASS_THRESHOLD_PERCENT

    # Per-competency evidence
    competency_evidence = calculate_competency_evidence(questions, answers)

    # Build per-competency results with competency updates
    competency_results = {}
    for comp_id, evidence in competency_evidence.items():
        existing_level = existing_levels.get(comp_id, 1)
        required_level = required_levels.get(comp_id)
        priority = priorities.get(comp_id, "MEDIUM")

        # Use the existing competency update engine
        new_level = next_competency_level(existing_level, evidence["evidence_level"])
        level_changed = new_level != existing_level

        # Gap calculation via existing gap_service
        if required_level is not None:
            gap_before = gap_service.calculate_gap(existing_level, required_level)
            gap_after = gap_service.calculate_gap(new_level, required_level)
        else:
            gap_before = None
            gap_after = None

        # Gap severity reuses the existing Phase 3 gap service rules - never
        # recomputed here and never decided by an LLM.
        if gap_after is None:
            gap_status = None
            gap_priority = None
        else:
            gap_status = gap_service.calculate_gap_status(gap_after)
            gap_priority = gap_service.calculate_gap_priority(gap_after, priority)

        competency_results[comp_id] = {
            "competency_id": comp_id,
            "total_questions": evidence["total_questions"],
            "total_correct": evidence["total_correct"],
            "weighted_percent": evidence["weighted_percent"],
            "evidence_level": evidence["evidence_level"],
            "previous_level": existing_level,
            "new_level": new_level,
            "level_changed": level_changed,
            "required_level": required_level,
            "priority": priority,
            "gap_before": gap_before,
            "gap_after": gap_after,
            "gap_status": gap_status,
            "gap_priority": gap_priority,
            "recommended_action": recommended_action(gap_after),
            "difficulty_breakdown": evidence["difficulty_breakdown"],
        }

    return {
        "overall": {
            "total_questions": overall["total_correct"] + (len(questions) - overall["total_answered"]),
            "total_answered": overall["total_answered"],
            "total_correct": overall["total_correct"],
            "weighted_percent": overall["weighted_percent"],
            "pass_threshold_percent": PASS_THRESHOLD_PERCENT,
            "passed": overall_passed,
            "status": "PASSED" if overall_passed else "FAILED",
        },
        "competencies": competency_results,
    }
