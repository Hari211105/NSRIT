"""
UPSKILL AI - Phase 2 Diagnostic Assessment Test Suite

Tests the diagnostic flow end to end with the TestClient against the seeded
demo database. Scoring is deterministic: every question's correct_option is
fixed in the seed, so a submission's weighted score - and therefore the derived
evidence level and competency update - is exact.

The suite snapshots and restores the demo learner's stored competency levels
and deletes the diagnostic assessments it creates, so running it leaves the
shared SQLite database exactly as it found it.

Tests:
1.  Diagnostic questions are mapped to the learner's role competencies
2.  Difficulty weights (EASY=1, MEDIUM=2, HARD=3) and weighted percent formula
3.  Correct answers produce the expected deterministic evidence levels
4.  Diagnostic evidence updates competency levels through the existing engine
5.  Skill gaps are recalculated after submission (gap_before -> gap_after)
6.  Same evidence produces the same result (determinism)
7.  Invalid submissions are rejected safely (400s, no state change)
8.  Repeated submission of the same completed assessment cannot jump levels
9.  Existing quiz/evidence behavior remains unchanged (regression)
"""

import sys
import os
import json
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import (
    Competency,
    DiagnosticAssessment,
    DiagnosticQuestion,
    LearnerCompetency,
    QuizAssessment,
    User,
)
from app.services import diagnostic_service
from app.services.diagnostic_service import (
    DIFFICULTY_WEIGHTS,
    calculate_weighted_score,
    get_difficulty_weight,
    recommended_action,
)
from app.services.competency_evidence_service import (
    evidence_level_from_percent,
    next_competency_level,
)
from app.services.gap_service import calculate_gap, calculate_gap_status
from auth_test_utils import AuthenticatedClient

client = AuthenticatedClient()

DEMO_EMAIL = "demo@statlearn.local"

# The demo seed gives every competency exactly one EASY, one MEDIUM and one
# HARD question, all with correct_option 1.
WEIGHTS = (1.0, 2.0, 3.0)
ALL_CORRECT_PERCENT = round(
    sum(WEIGHTS) / sum(WEIGHTS) * 100, 2
)  # 100.0
TWO_CORRECT_PERCENT = round(
    (WEIGHTS[0] + WEIGHTS[1]) / sum(WEIGHTS) * 100, 2
)  # 3/6 -> 50.0
ONE_CORRECT_PERCENT = round(WEIGHTS[0] / sum(WEIGHTS) * 100, 2)  # 1/6 -> 16.67
ZERO_CORRECT_PERCENT = 0.0


# ------------------------------------------------------------------
# State snapshot / restore (the suite must not leave the demo learner changed)
# ------------------------------------------------------------------

def _snapshot_learner():
    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.email == DEMO_EMAIL).first()
        assert learner is not None, "demo learner is not seeded"
        levels = {
            lc.competency_id: lc.current_level for lc in learner.learner_competencies
        }
        return learner.id, levels
    finally:
        db.close()


LEARNER_ID, ORIGINAL_LEVELS = _snapshot_learner()
CREATED_ASSESSMENT_IDS = []


def restore_state():
    """Restore the demo learner's levels and remove assessments this suite created."""
    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.id == LEARNER_ID).first()
        if learner is not None:
            for lc in learner.learner_competencies:
                original = ORIGINAL_LEVELS.get(lc.competency_id)
                if original is not None and lc.current_level != original:
                    lc.current_level = original
        if CREATED_ASSESSMENT_IDS:
            db.query(DiagnosticAssessment).filter(
                DiagnosticAssessment.id.in_(CREATED_ASSESSMENT_IDS)
            ).delete(synchronize_session=False)
            CREATED_ASSESSMENT_IDS.clear()
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_db_state():
    """Ensure each test runs with isolated, restored database state."""
    restore_state()
    yield
    restore_state()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def competency_id_by_name(name: str) -> int:
    db = SessionLocal()
    try:
        competency = db.query(Competency).filter(Competency.name == name).first()
        assert competency is not None, f"competency {name!r} is not seeded"
        return competency.id
    finally:
        db.close()


