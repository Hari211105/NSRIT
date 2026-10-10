"""
UPSKILL AI - MCQ Generation Service (Phase 5 Step 4A)

Turns one document chunk into exactly five validated multiple-choice questions
using a single OpenRouter request, made through the existing ai_service.

Design:
  - no database access and no HTTP of its own: the chunk text is passed in and
    the caller decides what to persist
  - the model is reached only via app.services.ai_service.generate_completion;
    this module never calls OpenRouter directly
  - the reply is parsed as JSON and validated strictly against the MCQ rules.
    Invalid output raises MCQGenerationError. Nothing is silently repaired,
    truncated or dropped - no code fences are stripped, no missing questions are
    back-filled, no duplicate options are rewritten.

Error types:
  - MCQGenerationError  - the reply was unparseable or broke an MCQ rule
  - AIServiceError      - the OpenRouter call itself failed (propagated as-is
                          from ai_service, so callers can tell the two apart)
"""

import json
from typing import Any, Callable, Dict, List, Optional

from app.services.ai_service import generate_completion

# ---------------------------------------------------------------
# MCQ contract
# ---------------------------------------------------------------

MCQ_COUNT = 5
OPTIONS_PER_QUESTION = 4

# Free-tier models intermittently return an empty or non-JSON reply. Validation
# stays strict (nothing is repaired or dropped), but the request is retried a
# couple of times before giving up - a fresh call often succeeds. Only invalid
# OUTPUT is retried; AIServiceError (transport/auth failures) propagates
# immediately because retrying those cannot help.
MAX_GENERATION_ATTEMPTS = 3

REQUIRED_FIELDS = (
    "question",
    "options",
    "correct_option",
    "explanation",
    "source_chunk_id",
)

_JSON_SHAPE = (
    '{"questions": ['
    '{"question": "...", "options": ["...", "...", "...", "..."], '
    '"correct_option": 0, "explanation": "...", "source_chunk_id": <CHUNK_ID>}'
    ']}'
)


class MCQGenerationError(RuntimeError):
    """Raised when the AI reply is malformed or violates an MCQ rule."""


# ---------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------

def _build_instruction(
    source_chunk_id: int, competency_context: Optional[str] = None
) -> str:
    """Build the single instruction that asks for all questions at once."""
    competency_lines = ""
    if competency_context and competency_context.strip():
        competency_lines = (
            "\nCompetency context (use it only to choose the focus of the "
            f"questions, never as a source of facts): {competency_context.strip()}\n"
        )

    return (
        f"Create exactly {MCQ_COUNT} multiple-choice questions from the source "
        "context above.\n"
        f"{competency_lines}\n"
        "Return ONLY valid JSON. No markdown, no code fences, no commentary "
        "before or after the JSON.\n"
        "\n"
        "Required JSON shape:\n"
        f"{_JSON_SHAPE.replace('<CHUNK_ID>', str(source_chunk_id))}\n"
        "\n"
        "Rules:\n"
        f"- exactly {MCQ_COUNT} questions\n"
        f"- exactly {OPTIONS_PER_QUESTION} options per question\n"
        "- exactly one correct option per question\n"
        f"- \"correct_option\" is the 0-based index of the correct option, so it "
        f"must be 0, 1, 2 or {OPTIONS_PER_QUESTION - 1}\n"
        "- no duplicate options within a question\n"
        "- \"question\" must not be empty\n"
        "- \"explanation\" must not be empty, and must say why the correct "
        "option is correct using only the source context\n"
        "- every question must be answerable from the source context alone\n"
        "- do not use outside knowledge\n"
        "- do not invent facts, numbers, names, dates or citations\n"
        f"- \"source_chunk_id\" must be {source_chunk_id} for every question\n"
    )


# ---------------------------------------------------------------
# Validation helpers (pure, individually testable)
# ---------------------------------------------------------------

def _require_non_empty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MCQGenerationError(f"{label} must be a non-empty string.")
    return value.strip()


def _require_int(value: Any, label: str) -> int:
    # bool is a subclass of int in Python, but a boolean is not a valid index.
    if isinstance(value, bool) or not isinstance(value, int):
        raise MCQGenerationError(
            f"{label} must be an integer, got {type(value).__name__}."
        )
    return value


def _validate_options(options: Any, label: str) -> List[str]:
    if not isinstance(options, list):
        raise MCQGenerationError(f"{label} 'options' must be a JSON array.")

    if len(options) != OPTIONS_PER_QUESTION:
        raise MCQGenerationError(
            f"{label} must have exactly {OPTIONS_PER_QUESTION} options, "
            f"got {len(options)}."
        )

    cleaned = [
        _require_non_empty_text(option, f"{label} option {index + 1}")
        for index, option in enumerate(options)
    ]

    # Duplicate detection is case-insensitive so "Data" and "data" do not slip
    # through as two distinct choices.
    seen: Dict[str, int] = {}
    for index, option in enumerate(cleaned):
        key = option.casefold()
        if key in seen:
            raise MCQGenerationError(
                f"{label} has duplicate options: option {seen[key] + 1} and "
                f"option {index + 1} are the same."
            )
        seen[key] = index

    return cleaned


