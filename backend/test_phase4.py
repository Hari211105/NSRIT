"""
UPSKILL AI - Phase 4 Verification Test Suite

Tests:
1. Database seeding and idempotency.
2. Learning Resource model & catalog query.
3. Recommendation Engine algorithm scoring, reason generation, and ranking.
4. Competencies with gap <= 0 do NOT generate recommendations.
5. Exact API endpoint responses:
   - GET /api/v1/health
   - GET /api/v1/roles
   - GET /api/v1/competencies
   - GET /api/v1/roles/1/competencies
   - GET /api/v1/me
   - GET /api/v1/me/competencies
   - GET /api/v1/me/gaps
   - GET /api/v1/catalog/resources
   - GET /api/v1/me/recommendations
"""

import sys
import os
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database import SessionLocal
from app.seed import seed_demo_data
from app.models import LearningResource
from auth_test_utils import AuthenticatedClient

client = AuthenticatedClient()

def test_health():
    print("Testing GET /api/v1/health...")
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("[OK] Health check passed")

def test_existing_endpoints():
    print("Testing existing Phase 1-3 endpoints...")
    assert client.get("/api/v1/roles").status_code == 200
    assert client.get("/api/v1/competencies").status_code == 200
    assert client.get("/api/v1/roles/1/competencies").status_code == 200
    assert client.get("/api/v1/me").status_code == 200
    assert client.get("/api/v1/me/competencies").status_code == 200
    assert client.get("/api/v1/me/gaps").status_code == 200
    print("[OK] Existing endpoints passed")

def test_idempotent_seeding():
    print("Testing seeding idempotency...")
    db = SessionLocal()
    count_before = db.query(LearningResource).count()
    db.close()

    # Re-run seed
    seed_demo_data()

    db = SessionLocal()
    count_after = db.query(LearningResource).count()
    db.close()

    assert count_before == count_after, f"Expected {count_before} resources, got {count_after}"
    assert count_after >= 16, f"Expected at least 16 resources, got {count_after}"
    print(f"[OK] Seeding is idempotent ({count_after} resources present)")

def test_catalog_api():
    print("Testing GET /api/v1/catalog/resources...")
    response = client.get("/api/v1/catalog/resources")
    assert response.status_code == 200
    data = response.json()
    assert "resources" in data
    assert data["total"] >= 16
    first_res = data["resources"][0]
    assert "is_demo" in first_res
    assert first_res["is_demo"] is True
    assert first_res["source"] in ["IGOT_DEMO", "NSSTA_TPAC_DEMO"]
    print(f"[OK] Catalog API returned {data['total']} resources successfully")

def test_recommendations_api():
    print("Testing GET /api/v1/me/recommendations...")
    response = client.get("/api/v1/me/recommendations")
    assert response.status_code == 200
    data = response.json()
    
    assert "learner" in data
    assert "summary" in data
    assert "recommendations" in data

    recs = data["recommendations"]
    summary = data["summary"]

    assert summary["total_recommendations"] == len(recs)
    assert len(recs) > 0

    # Verify Data Visualization (gap <= 0) has NO recommendations
    dv_recs = [r for r in recs if r["competency_name"] == "Data Visualization"]
    assert len(dv_recs) == 0, "Competencies with gap <= 0 must not receive recommendations"
    print("[OK] Zero-gap filtering verified (Data Visualization correctly excluded)")

    # Verify ranking, priority, and reason format
    prev_priority_idx = -1
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    
    for idx, r in enumerate(recs, start=1):
        assert r["rank"] == idx
        curr_p_idx = priority_order[r["priority"]]
        assert curr_p_idx >= prev_priority_idx, "Recommendations must be sorted by priority (CRITICAL > HIGH > MEDIUM)"
        prev_priority_idx = curr_p_idx
        
        # Verify reason contains competency and level information
        assert r["competency_name"] in r["reason"]
        assert f"Level {r['current_level']}" in r["reason"]
        assert f"Level {r['required_level']}" in r["reason"]
        assert r["learning_resource"]["is_demo"] is True

    print("[OK] Priority ordering, rank assignment, and dynamic reason generation verified")

def test_gap_analysis_rules():
    print("Testing GET /api/v1/me/gaps calculation and status rules...")
    response = client.get("/api/v1/me/gaps")
    assert response.status_code == 200
    data = response.json()
    assert "gaps" in data
    assert "summary" in data
    for g in data["gaps"]:
        expected_gap = g["required_level"] - g["current_level"]
        assert g["gap"] == expected_gap
        if g["gap"] >= 2:
            assert g["status"] == "MAJOR_GAP"
        elif g["gap"] == 1:
            assert g["status"] == "MODERATE_GAP"
        elif g["gap"] == 0:
            assert g["status"] == "MEETS_TARGET"
        else:
            assert g["status"] == "ABOVE_TARGET"
    print("[OK] Gap analysis rules and status calculations verified")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING STATLEARN AI PHASE 4 TEST SUITE")
    print("=" * 60)
    test_health()
    test_existing_endpoints()
    test_gap_analysis_rules()
    test_idempotent_seeding()
    test_catalog_api()
    test_recommendations_api()
    print("=" * 60)
    print("ALL PHASE 4 TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