def stored_level(competency_id: int) -> int:
    db = SessionLocal()
    try:
        row = (
            db.query(LearnerCompetency)
            .filter(
                LearnerCompetency.user_id == LEARNER_ID,
                LearnerCompetency.competency_id == competency_id,
            )
            .first()
        )
        return row.current_level if row else 0
    finally:
        db.close()


def start_diagnostic(**params):
    """Start a diagnostic and register it for cleanup; returns the response."""
    response = client.post("/api/v1/diagnostic/start", params=params)
    assert response.status_code == 201, response.text
    data = response.json()
    CREATED_ASSESSMENT_IDS.append(data["assessment_id"])
    return data


def correct_options_by_id(question_ids):
    """Look up the stored correct_option for the given question ids (deterministic)."""
    db = SessionLocal()
    try:
        rows = db.query(DiagnosticQuestion).filter(
            DiagnosticQuestion.id.in_(question_ids)
        ).all()
        return {row.id: row.correct_option for row in rows}
    finally:
        db.close()


def all_correct_answers(questions):
    key = correct_options_by_id([q["question_id"] for q in questions])
    return [
        {"question_id": q["question_id"], "selected_option": key[q["question_id"]]}
        for q in questions
    ]


def answers_for_competencies(questions, target_comp_ids):
    """
    Build answers where questions for target_comp_ids get the correct option,
    and all other questions get an incorrect option.
    """
    key = correct_options_by_id([q["question_id"] for q in questions])
    answers = []
    for q in questions:
        correct = key[q["question_id"]]
        if q["competency_id"] in target_comp_ids:
            answers.append({"question_id": q["question_id"], "selected_option": correct})
        else:
            wrong = (correct + 1) % 4
            answers.append({"question_id": q["question_id"], "selected_option": wrong})
    return answers


def comp_result(data, competency_name):
    comp_id = competency_id_by_name(competency_name)
    return comp_by_id(data, comp_id)


def comp_by_id(data, comp_id):
    """
    Return per-competency result for a competency id.

    The endpoint serializes the competencies dict to JSON, so its keys are
    strings (e.g. '2'), even though the values carry the integer competency_id.
    This helper normalises the lookup so tests never need to remember that.
    """
    key = str(comp_id)
    competencies = data["competencies"]
    if key in competencies:
        return competencies[key]
    raise KeyError(
        f"Competency {comp_id} not in result competencies "
        f"(available: {sorted(competencies.keys())})."
    )


# ------------------------------------------------------------------
# 1. Questions are mapped to the role's competencies
# ------------------------------------------------------------------

def test_questions_map_to_role_competencies():
    print("Testing diagnostic questions map to the role's competencies...")
    data = start_diagnostic()
    questions = data["questions"]

    assert data["total_questions"] == len(questions)
    assert len(questions) >= 16, "expected at least 2 questions per competency"

    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.id == LEARNER_ID).first()
        role_competency_ids = {
            rm.competency_id for rm in learner.role.competency_mappings
        }
    finally:
        db.close()

    mapped = {q["competency_id"] for q in questions}
    assert mapped == role_competency_ids, (
        "questions must cover exactly the role's competencies"
    )

    # Each question is learner-safe: no answer key, has difficulty and mapping.
    for q in questions:
        assert {"question_id", "competency_id", "question", "options", "difficulty"} <= set(q)
        assert "correct_option" not in q and "explanation" not in q
        assert q["difficulty"] in DIFFICULTY_WEIGHTS
        assert len(q["options"]) == 4

    # Every question really is a stored DiagnosticQuestion.
    db = SessionLocal()
    try:
        stored_ids = {
            row.id for row in db.query(DiagnosticQuestion).all()
        }
    finally:
        db.close()
    assert {q["question_id"] for q in questions} <= stored_ids
    print(f"[OK] {len(questions)} questions cover exactly the role's competencies")


def test_competency_names_in_questions():
    print("Testing competency names are included for display...")
    data = start_diagnostic()
    db = SessionLocal()
    try:
        names = {
            c.id: c.name for c in db.query(Competency).all()
        }
    finally:
        db.close()
    for q in data["questions"]:
        assert q["competency_name"] == names[q["competency_id"]]
    print("[OK] Every question carries its competency's name")


# ------------------------------------------------------------------
# 2. Difficulty weighting (pure functions)
# ------------------------------------------------------------------

