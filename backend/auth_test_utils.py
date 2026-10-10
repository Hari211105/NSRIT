"""
Shared helpers for test suites that exercise authenticated learner routes
(Phase 7B).

Routes under /me and /documents now require a valid Bearer token (Phase 7B).
This module provides an AuthenticatedClient that transparently attaches the demo
learner's token to every request, so existing call sites that use
`client.get/post(...)` without an Authorization header keep working unchanged.

The file name deliberately does not match pytest's test_*.py / *_test.py
patterns, so it is never collected as a test module.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

DEMO_EMAIL = "demo@statlearn.local"
DEMO_PASSWORD = "Demo@12345"


def demo_token() -> str:
    """Log in as the demo learner and return its Bearer access token."""
    client = TestClient(app)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert resp.status_code == 200, f"demo login failed: {resp.text}"
    return resp.json()["access_token"]


class AuthenticatedClient(TestClient):
    """
    A TestClient that sends `Authorization: Bearer <token>` on every request.

    Keeps existing test helper code (which issues unauthenticated client calls)
    working once the underlying routes require authentication.
    """

    def __init__(self, token=None):
        super().__init__(app)
        self.token = token or demo_token()

    def request(self, method, url, **kwargs):
        headers = dict(kwargs.get("headers") or {})
        headers.setdefault("Authorization", f"Bearer {self.token}")
        kwargs["headers"] = headers
        return super().request(method, url, **kwargs)