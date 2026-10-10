"""
UPSKILL AI - Phase 5 Step 4A MCQ Generation Service Verification Test Suite

No OpenRouter call is made anywhere in this suite and no API key is used. The
AI call is replaced with an injected fake generator, which also records how many
requests were made and what prompt was sent.

Tests:
1. A valid 5-question response is parsed into the canonical shape
2. All questions are requested in ONE call, with the expected prompt content
3. Malformed JSON and non-object / missing-questions payloads are rejected
4. Wrong number of questions is rejected (not truncated or back-filled)
5. Invalid options and invalid correct_option are rejected
6. Duplicate options are rejected
7. Missing required fields are rejected, naming the field
8. A mismatched source_chunk_id is rejected
9. Empty / invalid inputs are rejected before any AI call
10. An AIServiceError from the AI layer propagates untouched
"""

import sys
import os
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.ai_service import AIServiceError
from app.services.mcq_service import (
    MCQ_COUNT,
    OPTIONS_PER_QUESTION,
    REQUIRED_FIELDS,
    MCQGenerationError,
    generate_mcqs,
    validate_mcq_response,
)

CHUNK_ID = 123
CHUNK_TEXT = (
    "Official statistics are produced by national statistical offices. "
    "Survey methodology covers sampling, questionnaire design and data collection."
)
COMPETENCY = "Survey Methodology"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