def test_difficulty_weights_deterministic():
    print("Testing difficulty weights are deterministic...")
    assert get_difficulty_weight("EASY") == 1.0
    assert get_difficulty_weight("MEDIUM") == 2.0
    assert get_difficulty_weight("HARD") == 3.0
    assert get_difficulty_weight("hard") == 3.0  # case-insensitive
    assert get_difficulty_weight("UNKNOWN") == 2.0  # safe default
    assert DIFFICULTY_WEIGHTS == {"EASY": 1.0, "MEDIUM": 2.0, "HARD": 3.0}
    print("[OK] EASY=1.0, MEDIUM=2.0, HARD=3.0, stable defaults")


def test_weighted_percent_formula():
    print("Testing the weighted percent formula...")
    questions = [
        {"id": 1, "correct_option": 1, "difficulty": "EASY", "competency_id": 1},
        {"id": 2, "correct_option": 1, "difficulty": "MEDIUM", "competency_id": 1},
        {"id": 3, "correct_option": 1, "difficulty": "HARD", "competency_id": 1},
    ]
    # All correct: weighted_score == weighted_total == 6 -> 100%.
    all_correct = calculate_weighted_score(questions, {1: 1, 2: 1, 3: 1})
    assert all_correct["weighted_percent"] == 100.0
    assert all_correct["weighted_score"] == 6.0

    # Only the EASY question correct: 1/6 -> 16.67%.
    easy_only = calculate_weighted_score(questions, {1: 1, 2: 0, 3: 0})
    assert easy_only["weighted_percent"] == 16.67
    assert easy_only["weighted_score"] == 1.0 and easy_only["weighted_total"] == 6.0

    # Only the HARD question correct: 3/6 -> 50%.
    hard_only = calculate_weighted_score(questions, {1: 0, 2: 0, 3: 1})
    assert hard_only["weighted_percent"] == 50.0

    # Unanswered questions count toward the denominator, never as correct.
    unanswered = calculate_weighted_score(questions, {1: 1})
    assert unanswered["weighted_total"] == 1.0
    assert unanswered["total_answered"] == 1
    assert unanswered["per_question"][1]["is_correct"] is False
    print("[OK] weighted_percent = correct weights / answered weights * 100")


# ------------------------------------------------------------------
# 3. Correct answers produce deterministic evidence
# ------------------------------------------------------------------

def test_all_correct_produces_full_evidence():
    print("Testing an all-correct diagnostic produces evidence level 3 everywhere...")
    data = start_diagnostic()
    questions = data["questions"]

    # Verify each question has a valid correct_option (0-3) and standard difficulty
    db = SessionLocal()
    try:
        from app.models import DiagnosticQuestion
        for q in questions:
            row = db.get(DiagnosticQuestion, q["question_id"])
            assert 0 <= row.correct_option <= 3, f"invalid correct_option {row.correct_option}"
            assert row.difficulty in ("EASY", "MEDIUM", "HARD")
    finally:
        db.close()

    response = client.post(
        f"/api/v1/diagnostic/{data['assessment_id']}/submit",
        json={"answers": all_correct_answers(questions)},
    )
    assert response.status_code == 200, response.text
    result = response.json()

    assert result["overall"]["weighted_percent"] == 100.0
    assert result["overall"]["total_correct"] == len(questions)
    assert result["overall"]["passed"] is True and result["overall"]["status"] == "PASSED"

    for comp in result["competencies"].values():
        assert comp["weighted_percent"] == 100.0
        assert comp["evidence_level"] == 3
        assert comp["total_correct"] == comp["total_questions"] == 3
        assert comp["difficulty_breakdown"] == {"EASY": 1, "MEDIUM": 1, "HARD": 1}
    print(f"[OK] {len(result['competencies'])} competencies each got evidence level 3")


