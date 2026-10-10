"""
UPSKILL AI - Phase 6A Competency Evidence & Gap Recalculation Test Suite

MCQ generation is replaced with an injected fake so no OpenRouter request is made
and no API key is read or used. The fake uses a known answer key
(correct_option = question index % 4), so a submission's score - and therefore
the derived evidence level - is exact.

The suite snapshots and restores the demo learner's stored competency levels and
deletes the evidence rows it creates, so running it leaves the shared SQLite
database exactly as it found it.

Tests:
1.  Percentage -> evidence level boundaries (<40=0, 40=1, 60=2, 80=3, 100=3)
2.  Invalid percentages are rejected
3.  The at-most-one-level rule, the cap and "never decreases"
4.  build_competency_update() refuses to guess a competency
5.  build_competency_update() recalculates the gap via the existing gap_service
6.  A successful quiz records evidence and raises the level by exactly one
7.  A poor score never lowers an established level
8.  Repeated submissions cannot jump the level uncontrollably
9.  A document with no competency association returns competency_update = null
10. An unknown competency id at upload is rejected
11. The existing quiz scoring contract is unchanged (success + validation errors)
12. GET /me/evidence returns the stored evidence
"""

import sys
import os
import io
import contextlib
import pymupdf as fitz  # PyMuPDF
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models import User, Competency, LearnerCompetency, QuizAssessment
from app.services import mcq_service
from app.services.competency_evidence_service import (
    CompetencyEvidenceError,
    build_competency_update,
    evidence_level_from_percent,
    next_competency_level,
)
from app.services.gap_service import calculate_gap
from auth_test_utils import AuthenticatedClient

client = AuthenticatedClient()

MCQ_COUNT = 5
ANSWER_KEY = [index % 4 for index in range(MCQ_COUNT)]  # [0, 1, 2, 3, 0]
DEMO_EMAIL = "demo@statlearn.local"

# Competency used for the level-raising tests: the demo learner is at level 1
# with a required level of 3, so the gap is 2 before and 1 after a +1 step.
RAISING_COMPETENCY = "Survey Methodology"
# Competency the learner is already advanced in (level 3, required 2), used to
# prove a poor quiz cannot demote them.
ESTABLISHED_COMPETENCY = "Data Visualization"

LEGACY_QUIZ_FIELDS = {
    "document_id",
    "score",
    "total_questions",
    "answered_questions",
    "unanswered_questions",
    "percentage",
    "pass_threshold_percent",
    "passed",
    "status",
    "results",
}

UPDATE_FIELDS = {
    "competency_id",
    "previous_level",
    "evidence_level",
    "new_level",
    "level_changed",
    "gap_before",
    "gap_after",
}


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
CREATED_DOC_IDS = []


