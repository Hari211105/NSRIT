"""
UPSKILL AI - Competency Evidence Service (Phase 6A)

Deterministic (no AI, no database) rules that turn a completed quiz score into
competency evidence and a bounded competency level change.

PROTOTYPE ASSESSMENT RULE
  This is an application rule for this MVP only. It is NOT an official MoSPI,
  iGOT Karmayogi, NSSTA, TPAC or Government competency scale.

Evidence level from quiz percentage:
    < 40%    -> 0   (no demonstrated evidence)
    40 - 59% -> 1
    60 - 79% -> 2
    80 - 100%-> 3

Level change safety rule:
    new_level = max(existing_level, min(evidence_level, existing_level + 1))
  * a single completed quiz can raise a level by at most ONE
  * a poor score never lowers an already-established level

Gaps are not computed here: the caller recalculates them with the existing
app.services.gap_service (calculate_gap), so gap logic has a single owner.
"""

from app.services import gap_service

MIN_EVIDENCE_LEVEL = 0
MAX_EVIDENCE_LEVEL = 3

# LearnerCompetency.current_level is 1-4 (see app.models.LEVEL_LABELS).
# 0 is only used internally to mean "no level recorded yet".
MIN_COMPETENCY_LEVEL = 1
MAX_COMPETENCY_LEVEL = 4


class CompetencyEvidenceError(ValueError):
    """
    Raised when quiz evidence cannot be derived or would have to be guessed.

    This includes a missing competency association: evidence is never recorded
    against a competency that was not explicitly linked to the document.
    """


def evidence_level_from_percent(score_percent) -> int:
    """
    Map a quiz percentage (0-100) to a prototype evidence level (0-3).

    Rejects anything outside 0-100, non-numeric values and NaN.
    """
    # bool is a subclass of int, but True/False is not a percentage.
    if isinstance(score_percent, bool) or not isinstance(score_percent, (int, float)):
        raise CompetencyEvidenceError(
            f"score_percent must be a number between 0 and 100, got "
            f"{type(score_percent).__name__}."
        )

    # NaN compares false against everything, so check it explicitly.
    if score_percent != score_percent:
        raise CompetencyEvidenceError("score_percent must be a number, got NaN.")

    if not 0 <= score_percent <= 100:
        raise CompetencyEvidenceError(
            f"score_percent must be between 0 and 100, got {score_percent}."
        )

    if score_percent < 40:
        return 0
    if score_percent < 60:
        return 1
    if score_percent < 80:
        return 2
    return 3


def next_competency_level(existing_level: int, evidence_level: int) -> int:
    """
    Apply the safety rule: max(existing, min(evidence, existing + 1)).

    The result is never below existing_level (a poor score cannot demote a
    learner) and never more than one level above it.
    """
    for label, value, low, high in (
        ("existing_level", existing_level, 0, MAX_COMPETENCY_LEVEL),
        ("evidence_level", evidence_level, MIN_EVIDENCE_LEVEL, MAX_EVIDENCE_LEVEL),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise CompetencyEvidenceError(
                f"{label} must be an integer, got {type(value).__name__}."
            )
        if not low <= value <= high:
            raise CompetencyEvidenceError(
                f"{label} must be between {low} and {high}, got {value}."
            )

    return max(existing_level, min(evidence_level, existing_level + 1))


def build_competency_update(
    competency_id,
    score_percent,
    existing_level: int,
    required_level=None,
) -> dict:
    """
    Build the competency_update payload returned to the quiz caller.

    competency_id is mandatory: a missing association raises
    CompetencyEvidenceError rather than assigning a competency silently.

    required_level is the learner's role requirement for that competency (may be
    None when the competency is not mapped to the role). Gaps are then computed
    with the existing gap_service and are None when there is no requirement.
    """
    if competency_id is None:
        raise CompetencyEvidenceError(
            "No competency is associated with this document, so competency "
            "evidence cannot be recorded. Link the document to a competency "
            "first; it is never guessed from the document text."
        )
    if isinstance(competency_id, bool) or not isinstance(competency_id, int):
        raise CompetencyEvidenceError(
            f"competency_id must be an integer, got {type(competency_id).__name__}."
        )

    evidence_level = evidence_level_from_percent(score_percent)
    new_level = next_competency_level(existing_level, evidence_level)

    # Recalculated with the existing Phase 3 gap service - never reimplemented.
    if required_level is None:
        gap_before = None
        gap_after = None
    else:
        gap_before = gap_service.calculate_gap(existing_level, required_level)
        gap_after = gap_service.calculate_gap(new_level, required_level)

    return {
        "competency_id": competency_id,
        "previous_level": existing_level,
        "evidence_level": evidence_level,
        "new_level": new_level,
        "level_changed": new_level != existing_level,
        "gap_before": gap_before,
        "gap_after": gap_after,
    }