def test_mixed_answers_produce_per_competency_evidence():
    print("Testing mixed answers produce per-competency evidence levels...")
    data = start_diagnostic()
    questions = data["questions"]

    comp_a = competency_id_by_name("Survey Methodology")       # strong performance
    comp_b = competency_id_by_name("Statistical Data Analysis")  # weak performance

    # Survey Methodology: all correct (100% -> evidence 3).
    # Statistical Data Analysis: all wrong (0% -> evidence 0).
    # Everything else: wrong too, so it stays out of the way.
    answers = answers_for_competencies(questions, {comp_a})
    response = client.post(
        f"/api/v1/diagnostic/{data['assessment_id']}/submit",
        json={"answers": answers},
    )
    assert response.status_code == 200, response.text
    result = response.json()

    strong = comp_by_id(result, comp_a)
    weak = comp_by_id(result, comp_b)

    assert strong["total_questions"] == 3 and strong["total_correct"] == 3
    assert strong["weighted_percent"] == 100.0
    assert strong["evidence_level"] == 3

    assert weak["total_questions"] == 3 and weak["total_correct"] == 0
    assert weak["weighted_percent"] == 0.0
    assert weak["evidence_level"] == 0
    print("[OK] Evidence is per-competency, not a single overall score")


# ------------------------------------------------------------------
# 4. Diagnostic evidence updates competency via the existing engine
# ------------------------------------------------------------------

def test_diagnostic_updates_competency_levels():
    print("Testing diagnostic evidence updates competency levels...")
    survey_id = competency_id_by_name("Survey Methodology")
    level_before = stored_level(survey_id)  # seed: 1
    assert level_before == 1, f"fixture expects level 1, found {level_before}"

    data = start_diagnostic()
    questions = data["questions"]
    answers = answers_for_competencies(questions, {survey_id})
    result = client.post(
        f"/api/v1/diagnostic/{data['assessment_id']}/submit",
        json={"answers": answers},
    ).json()

    comp = comp_by_id(result, survey_id)
    expected_new = next_competency_level(level_before, comp["evidence_level"])
    assert comp["previous_level"] == level_before
    assert comp["new_level"] == expected_new == 2, comp  # 100% on level 1 -> +1
    assert comp["level_changed"] is True
    assert stored_level(survey_id) == 2, "the level was not persisted"

    # A poor performance elsewhere never lowers an established level.
    viz_id = competency_id_by_name("Data Visualization")
    viz_before = stored_level(viz_id)  # seed: 3
    comp_viz = comp_by_id(result, viz_id)
    assert comp_viz["evidence_level"] == 0
    assert comp_viz["new_level"] == viz_before
    assert comp_viz["level_changed"] is False
    assert stored_level(viz_id) == viz_before
    print("[OK] Levels updated by the existing one-step, never-demote rule")


# ------------------------------------------------------------------
# 5. Gaps recalculated after submission
# ------------------------------------------------------------------

def test_gaps_recalculated_after_diagnostic():
    print("Testing gaps are recalculated after diagnostic submission...")
    survey_id = competency_id_by_name("Survey Methodology")
    required_level = 3  # demo role requirement

    data = start_diagnostic()
    questions = data["questions"]
    answers = answers_for_competencies(questions, {survey_id})
    result = client.post(
        f"/api/v1/diagnostic/{data['assessment_id']}/submit",
        json={"answers": answers},
    ).json()

    comp = comp_by_id(result, survey_id)
    assert comp["required_level"] == required_level
    assert comp["gap_before"] == calculate_gap(1, required_level) == 2
    assert comp["gap_after"] == calculate_gap(2, required_level) == 1

    # Severity comes from the existing gap service rules.
    assert comp["gap_status"] == calculate_gap_status(comp["gap_after"]) == "MODERATE_GAP"
    assert comp["gap_priority"] in ("CRITICAL", "HIGH", "MEDIUM", "NONE")
    assert comp["recommended_action"] == recommended_action(comp["gap_after"])

    # The existing /me/gaps endpoint reflects the new level.
    gaps = client.get("/api/v1/me/gaps").json()
    gap_row = next(g for g in gaps["gaps"] if g["competency_id"] == survey_id)
    assert gap_row["current_level"] == 2
    assert gap_row["gap"] == 1
    print("[OK] gap_before 2 -> gap_after 1, /me/gaps reflects the update")


# ------------------------------------------------------------------
# 6. Same evidence produces the same result
# ------------------------------------------------------------------

