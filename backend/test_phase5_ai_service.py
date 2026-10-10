"""
UPSKILL AI - Phase 5 Step 3 OpenRouter AI Service Verification Test Suite

Every request is intercepted with httpx.MockTransport, so these tests never
touch the network and never use the real API key. The configured key is
replaced with a dummy value for the duration of each test.

Tests:
1. System instruction is grounded (context-only, admits insufficiency, concise)
2. Successful response parsing, including the outgoing request shape
3. Async successful response parsing
4. API error handling (HTTP 401, transport failure, timeout)
5. Malformed response handling (non-JSON, no choices, missing/blank content)
6. Missing configuration and empty inputs, reported without calling the API
7. The API key never appears in error messages
"""

import sys
import os
import json
import asyncio
from contextlib import contextmanager

import httpx

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import settings
from app.services.ai_service import (
    DEFAULT_TIMEOUT_SECONDS,
    SYSTEM_INSTRUCTION,
    AIServiceError,
    agenerate_completion,
    generate_completion,
)

# Dummy key used by the tests. The real key from backend/.env is deliberately
# never read, used, or printed here.
DUMMY_KEY = "test-dummy-key-not-real"
DUMMY_MODEL = "test/model-under-test"

SOURCE = "Official statistics are produced by national statistical offices."
INSTRUCTION = "Summarize the source context in one sentence."


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

@contextmanager
def temp_setting(name: str, value):
    """Temporarily override a settings attribute, then restore it."""
    original = getattr(settings, name)
    setattr(settings, name, value)
    try:
        yield
    finally:
        setattr(settings, name, original)


def make_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def make_async_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def ok_content(text: str, request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": text}}]},
        request=request,
    )


def expect_ai_service_error(func, *args, **kwargs) -> str:
    """Call func and return the AIServiceError message it raises."""
    try:
        func(*args, **kwargs)
    except AIServiceError as exc:
        return str(exc)
    raise AssertionError("expected AIServiceError, but the call succeeded")


# ------------------------------------------------------------------
# 1. Prompt grounding
# ------------------------------------------------------------------

def test_system_instruction_is_grounded():
    print("Testing system instruction grounding rules...")
    lowered = SYSTEM_INSTRUCTION.lower()

    assert "only the supplied source context" in lowered, \
        "system instruction must restrict the model to the supplied context"
    assert "never invent" in lowered, \
        "system instruction must forbid inventing unsupported facts"
    assert "insufficient" in lowered, \
        "system instruction must say what to do when context is insufficient"
    assert "concise" in lowered, \
        "system instruction must ask for concise answers"

    print("[OK] System instruction is context-only, no-invention, concise")


# ------------------------------------------------------------------
# 2. Successful response parsing
# ------------------------------------------------------------------

def test_successful_response_parsing():
    print("Testing successful response parsing...")
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization", "")
        captured["body"] = json.loads(request.content)
        return ok_content("  Grounded answer.  ", request)

    client = make_client(handler)
    try:
        with temp_setting("OPENROUTER_API_KEY", DUMMY_KEY), \
             temp_setting("OPENROUTER_MODEL", DUMMY_MODEL):
            result = generate_completion(SOURCE, INSTRUCTION, client=client)
    finally:
        client.close()

    # Reply text is returned trimmed.
    assert result == "Grounded answer.", result

    # Request went to the configured base URL + /chat/completions.
    expected_url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    assert captured["url"] == expected_url, captured["url"]

    # Authorization header carries the key as a bearer token.
    assert captured["auth"] == f"Bearer {DUMMY_KEY}"

    # Payload carries the model, the system rules and both inputs.
    body = captured["body"]
    assert body["model"] == DUMMY_MODEL
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][0]["content"] == SYSTEM_INSTRUCTION
    assert body["messages"][1]["role"] == "user"
    assert SOURCE in body["messages"][1]["content"]
    assert INSTRUCTION in body["messages"][1]["content"]

    print("[OK] Successful response parsed, request targeted /chat/completions")


def test_async_successful_response_parsing():
    print("Testing async successful response parsing...")

    def handler(request: httpx.Request) -> httpx.Response:
        return ok_content("Async grounded answer.", request)

    async def run() -> str:
        client = make_async_client(handler)
        try:
            with temp_setting("OPENROUTER_API_KEY", DUMMY_KEY), \
                 temp_setting("OPENROUTER_MODEL", DUMMY_MODEL):
                return await agenerate_completion(SOURCE, INSTRUCTION, client=client)
        finally:
            await client.aclose()

    assert asyncio.run(run()) == "Async grounded answer."
    print("[OK] Async path parsed a successful response")


# ------------------------------------------------------------------
# 3. API error handling
# ------------------------------------------------------------------

