"""
UPSKILL AI - Gap Analysis Service (Phase 3)

Pure calculation logic — no database calls here.
The route passes data in; this service returns structured results.
All logic is deterministic (no AI).

Gap = required_level - current_level

Gap status labels (prototype application labels,
NOT official MoSPI/iGOT definitions):
  MAJOR_GAP      gap >= 2
  MODERATE_GAP   gap == 1
  MEETS_TARGET   gap == 0
  ABOVE_TARGET   gap < 0

Gap priority (uses the existing role-competency priority as input):
  CRITICAL  gap >= 2 and role priority is HIGH
  HIGH      gap >= 2 and role priority is MEDIUM
            OR gap == 1 and role priority is HIGH
  MEDIUM    gap == 1 and role priority is MEDIUM
  NONE      gap <= 0
"""

from app.models import get_level_label


# ---------------------------------------------------------------
# Sorting order constants
# ---------------------------------------------------------------

_PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "NONE": 3}


# ---------------------------------------------------------------
# Core calculation functions (pure — easy to test individually)
# ---------------------------------------------------------------

def calculate_gap(current_level: int, required_level: int) -> int:
    """Return the numeric gap: required - current."""
    return required_level - current_level


def calculate_gap_status(gap: int) -> str:
    """
    Map a numeric gap to a prototype status label.
    Labels are internal application labels for this MVP.
    """
    if gap >= 2:
        return "MAJOR_GAP"
    elif gap == 1:
        return "MODERATE_GAP"
    elif gap == 0:
        return "MEETS_TARGET"
    else:  # gap < 0
        return "ABOVE_TARGET"


def calculate_gap_priority(gap: int, role_priority: str) -> str:
    """
    Determine the action priority for this gap.

    Rules:
    - gap >= 2 + HIGH role priority  → CRITICAL
    - gap >= 2 + MEDIUM role priority → HIGH
    - gap == 1 + HIGH role priority   → HIGH
    - gap == 1 + MEDIUM role priority → MEDIUM
    - gap <= 0                        → NONE
    """
    rp = (role_priority or "MEDIUM").upper()

    if gap >= 2:
        return "CRITICAL" if rp == "HIGH" else "HIGH"
    elif gap == 1:
        return "HIGH" if rp == "HIGH" else "MEDIUM"
    else:
        return "NONE"


# ---------------------------------------------------------------
# Main service function
# ---------------------------------------------------------------

def compute_learner_gaps(learner_competency_records: list) -> dict:
    """
    Receive a list of learner competency dicts (already fetched from DB)
    and return a fully structured gap analysis result.

    Each input record must have:
      competency_id, competency_name, competency_description,
      current_level, required_level, priority (role priority)

    Returns a dict with keys:
      gaps    - sorted list of gap records
      summary - summary counts
    """
    gap_records = []

    for item in learner_competency_records:
        current  = item["current_level"]
        required = item.get("required_level")

        # Skip competencies with no required level set for this role
        if required is None:
            continue

        gap      = calculate_gap(current, required)
        status   = calculate_gap_status(gap)
        priority = calculate_gap_priority(gap, item.get("priority", "MEDIUM"))

        gap_records.append({
            "competency_id":         item["competency_id"],
            "competency_name":       item["competency_name"],
            "current_level":         current,
            "current_level_label":   get_level_label(current),
            "required_level":        required,
            "required_level_label":  get_level_label(required),
            "gap":                   gap,
            "status":                status,
            "priority":              priority,
        })

    # Sort: by priority order first, then by gap size descending (larger gap first)
    gap_records.sort(
        key=lambda r: (_PRIORITY_ORDER.get(r["priority"], 99), -r["gap"])
    )

    # Build summary counts
    total         = len(gap_records)
    with_gap      = sum(1 for r in gap_records if r["gap"] > 0)
    meeting       = sum(1 for r in gap_records if r["gap"] == 0)
    above         = sum(1 for r in gap_records if r["gap"] < 0)
    major_gaps    = sum(1 for r in gap_records if r["status"] == "MAJOR_GAP")
    moderate_gaps = sum(1 for r in gap_records if r["status"] == "MODERATE_GAP")

    summary = {
        "total_competencies":         total,
        "competencies_with_gap":      with_gap,
        "competencies_meeting_target": meeting,
        "competencies_above_target":  above,
        "major_gaps":                 major_gaps,
        "moderate_gaps":              moderate_gaps,
    }

    return {
        "gaps":    gap_records,
        "summary": summary,
    }