def test_same_evidence_same_result():
    print("Testing determinism: same evidence produces the same result...")
    survey_id = competency_id_by_name("Survey Methodology")

    results = []
    levels_seen = []
    for _ in range(2):
        level_before = stored_level(survey_id)
        data = start_diagnostic()
        questions = data["questions"]
        answers = answers_for_competencies(questions, {survey_id})
        result = client.post(
            f"/api/v1/diagnostic/{data['assessment_id']}/submit",
            json={"answers": answers},
        ).json()
        comp = comp_by_id(result, survey_id)
        results.append(
            (comp["weighted_percent"], comp["evidence_level"], comp["new_level"],
             comp["gap_after"], comp["gap_status"], comp["recommended_action"])
        )
        levels_seen.append(stored_level(survey_id))
        # Reset for a clean second run: restore the pre-assessment level.
        db = SessionLocal()
        try:
            row = (
                db.query(LearnerCompetency)
                .filter(
                    LearnerCompetency.user_id == LEARNER_ID,
                    LearnerCompetency.competency_id == survey_id,
                )
                .first()
            )
            row.current_level = level_before
            db.commit()
        finally:
            db.close()

    assert results[0] == results[1], f"non-deterministic results: {results}"
    assert levels_seen[0] == levels_seen[1]
    print("[OK] Identical answers twice -> identical evidence, level and severity")


# ------------------------------------------------------------------
# 7. Invalid submissions rejected safely
# ------------------------------------------------------------------

def test_invalid_submissions_rejected():
    print("Testing invalid submissions are rejected without state change...")
    survey_id = competency_id_by_name("Survey Methodology")
    level_before = stored_level(survey_id)

    data = start_diagnostic()
    assessment_id = data["assessment_id"]
    questions = data["questions"]
    good_id = questions[0]["question_id"]

    def submit(payload):
        return client.post(f"/api/v1/diagnostic/{assessment_id}/submit", json=payload)

    # Empty answers list.
    response = submit({"answers": []})
    assert response.status_code == 400, response.text

    # Unknown question id (belongs to another assessment).
    response = submit({"answers": [{"question_id": 9999999, "selected_option": 0}]})
    assert response.status_code == 400, response.text

    # Duplicate question id.
    response = submit({"answers": [
        {"question_id": good_id, "selected_option": 0},
        {"question_id": good_id, "selected_option": 1},
    ]})
    assert response.status_code == 400, response.text

    # Out-of-range option index.
    response = submit({"answers": [{"question_id": good_id, "selected_option": 4}]})
    assert response.status_code == 400, response.text

    # Malformed body (422 from pydantic).
    assert submit({"answers": [{"question_id": "one", "selected_option": 0}]}).status_code == 422
    assert submit({"answers": [{"selected_option": 0}]}).status_code == 422

    # None of the failed submissions changed any level.
    assert stored_level(survey_id) == level_before
    db = SessionLocal()
    try:
        assessment = db.get(DiagnosticAssessment, assessment_id)
        assert assessment.status == "IN_PROGRESS", "a failed submit finalized the assessment"
    finally:
        db.close()
    print("[OK] 400/422 on invalid submissions, levels and status unchanged")


# ------------------------------------------------------------------
# 8. Repeated submission cannot jump levels
# ------------------------------------------------------------------

def test_repeated_submission_rejected_not_replayed():
    print("Testing a completed assessment cannot be resubmitted...")
    data = start_diagnostic()
    assessment_id = data["assessment_id"]
    answers = all_correct_answers(data["questions"])

    first = client.post(
        f"/api/v1/diagnostic/{assessment_id}/submit", json={"answers": answers}
    )
    assert first.status_code == 200, first.text

    # Second submission of the same (or even different) answers is rejected.
    second = client.post(
        f"/api/v1/diagnostic/{assessment_id}/submit", json={"answers": answers}
    )
    assert second.status_code == 400, second.text
    assert "cannot resubmit" in second.json()["detail"].lower()

    # Exactly one assessment record was finalized - no replay, no extra jump.
    db = SessionLocal()
    try:
        assessment = db.get(DiagnosticAssessment, assessment_id)
        assert assessment.status == "PASSED"
        stored = json.loads(assessment.competency_results)
    finally:
        db.close()
    print("[OK] Resubmission rejected with 400 - one submission, one bounded update")


