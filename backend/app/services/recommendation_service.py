"""
UPSKILL AI - Recommendation Engine Service (Phase 4)

Pure recommendation service logic.
Deterministic scoring and dynamic reason generation — no AI used.

Flow:
1. Fetch learner gap analysis via gap_service.
2. Filter out competencies with gap <= 0.
3. For each positive gap competency, query active LearningResources for that competency.
4. Calculate relevance score (0–100 scale).
5. Generate dynamic human-readable explanation reason.
6. Rank recommendations by priority, gap size, score, and duration.
"""

from app.models import get_level_label, LearningResource
from app.services.gap_service import compute_learner_gaps


_PRIORITY_WEIGHTS = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
}


def calculate_relevance_score(
    gap_record: dict,
    resource: LearningResource
) -> int:
    """
    Calculate deterministic relevance score for a resource matching a learner's gap.

    Scoring system:
    - Base score = 0
    - +50 if resource competency matches gap competency
    - +25 if current_level is between resource minimum_level and maximum_level
    - +15 if resource maximum_level >= required_level
    - +10 if gap >= 2
    - +5  if source == 'IGOT_DEMO'
    - +5  if source == 'NSSTA_TPAC_DEMO'
    """
    score = 0
    current_level = gap_record["current_level"]
    required_level = gap_record["required_level"]
    gap = gap_record["gap"]

    # 1. Exact competency match (+50)
    if resource.competency_id == gap_record["competency_id"]:
        score += 50

    # 2. Level fit for current level (+25)
    if resource.minimum_level <= current_level <= resource.maximum_level:
        score += 25

    # 3. Target level progression fit (+15)
    if resource.maximum_level >= required_level:
        score += 15

    # 4. Gap magnitude urgency (+10)
    if gap >= 2:
        score += 10

    # 5. Catalog source quality bonus (+5)
    if resource.source == "IGOT_DEMO":
        score += 5
    elif resource.source == "NSSTA_TPAC_DEMO":
        score += 5

    return score


def generate_recommendation_reason(
    gap_record: dict,
    resource: LearningResource,
    relevance_score: int
) -> str:
    """
    Generate a clear, human-readable reason using actual competency, gap, and level values.
    """
    comp_name = gap_record["competency_name"]
    gap = gap_record["gap"]
    priority = gap_record["priority"]
    current_lvl = gap_record["current_level"]
    required_lvl = gap_record["required_level"]

    priority_str = priority.lower()
    gap_str = f"{gap}-level" if gap > 1 else "1-level"
    curr_label = get_level_label(current_lvl)
    req_label = get_level_label(required_lvl)

    reason = (
        f"You have a {priority_str} {gap_str} gap in {comp_name}. "
        f"This resource directly matches the competency and is suitable for your current "
        f"Level {current_lvl} ({curr_label}) knowledge while helping progress toward "
        f"the required Level {required_lvl} ({req_label})."
    )
    return reason


def generate_recommendations_for_learner(db, learner, raw_learner_competency_records: list) -> dict:
    """
    Generate personalized learning recommendations for a learner.

    Args:
        db: SQLAlchemy DB Session
        learner: User model instance
        raw_learner_competency_records: raw list of dicts suitable for compute_learner_gaps

    Returns dict containing:
        learner: summary learner info
        summary: overall recommendation statistics
        recommendations: list of ranked recommendation dicts
    """
    # 1. Compute gaps
    gap_analysis = compute_learner_gaps(raw_learner_competency_records)
    gaps = gap_analysis["gaps"]

    # 2. Filter positive gaps only (gap > 0)
    positive_gaps = [g for g in gaps if g["gap"] > 0]

    recommendation_list = []

    # 3. Match resources and score
    for gap_item in positive_gaps:
        comp_id = gap_item["competency_id"]
        resources = db.query(LearningResource).filter(
            LearningResource.competency_id == comp_id,
            LearningResource.active == True,
        ).all()

        for res in resources:
            score = calculate_relevance_score(gap_item, res)
            reason = generate_recommendation_reason(gap_item, res, score)

            recommendation_list.append({
                "competency_id": comp_id,
                "competency_name": gap_item["competency_name"],
                "gap": gap_item["gap"],
                "priority": gap_item["priority"],
                "learning_resource": {
                    "id": res.id,
                    "title": res.title,
                    "description": res.description,
                    "source": res.source,
                    "resource_type": res.resource_type,
                    "minimum_level": res.minimum_level,
                    "minimum_level_label": get_level_label(res.minimum_level),
                    "maximum_level": res.maximum_level,
                    "maximum_level_label": get_level_label(res.maximum_level),
                    "duration_hours": res.duration_hours,
                    "url": res.url,
                    "is_demo": res.is_demo,
                },
                "relevance_score": score,
                "reason": reason,
                "current_level": gap_item["current_level"],
                "current_level_label": gap_item["current_level_label"],
                "required_level": gap_item["required_level"],
                "required_level_label": gap_item["required_level_label"],
            })

    # 4. Deterministic Sort:
    #    Priority (CRITICAL < HIGH < MEDIUM),
    #    Larger gap first (-gap),
    #    Higher relevance score (-relevance_score),
    #    Shorter duration (duration_hours)
    recommendation_list.sort(
        key=lambda r: (
            _PRIORITY_WEIGHTS.get(r["priority"], 99),
            -r["gap"],
            -r["relevance_score"],
            r["learning_resource"]["duration_hours"],
        )
    )

    # 5. Assign rank
    for idx, rec in enumerate(recommendation_list, start=1):
        rec["rank"] = idx

    # 6. Build summary
    unique_competencies = len({r["competency_id"] for r in recommendation_list})
    critical_count = sum(1 for r in recommendation_list if r["priority"] == "CRITICAL")

    summary = {
        "total_recommendations": len(recommendation_list),
        "competencies_with_recommendations": unique_competencies,
        "critical_gap_competencies": critical_count,
    }

    return {
        "learner": {
            "id": learner.id,
            "name": learner.name,
            "role_name": learner.role.name if learner.role else None,
        },
        "summary": summary,
        "recommendations": recommendation_list,
    }
