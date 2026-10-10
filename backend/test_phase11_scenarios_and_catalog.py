"""
UPSKILL AI - Phase 11 / Phase 2 Assessment & Discovery Test Suite

Verifies:
1. question_type field default on DiagnosticQuestion ('MCQ') for backward compatibility.
2. Scenario question creation, fields, and payload delivery (question_type == 'SCENARIO').
3. Server-side difficulty-weighted scoring compatibility for scenario questions.
4. Course catalog keyword search (GET /api/v1/courses?search=...) and category filtering (GET /api/v1/courses?category=...).
5. Courses return estimated_hours in API payloads.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, DiagnosticQuestion, Competency, Course, DiagnosticAssessment, LearnerCompetency

client = TestClient(app)

TEST_PASSWORD = "ScenarioTestPass123!"

def _unique_email(prefix="phase2_test") -> str:
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

def _register_and_get_token(email: str, name: str = "Scenario Learner") -> str:
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


import json

def test_question_type_default_compatibility():
    """Verify that new DiagnosticQuestions default to 'MCQ' without explicit question_type."""
    db = SessionLocal()
    try:
        comp = db.query(Competency).first()
        assert comp is not None

        q = DiagnosticQuestion(
            competency_id=comp.id,
            question="What is the arithmetic mean?",
            options=json.dumps(["Sum divided by count", "Middle value", "Most frequent value", "Range"]),
            correct_option=0,
            difficulty="EASY",
            explanation="Mean is the sum divided by the number of observations."
        )
        db.add(q)
        db.commit()
        db.refresh(q)

        assert q.question_type == "MCQ"
        db.delete(q)
        db.commit()
    finally:
        db.close()


def test_scenario_question_delivery_and_scoring():
    """Verify diagnostic assessment handles scenario questions and scores them accurately."""
    email = _unique_email("scenario_diag")
    try:
        token = _register_and_get_token(email)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Onboard learner into non-technical course (e.g. Communication Skills)
        db = SessionLocal()
        comm_course = db.query(Course).filter(Course.code == "NONTECH_COMM_101").first()
        db.close()
        assert comm_course is not None

        ob_resp = client.post(
            "/api/v1/auth/complete-onboarding",
            json={"learning_mode": "GOAL", "course_id": comm_course.id},
            headers=headers
        )
        assert ob_resp.status_code == 200

        # 2. Start diagnostic assessment
        start_resp = client.post(
            "/api/v1/diagnostic/start",
            json={"assessment_type": "diagnostic"},
            headers=headers
        )
        assert start_resp.status_code == 201, f"Failed starting diagnostic: {start_resp.text}"
        diag_id = start_resp.json()["assessment_id"]

        # 3. Fetch questions
        get_resp = client.get(f"/api/v1/diagnostic/{diag_id}", headers=headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        questions = data["questions"]
        assert len(questions) > 0

        # Verify question_type is returned in API payload
        scenario_questions = [q for q in questions if q.get("question_type") == "SCENARIO"]
        assert len(scenario_questions) > 0, "Non-technical diagnostic must include SCENARIO questions"

        # 4. Submit answers for scoring
        # Submit correct answers (from DB)
        db = SessionLocal()
        sub_answers = []
        for q in questions:
            db_q = db.query(DiagnosticQuestion).filter(DiagnosticQuestion.id == q["question_id"]).first()
            sub_answers.append({"question_id": q["question_id"], "selected_option": db_q.correct_option})
        db.close()

        sub_resp = client.post(
            f"/api/v1/diagnostic/{diag_id}/submit",
            json={"answers": sub_answers},
            headers=headers
        )
        assert sub_resp.status_code == 200
        sub_data = sub_resp.json()
        assert sub_data["status"] in ("PASSED", "COMPLETED")
        assert "overall" in sub_data
        assert sub_data["overall"]["weighted_percent"] > 0
        assert len(sub_data["competencies"]) > 0

    finally:
        _cleanup(email)


def test_courses_search_and_filter_api():
    """Verify search, category filtering, and estimated_hours in GET /api/v1/courses."""
    email = _unique_email("courses_search")
    try:
        token = _register_and_get_token(email)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. All courses
        all_res = client.get("/api/v1/courses", headers=headers)
        assert all_res.status_code == 200
        courses = all_res.json()
        assert len(courses) >= 6
        assert all("estimated_hours" in c for c in courses)

        # 2. Category filter
        tech_res = client.get("/api/v1/courses?category=TECHNICAL", headers=headers)
        assert tech_res.status_code == 200
        tech_courses = tech_res.json()
        assert len(tech_courses) >= 3
        assert all(c["category"] == "TECHNICAL" for c in tech_courses)

        non_tech_res = client.get("/api/v1/courses?category=NON_TECHNICAL", headers=headers)
        assert non_tech_res.status_code == 200
        non_tech_courses = non_tech_res.json()
        assert len(non_tech_courses) >= 3
        assert all(c["category"] == "NON_TECHNICAL" for c in non_tech_courses)

        # 3. Search query
        search_res = client.get("/api/v1/courses?search=Python", headers=headers)
        assert search_res.status_code == 200
        matched = search_res.json()
        assert len(matched) >= 1
        assert any("python" in c["name"].lower() for c in matched)

        search_scenario = client.get("/api/v1/courses?search=Communication", headers=headers)
        assert search_scenario.status_code == 200
        matched_comm = search_scenario.json()
        assert len(matched_comm) >= 1
        assert any("communication" in c["name"].lower() for c in matched_comm)

    finally:
        _cleanup(email)