def restore_state():
    """Restore the demo learner's levels and remove evidence this suite created."""
    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.id == LEARNER_ID).first()
        if learner is not None:
            for lc in learner.learner_competencies:
                original = ORIGINAL_LEVELS.get(lc.competency_id)
                if original is not None and lc.current_level != original:
                    lc.current_level = original
        if CREATED_DOC_IDS:
            db.query(QuizAssessment).filter(
                QuizAssessment.learner_id == LEARNER_ID,
                QuizAssessment.document_id.in_(CREATED_DOC_IDS),
            ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def build_wrapped_pdf(words: int = 60) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    text = " ".join(f"token{i}" for i in range(words))
    rc = page.insert_textbox(fitz.Rect(36, 36, 559, 806), text, fontsize=9)
    assert rc >= 0, "fixture text did not fit the page box"
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


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


def stored_evidence(document_id: int):
    db = SessionLocal()
    try:
        return (
            db.query(QuizAssessment)
            .filter(QuizAssessment.document_id == document_id)
            .order_by(QuizAssessment.id.asc())
            .all()
        )
    finally:
        db.close()


def upload_document(name: str, competency_id=None) -> int:
    files = {"file": (name, io.BytesIO(build_wrapped_pdf()), "application/pdf")}
    params = {"competency_id": competency_id} if competency_id is not None else None
    response = client.post("/api/v1/documents/upload", files=files, params=params)
    assert response.status_code == 201, f"upload failed: {response.text}"
    doc_id = response.json()["id"]
    CREATED_DOC_IDS.append(doc_id)
    return doc_id


def build_question(index: int, chunk_id: int) -> dict:
    return {
        "question": f"Question {index + 1} for chunk {chunk_id}?",
        "options": [f"Q{index + 1} option {letter}" for letter in "ABCD"],
        "correct_option": ANSWER_KEY[index],
        "explanation": f"Because option {ANSWER_KEY[index]} is supported by the chunk.",
        "source_chunk_id": chunk_id,
    }


@contextlib.contextmanager
def fake_generation():
    """Replace mcq_service.generate_mcqs with a fake using a known answer key."""
    def fake_generate(chunk_text, source_chunk_id, **kwargs):
        return [build_question(i, source_chunk_id) for i in range(MCQ_COUNT)]

    original = mcq_service.generate_mcqs
    mcq_service.generate_mcqs = fake_generate
    try:
        yield
    finally:
        mcq_service.generate_mcqs = original


def document_with_mcqs(name: str, competency_id=None):
    """Upload a document and generate MCQs for it; returns (document_id, questions)."""
    doc_id = upload_document(name, competency_id)
    with fake_generation():
        generated = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")
    assert generated.status_code == 201, generated.text

    quiz = client.get(f"/api/v1/documents/{doc_id}/quiz")
    assert quiz.status_code == 200, quiz.text
    return doc_id, quiz.json()["questions"]


def answers_for_score(questions, correct_count: int):
    """Answer exactly `correct_count` questions correctly and the rest wrongly."""
    answers = []
    for index, question in enumerate(questions):
        if index < correct_count:
            selected = ANSWER_KEY[index]
        else:
            selected = (ANSWER_KEY[index] + 1) % 4
        answers.append({
            "question_id": question["question_id"],
            "selected_option": selected,
        })
    return answers


def submit(doc_id: int, answers):
    return client.post(f"/api/v1/documents/{doc_id}/quiz/submit", json={"answers": answers})


# ------------------------------------------------------------------
# 1-2. Percentage -> evidence level (pure function)
# ------------------------------------------------------------------

def test_evidence_level_boundaries():
    print("Testing evidence_level_from_percent() boundaries...")
    expected = [
        (0, 0), (10, 0), (39.99, 0),
        (40, 1), (50, 1), (59.99, 1),
        (60, 2), (70, 2), (79.99, 2),
        (80, 3), (90, 3), (100, 3),
        (100.0, 3), (39.5, 0),
    ]
    for percent, level in expected:
        actual = evidence_level_from_percent(percent)
        assert actual == level, f"{percent}% -> {actual}, expected {level}"
    print("[OK] <40 -> 0, 40-59 -> 1, 60-79 -> 2, 80-100 -> 3")


def test_invalid_percentages_rejected():
    print("Testing invalid percentages are rejected...")
    for bad in (-1, -0.01, 100.01, 101, 1000, float("nan"), "60", None, True, False):
        try:
            evidence_level_from_percent(bad)
        except CompetencyEvidenceError:
            pass
        else:
            raise AssertionError(f"expected CompetencyEvidenceError for {bad!r}")

    # Valid boundary values must still work.
    assert evidence_level_from_percent(0) == 0
    assert evidence_level_from_percent(100) == 3
    print("[OK] Out-of-range / non-numeric / NaN percentages rejected")


# ------------------------------------------------------------------
# 3. The level-change safety rule
# ------------------------------------------------------------------

def test_at_most_one_level_rule():
    print("Testing the at-most-one-level safety rule...")
    # A top evidence level from a low existing level moves exactly one step.
    assert next_competency_level(1, 3) == 2
    assert next_competency_level(2, 3) == 3
    assert next_competency_level(0, 3) == 1
    assert next_competency_level(1, 2) == 2
    # Already at/above the evidence level -> unchanged.
    assert next_competency_level(3, 3) == 3
    assert next_competency_level(3, 1) == 3
    assert next_competency_level(4, 3) == 4
    print("[OK] One quiz raises a level by at most one")


def test_level_never_decreases_and_is_capped():
    print("Testing that a poor score never decreases a level...")
    for existing in (1, 2, 3, 4):
        for evidence in (0, 1, 2, 3):
            new_level = next_competency_level(existing, evidence)
            assert new_level >= existing, \
                f"level dropped from {existing} to {new_level} (evidence {evidence})"
            assert new_level - existing <= 1, \
                f"level jumped {existing} -> {new_level} (evidence {evidence})"
            assert new_level <= 4, f"level {new_level} exceeds the 4-level scale"

    # Out-of-range inputs are rejected rather than silently clamped.
    for existing, evidence in ((5, 2), (-1, 2), (2, 4), (2, -1), (2, "2")):
        try:
            next_competency_level(existing, evidence)
        except CompetencyEvidenceError:
            pass
        else:
            raise AssertionError(f"expected error for ({existing!r}, {evidence!r})")
    print("[OK] Never decreases, capped at 4, invalid inputs rejected")


# ------------------------------------------------------------------
# 4-5. build_competency_update()
# ------------------------------------------------------------------

def test_build_update_refuses_to_guess_competency():
    print("Testing that a missing competency is never guessed...")
    try:
        build_competency_update(None, 100.0, 1, 3)
    except CompetencyEvidenceError as exc:
        assert "no competency" in str(exc).lower(), str(exc)
    else:
        raise AssertionError("expected CompetencyEvidenceError for competency_id=None")

    for bad_id in ("1", 1.5, True):
        try:
            build_competency_update(bad_id, 100.0, 1, 3)
        except CompetencyEvidenceError:
            pass
        else:
            raise AssertionError(f"expected error for competency_id={bad_id!r}")
    print("[OK] competency_id=None raises instead of assigning a competency")


def test_build_update_recalculates_gap():
    print("Testing gap recalculation through the existing gap_service...")
    update = build_competency_update(7, 100.0, 1, 3)

    assert set(update) == UPDATE_FIELDS, sorted(update)
    assert update["competency_id"] == 7
    assert update["previous_level"] == 1
    assert update["evidence_level"] == 3
    assert update["new_level"] == 2
    assert update["level_changed"] is True
    # Gap must match the Phase 3 gap service exactly, before and after.
    assert update["gap_before"] == calculate_gap(1, 3) == 2
    assert update["gap_after"] == calculate_gap(2, 3) == 1

    # A poor score changes nothing but still reports the unchanged gap.
    poor = build_competency_update(7, 20.0, 3, 3)
    assert poor["evidence_level"] == 0
    assert poor["new_level"] == 3
    assert poor["level_changed"] is False
    assert poor["gap_before"] == poor["gap_after"] == calculate_gap(3, 3) == 0

    # An unmapped competency has no requirement, so no gap is reported.
    unmapped = build_competency_update(7, 100.0, 1, None)
    assert unmapped["gap_before"] is None and unmapped["gap_after"] is None
    print("[OK] gap_before/gap_after come from gap_service.calculate_gap")


# ------------------------------------------------------------------
# 6. Successful quiz -> evidence + one level up
# ------------------------------------------------------------------

def test_successful_quiz_records_evidence_and_raises_level():
    print("Testing a 100% quiz records evidence and raises the level by one...")
    competency_id = competency_id_by_name(RAISING_COMPETENCY)
    level_before = stored_level(competency_id)
    required_level = 3  # Survey Methodology requirement in the demo seed
    assert level_before >= 1, f"fixture expects an established level, found {level_before}"

    doc_id, questions = document_with_mcqs("phase6a_success.pdf", competency_id)
    response = submit(doc_id, answers_for_score(questions, MCQ_COUNT))
    assert response.status_code == 200, response.text
    data = response.json()

    # The pre-existing quiz response contract is unchanged.
    assert LEGACY_QUIZ_FIELDS.issubset(data), sorted(set(data) - LEGACY_QUIZ_FIELDS)
    assert data["score"] == 5 and data["total_questions"] == 5
    assert data["percentage"] == 100.0
    assert data["passed"] is True and data["status"] == "PASSED"
    assert "correct_option" not in response.text, "the answer key leaked"
    assert "competency_update" in data, "the competency update is missing"

    expected_new = next_competency_level(level_before, 3)
    update = data["competency_update"]
    assert set(update) == UPDATE_FIELDS, sorted(update)
    assert update == {
        "competency_id": competency_id,
        "previous_level": level_before,
        "evidence_level": 3,
        "new_level": expected_new,
        "level_changed": expected_new != level_before,
        "gap_before": calculate_gap(level_before, required_level),
        "gap_after": calculate_gap(expected_new, required_level),
    }, update
    assert expected_new - level_before <= 1, "more than one level was granted"

    # Persisted evidence and the recalculated learner level.
    assert stored_level(competency_id) == expected_new, "the learner level was not updated"
    evidence = stored_evidence(doc_id)
    assert len(evidence) == 1, f"expected 1 evidence row, found {len(evidence)}"
    assert evidence[0].learner_id == LEARNER_ID
    assert evidence[0].competency_id == competency_id
    assert evidence[0].score_percent == 100.0
    assert evidence[0].evidence_level == 3
    assert evidence[0].created_at
    print(f"[OK] 100% quiz: level {level_before} -> {expected_new}, "
          f"gap {update['gap_before']} -> {update['gap_after']}, one evidence row stored")


def test_moderate_score_records_lower_evidence():
    print("Testing a 60% quiz (evidence 2) still moves the level by one step...")
    competency_id = competency_id_by_name("Statistical Software")  # level 1, required 2
    level_before = stored_level(competency_id)

    doc_id, questions = document_with_mcqs("phase6a_moderate.pdf", competency_id)
    data = submit(doc_id, answers_for_score(questions, 3)).json()

    # 3 of 5 = 60%.
    assert data["percentage"] == 60.0, data
    update = data["competency_update"]
    expected_new = next_competency_level(level_before, 2)
    assert update["evidence_level"] == 2, update
    assert update["previous_level"] == level_before
    assert update["new_level"] == expected_new, update
    assert update["gap_before"] == calculate_gap(level_before, 2)
    assert update["gap_after"] == calculate_gap(expected_new, 2)
    assert stored_evidence(doc_id)[0].evidence_level == 2
    print("[OK] 60% quiz recorded evidence level 2 with a bounded level step")


# ------------------------------------------------------------------
# 7. Poor score never demotes
# ------------------------------------------------------------------

def test_poor_score_never_lowers_level():
    print("Testing a 0% quiz cannot lower an established level...")
    competency_id = competency_id_by_name(ESTABLISHED_COMPETENCY)
    level_before = stored_level(competency_id)
    assert level_before >= 1, f"fixture expects an established level, found {level_before}"

    doc_id, questions = document_with_mcqs("phase6a_poor.pdf", competency_id)
    data = submit(doc_id, answers_for_score(questions, 0)).json()

    assert data["percentage"] == 0.0
    assert data["passed"] is False and data["status"] == "FAILED"
    update = data["competency_update"]
    assert update["evidence_level"] == 0
    assert update["previous_level"] == level_before
    assert update["new_level"] == level_before, "a poor score changed the level"
    assert update["level_changed"] is False
    assert update["gap_before"] == update["gap_after"]

    assert stored_level(competency_id) == level_before, "a poor score lowered the level"
    # The evidence is still recorded, even though no level changed.
    evidence = stored_evidence(doc_id)
    assert len(evidence) == 1 and evidence[0].evidence_level == 0
    print(f"[OK] 0% quiz stored evidence level 0 and left the level at {level_before}")


# ------------------------------------------------------------------
# 8. Repeated submissions cannot jump the level
# ------------------------------------------------------------------

def test_repeated_submissions_do_not_jump_levels():
    print("Testing repeated submissions only move the level one step at a time...")
    competency_id = competency_id_by_name(RAISING_COMPETENCY)
    doc_id, questions = document_with_mcqs("phase6a_repeat.pdf", competency_id)
    answers = answers_for_score(questions, MCQ_COUNT)

    level = stored_level(competency_id)
    start_level = level
    for attempt in range(3):
        data = submit(doc_id, answers).json()
        update = data["competency_update"]
        assert update["previous_level"] == level, \
            f"attempt {attempt + 1} reported previous_level {update['previous_level']} != {level}"
        step = update["new_level"] - update["previous_level"]
        assert step in (0, 1), f"attempt {attempt + 1} jumped {step} levels"
        level = update["new_level"]
        assert level <= 4
        # Evidence level 3 can never lift a learner past level 3, so repeated
        # submissions converge instead of climbing without limit.
        assert level <= max(start_level, 3), \
            f"level {level} exceeded the evidence-supported cap"
        assert stored_level(competency_id) == level

    assert len(stored_evidence(doc_id)) == 3, "each submission should record evidence"
    print(f"[OK] Three repeated 100% submissions -> level {stored_level(competency_id)}, +1 max per call")


# ------------------------------------------------------------------
# 9-10. No competency association
# ------------------------------------------------------------------

def test_document_without_competency_returns_null_update():
    print("Testing a document with no competency association...")
    doc_id, questions = document_with_mcqs("phase6a_unlinked.pdf")  # no competency_id

    response = submit(doc_id, answers_for_score(questions, MCQ_COUNT))
    assert response.status_code == 200, response.text
    data = response.json()

    # The quiz still scores normally - only the competency part is skipped.
    assert LEGACY_QUIZ_FIELDS.issubset(data)
    assert data["score"] == 5 and data["percentage"] == 100.0
    assert data["passed"] is True
    assert "competency_update" in data, "the key must be present, explicitly null"
    assert data["competency_update"] is None, data["competency_update"]

    # No competency was guessed and no evidence was invented for it.
    assert stored_evidence(doc_id) == [], "evidence was recorded without a competency"

    db = SessionLocal()
    try:
        assert db.query(QuizAssessment).filter(
            QuizAssessment.document_id == doc_id
        ).count() == 0
    finally:
        db.close()
    print("[OK] competency_update is null and no evidence is guessed or stored")


def test_unknown_competency_on_upload_rejected():
    print("Testing an unknown competency id on upload...")
    files = {"file": ("phase6a_bad_comp.pdf", io.BytesIO(build_wrapped_pdf()), "application/pdf")}
    response = client.post(
        "/api/v1/documents/upload", files=files, params={"competency_id": 9999999}
    )
    assert response.status_code == 400, f"expected 400, got {response.status_code}"
    assert "not found" in response.json()["detail"].lower()

    # A nonexistent document id still 404s on the quiz endpoints.
    assert client.get("/api/v1/documents/9999999/quiz").status_code == 404
    print("[OK] Unknown competency -> 400, unknown document -> 404")


# ------------------------------------------------------------------
# 11. Existing quiz scoring contract unchanged
# ------------------------------------------------------------------

def test_existing_quiz_scoring_still_works():
    print("Testing that the existing quiz scoring rules are unchanged...")
    doc_id, questions = document_with_mcqs("phase6a_regression.pdf")

    # Partial answers: score is out of the full quiz, unanswered not revealed.
    partial = submit(doc_id, answers_for_score(questions, 2)[:2]).json()
    assert partial["score"] == 2
    assert partial["total_questions"] == 5
    assert partial["answered_questions"] == 2
    assert partial["unanswered_questions"] == 3
    assert partial["percentage"] == 40.0
    assert len(partial["results"]) == 2
    assert "correct_option" not in partial["results"][0]

    # Validation errors keep their status codes and messages.
    question_id = questions[0]["question_id"]
    assert submit(doc_id, [{"question_id": question_id, "selected_option": 4}]).status_code == 400
    assert submit(doc_id, [
        {"question_id": question_id, "selected_option": 0},
        {"question_id": question_id, "selected_option": 1},
    ]).status_code == 400
    assert submit(doc_id, [{"question_id": 9999999, "selected_option": 0}]).status_code == 400
    assert submit(doc_id, []).status_code == 400

    no_mcqs_doc = upload_document("phase6a_no_mcqs.pdf")
    assert submit(no_mcqs_doc, [{"question_id": 1, "selected_option": 0}]).status_code == 404
    print("[OK] Success, partial scoring and all validation errors behave as before")


# ------------------------------------------------------------------
# 12. GET /me/evidence
# ------------------------------------------------------------------

def test_me_evidence_endpoint():
    print("Testing GET /api/v1/me/evidence...")
    response = client.get("/api/v1/me/evidence")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["learner_id"] == LEARNER_ID
    assert data["total_evidence"] == len(data["evidence"])
    assert "prototype" in data["assessment_rule_note"].lower()
    assert "not an official" in data["assessment_rule_note"].lower()

    assert data["evidence"], "expected the earlier tests to have recorded evidence"
    for record in data["evidence"]:
        assert {
            "id", "document_id", "document_filename", "competency_id",
            "competency_name", "score_percent", "evidence_level",
            "current_level", "current_level_label", "created_at",
        } == set(record), sorted(record)
        assert record["evidence_level"] in (0, 1, 2, 3)
        assert 0 <= record["score_percent"] <= 100
        assert record["document_filename"]
        assert "correct_option" not in response.text

    # Every returned row is an assessment of the demo learner, and every stored
    # assessment of the demo learner is returned.
    db = SessionLocal()
    try:
        ids = {row.id for row in db.query(QuizAssessment).filter(
            QuizAssessment.learner_id == LEARNER_ID
        ).all()}
    finally:
        db.close()
    assert {record["id"] for record in data["evidence"]} == ids
    print(f"[OK] /me/evidence returned {data['total_evidence']} assessment record(s)")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING STATLEARN AI PHASE 6A COMPETENCY EVIDENCE TEST SUITE")
    print("=" * 60)
    try:
        test_evidence_level_boundaries()
        test_invalid_percentages_rejected()
        test_at_most_one_level_rule()
        test_level_never_decreases_and_is_capped()
        test_build_update_refuses_to_guess_competency()
        test_build_update_recalculates_gap()
        test_successful_quiz_records_evidence_and_raises_level()
        test_moderate_score_records_lower_evidence()
        test_poor_score_never_lowers_level()
        test_repeated_submissions_do_not_jump_levels()
        test_document_without_competency_returns_null_update()
        test_unknown_competency_on_upload_rejected()
        test_existing_quiz_scoring_still_works()
        test_me_evidence_endpoint()
    finally:
        restore_state()
    print("=" * 60)
    print("ALL PHASE 6A COMPETENCY EVIDENCE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
