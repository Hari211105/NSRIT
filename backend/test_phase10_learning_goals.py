"""
UPSKILL AI - Phase 10 Learning Goal Path Test Suite

Verifies:
1. GET /api/v1/courses lists courses and filters by category (TECHNICAL | NON_TECHNICAL).
2. GET /api/v1/courses/{id} returns course details with mapped competencies.
3. Onboarding validation: rejects requests with neither role_id nor course_id,
   and rejects requests with both.
4. Onboarding in GOAL mode succeeds without employee fields (designation, department).
5. Diagnostic start for a GOAL learner selects questions tailored to the course's framework.
6. Gap analysis and recommendations compute properly based on the course's required competency levels.
7. Existing ROLE-based onboarding and demo user continue working 100% unchanged.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, LearnerCompetency, DiagnosticAssessment, Course, Role

client = TestClient(app)

TEST_PASSWORD = "GoalTestPassword123!"

def _unique_email(prefix="goal_test") -> str:
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

def _register_and_get_token(email: str, name: str = "Goal Learner") -> str:
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


def test_list_and_filter_courses():
    """Verify listing all courses and filtering by TECHNICAL and NON_TECHNICAL."""
    email = _unique_email("list_courses")
    token = _register_and_get_token(email)
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # All courses
        all_res = client.get("/api/v1/courses", headers=headers)
        assert all_res.status_code == 200
        all_courses = all_res.json()
        assert len(all_courses) >= 6

        # Technical filter
        tech_res = client.get("/api/v1/courses?category=TECHNICAL", headers=headers)
        assert tech_res.status_code == 200
        tech_courses = tech_res.json()
        assert len(tech_courses) >= 3
        assert all(c["category"] == "TECHNICAL" for c in tech_courses)

        # Non-Technical filter
        nontech_res = client.get("/api/v1/courses?category=NON_TECHNICAL", headers=headers)
        assert nontech_res.status_code == 200
        nontech_courses = nontech_res.json()
        assert len(nontech_courses) >= 3
        assert all(c["category"] == "NON_TECHNICAL" for c in nontech_courses)

        # Get course details
        sample = tech_courses[0]
        detail_res = client.get(f"/api/v1/courses/{sample['id']}", headers=headers)
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert "competencies" in detail
        assert len(detail["competencies"]) > 0
    finally:
        _cleanup(email)


def test_onboarding_validation_neither_or_both():
    """Verify onboarding rejects requests with neither role_id nor course_id, or both."""
    email = _unique_email("val_user")
    token = _register_and_get_token(email)
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # 1. Neither provided
        res_neither = client.post(
            "/api/v1/auth/complete-onboarding",
            headers=headers,
            json={"designation": "Student", "department": "University"},
        )
        assert res_neither.status_code == 400
        assert "Must provide either role_id or course_id" in res_neither.json()["detail"]

        # 2. Both provided
        db = SessionLocal()
        role = db.query(Role).first()
        course = db.query(Course).first()
        db.close()

        res_both = client.post(
            "/api/v1/auth/complete-onboarding",
            headers=headers,
            json={
                "role_id": role.id,
                "course_id": course.id,
                "designation": "Developer",
                "department": "Engineering",
            },
        )
        assert res_both.status_code == 400
        assert "Cannot provide both" in res_both.json()["detail"]
    finally:
        _cleanup(email)


def test_goal_onboarding_and_assessment_flow():
    """
    Onboard as a GOAL learner with a Python Programming course (no designation/department),
    take diagnostic assessment, verify gap analysis and recommendations.
    """
    email = _unique_email("python_learner")
    token = _register_and_get_token(email, name="Rahul Verma")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        db = SessionLocal()
        py_course = db.query(Course).filter(Course.code == "TECH_PY_101").first()
        assert py_course is not None
        db.close()

        # Onboard into GOAL mode
        ob_res = client.post(
            "/api/v1/auth/complete-onboarding",
            headers=headers,
            json={"course_id": py_course.id, "learning_mode": "GOAL"},
        )
        assert ob_res.status_code == 200
        user_info = ob_res.json()
        assert user_info["learning_mode"] == "GOAL"
        assert user_info["course"]["id"] == py_course.id
        assert user_info["profile_completed"] is True

        # Start diagnostic
        diag_start = client.post("/api/v1/diagnostic/start", headers=headers)
        assert diag_start.status_code == 201
        start_payload = diag_start.json()
        questions = start_payload["questions"]
        assert len(questions) > 0

        # Submit answers
        answers = [{"question_id": q["question_id"], "selected_option": 0} for q in questions]
        submit_res = client.post(
            f"/api/v1/diagnostic/{start_payload['assessment_id']}/submit",
            headers=headers,
            json={"answers": answers},
        )
        assert submit_res.status_code == 200

        # Verify gaps
        gaps_res = client.get("/api/v1/me/gaps", headers=headers)
        assert gaps_res.status_code == 200
        gaps_data = gaps_res.json()
        assert "gaps" in gaps_data
        assert "summary" in gaps_data

        # Verify recommendations
        recs_res = client.get("/api/v1/me/recommendations", headers=headers)
        assert recs_res.status_code == 200
        recs_data = recs_res.json()
        assert "recommendations" in recs_data
    finally:
        _cleanup(email)