class FakeGenerator:
    """Stand-in for ai_service.generate_completion that never hits the network."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, source_context, instruction, **kwargs):
        self.calls.append({
            "source_context": source_context,
            "instruction": instruction,
            "kwargs": kwargs,
        })
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def valid_question(index: int, chunk_id: int = CHUNK_ID):
    return {
        "question": f"Question {index + 1} about the source context?",
        "options": [f"Choice {index + 1}A", f"Choice {index + 1}B",
                    f"Choice {index + 1}C", f"Choice {index + 1}D"],
        "correct_option": index % OPTIONS_PER_QUESTION,
        "explanation": f"Explanation {index + 1} taken from the source context.",
        "source_chunk_id": chunk_id,
    }


def payload(questions=None, chunk_id: int = CHUNK_ID):
    if questions is None:
        questions = [valid_question(i, chunk_id) for i in range(MCQ_COUNT)]
    return {"questions": questions}


def dump(questions=None, chunk_id: int = CHUNK_ID) -> str:
    return json.dumps(payload(questions, chunk_id))


def expect_mcq_error(func, *args, **kwargs) -> str:
    """Call func and return the MCQGenerationError message it raises."""
    try:
        func(*args, **kwargs)
    except MCQGenerationError as exc:
        return str(exc)
    raise AssertionError("expected MCQGenerationError, but the call succeeded")


def fail_with(questions) -> str:
    """Validate a payload expected to violate a rule; return the error message."""
    return expect_mcq_error(validate_mcq_response, dump(questions), CHUNK_ID)


# ------------------------------------------------------------------
# 1-2. Happy path and prompt shape
# ------------------------------------------------------------------

def test_valid_response_is_parsed():
    print("Testing a valid 5-question response...")
    generator = FakeGenerator(dump())

    questions = generate_mcqs(CHUNK_TEXT, CHUNK_ID, generator=generator)

    assert len(questions) == MCQ_COUNT, f"expected {MCQ_COUNT}, got {len(questions)}"
    for index, question in enumerate(questions):
        assert set(question) == {
            "question", "options", "correct_option", "explanation", "source_chunk_id"
        }, f"unexpected keys: {sorted(question)}"
        assert question["question"] == f"Question {index + 1} about the source context?"
        assert len(question["options"]) == OPTIONS_PER_QUESTION
        assert question["correct_option"] == index % OPTIONS_PER_QUESTION
        assert question["explanation"]
        assert question["source_chunk_id"] == CHUNK_ID

    print(f"[OK] Valid response parsed into {len(questions)} canonical questions")


def test_single_call_with_expected_prompt():
    print("Testing that all questions are requested in one call...")
    generator = FakeGenerator(dump())

    generate_mcqs(
        CHUNK_TEXT, CHUNK_ID, competency_context=COMPETENCY, generator=generator
    )

    assert len(generator.calls) == 1, \
        f"expected exactly 1 AI call, got {len(generator.calls)}"

    call = generator.calls[0]
    assert call["source_context"] == CHUNK_TEXT, "chunk text was not sent as the context"
    instruction = call["instruction"]
    assert f"exactly {MCQ_COUNT}" in instruction, "instruction must ask for exactly 5"
    assert "ONLY valid JSON" in instruction, "instruction must demand JSON only"
    assert str(CHUNK_ID) in instruction, "instruction must state the chunk id"
    assert COMPETENCY in instruction, "competency context was not passed through"
    assert "do not use outside knowledge" in instruction
    assert "do not invent facts" in instruction

    # Without competency context the instruction must not mention it.
    generator = FakeGenerator(dump())
    generate_mcqs(CHUNK_TEXT, CHUNK_ID, generator=generator)
    assert COMPETENCY not in generator.calls[0]["instruction"]

    print("[OK] Exactly one call, carrying the chunk text and MCQ rules")


# ------------------------------------------------------------------
# 3. Malformed JSON
# ------------------------------------------------------------------

def test_malformed_json_is_rejected():
    print("Testing malformed JSON responses...")

    cases = [
        ("not JSON at all", "not json at all"),
        ("truncated JSON", '{"questions": [{"question": "x"'),
        ("empty string", "   "),
        ("JSON array root", json.dumps([1, 2, 3])),
        ("JSON string root", json.dumps("hello")),
        ("missing questions key", json.dumps({"items": []})),
        ("questions not an array", json.dumps({"questions": "nope"})),
        ("code-fenced JSON", "```json\n" + dump() + "\n```"),
    ]

    for label, response in cases:
        message = expect_mcq_error(validate_mcq_response, response, CHUNK_ID)
        assert message, f"empty error message for case: {label}"

    print(f"[OK] All {len(cases)} malformed payloads raised MCQGenerationError")


# ------------------------------------------------------------------
# 4. Wrong number of questions
# ------------------------------------------------------------------

def test_wrong_number_of_questions_is_rejected():
    print("Testing wrong number of questions...")

    for count in (0, 1, 4, 6, 10):
        message = fail_with([valid_question(i) for i in range(count)])
        assert f"exactly {MCQ_COUNT}" in message, message
        assert str(count) in message, message

    print(f"[OK] Question counts other than {MCQ_COUNT} rejected, not truncated")


# ------------------------------------------------------------------
# 5. Invalid options and correct_option
# ------------------------------------------------------------------

def test_invalid_options_are_rejected():
    print("Testing invalid options...")

    def with_options(options):
        question = valid_question(0)
        question["options"] = options
        return [question] + [valid_question(i) for i in range(1, MCQ_COUNT)]

    too_few = fail_with(with_options(["A", "B", "C"]))
    assert f"exactly {OPTIONS_PER_QUESTION} options" in too_few, too_few

    too_many = fail_with(with_options(["A", "B", "C", "D", "E"]))
    assert f"exactly {OPTIONS_PER_QUESTION} options" in too_many, too_many

    not_a_list = fail_with(with_options("A, B, C, D"))
    assert "must be a JSON array" in not_a_list, not_a_list

    blank_option = fail_with(with_options(["A", "   ", "C", "D"]))
    assert "option 2 must be a non-empty string" in blank_option, blank_option

    non_string_option = fail_with(with_options(["A", None, "C", "D"]))
    assert "option 2 must be a non-empty string" in non_string_option, non_string_option

    print("[OK] Wrong option counts, non-arrays and blank options rejected")


def test_invalid_correct_option_is_rejected():
    print("Testing invalid correct_option...")

    def with_correct(value):
        question = valid_question(0)
        question["correct_option"] = value
        return [question] + [valid_question(i) for i in range(1, MCQ_COUNT)]

    for value in (4, -1, 99):
        message = fail_with(with_correct(value))
        assert "between 0 and" in message, message

    for value in ("1", 1.0, None, True):
        message = fail_with(with_correct(value))
        assert "must be an integer" in message, message

    print("[OK] Out-of-range, non-integer and boolean correct_option rejected")


# ------------------------------------------------------------------
# 6. Duplicate options
# ------------------------------------------------------------------

def test_duplicate_options_are_rejected():
    print("Testing duplicate options...")

    def with_options(options):
        question = valid_question(0)
        question["options"] = options
        return [question] + [valid_question(i) for i in range(1, MCQ_COUNT)]

    exact = fail_with(with_options(["Same", "Same", "C", "D"]))
    assert "duplicate options" in exact, exact

    case_only = fail_with(with_options(["Data", "C", "data", "D"]))
    assert "duplicate options" in case_only, case_only

    whitespace_only = fail_with(with_options([" Data ", "data", "C", "D"]))
    assert "duplicate options" in whitespace_only, whitespace_only

    print("[OK] Exact, case-insensitive and whitespace-variant duplicates rejected")


# ------------------------------------------------------------------
# 7-8. Missing fields and chunk id mismatch
# ------------------------------------------------------------------

def test_missing_required_fields_are_rejected():
    print("Testing missing required fields...")

    for field in REQUIRED_FIELDS:
        question = valid_question(0)
        del question[field]
        message = fail_with([question] + [valid_question(i) for i in range(1, MCQ_COUNT)])
        assert field in message, f"error must name the missing field '{field}': {message}"
        assert "missing required field" in message, message

    # A response is validated only if every question is well formed; a bad
    # question anywhere in the list is caught, not just the first.
    broken = [valid_question(i) for i in range(MCQ_COUNT)]
    broken[3]["explanation"] = "  "
    message = fail_with(broken)
    assert "Question 4" in message, message

    print("[OK] Every missing field named; later questions are validated too")


def test_source_chunk_id_mismatch_is_rejected():
    print("Testing source_chunk_id mismatch...")

    message = fail_with([valid_question(i, chunk_id=999) for i in range(MCQ_COUNT)])
    assert "999" in message and str(CHUNK_ID) in message, message

    # A non-integer chunk id is rejected too.
    mixed = [valid_question(i) for i in range(MCQ_COUNT)]
    mixed[2]["source_chunk_id"] = str(CHUNK_ID)
    message = fail_with(mixed)
    assert "must be an integer" in message, message

    print("[OK] Mismatched and non-integer source_chunk_id rejected")


# ------------------------------------------------------------------
# 9-10. Input validation and AI-layer errors
# ------------------------------------------------------------------

def test_empty_inputs_are_rejected_without_an_ai_call():
    print("Testing empty inputs...")
    generator = FakeGenerator(dump())

    for chunk_text in ("", "   ", None, 123):
        message = expect_mcq_error(
            generate_mcqs, chunk_text, CHUNK_ID, generator=generator
        )
        assert "chunk_text" in message, message

    for chunk_id in (None, "123", 1.5, True):
        message = expect_mcq_error(
            generate_mcqs, CHUNK_TEXT, chunk_id, generator=generator
        )
        assert "source_chunk_id" in message, message

    assert generator.calls == [], "the AI was called despite invalid input"
    print("[OK] Invalid inputs rejected before any AI call")


def test_ai_service_error_propagates():
    print("Testing AIServiceError propagation...")
    generator = FakeGenerator(AIServiceError("OpenRouter returned HTTP 401: bad key"))

    try:
        generate_mcqs(CHUNK_TEXT, CHUNK_ID, generator=generator)
    except AIServiceError as exc:
        assert "401" in str(exc), str(exc)
    else:
        raise AssertionError("expected AIServiceError to propagate")

    print("[OK] AIServiceError propagated unchanged from the AI layer")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING STATLEARN AI PHASE 5 STEP 4A MCQ SERVICE TEST SUITE")
    print("=" * 60)
    test_valid_response_is_parsed()
    test_single_call_with_expected_prompt()
    test_malformed_json_is_rejected()
    test_wrong_number_of_questions_is_rejected()
    test_invalid_options_are_rejected()
    test_invalid_correct_option_is_rejected()
    test_duplicate_options_are_rejected()
    test_missing_required_fields_are_rejected()
    test_source_chunk_id_mismatch_is_rejected()
    test_empty_inputs_are_rejected_without_an_ai_call()
    test_ai_service_error_propagates()
    print("=" * 60)
    print("ALL PHASE 5 STEP 4A MCQ SERVICE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