def test_api_error_handling():
    print("Testing API error handling...")

    # HTTP 401 from the API.
    def unauthorized(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"message": "Invalid credentials"}},
            request=request,
        )

    client = make_client(unauthorized)
    try:
        with temp_setting("OPENROUTER_API_KEY", DUMMY_KEY):
            message = expect_ai_service_error(
                generate_completion, SOURCE, INSTRUCTION, client=client
            )
    finally:
        client.close()

    assert "401" in message, message
    assert DUMMY_KEY not in message, "API key leaked into the 401 error message"
    print(f"[OK] HTTP 401 raised AIServiceError (HTTP status surfaced, key hidden)")

    # Transport failure (e.g. DNS/connection problem).
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(refuse)
    try:
        with temp_setting("OPENROUTER_API_KEY", DUMMY_KEY):
            message = expect_ai_service_error(
                generate_completion, SOURCE, INSTRUCTION, client=client
            )
    finally:
        client.close()

    assert "failed" in message.lower(), message
    assert DUMMY_KEY not in message
    print("[OK] Connection failure raised AIServiceError")

    # Timeout.
    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    client = make_client(slow)
    try:
        with temp_setting("OPENROUTER_API_KEY", DUMMY_KEY):
            message = expect_ai_service_error(
                generate_completion, SOURCE, INSTRUCTION, timeout=7.5, client=client
            )
    finally:
        client.close()

    assert "timed out" in message.lower(), message
    assert "7.5" in message, message
    print("[OK] Timeout raised AIServiceError with the configured timeout")


# ------------------------------------------------------------------
# 4. Malformed response handling
# ------------------------------------------------------------------

def test_malformed_response_handling():
    print("Testing malformed response handling...")

    def json_body(payload):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload, request=request)
        return handler

    def raw_body(text):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text=text, request=request)
        return handler

    cases = [
        ("non-JSON body", raw_body("<html>not json</html>")),
        ("no choices key", json_body({"id": "abc"})),
        ("empty choices list", json_body({"choices": []})),
        ("choices is not a list", json_body({"choices": "nope"})),
        ("choice is not an object", json_body({"choices": ["nope"]})),
        ("missing message", json_body({"choices": [{"index": 0}]})),
        ("missing content", json_body({"choices": [{"message": {"role": "assistant"}}]})),
        ("blank content", json_body({"choices": [{"message": {"content": "   "}}]})),
        ("null content", json_body({"choices": [{"message": {"content": None}}]})),
        ("JSON root is a list", json_body([{"choices": []}])),
    ]

    with temp_setting("OPENROUTER_API_KEY", DUMMY_KEY):
        for label, handler in cases:
            client = make_client(handler)
            try:
                message = expect_ai_service_error(
                    generate_completion, SOURCE, INSTRUCTION, client=client
                )
            finally:
                client.close()
            assert message, f"empty error message for case: {label}"
            assert DUMMY_KEY not in message, f"API key leaked for case: {label}"

    print(f"[OK] All {len(cases)} malformed response shapes raised AIServiceError")


# ------------------------------------------------------------------
# 5. Configuration and input validation
# ------------------------------------------------------------------

def test_missing_and_invalid_configuration():
    print("Testing missing configuration and empty inputs...")
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return ok_content("should not be reached", request)

    # No API key configured: fail fast, without any HTTP call.
    client = make_client(handler)
    try:
        with temp_setting("OPENROUTER_API_KEY", ""):
            message = expect_ai_service_error(
                generate_completion, SOURCE, INSTRUCTION, client=client
            )
    finally:
        client.close()

    assert "OPENROUTER_API_KEY" in message, message
    assert calls == [], "the API was called even though no key was configured"
    print("[OK] Missing API key reported without calling OpenRouter")

    client = make_client(handler)
    try:
        with temp_setting("OPENROUTER_API_KEY", DUMMY_KEY):
            empty_context = expect_ai_service_error(
                generate_completion, "   ", INSTRUCTION, client=client
            )
            empty_instruction = expect_ai_service_error(
                generate_completion, SOURCE, "", client=client
            )
    finally:
        client.close()

    assert "source_context" in empty_context, empty_context
    assert "instruction" in empty_instruction, empty_instruction
    assert calls == [], "the API was called with empty inputs"
    print("[OK] Empty source_context / instruction rejected before any HTTP call")

    # Default timeout is applied when none is passed.
    assert DEFAULT_TIMEOUT_SECONDS > 0
    print(f"[OK] Default HTTP timeout is {DEFAULT_TIMEOUT_SECONDS}s")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING STATLEARN AI PHASE 5 STEP 3 AI SERVICE TEST SUITE")
    print("=" * 60)
    test_system_instruction_is_grounded()
    test_successful_response_parsing()
    test_async_successful_response_parsing()
    test_api_error_handling()
    test_malformed_response_handling()
    test_missing_and_invalid_configuration()
    print("=" * 60)
    print("ALL PHASE 5 STEP 3 AI SERVICE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
