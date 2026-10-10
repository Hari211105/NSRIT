"""
UPSKILL AI - Phase 7B Route Authentication & Isolation Test Suite

Verifies the routes migrated in Phase 7B now require a valid Bearer token and
that each authenticated learner only ever sees their own learner-specific data.

Tests:
1. Unauthorized access: every protected route returns 401 without a token,
   while /health and the public catalog/roles/competencies stay open.
2. Authorized access works: a valid token reaches the learner routes (200).
3. A registered user sees only their own profile (not the demo learner's).
4. Quiz evidence is scoped per user: two learners each record quiz evidence
   and neither ever sees the other's evidence.
5. Diagnostic assessments are ownership-scoped: a user cannot view or submit
   another user's assessment (403).

Every test cleans up the users, documents and assessments it creates, leaving
the shared database exactly as it found it.
"""

import sys
import os
import io
import secrets
import contextlib
import pymupdf as fitz
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models import (
    User,
    Competency,
    Document,
    DocumentChunk,
    GeneratedMCQ,
    LearnerCompetency,
    QuizAssessment,
    DiagnosticAssessment,
)
from app.services import mcq_service
from auth_test_utils import AuthenticatedClient

# Public (unauthenticated) client for the unauthorized-access tests.
plain_client = TestClient(app)

MCQ_COUNT = 5
ANSWER_KEY = [i % 4 for i in range(MCQ_COUNT)]
COMPETENCY_NAME = "Survey Methodology"

# ---------------------------------------------------------------
# Test-logged state, restored after every test
# ---------------------------------------------------------------

CREATED = {"emails": [], "docs": [], "assessments": []}


@pytest.fixture(autouse=True)
def cleanup_state():
    yield
    _cleanup()


def _cleanup():
    db = SessionLocal()
    try:
        if CREATED["assessments"]:
            db.query(DiagnosticAssessment).filter(
                DiagnosticAssessment.id.in_(CREATED["assessments"])
            ).delete(synchronize_session=False)
            CREATED["assessments"].clear()
        for doc_id in list(CREATED["docs"]):
            db.query(QuizAssessment).filter(
                QuizAssessment.document_id == doc_id
            ).delete(synchronize_session=False)
            db.query(GeneratedMCQ).filter(
                GeneratedMCQ.document_id == doc_id
            ).delete(synchronize_session=False)
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc_id
            ).delete(synchronize_session=False)
            db.query(Document).filter(Document.id == doc_id).delete(
                synchronize_session=False
            )
        CREATED["docs"].clear()
        for email in list(CREATED["emails"]):
            user = db.query(User).filter(User.email == email).first()
            if user is not None:
                db.query(QuizAssessment).filter(
                    QuizAssessment.learner_id == user.id
                ).delete(synchronize_session=False)
                db.query(DiagnosticAssessment).filter(
                    DiagnosticAssessment.learner_id == user.id
                ).delete(synchronize_session=False)
                db.query(LearnerCompetency).filter(
                    LearnerCompetency.user_id == user.id
                ).delete(synchronize_session=False)
                db.delete(user)
        CREATED["emails"].clear()
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _unique(tag: str) -> str:
    return f"pb7b_{tag}_{os.getpid()}_{secrets.token_hex(3)}@statlearn.local"


def make_user(tag: str):
    """Register + log in a throwaway user; returns (email, token)."""
    email = _unique(tag)
    reg = plain_client.post(
        "/api/v1/auth/register",
        json={"name": "Phase 7B User", "email": email, "password": "Test1234"},
    )
    assert reg.status_code == 201, reg.text
    CREATED["emails"].append(email)
    login = plain_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Test1234"},
    )
    assert login.status_code == 200, login.text
    return email, login.json()["access_token"]


def _competency_id() -> int:
    db = SessionLocal()
    try:
        comp = db.query(Competency).filter(Competency.name == COMPETENCY_NAME).first()
        assert comp is not None, f"{COMPETENCY_NAME} not seeded"
        return comp.id
    finally:
        db.close()


def _pdf(label: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), f"Phase 7B {label} statistical document.")
    data = doc.tobytes()
    doc.close()
    return data


def upload_linked_doc(client, label: str) -> int:
    """Upload a competency-linked PDF as the authenticated client."""
    files = {"file": (f"{label}.pdf", io.BytesIO(_pdf(label)), "application/pdf")}
    resp = client.post(
        "/api/v1/documents/upload",
        files=files,
        params={"competency_id": _competency_id()},
    )
    assert resp.status_code == 201, resp.text
    doc_id = resp.json()["id"]
    CREATED["docs"].append(doc_id)
    return doc_id


@contextlib.contextmanager
def fake_generation():
    def fake_generate(chunk_text, source_chunk_id, **kwargs):
        return [
            {
                "question": f"Question {i + 1}?",
                "options": [f"Opt{i + 1}{letter}" for letter in "ABCD"],
                "correct_option": ANSWER_KEY[i],
                "explanation": f"Explanation {i + 1}.",
                "source_chunk_id": source_chunk_id,
            }
            for i in range(MCQ_COUNT)
        ]

    original = mcq_service.generate_mcqs
    mcq_service.generate_mcqs = fake_generate
    try:
        yield
    finally:
        mcq_service.generate_mcqs = original


