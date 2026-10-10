"""
UPSKILL AI - Phase 9 Multi-Sector Expansion Test Suite

Verifies multi-sector capabilities across all domains:
1. GET /api/v1/sectors returns all 6 sectors (Governance, IT/Tech, Healthcare, Finance, Agriculture, Education).
2. GET /api/v1/sectors/{id}/roles returns specific roles for that sector.
3. GET /api/v1/auth/onboarding-status includes sectors list and sector_id on roles.
4. Completing onboarding with a Tech/IT role (e.g. Full Stack Developer) associates the user correctly.
5. Starting a diagnostic assessment for a multi-sector role generates questions matched to that role's competency framework.
6. Submitting diagnostic responses records multi-sector competency levels and enables learning recommendations from SWAYAM/NPTEL/Skill India.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, LearnerCompetency, DiagnosticAssessment, Role, Sector

client = TestClient(app)

TEST_PASSWORD = "SectorTest123!"

def _unique_email(prefix="multisector") -> str:
    return f"{prefix}_{os.getpid()}_{os.urandom(4).hex()}@platform.local"

def _cleanup(email: str):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if u is not None:
            db.query(LearnerCompetency).filter(LearnerCompetency.user_id == u.id).delete()
            db.query(DiagnosticAssessment).filter(DiagnosticAssessment.learner_id == u.id).delete()
            db.delete(u)
            db.commit()
    finally:
        db.close()

def _register_and_get_token(email: str, name: str = "Sector Learner") -> str:
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": TEST_PASSWORD, "name": name},
    )
    assert reg.status_code == 201, f"Register failed: {reg.text}"
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200, f"Login failed: {login.text}"
    return login.json()["access_token"]


def test_list_sectors():
    """Verify that all 6 sectors are seeded and exposed via GET /api/v1/sectors."""
    res = client.get("/api/v1/sectors")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 6

    codes = [s["code"] for s in data]
    expected_codes = ["GOV_STATS", "TECH_IT", "HEALTHCARE", "FINANCE_BFSI", "AGRICULTURE", "EDUCATION"]
    for code in expected_codes:
        assert code in codes, f"Sector code {code} missing from GET /api/v1/sectors"


def test_get_sector_roles():
    """Verify querying roles filtered by a specific sector."""
    sec_res = client.get("/api/v1/sectors")
    tech_sector = next((s for s in sec_res.json() if s["code"] == "TECH_IT"), None)
    assert tech_sector is not None

    roles_res = client.get(f"/api/v1/sectors/{tech_sector['id']}/roles")
    assert roles_res.status_code == 200
    roles = roles_res.json()
    assert len(roles) >= 2
    role_names = [r["name"] for r in roles]
    assert "Full Stack Developer" in role_names


def test_onboarding_status_has_sectors():
    """Verify that /api/v1/auth/onboarding-status provides sectors and enriched roles."""
    email = _unique_email("onboarding_status")
    token = _register_and_get_token(email)

    try:
        status_res = client.get(
            "/api/v1/auth/onboarding-status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert status_res.status_code == 200
        data = status_res.json()
        assert "sectors" in data
        assert len(data["sectors"]) >= 6
        assert "roles" in data
        assert len(data["roles"]) > 0
        # Ensure sector_id is populated on roles
        assert any(r.get("sector_id") is not None for r in data["roles"])
    finally:
        _cleanup(email)


def test_multisector_onboarding_and_diagnostic():
    """
    Register a learner, onboard them as a Full Stack Developer (Tech sector),
    verify their diagnostic questions match IT competencies, and submit an assessment.
    """
    email = _unique_email("tech_developer")
    token = _register_and_get_token(email, name="Aditi Sharma")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. Identify the Tech role id
        db = SessionLocal()
        tech_role = db.query(Role).filter(Role.name == "Full Stack Developer").first()
        assert tech_role is not None
        db.close()

        # 2. Complete onboarding with this role
        ob_res = client.post(
            "/api/v1/auth/complete-onboarding",
            headers=headers,
            json={
                "role_id": tech_role.id,
                "designation": "Frontend Specialist",
                "department": "Engineering Labs",
                "assignment": "Web Portal Revamp",
                "education": "B.Tech Computer Science",
                "work_experience": "2 years",
                "previous_training": "NPTEL Full Stack certification",
            },
        )
        assert ob_res.status_code == 200
        user_data = ob_res.json()
        assert user_data["role"]["id"] == tech_role.id
        assert user_data["profile_completed"] is True

        # 3. Start diagnostic assessment (returns 201 CREATED)
        diag_start = client.post("/api/v1/diagnostic/start", headers=headers)
        assert diag_start.status_code == 201
        start_data = diag_start.json()
        assessment_id = start_data["assessment_id"]
        questions = start_data["questions"]
        assert len(questions) > 0

        # Verify the questions correspond to competencies in the Tech role framework
        q_comp_names = [q.get("competency_name") for q in questions]
        assert any("Software Engineering Principles" in name or "DevOps" in name or "Database Architecture" in name for name in q_comp_names)

        # 4. Submit answers for all questions
        answers = [
            {"question_id": q["question_id"], "selected_option": 0}
            for q in questions
        ]
        submit_res = client.post(
            f"/api/v1/diagnostic/{assessment_id}/submit",
            headers=headers,
            json={"answers": answers},
        )
        assert submit_res.status_code == 200, submit_res.text

        # 5. Fetch updated competencies, gaps, and recommendations
        comps_res = client.get("/api/v1/me/competencies", headers=headers)
        assert comps_res.status_code == 200
        comps_data = comps_res.json()["competencies"]
        assert len(comps_data) > 0

        gaps_res = client.get("/api/v1/me/gaps", headers=headers)
        assert gaps_res.status_code == 200

        recs_res = client.get("/api/v1/me/recommendations", headers=headers)
        assert recs_res.status_code == 200
    finally:
        _cleanup(email)