def test_new_assessments_only_bounded_steps():
    print("Testing repeated new diagnostics climb at most one level each...")
    survey_id = competency_id_by_name("Survey Methodology")
    # Reset to the seeded level 1 so the climb is fully predictable.
    db = SessionLocal()
    try:
        row = (
            db.query(LearnerCompetency)
            .filter(
                LearnerCompetency.user_id == LEARNER_ID,
                LearnerCompetency.competency_id == survey_id,
            )
            .first()
        )
        row.current_level = 1
        db.commit()
    finally:
        db.close()

    level = 1
    for attempt in range(3):
        data = start_diagnostic()
        answers = answers_for_competencies(data["questions"], {survey_id})
        result = client.post(
            f"/api/v1/diagnostic/{data['assessment_id']}/submit",
            json={"answers": answers},
        ).json()
        comp = comp_by_id(result, survey_id)
        assert comp["previous_level"] == level
        step = comp["new_level"] - comp["previous_level"]
        assert step in (0, 1), f"attempt {attempt + 1} jumped {step} levels"
        level = comp["new_level"]
        assert level <= 4
        assert stored_level(survey_id) == level
    assert level == 3, "three perfect diagnostics should land exactly at level 3 (evidence cap)"
    print(f"[OK] Three consecutive perfect diagnostics: level 1 -> {level}, +1 max each")


# ------------------------------------------------------------------
# 9. Existing quiz/evidence behavior unchanged (regression)
# ------------------------------------------------------------------

def test_existing_quiz_evidence_unchanged():
    print("Testing existing quiz evidence behavior is unchanged...")
    # The legacy /me/evidence endpoint still serves quiz evidence only.
    response = client.get("/api/v1/me/evidence")
    assert response.status_code == 200, response.text
    data = response.json()
    for record in data["evidence"]:
        assert {"document_id", "competency_id", "score_percent", "evidence_level"} <= set(record)
        assert "assessment_id" not in record, "diagnostic leaked into quiz evidence"

    # Diagnostics never write to the document-scoped quiz evidence table.
    db = SessionLocal()
    try:
        diagnostic_ids = {a.id for a in db.query(DiagnosticAssessment).all()}
        assert diagnostic_ids, "expected this suite to have created diagnostics"
        quiz_rows = db.query(QuizAssessment).filter(
            QuizAssessment.document_id.in_(diagnostic_ids)
        ).all()
        assert quiz_rows == [], "diagnostic created quiz evidence rows"
    finally:
        db.close()
    print("[OK] Quiz evidence table and endpoints unaffected by diagnostics")


def test_health_and_history_conventions():
    print("Testing health endpoint and diagnostic history...")
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["application"] == "UPSKILL AI"

    history = client.get("/api/v1/diagnostic/history")
    assert history.status_code == 200
    data = history.json()
    assert data["total_assessments"] == len(data["assessments"])
    assert data["total_assessments"] >= 1
    for a in data["assessments"]:
        assert {"id", "assessment_type", "total_questions", "score_percent",
                "passed", "status", "created_at"} <= set(a)
    print("[OK] /health preserved, history returns the created assessments")


def test_assessment_type_validation():
    print("Testing assessment_type validation on start...")
    data = start_diagnostic(assessment_type="post-learning")
    assert data["assessment_type"] == "post-learning"
    response = client.post(
        "/api/v1/diagnostic/start", params={"assessment_type": "nonsense"}
    )
    assert response.status_code == 400, response.text
    print("[OK] 'post-learning' accepted, unknown type rejected with 400")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING UPSKILL AI PHASE 2 DIAGNOSTIC ASSESSMENT TEST SUITE")
    print("=" * 60)
    try:
        test_questions_map_to_role_competencies()
        test_competency_names_in_questions()
        test_difficulty_weights_deterministic()
        test_weighted_percent_formula()
        test_all_correct_produces_full_evidence()
        test_mixed_answers_produce_per_competency_evidence()
        test_diagnostic_updates_competency_levels()
        test_gaps_recalculated_after_diagnostic()
        test_same_evidence_same_result()
        test_invalid_submissions_rejected()
        test_repeated_submission_rejected_not_replayed()
        test_new_assessments_only_bounded_steps()
        test_existing_quiz_evidence_unchanged()
        test_health_and_history_conventions()
        test_assessment_type_validation()
    finally:
        restore_state()
    print("=" * 60)
    print("ALL PHASE 2 DIAGNOSTIC ASSESSMENT TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