def submit_all_correct(client, doc_id: int):
    quiz = client.get(f"/api/v1/documents/{doc_id}/quiz")
    assert quiz.status_code == 200, quiz.text
    questions = quiz.json()["questions"]
    answers = [
        {"question_id": q["question_id"], "selected_option": ANSWER_KEY[i]}
        for i, q in enumerate(questions)
    ]
    resp = client.post(
        f"/api/v1/documents/{doc_id}/quiz/submit", json={"answers": answers}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------
# 1. Unauthorized access rejected (401)
# ---------------------------------------------------------------

def test_protected_routes_require_token():
    print("Testing protected routes return 401 without a token...")
    for url in (
        "/api/v1/me",
        "/api/v1/me/competencies",
        "/api/v1/me/evidence",
        "/api/v1/me/gaps",
        "/api/v1/me/recommendations",
        "/api/v1/diagnostic/history",
    ):
        assert plain_client.get(url).status_code == 401, url

    # POST-only routes.
    assert plain_client.post("/api/v1/diagnostic/start").status_code == 401

    files = {"file": ("unauth.pdf", io.BytesIO(_pdf("unauth")), "application/pdf")}
    assert plain_client.post("/api/v1/documents/upload", files=files).status_code == 401
    print("[OK] All learner/diagnostic/document routes reject unauthenticated requests")


def test_public_endpoints_stay_open():
    print("Testing public endpoints remain open without a token...")
    assert plain_client.get("/api/v1/health").status_code == 200
    assert plain_client.get("/api/v1/roles").status_code == 200
    assert plain_client.get("/api/v1/competencies").status_code == 200
    assert plain_client.get("/api/v1/catalog/resources").status_code == 200
    print("[OK] /health, roles, competencies and catalog remain public")


# ---------------------------------------------------------------
# 2-3. Authorized access + profile isolation
# ---------------------------------------------------------------

def test_authorized_profile_isolation():
    print("Testing a registered user sees only their own profile...")
    email, token = make_user("me")
    client = AuthenticatedClient(token=token)

    me = client.get("/api/v1/me")
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["email"] == email, "the profile did not match the authenticated user"
    assert body["name"] == "Phase 7B User"
    # A fresh user has no role and no evidence.
    assert client.get("/api/v1/me/competencies").status_code == 200
    assert client.get("/api/v1/me/evidence").json()["total_evidence"] == 0
    print(f"[OK] GET /me returned the authenticated user ({email})")


# ---------------------------------------------------------------
# 4. Quiz evidence is scoped per user
# ---------------------------------------------------------------

def test_quiz_evidence_is_user_isolated():
    print("Testing quiz evidence is scoped per user...")
    email_a, token_a = make_user("aiso")
    email_b, token_b = make_user("biso")
    client_a = AuthenticatedClient(token=token_a)
    client_b = AuthenticatedClient(token=token_b)

    doc_a = upload_linked_doc(client_a, "isoA")
    doc_b = upload_linked_doc(client_b, "isoB")

    with fake_generation():
        assert client_a.post(f"/api/v1/documents/{doc_a}/mcqs/generate").status_code == 201
        assert client_b.post(f"/api/v1/documents/{doc_b}/mcqs/generate").status_code == 201

    submit_all_correct(client_a, doc_a)
    submit_all_correct(client_b, doc_b)

    ev_a = client_a.get("/api/v1/me/evidence").json()["evidence"]
    ev_b = client_b.get("/api/v1/me/evidence").json()["evidence"]

    assert [e["document_id"] for e in ev_a] == [doc_a], "A should see only its own evidence"
    assert [e["document_id"] for e in ev_b] == [doc_b], "B should see only its own evidence"
    assert doc_b not in [e["document_id"] for e in ev_a], "leaked B's evidence to A"
    assert doc_a not in [e["document_id"] for e in ev_b], "leaked A's evidence to B"
    print(f"[OK] A saw {len(ev_a)} record(s), B saw {len(ev_b)} record(s), fully isolated")


# ---------------------------------------------------------------
# 5. Diagnostic assessments are ownership-scoped
# ---------------------------------------------------------------

def test_diagnostic_ownership_isolation():
    print("Testing a user cannot view or submit another user's assessment...")
    demo = AuthenticatedClient()  # demo learner (has a role)

    start = demo.post("/api/v1/diagnostic/start")
    assert start.status_code == 201, start.text
    assessment_id = start.json()["assessment_id"]
    CREATED["assessments"].append(assessment_id)

    _, token = make_user("own")
    other = AuthenticatedClient(token=token)

    # Viewing another learner's assessment is forbidden.
    view = other.get(f"/api/v1/diagnostic/{assessment_id}")
    assert view.status_code == 403, f"expected 403, got {view.status_code}"
    assert "different learner" in view.json()["detail"].lower()

    # Submitting another learner's assessment is forbidden too.
    question_id = start.json()["questions"][0]["question_id"]
    submit = other.post(
        f"/api/v1/diagnostic/{assessment_id}/submit",
        json={"answers": [{"question_id": question_id, "selected_option": 0}]},
    )
    assert submit.status_code == 403, f"expected 403, got {submit.status_code}"
    print(f"[OK] Cross-user diagnostic access returns 403 for view and submit")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING UPSKILL AI PHASE 7B ROUTE AUTH TEST SUITE")
    print("=" * 60)
    test_protected_routes_require_token()
    test_public_endpoints_stay_open()
    test_authorized_profile_isolation()
    test_quiz_evidence_is_user_isolated()
    test_diagnostic_ownership_isolation()
    _cleanup()
    print("=" * 60)
    print("ALL PHASE 7B ROUTE AUTH TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)