def _validate_question(
    raw_question: Any, index: int, source_chunk_id: int
) -> Dict[str, Any]:
    """Validate one question and return it in the canonical shape."""
    label = f"Question {index + 1}"

    if not isinstance(raw_question, dict):
        raise MCQGenerationError(f"{label} must be a JSON object.")

    missing = [field for field in REQUIRED_FIELDS if field not in raw_question]
    if missing:
        raise MCQGenerationError(
            f"{label} is missing required field(s): {', '.join(missing)}."
        )

    question = _require_non_empty_text(raw_question["question"], f"{label} 'question'")
    explanation = _require_non_empty_text(
        raw_question["explanation"], f"{label} 'explanation'"
    )
    options = _validate_options(raw_question["options"], label)

    correct_option = _require_int(
        raw_question["correct_option"], f"{label} 'correct_option'"
    )
    if not 0 <= correct_option < OPTIONS_PER_QUESTION:
        raise MCQGenerationError(
            f"{label} 'correct_option' must be between 0 and "
            f"{OPTIONS_PER_QUESTION - 1}, got {correct_option}."
        )

    chunk_id = _require_int(
        raw_question["source_chunk_id"], f"{label} 'source_chunk_id'"
    )
    if chunk_id != source_chunk_id:
        raise MCQGenerationError(
            f"{label} 'source_chunk_id' is {chunk_id} but the supplied chunk id "
            f"is {source_chunk_id}."
        )

    return {
        "question": question,
        "options": options,
        "correct_option": correct_option,
        "explanation": explanation,
        "source_chunk_id": chunk_id,
    }


def validate_mcq_response(
    raw_response: str, source_chunk_id: int
) -> List[Dict[str, Any]]:
    """
    Parse and strictly validate an AI reply against the MCQ contract.

    Returns the canonical list of questions, or raises MCQGenerationError.
    Public so callers can re-validate a stored payload without regenerating it.
    """
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise MCQGenerationError(
            "The AI response was empty; expected a JSON object."
        )

    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise MCQGenerationError(
            "The AI response was not valid JSON "
            f"({exc.msg} at line {exc.lineno} column {exc.colno})."
        ) from exc

    if not isinstance(payload, dict):
        raise MCQGenerationError(
            "The AI response JSON must be an object containing a 'questions' key."
        )

    if "questions" not in payload:
        raise MCQGenerationError(
            "The AI response JSON is missing the 'questions' key."
        )

    questions = payload["questions"]
    if not isinstance(questions, list):
        raise MCQGenerationError("'questions' must be a JSON array.")

    if len(questions) != MCQ_COUNT:
        raise MCQGenerationError(
            f"Expected exactly {MCQ_COUNT} questions, got {len(questions)}."
        )

    return [
        _validate_question(raw_question, index, source_chunk_id)
        for index, raw_question in enumerate(questions)
    ]


# ---------------------------------------------------------------
# Public API
# ---------------------------------------------------------------

def generate_mcqs(
    chunk_text: str,
    source_chunk_id: int,
    *,
    competency_context: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[float] = None,
    generator: Optional[Callable[..., str]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate exactly MCQ_COUNT validated MCQs from one document chunk.

    chunk_text is the only material the questions may be based on; source_chunk_id
    is echoed back on every question so the caller can trace it to the chunk;
    competency_context optionally steers the focus without becoming a fact source.

    All questions are requested in a single OpenRouter call.

    `generator` is an injection point for tests: it defaults to
    ai_service.generate_completion and must accept (source_context, instruction)
    plus optional `model` / `timeout` keywords.

    Raises MCQGenerationError for empty input or invalid AI output, and lets
    AIServiceError propagate when the OpenRouter call itself fails.
    """
    if isinstance(source_chunk_id, bool) or not isinstance(source_chunk_id, int):
        raise MCQGenerationError(
            f"source_chunk_id must be an integer, got {type(source_chunk_id).__name__}."
        )

    if not isinstance(chunk_text, str) or not chunk_text.strip():
        raise MCQGenerationError("chunk_text is required and cannot be empty.")

    instruction = _build_instruction(source_chunk_id, competency_context)

    extra_kwargs: Dict[str, Any] = {}
    if model is not None:
        extra_kwargs["model"] = model
    if timeout is not None:
        extra_kwargs["timeout"] = timeout

    completion = generator or generate_completion

    last_error: MCQGenerationError = None  # type: ignore[assignment]
    for _attempt in range(MAX_GENERATION_ATTEMPTS):
        # AIServiceError (network/auth/model failure) propagates unchanged.
        raw_response = completion(chunk_text.strip(), instruction, **extra_kwargs)
        try:
            return validate_mcq_response(raw_response, source_chunk_id)
        except MCQGenerationError as exc:
            # Invalid reply (empty / non-JSON / broken contract): retry.
            last_error = exc
    raise last_error
