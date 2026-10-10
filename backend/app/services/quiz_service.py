"""
UPSKILL AI - Learner Quiz Service (Phase 5 Step 5A)

Pure, database-free logic for the learner-facing quiz: shaping stored MCQs into
learner-safe questions, and scoring a submission server-side.

Security:
  build_learner_questions() is the single place that converts stored MCQs into
  learner-facing questions. It emits only question_id, question and options, so
  correct_option / explanation / source_chunk_id cannot leak to a learner
  through the quiz endpoints. Scoring compares the learner's answers against the
  stored correct_option inside the server and never returns it.

Scoring:
  Answers are validated first (see _validate_answers), then scored against the
  stored correct_option. Only answered questions appear in the results;
  unanswered questions are counted as not correct and are never revealed.

Pass threshold:
  PASS_THRESHOLD_PERCENT is a PROTOTYPE APPLICATION THRESHOLD for this MVP.
  It is NOT an official MoSPI / iGOT / NSSTA definition or government standard.
"""

from typing import Any, Dict, Iterable, List, Tuple

# Prototype threshold only - not an official government standard.
PASS_THRESHOLD_PERCENT = 60

OPTIONS_PER_QUESTION = 4



class QuizValidationError(ValueError):
    """Raised when a quiz submission is not valid for the document's questions."""


# ---------------------------------------------------------------
# Learner-safe shaping
# ---------------------------------------------------------------

def build_learner_questions(mcqs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert stored MCQs into learner-safe questions.

    Each returned dict contains exactly question_id, question and options -
    never correct_option, explanation or source_chunk_id.
    """
    return [
        {
            "question_id": mcq["id"],
            "question": mcq["question"],
            "options": list(mcq["options"]),
        }
        for mcq in mcqs
    ]


# ---------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------

def calculate_percentage(score: int, total_questions: int) -> float:
    """Percentage of the quiz answered correctly, rounded to 2 decimals."""
    if total_questions <= 0:
        return 0.0
    return round(score / total_questions * 100, 2)


def _validate_answers(
    answers: Any, mcqs_by_id: Dict[int, Dict[str, Any]]
) -> List[Tuple[int, int]]:
    """Validate a submission's answers; returns (question_id, selected_option) pairs."""
    if not isinstance(answers, list) or not answers:
        raise QuizValidationError(
            "'answers' must contain at least one answer with 'question_id' and "
            "'selected_option'."
        )

    seen_question_ids = set()
    validated: List[Tuple[int, int]] = []

    for index, answer in enumerate(answers):
        label = f"answers[{index}]"

        if not isinstance(answer, dict):
            raise QuizValidationError(
                f"{label} must be an object with 'question_id' and 'selected_option'."
            )

        for field in ("question_id", "selected_option"):
            if field not in answer:
                raise QuizValidationError(f"{label} is missing '{field}'.")

        question_id = answer["question_id"]
        selected_option = answer["selected_option"]

        # bool is a subclass of int, but a boolean is not a valid id or index.
        if isinstance(question_id, bool) or not isinstance(question_id, int):
            raise QuizValidationError(f"{label} 'question_id' must be an integer.")

        if question_id not in mcqs_by_id:
            raise QuizValidationError(
                f"{label} 'question_id' {question_id} does not belong to this document."
            )

        if question_id in seen_question_ids:
            raise QuizValidationError(
                f"Duplicate answer for question_id {question_id}."
            )
        seen_question_ids.add(question_id)

        if isinstance(selected_option, bool) or not isinstance(selected_option, int):
            raise QuizValidationError(
                f"{label} 'selected_option' must be an integer."
            )

        if not 0 <= selected_option < OPTIONS_PER_QUESTION:
            raise QuizValidationError(
                f"{label} 'selected_option' must be between 0 and "
                f"{OPTIONS_PER_QUESTION - 1}, got {selected_option}."
            )

        validated.append((question_id, selected_option))

    return validated


def score_submission(
    mcqs: List[Dict[str, Any]], answers: Any
) -> Dict[str, Any]:
    """
    Score a learner submission server-side against the stored correct options.

    `mcqs` are the document's stored MCQs as dicts with id, question, options,
    correct_option and explanation. `answers` is the submitted list of
    {question_id, selected_option}.

    Returns score, total_questions, answered/unanswered counts, percentage, the
    prototype threshold and pass status, plus one result per ANSWERED question
    (question_id, selected_option, is_correct, explanation). The correct option
    is never included, and unanswered questions are not revealed at all.

    Raises QuizValidationError for an invalid submission.
    """
    if not mcqs:
        raise QuizValidationError("This document has no MCQs to score against.")

    mcqs_by_id = {mcq["id"]: mcq for mcq in mcqs}
    validated = _validate_answers(answers, mcqs_by_id)

    score = 0
    results = []
    # Sorted so the response order is deterministic regardless of input order.
    for question_id, selected_option in sorted(validated):
        mcq = mcqs_by_id[question_id]
        is_correct = selected_option == mcq["correct_option"]
        if is_correct:
            score += 1
        results.append({
            "question_id": question_id,
            "selected_option": selected_option,
            "is_correct": is_correct,
            "explanation": mcq["explanation"],
        })

    total_questions = len(mcqs)
    percentage = calculate_percentage(score, total_questions)
    passed = percentage >= PASS_THRESHOLD_PERCENT

    return {
        "score": score,
        "total_questions": total_questions,
        "answered_questions": len(validated),
        "unanswered_questions": total_questions - len(validated),
        "percentage": percentage,
        "pass_threshold_percent": PASS_THRESHOLD_PERCENT,
        "passed": passed,
        "status": "PASSED" if passed else "FAILED",
        "results": results,
    }
