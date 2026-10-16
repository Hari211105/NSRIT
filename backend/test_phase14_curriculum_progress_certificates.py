"""
UPSKILL AI - Phase 14 Test Suite: Courses, Curriculum, Progress, Prerequisites & Certificates

Covers:
1. Course enrollment, non-blocking prerequisite warnings.
2. My Courses list with live progress and lesson counts.
3. Curriculum modules & lesson viewing with navigation (prev/next lesson).
4. Lesson completion and deterministic course progress percentage recalculation.
5. Course completion and certificate generation with certificate ID.
6. Optional minimum diagnostic score requirement enforcement for course completion.
7. Prerequisite-aware ordering in recommendations.
8. Trainer curriculum management (add/edit/delete module & lesson, reorder, prerequisites).
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import (
    Course,
    CourseCompetency,
    CourseEnrollment,
    CourseModule,
    CoursePrerequisite,
    DiagnosticAssessment,
    Lesson,
    LessonProgress,
    User,
    Competency,
    LearningResource,
)
from app.security import hash_password, create_access_token

client = TestClient(app)


def get_auth_headers(email: str, account_type: str = "LEARNER", name: str = "Test User"):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                name=name,
                email=email,
                account_type=account_type,
                hashed_password=hash_password("Password@123"),
                is_active=True,
                profile_completed=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token(user_id=user.id)
        return {"Authorization": f"Bearer {token}"}, user.id
    finally:
        db.close()


def test_enrollment_and_prerequisite_warning():
    headers, learner_id = get_auth_headers("learner1@test.local", "LEARNER", "Learner One")
    db = SessionLocal()
    try:
        # Create Prereq Course and Main Course
        prereq = Course(code="PREREQ_101", name="Prerequisite Course", category="TECHNICAL", status="PUBLISHED", active=True)
        main_c = Course(code="MAIN_201", name="Advanced Course", category="TECHNICAL", status="PUBLISHED", active=True)
        db.add_all([prereq, main_c])
        db.commit()
        db.refresh(prereq)
        db.refresh(main_c)

        # Link as prerequisite
        cp = CoursePrerequisite(course_id=main_c.id, prerequisite_course_id=prereq.id)
        db.add(cp)
        db.commit()

        main_id = main_c.id
    finally:
        db.close()

    # Enrolling in main_c before prereq is completed returns warning, but DOES NOT block enrollment
    resp = client.post(f"/api/v1/courses/{main_id}/enroll", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_id"] == main_id
    assert data["status"] == "ENROLLED"
    assert "Prerequisite recommended" in data["warning"]
    assert "Prerequisite Course" in data["unmet_prerequisites"]

    # Verify CourseDetail reflects prerequisite status
    detail_resp = client.get(f"/api/v1/courses/{main_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["is_enrolled"] is True
    assert len(detail["prerequisites"]) == 1
    assert detail["prerequisites"][0]["is_completed"] is False


def test_curriculum_and_lesson_navigation():
    headers, learner_id = get_auth_headers("learner2@test.local", "LEARNER", "Learner Two")
    db = SessionLocal()
    try:
        course = Course(code="CURR_101", name="Curriculum Course", category="TECHNICAL", status="PUBLISHED", active=True)
        db.add(course)
        db.commit()
        db.refresh(course)

        m1 = CourseModule(course_id=course.id, title="Module 1", order=1)
        m2 = CourseModule(course_id=course.id, title="Module 2", order=2)
        db.add_all([m1, m2])
        db.commit()
        db.refresh(m1)
        db.refresh(m2)

        l1 = Lesson(module_id=m1.id, title="Lesson 1.1", lesson_type="TEXT", body="# Lesson 1 Content", order=1, estimated_minutes=10)
        l2 = Lesson(module_id=m1.id, title="Lesson 1.2", lesson_type="LINK", body="https://example.com/guide", order=2, estimated_minutes=15)
        l3 = Lesson(module_id=m2.id, title="Lesson 2.1", lesson_type="VIDEO_URL", body="https://youtube.com/watch?v=123", order=1, estimated_minutes=20)
        db.add_all([l1, l2, l3])
        db.commit()
        db.refresh(l1)
        db.refresh(l2)
        db.refresh(l3)

        course_id = course.id
        l1_id, l2_id, l3_id = l1.id, l2.id, l3.id
    finally:
        db.close()

    # Fetch curriculum
    cur_resp = client.get(f"/api/v1/courses/{course_id}/modules", headers=headers)
    assert cur_resp.status_code == 200
    cur_data = cur_resp.json()
    assert cur_data["total_modules"] == 2
    assert cur_data["total_lessons"] == 3
    assert cur_data["completed_lessons"] == 0

    # Fetch individual lesson and verify linear navigation
    l1_resp = client.get(f"/api/v1/lessons/{l1_id}", headers=headers)
    assert l1_resp.status_code == 200
    l1_data = l1_resp.json()
    assert l1_data["title"] == "Lesson 1.1"
    assert l1_data["lesson_type"] == "TEXT"
    assert l1_data["prev_lesson_id"] is None
    assert l1_data["next_lesson_id"] == l2_id

    l2_resp = client.get(f"/api/v1/lessons/{l2_id}", headers=headers)
    assert l2_resp.status_code == 200
    l2_data = l2_resp.json()
    assert l2_data["prev_lesson_id"] == l1_id
    assert l2_data["next_lesson_id"] == l3_id


def test_lesson_completion_and_course_certificate():
    headers, learner_id = get_auth_headers("learner3@test.local", "LEARNER", "Learner Three")
    db = SessionLocal()
    try:
        course = Course(code="CERT_101", name="Certification Course", category="TECHNICAL", status="PUBLISHED", active=True)
        db.add(course)
        db.commit()
        db.refresh(course)

        m = CourseModule(course_id=course.id, title="Module 1", order=1)
        db.add(m)
        db.commit()
        db.refresh(m)

        l1 = Lesson(module_id=m.id, title="Lesson A", lesson_type="TEXT", body="Body A", order=1)
        l2 = Lesson(module_id=m.id, title="Lesson B", lesson_type="TEXT", body="Body B", order=2)
        db.add_all([l1, l2])
        db.commit()
        db.refresh(l1)
        db.refresh(l2)

        course_id = course.id
        l1_id, l2_id = l1.id, l2.id
    finally:
        db.close()

    # Certificate request before completion should fail (400)
    cert_fail = client.get(f"/api/v1/courses/{course_id}/certificate", headers=headers)
    assert cert_fail.status_code == 400

    # Complete lesson 1: progress should be 50%
    c1_resp = client.post(f"/api/v1/lessons/{l1_id}/complete", headers=headers)
    assert c1_resp.status_code == 200
    c1_data = c1_resp.json()
    assert c1_data["completed"] is True
    assert c1_data["progress_percent"] == 50.0
    assert c1_data["course_status"] == "IN_PROGRESS"
    assert c1_data["is_course_completed"] is False

    # Check My Courses reflects 50%
    my_resp = client.get("/api/v1/courses/my", headers=headers)
    assert my_resp.status_code == 200
    my_courses = my_resp.json()
    target = next((c for c in my_courses if c["course_id"] == course_id), None)
    assert target is not None
    assert target["progress_percent"] == 50.0
    assert target["completed_lessons"] == 1
    assert target["total_lessons"] == 2

    # Complete lesson 2: course reaches 100% and completes
    c2_resp = client.post(f"/api/v1/lessons/{l2_id}/complete", headers=headers)
    assert c2_resp.status_code == 200
    c2_data = c2_resp.json()
    assert c2_data["progress_percent"] == 100.0
    assert c2_data["course_status"] == "COMPLETED"
    assert c2_data["is_course_completed"] is True
    assert c2_data["certificate"] is not None
    assert "UPSKILL-CERT-" in c2_data["certificate"]["certificate_id"]

    # Verify certificate endpoint returns 200 and matches
    cert_resp = client.get(f"/api/v1/courses/{course_id}/certificate", headers=headers)
    assert cert_resp.status_code == 200
    cert = cert_resp.json()
    assert cert["recipient_name"] == "Learner Three"
    assert cert["course_name"] == "Certification Course"
    assert cert["status"] == "VERIFIED"


def test_min_diagnostic_score_completion_gate():
    headers, learner_id = get_auth_headers("learner4@test.local", "LEARNER", "Learner Four")
    db = SessionLocal()
    try:
        # Course with minimum diagnostic score of 70% required
        course = Course(
            code="DIAG_GATE_101",
            name="Rigorous Gated Course",
            category="TECHNICAL",
            status="PUBLISHED",
            active=True,
            min_diagnostic_score=70.0,
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        m = CourseModule(course_id=course.id, title="Module 1", order=1)
        db.add(m)
        db.commit()
        db.refresh(m)

        lesson = Lesson(module_id=m.id, title="Single Lesson", lesson_type="TEXT", body="Content", order=1)
        db.add(lesson)
        db.commit()
        db.refresh(lesson)

        course_id = course.id
        lesson_id = lesson.id
    finally:
        db.close()

    # User completes lesson, but has NOT met diagnostic score 70%
    comp_resp = client.post(f"/api/v1/lessons/{lesson_id}/complete", headers=headers)
    assert comp_resp.status_code == 200
    data = comp_resp.json()
    # Lessons done, but diagnostic score not met -> is_course_completed remains False
    assert data["is_course_completed"] is False
    assert data["course_status"] == "IN_PROGRESS"

    # User takes diagnostic assessment and scores 85%
    db = SessionLocal()
    try:
        diag = DiagnosticAssessment(
            learner_id=learner_id,
            assessment_type="diagnostic",
            total_questions=10,
            total_correct=8,
            score_percent=85.0,
            passed=True,
            status="PASSED",
        )
        db.add(diag)
        db.commit()
    finally:
        db.close()

    # Re-completing / checking triggers completion
    comp_resp2 = client.post(f"/api/v1/lessons/{lesson_id}/complete", headers=headers)
    assert comp_resp2.status_code == 200
    data2 = comp_resp2.json()
    assert data2["is_course_completed"] is True
    assert data2["course_status"] == "COMPLETED"


def test_trainer_curriculum_crud_and_reorder():
    trainer_headers, trainer_id = get_auth_headers("trainer_curr@test.local", "TRAINER", "Trainer Curr")
    other_headers, other_id = get_auth_headers("trainer_other@test.local", "TRAINER", "Other Trainer")

    # Create course
    course_resp = client.post(
        "/api/v1/trainer/courses",
        headers=trainer_headers,
        json={"code": "TRAIN_CURR", "name": "Trainer Authored Course", "category": "TECHNICAL"},
    )
    assert course_resp.status_code == 201
    course_id = course_resp.json()["id"]

    # Other trainer cannot add modules to this course (403)
    mod_forbidden = client.post(
        f"/api/v1/trainer/courses/{course_id}/modules",
        headers=other_headers,
        json={"title": "Unauthorized Module"},
    )
    assert mod_forbidden.status_code == 403

    # Owner trainer adds Module 1 and Module 2
    mod1_resp = client.post(
        f"/api/v1/trainer/courses/{course_id}/modules",
        headers=trainer_headers,
        json={"title": "Introduction Module", "description": "Intro description", "order": 1},
    )
    assert mod1_resp.status_code == 201
    mod1_id = mod1_resp.json()["id"]

    mod2_resp = client.post(
        f"/api/v1/trainer/courses/{course_id}/modules",
        headers=trainer_headers,
        json={"title": "Advanced Module", "description": "Advanced description", "order": 2},
    )
    assert mod2_resp.status_code == 201
    mod2_id = mod2_resp.json()["id"]

    # Owner trainer adds lessons
    l1_resp = client.post(
        f"/api/v1/trainer/modules/{mod1_id}/lessons",
        headers=trainer_headers,
        json={"title": "Lesson 1", "lesson_type": "TEXT", "body": "# Hello", "order": 1, "estimated_minutes": 15},
    )
    assert l1_resp.status_code == 201
    l1_id = l1_resp.json()["id"]

    l2_resp = client.post(
        f"/api/v1/trainer/modules/{mod1_id}/lessons",
        headers=trainer_headers,
        json={"title": "Lesson 2", "lesson_type": "LINK", "body": "https://docs.python.org", "order": 2},
    )
    assert l2_resp.status_code == 201
    l2_id = l2_resp.json()["id"]

    # Reorder lessons: put Lesson 2 first (order 1), Lesson 1 second (order 2)
    reorder_resp = client.post(
        f"/api/v1/trainer/courses/{course_id}/reorder",
        headers=trainer_headers,
        json={
            "modules": [{"id": mod1_id, "order": 2}, {"id": mod2_id, "order": 1}],
            "lessons": [{"id": l1_id, "order": 2}, {"id": l2_id, "order": 1}],
        },
    )
    assert reorder_resp.status_code == 200

    # Fetch curriculum and confirm reordered state
    cur_resp = client.get(f"/api/v1/trainer/courses/{course_id}/curriculum", headers=trainer_headers)
    assert cur_resp.status_code == 200
    modules = cur_resp.json()
    assert modules[0]["id"] == mod2_id  # mod2 now order 1
    assert modules[1]["id"] == mod1_id  # mod1 now order 2
    assert modules[1]["lessons"][0]["id"] == l2_id  # l2 now order 1

    # Edit lesson
    edit_resp = client.put(
        f"/api/v1/trainer/lessons/{l1_id}",
        headers=trainer_headers,
        json={"title": "Updated Lesson 1 Title", "estimated_minutes": 30},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["title"] == "Updated Lesson 1 Title"
    assert edit_resp.json()["estimated_minutes"] == 30

    # Delete lesson
    del_resp = client.delete(f"/api/v1/trainer/lessons/{l2_id}", headers=trainer_headers)
    assert del_resp.status_code == 204


def test_prerequisite_aware_recommendations_ranking():
    headers, learner_id = get_auth_headers("learner_rec@test.local", "LEARNER", "Learner Rec")
    db = SessionLocal()
    try:
        # Create competency
        comp = Competency(name="Data Arch & Pipelines", description="Data Architecture", is_demo=True)
        db.add(comp)
        db.commit()
        db.refresh(comp)

        # Assign learner competency gap (current level 1, required level 3)
        from app.models import LearnerCompetency, Role, RoleCompetency
        role = Role(name="Pipeline Engineer", description="Data Engineering Role", is_demo=True)
        db.add(role)
        db.commit()
        db.refresh(role)

        rcm = RoleCompetency(role_id=role.id, competency_id=comp.id, required_level=3, priority="HIGH")
        db.add(rcm)

        user = db.query(User).filter_by(id=learner_id).first()
        user.role_id = role.id
        user.learning_mode = "ROLE"

        lc = LearnerCompetency(user_id=learner_id, competency_id=comp.id, current_level=1)
        db.add(lc)

        # Create two courses: Base Course and Advanced Course
        base_c = Course(code="BASE_PIPE", name="Base Pipeline Foundations", category="TECHNICAL", status="PUBLISHED", active=True)
        adv_c = Course(code="ADV_PIPE", name="Advanced Streaming Architecture", category="TECHNICAL", status="PUBLISHED", active=True)
        db.add_all([base_c, adv_c])
        db.commit()
        db.refresh(base_c)
        db.refresh(adv_c)

        # Set adv_c prerequisite as base_c
        prereq = CoursePrerequisite(course_id=adv_c.id, prerequisite_course_id=base_c.id)
        db.add(prereq)

        # Create learning resources for the competency
        res_adv = LearningResource(
            title="Advanced Streaming Systems",
            source="SWAYAM_NPTEL_DEMO",
            resource_type="COURSE",
            competency_id=comp.id,
            minimum_level=1,
            maximum_level=4,
            duration_hours=20,
            course_id=adv_c.id,
            active=True,
        )
        res_base = LearningResource(
            title="Base Pipeline Foundations Guide",
            source="SWAYAM_NPTEL_DEMO",
            resource_type="COURSE",
            competency_id=comp.id,
            minimum_level=1,
            maximum_level=3,
            duration_hours=25,
            course_id=base_c.id,
            active=True,
        )
        db.add_all([res_adv, res_base])
        db.commit()

        comp_id = comp.id
        res_adv_id = res_adv.id
        res_base_id = res_base.id
    finally:
        db.close()

    # Query recommendations for learner
    rec_resp = client.get("/api/v1/me/recommendations", headers=headers)
    assert rec_resp.status_code == 200
    recs = rec_resp.json()["recommendations"]

    # Filter to our newly added resources
    target_recs = [r for r in recs if r["competency_id"] == comp_id]
    assert len(target_recs) >= 2

    # Verify that the resource with unmet prerequisite has warning and is ranked after the met prerequisite
    unmet_item = next((r for r in target_recs if r["learning_resource"]["id"] == res_adv_id), None)
    met_item = next((r for r in target_recs if r["learning_resource"]["id"] == res_base_id), None)

    assert unmet_item is not None
    assert unmet_item["has_unmet_prerequisites"] is True
    assert "Base Pipeline Foundations" in unmet_item["unmet_prerequisites"]
    assert "Prerequisite recommended first" in unmet_item["warning"]

    assert met_item is not None
    assert met_item["has_unmet_prerequisites"] is False
    # Ranking: met_item should have a lower rank number (ranked first) than unmet_item
    assert met_item["rank"] < unmet_item["rank"]

