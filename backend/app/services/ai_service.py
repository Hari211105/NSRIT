"""
UPSKILL AI - OpenRouter AI Service (Phase 5 Step 3)

Small reusable wrapper around the OpenRouter chat completions endpoint.
This module only *calls* the model. It holds no domain prompt beyond the
grounding rules below, so later phases can reuse it for other tasks.

Responsibilities:
  - build a grounded prompt from a supplied source context + instruction
  - POST {OPENROUTER_BASE_URL}/chat/completions
  - return the reply text, or raise AIServiceError

Secrets:
  The API key is read from settings, placed only in the Authorization header,
  and is never logged or returned. Every message that could surface in an error
  passes through _redact_secrets() first.
"""

from typing import Any, Dict, Optional

import httpx

from app.config import settings


# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------

DEFAULT_TIMEOUT_SECONDS = 30.0

# System prompt: the model must stay inside the supplied source context.
SYSTEM_INSTRUCTION = (
    "You answer strictly from the source context you are given.\n"
    "Rules:\n"
    "1. Use only the supplied source context. Never add outside knowledge.\n"
    "2. Never invent facts, figures, names, dates or citations.\n"
    "3. If the source context is insufficient to answer, say so plainly "
    "instead of guessing.\n"
    "4. Stay concise and on topic."
)


class AIServiceError(RuntimeError):
    """Raised when an OpenRouter call fails or returns an unusable response."""


# ---------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------

def _redact_secrets(message: str) -> str:
    """Remove the configured API key from any text that may be surfaced."""
    api_key = (settings.OPENROUTER_API_KEY or "").strip()
    if api_key and api_key in message:
        return message.replace(api_key, "***")
    return message


def _chat_completions_url() -> str:
    return f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"


def _effective_timeout(timeout: Optional[float]) -> float:
    return DEFAULT_TIMEOUT_SECONDS if timeout is None else timeout


def _validate_request(source_context: str, instruction: str) -> None:
    if not (source_context or "").strip():
        raise AIServiceError("source_context is required and cannot be empty.")
    if not (instruction or "").strip():
        raise AIServiceError("instruction is required and cannot be empty.")


def _require_api_key() -> str:
    api_key = (settings.OPENROUTER_API_KEY or "").strip()
    if not api_key:
        raise AIServiceError(
            "OPENROUTER_API_KEY is not configured. Set it in backend/.env."
        )
    return api_key


def _build_payload(
    source_context: str, instruction: str, model: str
) -> Dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {
                "role": "user",
                "content": (
                    f"Source context:\n{source_context}\n\n"
                    f"Instruction: {instruction}"
                ),
            },
        ],
        # Low temperature: keep the model close to the supplied context.
        "temperature": 0.2,
    }


def _request_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _translate_transport_error(
    exc: httpx.HTTPError, timeout: float
) -> AIServiceError:
    """Convert any httpx transport failure into a safe AIServiceError."""
    if isinstance(exc, httpx.TimeoutException):
        return AIServiceError(f"OpenRouter request timed out after {timeout}s.")
    return AIServiceError(f"OpenRouter request failed: {_redact_secrets(str(exc))}")


def _extract_content(response: httpx.Response) -> str:
    """
    Pull the assistant text out of a chat completions response.
    Raises AIServiceError for non-200 responses and malformed bodies.
    """
    if response.status_code != 200:
        raise AIServiceError(
            f"OpenRouter returned HTTP {response.status_code}: "
            f"{_redact_secrets(response.text[:300])}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise AIServiceError(
            "OpenRouter returned a response that was not valid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise AIServiceError("OpenRouter returned JSON of an unexpected shape.")

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIServiceError("OpenRouter response contained no choices.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise AIServiceError("OpenRouter returned an unexpected choice format.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise AIServiceError("OpenRouter choice contained no message object.")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise AIServiceError("OpenRouter message contained no text content.")

    return content.strip()


# ---------------------------------------------------------------
# Public API
# ---------------------------------------------------------------

def generate_completion(
    source_context: str,
    instruction: str,
    *,
    model: Optional[str] = None,
    timeout: Optional[float] = None,
    client: Optional[httpx.Client] = None,
) -> str:
    """
    Send one grounded chat completion request and return the reply text.

    `source_context` is the only material the model is allowed to use;
    `instruction` says what to do with it.

    `client` is an injection point (an httpx.Client with a custom transport),
    used by tests so no network call is ever made. When omitted, a client with
    DEFAULT_TIMEOUT_SECONDS is created and closed here.

    Raises AIServiceError for missing configuration, empty inputs, transport
    failures (including timeouts), non-200 responses and malformed responses.
    """
    _validate_request(source_context, instruction)
    api_key = _require_api_key()
    effective_timeout = _effective_timeout(timeout)

    payload = _build_payload(
        source_context, instruction, model or settings.OPENROUTER_MODEL
    )

    owns_client = client is None
    http_client = client or httpx.Client(timeout=effective_timeout)
    try:
        response = http_client.post(
            _chat_completions_url(),
            json=payload,
            headers=_request_headers(api_key),
        )
    except httpx.HTTPError as exc:
        raise _translate_transport_error(exc, effective_timeout) from exc
    finally:
        if owns_client:
            http_client.close()

    return _extract_content(response)


async def agenerate_completion(
    source_context: str,
    instruction: str,
    *,
    model: Optional[str] = None,
    timeout: Optional[float] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> str:
    """
    Async counterpart of generate_completion(), for use from async routes so the
    event loop is not blocked while OpenRouter is called.
    """
    _validate_request(source_context, instruction)
    api_key = _require_api_key()
    effective_timeout = _effective_timeout(timeout)

    payload = _build_payload(
        source_context, instruction, model or settings.OPENROUTER_MODEL
    )

    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=effective_timeout)
    try:
        response = await http_client.post(
            _chat_completions_url(),
            json=payload,
            headers=_request_headers(api_key),
        )
    except httpx.HTTPError as exc:
        raise _translate_transport_error(exc, effective_timeout) from exc
    finally:
        if owns_client:
            await http_client.aclose()

    return _extract_content(response)
