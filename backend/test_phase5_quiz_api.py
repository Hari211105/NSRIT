"""
UPSKILL AI - Phase 5 Step 5A Learner Quiz & Scoring Verification Test Suite

MCQ generation is replaced with an injected fake so no OpenRouter request is made
and no API key is read or used. The fake uses a known answer key
(correct_option = question index % 4) so scoring can be asserted exactly.

Tests:
1. The learner quiz endpoint never exposes correct_option / explanation /
   source_chunk_id
2. Successful submission: score, total, percentage, pass status
3. Correct score calculation, including the 60% prototype threshold boundary
4. Partial answers: unanswered questions are counted but never revealed
5. Invalid question id, invalid selected option, duplicate question id
6. Empty answers, no MCQs, unknown document, malformed body
7. quiz_service unit tests (percentage, learner shaping, empty MCQ list)
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
from app.services import mcq_service, quiz_service
from app.services.quiz_service import (
    PASS_THRESHOLD_PERCENT,
    QuizValidationError,
    build_learner_questions,
    calculate_percentage,
    score_submission,
)
from auth_test_utils import AuthenticatedClient

client = AuthenticatedClient()

MCQ_COUNT = 5
LEARNER_FIELDS = {"question_id", "question", "options"}
ANSWER_KEY = [index % 4 for index in range(MCQ_COUNT)]  # [0, 1, 2, 3, 0]


# ------------------------------------------------------------------
# Fixtures / helpers
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


def upload_document(name: str) -> int:
    files = {"file": (name, io.BytesIO(build_wrapped_pdf()), "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201, f"upload failed: {response.text}"
    return response.json()["id"]


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
        if isinstance(source_chunk_id, bool) or not isinstance(source_chunk_id, int):
            raise mcq_service.MCQGenerationError("bad chunk id in test fixture")
        return [build_question(i, source_chunk_id) for i in range(MCQ_COUNT)]

    original = mcq_service.generate_mcqs
    mcq_service.generate_mcqs = fake_generate
    try:
        yield
    finally:
        mcq_service.generate_mcqs = original


def document_with_mcqs(name: str) -> tuple:
    """Upload a document and generate MCQs for it; returns (document_id, questions)."""
    doc_id = upload_document(name)
    with fake_generation():
        generated = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")
    assert generated.status_code == 201, generated.text

    quiz = client.get(f"/api/v1/documents/{doc_id}/quiz")
    assert quiz.status_code == 200, quiz.text
    return doc_id, quiz.json()["questions"]


def submit(doc_id: int, answers):
    return client.post(f"/api/v1/documents/{doc_id}/quiz/submit", json={"answers": answers})


def answer_all(questions, offset: int = 0):
    """Answer every question with the correct option shifted by `offset`."""
    return [
        {
            "question_id": question["question_id"],
            "selected_option": (ANSWER_KEY[index] + offset) % 4,
        }
        for index, question in enumerate(questions)
    ]


# ------------------------------------------------------------------
# 1. The security rule: learner view never exposes the answer key
# ------------------------------------------------------------------

def test_learner_quiz_does_not_expose_answers():
    print("Testing that the learner quiz never exposes the answer key...")
    doc_id, questions = document_with_mcqs("quiz_no_leak.pdf")

    response = client.get(f"/api/v1/documents/{doc_id}/quiz")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["document_id"] == doc_id
    assert data["total_questions"] == MCQ_COUNT
    assert len(data["questions"]) == MCQ_COUNT

    for question in data["questions"]:
        assert set(question) == LEARNER_FIELDS, \
            f"learner question leaked extra fields: {sorted(question)}"
        assert question["question"]
        assert len(question["options"]) == 4

    # No answer-key keys anywhere in the raw body...
    for forbidden in ('"correct_option"', '"explanation"', '"source_chunk_id"'):
        assert forbidden not in response.text, f"{forbidden} leaked in the quiz body"

    # ...and no answer-key values either: the explanation text is never sent.
    assert "Because option" not in response.text, "explanation text leaked"
    assert '"mcqs"' not in response.text, "inspection payload leaked into the quiz view"

    print("[OK] Quiz exposes only question_id, question and options")


def test_inspection_endpoint_still_has_the_answer_key():
    print("Testing that GET /mcqs still returns the answer key (unchanged)...")
    doc_id, _ = document_with_mcqs("quiz_admin_view.pdf")

    response = client.get(f"/api/v1/documents/{doc_id}/mcqs")
    assert response.status_code == 200, response.text
    mcqs = response.json()["mcqs"]
    assert len(mcqs) == MCQ_COUNT
    for mcq in mcqs:
        assert "correct_option" in mcq
        assert "explanation" in mcq
        assert "source_chunk_id" in mcq

    print("[OK] Admin/inspection endpoint unchanged")


# ------------------------------------------------------------------
# 2-3. Scoring
# ------------------------------------------------------------------

def test_successful_submission():
    print("Testing a fully correct submission...")
    doc_id, questions = document_with_mcqs("quiz_all_correct.pdf")

    response = submit(doc_id, answer_all(questions))
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["document_id"] == doc_id
    assert data["score"] == MCQ_COUNT
    assert data["total_questions"] == MCQ_COUNT
    assert data["answered_questions"] == MCQ_COUNT
    assert data["unanswered_questions"] == 0
    assert data["percentage"] == 100.0
    assert data["passed"] is True
    assert data["status"] == "PASSED"
    assert data["pass_threshold_percent"] == PASS_THRESHOLD_PERCENT

    assert len(data["results"]) == MCQ_COUNT
    for index, result in enumerate(data["results"]):
        assert result["is_correct"] is True
        assert result["selected_option"] == ANSWER_KEY[index]
        assert result["explanation"]
        assert "correct_option" not in result, \
            "submit results must not include the correct option"

    print("[OK] Fully correct submission scored 5/5 = 100% PASSED")


def test_score_calculation_and_threshold():
    print("Testing score calculation and the 60% prototype threshold...")

    # 3 of 5 correct = 60% -> passes exactly at the threshold.
    doc_id, questions = document_with_mcqs("quiz_threshold_pass.pdf")
    partial = answer_all(questions)
    for answer in partial[3:]:
        answer["selected_option"] = (answer["selected_option"] + 1) % 4

    at_threshold = submit(doc_id, partial)
    assert at_threshold.status_code == 200, at_threshold.text
    data = at_threshold.json()
    assert data["score"] == 3, data
    assert data["percentage"] == 60.0, data
    assert data["passed"] is True and data["status"] == "PASSED", "60% must pass"
    assert [r["is_correct"] for r in data["results"]] == [True, True, True, False, False]

    # 2 of 5 correct = 40% -> fails.
    doc_id, questions = document_with_mcqs("quiz_threshold_fail.pdf")
    most_wrong = answer_all(questions)
    for answer in most_wrong[2:]:
        answer["selected_option"] = (answer["selected_option"] + 1) % 4

    below = submit(doc_id, most_wrong).json()
    assert below["score"] == 2, below
    assert below["percentage"] == 40.0, below
    assert below["passed"] is False and below["status"] == "FAILED"

    # 0 of 5 correct.
    doc_id, questions = document_with_mcqs("quiz_zero.pdf")
    zero = submit(doc_id, answer_all(questions, offset=1)).json()
    assert zero["score"] == 0 and zero["percentage"] == 0.0
    assert zero["passed"] is False and zero["status"] == "FAILED"
    assert all(result["is_correct"] is False for result in zero["results"])

    print("[OK] 3/5=60% PASSED, 2/5=40% FAILED, 0/5=0% FAILED")


def test_partial_answers():
    print("Testing a partially answered submission...")
    doc_id, questions = document_with_mcqs("quiz_partial.pdf")

    answered = answer_all(questions)[:2]
    answered_ids = [answer["question_id"] for answer in answered]
    unanswered_ids = [q["question_id"] for q in questions if q["question_id"] not in answered_ids]

    response = submit(doc_id, answered)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["score"] == 2
    assert data["total_questions"] == MCQ_COUNT
    assert data["answered_questions"] == 2
    assert data["unanswered_questions"] == MCQ_COUNT - 2
    # Percentage is out of the whole quiz, not just the answered part.
    assert data["percentage"] == 40.0

    result_ids = [result["question_id"] for result in data["results"]]
    assert len(data["results"]) == data["answered_questions"]
    assert result_ids == answered_ids
    for question_id in unanswered_ids:
        assert question_id not in result_ids, \
            "an unanswered question was revealed in the results"
    # Explained for answered questions, but the correct option is never returned.
    assert all(result["explanation"] for result in data["results"])
    assert "correct_option" not in response.text

    print("[OK] Partial submission scored out of the full quiz, unanswered not revealed")


# ------------------------------------------------------------------
# 4. Submission validation
# ------------------------------------------------------------------

def test_invalid_question_id():
    print("Testing invalid question ids...")
    doc_id, questions = document_with_mcqs("quiz_bad_id.pdf")
    other_doc_id, _ = document_with_mcqs("quiz_other_doc.pdf")

    # A question id that does not belong to this document at all.
    response = submit(doc_id, [{"question_id": 9999999, "selected_option": 0}])
    assert response.status_code == 400, response.text
    assert "does not belong to this document" in response.json()["detail"]

    # A question id belonging to a different document is rejected too.
    other_quiz = client.get(f"/api/v1/documents/{other_doc_id}/quiz").json()
    foreign_id = other_quiz["questions"][0]["question_id"]
    response = submit(doc_id, [{"question_id": foreign_id, "selected_option": 0}])
    assert response.status_code == 400, response.text
    assert "does not belong to this document" in response.json()["detail"]

    # A non-integer id is a malformed request.
    response = submit(doc_id, [{"question_id": "abc", "selected_option": 0}])
    assert response.status_code == 422, f"expected 422, got {response.status_code}"

    assert questions, "fixture should have questions"
    print("[OK] Unknown and foreign question ids -> 400, non-integer -> 422")


def test_invalid_selected_option():
    print("Testing invalid selected options...")
    doc_id, questions = document_with_mcqs("quiz_bad_option.pdf")
    question_id = questions[0]["question_id"]

    for bad_option in (4, -1, 99):
        response = submit(doc_id, [{"question_id": question_id, "selected_option": bad_option}])
        assert response.status_code == 400, f"{bad_option}: {response.text}"
        assert "selected_option" in response.json()["detail"]

    # Wrong types are rejected as malformed requests.
    for bad_option in ("0", 1.5, True, None):
        response = submit(doc_id, [{"question_id": question_id, "selected_option": bad_option}])
        assert response.status_code == 422, \
            f"{bad_option!r} should be a 422, got {response.status_code}"

    print("[OK] Out-of-range options -> 400, wrong types -> 422")


def test_duplicate_question_ids():
    print("Testing duplicate question ids...")
    doc_id, questions = document_with_mcqs("quiz_duplicates.pdf")
    question_id = questions[0]["question_id"]

    response = submit(doc_id, [
        {"question_id": question_id, "selected_option": 0},
        {"question_id": question_id, "selected_option": 1},
    ])
    assert response.status_code == 400, response.text
    assert "duplicate" in response.json()["detail"].lower()

    print("[OK] Duplicate question id rejected")


def test_empty_answers_and_malformed_body():
    print("Testing empty answers and malformed bodies...")
    doc_id, _ = document_with_mcqs("quiz_empty_answers.pdf")

    empty = submit(doc_id, [])
    assert empty.status_code == 400, empty.text
    assert "at least one answer" in empty.json()["detail"]

    missing = client.post(f"/api/v1/documents/{doc_id}/quiz/submit", json={})
    assert missing.status_code == 422, f"expected 422, got {missing.status_code}"

    wrong_shape = client.post(
        f"/api/v1/documents/{doc_id}/quiz/submit", json={"answers": "not a list"}
    )
    assert wrong_shape.status_code == 422

    not_json = client.post(
        f"/api/v1/documents/{doc_id}/quiz/submit",
        content=b"{not json",
        headers={"Content-Type": "application/json"},
    )
    assert not_json.status_code == 422, f"expected 422, got {not_json.status_code}"

    print("[OK] Empty answers -> 400, missing/invalid body -> 422")


# ------------------------------------------------------------------
# 5. Missing resources
# ------------------------------------------------------------------

def test_no_mcqs_and_unknown_document():
    print("Testing documents with no MCQs and unknown documents...")
    doc_id = upload_document("quiz_without_mcqs.pdf")

    quiz = client.get(f"/api/v1/documents/{doc_id}/quiz")
    assert quiz.status_code == 404, f"expected 404, got {quiz.status_code}"
    assert "no mcqs" in quiz.json()["detail"].lower()

    submission = submit(doc_id, [{"question_id": 1, "selected_option": 0}])
    assert submission.status_code == 404, f"expected 404, got {submission.status_code}"
    assert "no mcqs" in submission.json()["detail"].lower()

    missing = 9999999
    unknown_quiz = client.get(f"/api/v1/documents/{missing}/quiz")
    unknown_submit = submit(missing, [{"question_id": 1, "selected_option": 0}])
    assert unknown_quiz.status_code == 404, unknown_quiz.text
    assert unknown_submit.status_code == 404, unknown_submit.text
    assert "not found" in unknown_quiz.json()["detail"].lower()
    assert "not found" in unknown_submit.json()["detail"].lower()

    print("[OK] No MCQs -> 404 with a clear message, unknown document -> 404")


# ------------------------------------------------------------------
# 6. Service unit tests
# ------------------------------------------------------------------

def test_calculate_percentage_unit():
    print("Testing calculate_percentage()...")
    assert calculate_percentage(5, 5) == 100.0
    assert calculate_percentage(3, 5) == 60.0
    assert calculate_percentage(2, 5) == 40.0
    assert calculate_percentage(0, 5) == 0.0
    assert calculate_percentage(1, 3) == 33.33
    assert calculate_percentage(1, 0) == 0.0
    assert calculate_percentage(0, 0) == 0.0
    print("[OK] Percentages rounded to 2 decimals, zero-total guarded")


def test_build_learner_questions_unit():
    print("Testing build_learner_questions()...")
    stored = [{
        "id": 7,
        "question": "Which one?",
        "options": ["a", "b", "c", "d"],
        "correct_option": 2,
        "explanation": "Because c.",
        "source_chunk_id": 42,
        "document_id": 1,
        "created_at": "2026-01-01T00:00:00",
    }]

    learner = build_learner_questions(stored)
    assert learner == [{
        "question_id": 7,
        "question": "Which one?",
        "options": ["a", "b", "c", "d"],
    }]
    assert set(learner[0]) == LEARNER_FIELDS
    print("[OK] Only learner-safe fields are emitted")


def test_score_submission_requires_mcqs():
    print("Testing score_submission() with no MCQs...")
    try:
        score_submission([], [{"question_id": 1, "selected_option": 0}])
    except QuizValidationError as exc:
        assert "no MCQs" in str(exc)
    else:
        raise AssertionError("expected QuizValidationError for an empty MCQ list")
    print("[OK] Empty MCQ list raises QuizValidationError")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING STATLEARN AI PHASE 5 STEP 5A QUIZ TEST SUITE")
    print("=" * 60)
    test_learner_quiz_does_not_expose_answers()
    test_inspection_endpoint_still_has_the_answer_key()
    test_successful_submission()
    test_score_calculation_and_threshold()
    test_partial_answers()
    test_invalid_question_id()
    test_invalid_selected_option()
    test_duplicate_question_ids()
    test_empty_answers_and_malformed_body()
    test_no_mcqs_and_unknown_document()
    test_calculate_percentage_unit()
    test_build_learner_questions_unit()
    test_score_submission_requires_mcqs()
    print("=" * 60)
    print("ALL PHASE 5 STEP 5A QUIZ TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
