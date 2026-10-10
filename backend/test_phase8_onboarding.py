"""
UPSKILL AI - Phase 8 Onboarding Test Suite

Tests the new-user onboarding flow end to end against the shared SQLite demo
database:
- GET  /auth/onboarding-status for a fresh user (profile_completed=False and
  the seeded framework positions are listed).
- POST /auth/complete-onboarding persists the position + professional profile
  and sets profile_completed.
- /me reflects the saved onboarding profile.
- Diagnostic start is refused before onboarding and works after it, with
  questions selected from the chosen position's competency framework.
- Diagnostic submit persists the FULL assessed competency profile for a new
  user (all assessed competencies, not only the ones that levelled up).
- Changing position later resets profile_completed but preserves assessed
  levels.

Every test creates only users it owns and deletes them (and their assessment /
competency rows) afterwards, leaving the shared database exactly as found.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import User, LearnerCompetency, DiagnosticAssessment

client = TestClient(app)

REGISTER_PASSWORD = "Test1234"
NAME = "Onboarding Test User"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _unique_email() -> str:
    return f"onboarding_test_{os.getpid()}_{len(NAME)}@statlearn.local"


def _cleanup(email):
    """Delete the test user and every row that references it."""
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if u is not None:
            db.query(LearnerCompetency).filter(
                LearnerCompetency.user_id == u.id
            ).delete()
            db.query(DiagnosticAssessment).filter(
                DiagnosticAssessment.learner_id == u.id
            ).delete()
            db.delete(u)
            db.commit()
    finally:
        db.close()


def _register(email):
    return client.post(
        "/api/v1/auth/register",
        json={"name": NAME, "email": email, "password": REGISTER_PASSWORD},
    )


def _login_token(email):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": REGISTER_PASSWORD},
    )
    assert resp.status_code == 200, f"login failed: {resp.text}"
    return resp.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _role_id_by_name(token, name):
    resp = client.get("/api/v1/auth/onboarding-status", headers=_headers(token))
    assert resp.status_code == 200
    for role in resp.json()["roles"]:
        if role["name"] == name:
            return role["id"]
    raise AssertionError(f"framework role {name!r} not found in onboarding-status")


def _complete_onboarding(token, role_id):
    return client.post(
        "/api/v1/auth/complete-onboarding",
        headers=_headers(token),
        json={
            "role_id": role_id,
            "designation": "Junior Analyst",
            "department": "State Statistics Bureau",
            "assignment": "District survey compilation and indicator reporting.",
            "education": "B.Sc. Statistics",
            "work_experience": "2 years data handling",
            "previous_training": "Introductory sampling workshop",
        },
    )


# ------------------------------------------------------------------
# Onboarding status
# ------------------------------------------------------------------

def test_onboarding_status_for_fresh_user_lists_positions():
    email = _unique_email()
    try:
        assert _register(email).status_code == 201
        token = _login_token(email)

        resp = client.get("/api/v1/auth/onboarding-status", headers=_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["profile_completed"] is False
        assert body["has_role"] is False
        names = [r["name"] for r in body["roles"]]
        # The seeded onboarding positions must be offered.
        assert "Statistical Officer" in names
        assert "Data Analyst" in names
        assert "Statistical Assistant" in names
    finally:
        _cleanup(email)


def test_diagnostic_start_refused_before_onboarding():
    email = _unique_email()
    try:
        assert _register(email).status_code == 201
        token = _login_token(email)
        resp = client.post("/api/v1/diagnostic/start", headers=_headers(token))
        assert resp.status_code == 400
        assert "no assigned role" in resp.json()["detail"]
    finally:
        _cleanup(email)


# ------------------------------------------------------------------
# Complete onboarding
# ------------------------------------------------------------------

def test_complete_onboarding_persists_profile_and_flag():
    email = _unique_email()
    try:
        assert _register(email).status_code == 201
        token = _login_token(email)
        role_id = _role_id_by_name(token, "Data Analyst")

        resp = _complete_onboarding(token, role_id)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["profile_completed"] is True
        assert body["designation"] == "Junior Analyst"
        assert body["department"] == "State Statistics Bureau"
        assert body["role"]["id"] == role_id
        assert body["role"]["name"] == "Data Analyst"
        assert "hashed_password" not in body

        # The saved profile is reflected by /me as well.
        me = client.get("/api/v1/me", headers=_headers(token)).json()
        assert me["designation"] == "Junior Analyst"
        assert me["profile_completed"] is True
        assert me["role"]["name"] == "Data Analyst"

        # onboarding-status flips to completed.
        status = client.get(
            "/api/v1/auth/onboarding-status", headers=_headers(token)
        ).json()
        assert status["profile_completed"] is True
        assert status["has_role"] is True
    finally:
        _cleanup(email)


def test_complete_onboarding_rejects_unknown_role():
    email = _unique_email()
    try:
        assert _register(email).status_code == 201
        token = _login_token(email)
        resp = _complete_onboarding(token, 999999)
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"]
    finally:
        _cleanup(email)


# ------------------------------------------------------------------
# Assessment after onboarding (role-driven)
# ------------------------------------------------------------------

def test_assessment_flow_after_onboarding_persists_full_profile():
    email = _unique_email()
    try:
        assert _register(email).status_code == 201
        token = _login_token(email)

        # Before onboarding: no competency profile at all.
        comps_before = client.get(
            "/api/v1/me/competencies", headers=_headers(token)
        ).json()
        assert comps_before["competencies"] == []

        # Onboard as Data Analyst (6 mapped competencies, distinct from the
        # demo learner's 8) and start the diagnostic.
        role_id = _role_id_by_name(token, "Data Analyst")
        assert _complete_onboarding(token, role_id).status_code == 200

        start = client.post("/api/v1/diagnostic/start", headers=_headers(token))
        assert start.status_code == 201, start.text
        questions = start.json()["questions"]
        assert len(questions) > 0

        # Questions must cover exactly the Data Analyst framework.
        expected_comp_ids = {
            m.competency_id
            for m in _role_mappings(role_id)
        }
        assert {q["competency_id"] for q in questions} == expected_comp_ids

        # Submit (answers content does not matter for persistence checks).
        answers = [
            {"question_id": q["question_id"], "selected_option": 0}
            for q in questions
        ]
        submit = client.post(
            f"/api/v1/diagnostic/{start.json()['assessment_id']}/submit",
            headers=_headers(token),
            json={"answers": answers},
        )
        assert submit.status_code == 200, submit.text

        # The FULL assessed profile is persisted: one row per assessed
        # competency, each with a valid level (including unchanged ones).
        comps_after = client.get(
            "/api/v1/me/competencies", headers=_headers(token)
        ).json()
        comp_rows = comps_after["competencies"]
        assert {c["competency_id"] for c in comp_rows} == expected_comp_ids
        for row in comp_rows:
            assert 1 <= row["current_level"] <= 4
            assert row["required_level"] is not None

        # Gaps and recommendations now work off the assessed profile.
        gaps = client.get("/api/v1/me/gaps", headers=_headers(token)).json()
        assert gaps["summary"]["total_competencies"] == len(expected_comp_ids)

        recs = client.get(
            "/api/v1/me/recommendations", headers=_headers(token)
        ).json()
        assert recs["summary"]["total_recommendations"] >= 0
    finally:
        _cleanup(email)


# ------------------------------------------------------------------
# Position change after onboarding
# ------------------------------------------------------------------

def test_position_change_resets_flag_but_preserves_levels():
    email = _unique_email()
    try:
        assert _register(email).status_code == 201
        token = _login_token(email)

        # Onboard as Data Analyst and take the diagnostic.
        analyst_id = _role_id_by_name(token, "Data Analyst")
        assert _complete_onboarding(token, analyst_id).status_code == 200
        start = client.post("/api/v1/diagnostic/start", headers=_headers(token))
        assert start.status_code == 201
        questions = start.json()["questions"]
        answers = [
            {"question_id": q["question_id"], "selected_option": 2}
            for q in questions
        ]
        client.post(
            f"/api/v1/diagnostic/{start.json()['assessment_id']}/submit",
            headers=_headers(token),
            json={"answers": answers},
        )

        levels_before = {
            c["competency_id"]: c["current_level"]
            for c in client.get(
                "/api/v1/me/competencies", headers=_headers(token)
            ).json()["competencies"]
        }
        assert len(levels_before) > 0

        # Change position to Statistical Officer.
        officer_id = _role_id_by_name(token, "Statistical Officer")
        change = _complete_onboarding(token, officer_id)
        assert change.status_code == 200
        body = change.json()
        assert body["role"]["id"] == officer_id
        # Flag reset so the new framework's (re)assessment is offered.
        assert body["profile_completed"] is False

        # Previously assessed levels are preserved (never decrease).
        comps = client.get(
            "/api/v1/me/competencies", headers=_headers(token)
        ).json()["competencies"]
        levels_now = {c["competency_id"]: c["current_level"] for c in comps}
        for comp_id, level in levels_before.items():
            assert levels_now.get(comp_id) == level

        # A new assessment for the new role can be started.
        start2 = client.post("/api/v1/diagnostic/start", headers=_headers(token))
        assert start2.status_code == 201
        assert len(start2.json()["questions"]) > 0
    finally:
        _cleanup(email)


# ------------------------------------------------------------------
# Internal helper
# ------------------------------------------------------------------

def _role_mappings(role_id):
    """RoleCompetency rows for a role id (fresh session, read-only)."""
    from app.database import SessionLocal
    from app.models import RoleCompetency

    db = SessionLocal()
    try:
        return db.query(RoleCompetency).filter(
            RoleCompetency.role_id == role_id
        ).all()
    finally:
        db.close()
