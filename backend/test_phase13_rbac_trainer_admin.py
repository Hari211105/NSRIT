"""
UPSKILL AI - Phase 13 Test Suite: Role-Based Access Control (RBAC), Trainer Studio, and Admin Console.

Verifies:
1. Login and /me include account_type and is_active.
2. Registration cannot escalate account_type (always defaults to LEARNER).
3. Authorization matrix: unauthenticated (401), wrong role (403), correct role (200).
4. Deactivated users cannot log in or use tokens.
5. Learner sees only PUBLISHED courses; cannot see DRAFT courses in listing or detail.
6. Trainer isolation: trainers cannot view, edit, or submit other trainers' courses.
7. Complete Trainer authoring lifecycle: create course, map competency, add questions (MCQ & SCENARIO), submit for review, archive.
8. Admin review workflow: view pending queue, reject with review note, approve for publication.
9. Admin user management (role changes, activate/deactivate), platform stats, and audit logs.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

DEMO_LEARNER_EMAIL = "demo@statlearn.local"
DEMO_LEARNER_PASS = "Demo@12345"

DEMO_TRAINER_EMAIL = "trainer@statlearn.local"
DEMO_TRAINER_PASS = "Trainer@12345"

DEMO_ADMIN_EMAIL = "admin@statlearn.local"
DEMO_ADMIN_PASS = "Admin@12345"


def get_token(email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------
# 1. Login & Token serialization with account_type
# ------------------------------------------------------------------

def test_login_and_me_include_account_type():
    learner_tok = get_token(DEMO_LEARNER_EMAIL, DEMO_LEARNER_PASS)
    trainer_tok = get_token(DEMO_TRAINER_EMAIL, DEMO_TRAINER_PASS)
    admin_tok = get_token(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS)

    # Learner /me
    r_l = client.get("/api/v1/auth/me", headers=auth_headers(learner_tok))
    assert r_l.status_code == 200
    assert r_l.json()["account_type"] == "LEARNER"
    assert r_l.json()["is_active"] is True

    # Trainer /me
    r_t = client.get("/api/v1/auth/me", headers=auth_headers(trainer_tok))
    assert r_t.status_code == 200
    assert r_t.json()["account_type"] == "TRAINER"
    assert r_t.json()["is_active"] is True

    # Admin /me
    r_a = client.get("/api/v1/auth/me", headers=auth_headers(admin_tok))
    assert r_a.status_code == 200
    assert r_a.json()["account_type"] == "ADMIN"
    assert r_a.json()["is_active"] is True


# ------------------------------------------------------------------
# 2. Registration escalation prevention
# ------------------------------------------------------------------

def test_registration_always_creates_learner():
    reg_email = "new_user_attempt@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Sneaky User",
            "email": reg_email,
            "password": "Password123!",
            "account_type": "ADMIN",  # Attempt to escalate
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == reg_email
    assert data["account_type"] == "LEARNER"
    assert data["is_active"] is True


# ------------------------------------------------------------------
# 3. Deactivated user handling
# ------------------------------------------------------------------

def test_deactivated_user_cannot_login_or_access_endpoints():
    user_email = "deactivate_test@example.com"
    r_reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Temp User", "email": user_email, "password": "Password123!"},
    )
    assert r_reg.status_code == 201
    user_id = r_reg.json()["id"]

    # Log in and get token before deactivation
    user_tok = get_token(user_email, "Password123!")
    r_me = client.get("/api/v1/auth/me", headers=auth_headers(user_tok))
    assert r_me.status_code == 200

    # Admin deactivates this user
    admin_tok = get_token(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS)
    r_deact = client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        headers=auth_headers(admin_tok),
        json={"is_active": False},
    )
    assert r_deact.status_code == 200
    assert r_deact.json()["is_active"] is False

    # Existing token fails with 403
    r_me_blocked = client.get("/api/v1/auth/me", headers=auth_headers(user_tok))
    assert r_me_blocked.status_code == 403
    assert "deactivated" in r_me_blocked.json()["detail"].lower()

    # Login fails with 403
    r_login_blocked = client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": "Password123!"},
    )
    assert r_login_blocked.status_code == 403
    assert "deactivated" in r_login_blocked.json()["detail"].lower()

    # Admin reactivates the user
    r_react = client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        headers=auth_headers(admin_tok),
        json={"is_active": True},
    )
    assert r_react.status_code == 200
    assert r_react.json()["is_active"] is True

    # Login succeeds again
    new_tok = get_token(user_email, "Password123!")
    assert new_tok is not None


# ------------------------------------------------------------------
# 4. Authorization Matrix (401 unauth, 403 wrong role, 200 allowed)
# ------------------------------------------------------------------

def test_authorization_matrix():
    learner_tok = get_token(DEMO_LEARNER_EMAIL, DEMO_LEARNER_PASS)
    trainer_tok = get_token(DEMO_TRAINER_EMAIL, DEMO_TRAINER_PASS)
    admin_tok = get_token(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS)

    # 1. Unauthenticated requests -> 401
    assert client.get("/api/v1/trainer/courses").status_code == 401
    assert client.post("/api/v1/trainer/courses", json={}).status_code == 401
    assert client.get("/api/v1/admin/users").status_code == 401
    assert client.get("/api/v1/admin/stats").status_code == 401
    assert client.get("/api/v1/admin/courses/pending").status_code == 401
    assert client.get("/api/v1/admin/audit-logs").status_code == 401

    # 2. Learner calling Trainer endpoints -> 403
    assert client.get("/api/v1/trainer/courses", headers=auth_headers(learner_tok)).status_code == 403
    assert client.post("/api/v1/trainer/courses", headers=auth_headers(learner_tok), json={}).status_code == 403

    # 3. Learner calling Admin endpoints -> 403
    assert client.get("/api/v1/admin/users", headers=auth_headers(learner_tok)).status_code == 403
    assert client.get("/api/v1/admin/stats", headers=auth_headers(learner_tok)).status_code == 403

    # 4. Trainer calling Admin endpoints -> 403
    assert client.get("/api/v1/admin/users", headers=auth_headers(trainer_tok)).status_code == 403
    assert client.get("/api/v1/admin/stats", headers=auth_headers(trainer_tok)).status_code == 403
    assert client.get("/api/v1/admin/courses/pending", headers=auth_headers(trainer_tok)).status_code == 403

    # 5. Correct roles -> 200
    assert client.get("/api/v1/trainer/courses", headers=auth_headers(trainer_tok)).status_code == 200
    assert client.get("/api/v1/trainer/courses", headers=auth_headers(admin_tok)).status_code == 200
    assert client.get("/api/v1/admin/users", headers=auth_headers(admin_tok)).status_code == 200
    assert client.get("/api/v1/admin/stats", headers=auth_headers(admin_tok)).status_code == 200


# ------------------------------------------------------------------
# 5. Course visibility isolation & Trainer isolation
# ------------------------------------------------------------------

def test_course_visibility_and_trainer_isolation():
    trainer_tok = get_token(DEMO_TRAINER_EMAIL, DEMO_TRAINER_PASS)
    learner_tok = get_token(DEMO_LEARNER_EMAIL, DEMO_LEARNER_PASS)
    admin_tok = get_token(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS)

    # Register a second trainer
    t2_email = "trainer2@statlearn.local"
    client.post(
        "/api/v1/auth/register",
        json={"name": "Trainer Two", "email": t2_email, "password": "Password123!"},
    )
    # Admin promotes trainer 2
    r_user = client.get(f"/api/v1/admin/users?search={t2_email}", headers=auth_headers(admin_tok))
    t2_id = r_user.json()["users"][0]["id"]
    client.patch(
        f"/api/v1/admin/users/{t2_id}/role",
        headers=auth_headers(admin_tok),
        json={"account_type": "TRAINER"},
    )
    t2_tok = get_token(t2_email, "Password123!")

    # Trainer 1 creates a course in DRAFT
    r_create = client.post(
        "/api/v1/trainer/courses",
        headers=auth_headers(trainer_tok),
        json={
            "code": "ISOLATION_TEST_01",
            "name": "Isolation Course by Trainer 1",
            "category": "TECHNICAL",
            "estimated_hours": 15,
        },
    )
    assert r_create.status_code == 201
    course_id = r_create.json()["id"]
    assert r_create.json()["status"] == "DRAFT"

    # Learner lists courses: draft course must NOT appear
    r_courses = client.get("/api/v1/courses", headers=auth_headers(learner_tok))
    assert r_courses.status_code == 200
    course_codes = [c["code"] for c in r_courses.json()]
    assert "ISOLATION_TEST_01" not in course_codes

    # Learner attempts to get course detail directly -> 404
    r_detail_l = client.get(f"/api/v1/courses/{course_id}", headers=auth_headers(learner_tok))
    assert r_detail_l.status_code == 404

    # Trainer 2 attempts to get course detail directly -> 404
    r_detail_t2 = client.get(f"/api/v1/courses/{course_id}", headers=auth_headers(t2_tok))
    assert r_detail_t2.status_code == 404

    # Trainer 1 can view their own course detail -> 200
    r_detail_t1 = client.get(f"/api/v1/courses/{course_id}", headers=auth_headers(trainer_tok))
    assert r_detail_t1.status_code == 200

    # Admin can view course detail -> 200
    r_detail_a = client.get(f"/api/v1/courses/{course_id}", headers=auth_headers(admin_tok))
    assert r_detail_a.status_code == 200

    # Trainer 2 attempts to edit Trainer 1's course -> 403
    r_edit_forbidden = client.put(
        f"/api/v1/trainer/courses/{course_id}",
        headers=auth_headers(t2_tok),
        json={"name": "Hacked Course Name"},
    )
    assert r_edit_forbidden.status_code == 403

    # Trainer 2 attempts to submit Trainer 1's course -> 403
    r_submit_forbidden = client.post(
        f"/api/v1/trainer/courses/{course_id}/submit",
        headers=auth_headers(t2_tok),
    )
    assert r_submit_forbidden.status_code == 403


# ------------------------------------------------------------------
# 6. Complete Course Authoring, Review, and Approval Lifecycle
# ------------------------------------------------------------------

def test_course_authoring_and_admin_review_lifecycle():
    trainer_tok = get_token(DEMO_TRAINER_EMAIL, DEMO_TRAINER_PASS)
    learner_tok = get_token(DEMO_LEARNER_EMAIL, DEMO_LEARNER_PASS)
    admin_tok = get_token(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS)

    # 1. Trainer creates course
    c_resp = client.post(
        "/api/v1/trainer/courses",
        headers=auth_headers(trainer_tok),
        json={
            "code": "LIFECYCLE_101",
            "name": "Survey Quality & Data Lifecycle",
            "description": "Comprehensive course on data quality controls.",
            "category": "TECHNICAL",
            "estimated_hours": 30,
        },
    )
    assert c_resp.status_code == 201
    course_id = c_resp.json()["id"]
    assert c_resp.json()["status"] == "DRAFT"

    # 2. Cannot submit without competency mapped -> 400
    r_sub_empty = client.post(
        f"/api/v1/trainer/courses/{course_id}/submit",
        headers=auth_headers(trainer_tok),
    )
    assert r_sub_empty.status_code == 400
    assert "competency" in r_sub_empty.json()["detail"].lower()

    # 3. Map competency
    r_map = client.post(
        f"/api/v1/trainer/courses/{course_id}/competencies",
        headers=auth_headers(trainer_tok),
        json={"competency_id": 1, "required_level": 3, "priority": "HIGH"},
    )
    assert r_map.status_code == 200
    assert r_map.json()["competencies_count"] >= 1

    # 4. Add MCQ question
    r_mcq = client.post(
        f"/api/v1/trainer/courses/{course_id}/questions",
        headers=auth_headers(trainer_tok),
        json={
            "competency_id": 1,
            "question_type": "MCQ",
            "question": "What is the primary indicator of survey sample representation?",
            "options": ["Sample size", "Random sampling frame", "Interviewer bias", "Cost per response"],
            "correct_option": 1,
            "difficulty": "MEDIUM",
            "explanation": "A representative random frame minimizes selection bias.",
        },
    )
    assert r_mcq.status_code == 201
    q_id = r_mcq.json()["id"]
    assert r_mcq.json()["question_type"] == "MCQ"

    # 5. Add Scenario question
    r_scen = client.post(
        f"/api/v1/trainer/courses/{course_id}/questions",
        headers=auth_headers(trainer_tok),
        json={
            "competency_id": 1,
            "question_type": "SCENARIO",
            "question": "An enumerator notices discrepant rural household data during field checks. What immediate step is required?",
            "options": ["Discard the records", "Conduct re-enumeration verification", "Estimate missing figures", "Notify press"],
            "correct_option": 1,
            "difficulty": "HARD",
            "explanation": "Field re-enumeration ensures authoritative data audit.",
        },
    )
    assert r_scen.status_code == 201
    assert r_scen.json()["question_type"] == "SCENARIO"

    # List questions
    r_qlist = client.get(
        f"/api/v1/trainer/courses/{course_id}/questions",
        headers=auth_headers(trainer_tok),
    )
    assert r_qlist.status_code == 200
    assert len(r_qlist.json()) == 2

    # 6. Submit course for review
    r_submit = client.post(
        f"/api/v1/trainer/courses/{course_id}/submit",
        headers=auth_headers(trainer_tok),
    )
    assert r_submit.status_code == 200
    assert r_submit.json()["status"] == "PENDING_REVIEW"

    # Cannot edit while pending review
    r_edit_pending = client.put(
        f"/api/v1/trainer/courses/{course_id}",
        headers=auth_headers(trainer_tok),
        json={"name": "Attempted Edit"},
    )
    assert r_edit_pending.status_code == 400

    # 7. Admin views pending queue
    r_pending = client.get("/api/v1/admin/courses/pending", headers=auth_headers(admin_tok))
    assert r_pending.status_code == 200
    pending_ids = [c["id"] for c in r_pending.json()]
    assert course_id in pending_ids

    # 8. Admin rejects with review note
    r_reject = client.post(
        f"/api/v1/admin/courses/{course_id}/reject",
        headers=auth_headers(admin_tok),
        json={"note": "Please expand the course description and add one more scenario."},
    )
    assert r_reject.status_code == 200
    assert r_reject.json()["status"] == "DRAFT"
    assert "expand the course" in r_reject.json()["review_note"]

    # 9. Trainer sees review note, updates course description, and resubmits
    r_update = client.put(
        f"/api/v1/trainer/courses/{course_id}",
        headers=auth_headers(trainer_tok),
        json={"description": "Expanded comprehensive course covering rural/urban survey standards."},
    )
    assert r_update.status_code == 200

    r_resubmit = client.post(
        f"/api/v1/trainer/courses/{course_id}/submit",
        headers=auth_headers(trainer_tok),
    )
    assert r_resubmit.status_code == 200
    assert r_resubmit.json()["status"] == "PENDING_REVIEW"

    # 10. Admin approves course
    r_approve = client.post(
        f"/api/v1/admin/courses/{course_id}/approve",
        headers=auth_headers(admin_tok),
    )
    assert r_approve.status_code == 200
    assert r_approve.json()["status"] == "PUBLISHED"

    # 11. Now course is visible to learners everywhere
    r_learner_list = client.get("/api/v1/courses", headers=auth_headers(learner_tok))
    assert r_learner_list.status_code == 200
    published_codes = [c["code"] for c in r_learner_list.json()]
    assert "LIFECYCLE_101" in published_codes

    r_learner_detail = client.get(f"/api/v1/courses/{course_id}", headers=auth_headers(learner_tok))
    assert r_learner_detail.status_code == 200
    assert r_learner_detail.json()["code"] == "LIFECYCLE_101"

    # 12. Trainer can archive course
    r_archive = client.post(
        f"/api/v1/trainer/courses/{course_id}/archive",
        headers=auth_headers(trainer_tok),
    )
    assert r_archive.status_code == 200
    assert r_archive.json()["status"] == "ARCHIVED"


# ------------------------------------------------------------------
# 7. Admin Platform Stats & Audit Logs
# ------------------------------------------------------------------

def test_admin_stats_and_audit_logs():
    admin_tok = get_token(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASS)

    # 1. Platform stats
    r_stats = client.get("/api/v1/admin/stats", headers=auth_headers(admin_tok))
    assert r_stats.status_code == 200
    stats = r_stats.json()
    assert "total_users" in stats
    assert "learners_count" in stats
    assert "trainers_count" in stats
    assert "admins_count" in stats
    assert "published_courses" in stats
    assert stats["total_users"] >= 3

    # 2. Audit logs
    r_logs = client.get("/api/v1/admin/audit-logs", headers=auth_headers(admin_tok))
    assert r_logs.status_code == 200
    logs = r_logs.json()
    assert isinstance(logs, list)
    # Check that previous approve/reject actions generated logs
    actions = [l["action"] for l in logs]
    assert any(a in actions for a in ["COURSE_APPROVE", "COURSE_REJECT", "ROLE_CHANGE", "USER_STATUS_CHANGE"])
