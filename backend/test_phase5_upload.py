"""
UPSKILL AI - Phase 5 Step 1 Document Upload Verification Test Suite

Tests:
1. Valid PDF file upload & text extraction (HTTP 201).
2. Invalid non-PDF file rejection (HTTP 400).
3. Document metadata & extracted text database persistence.
"""

import sys
import os
import io
import pymupdf as fitz  # PyMuPDF
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models import Document
from auth_test_utils import AuthenticatedClient

client = AuthenticatedClient()

def create_sample_pdf_bytes(text: str = "Official Statistics and Survey Methodology sample test document.") -> bytes:
    """Helper to generate a minimal valid PDF in memory using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_pdf_upload_success():
    print("Testing POST /api/v1/documents/upload with valid PDF...")
    pdf_bytes = create_sample_pdf_bytes("Statistical Data Analysis and Official Statistics Guidelines 2026.")
    
    files = {
        "file": ("official_stats_guide.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    }
    
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "id" in data
    assert data["filename"] == "official_stats_guide.pdf"
    assert data["content_type"] == "application/pdf"
    assert data["text_length"] > 0
    assert "successfully" in data["message"]
    
    # Verify database persistence
    db = SessionLocal()
    doc_record = db.query(Document).filter(Document.id == data["id"]).first()
    db.close()
    
    assert doc_record is not None
    assert doc_record.filename == "official_stats_guide.pdf"
    assert "Official Statistics Guidelines 2026" in doc_record.extracted_text
    print(f"[OK] PDF Upload & text extraction passed (Doc ID {data['id']}, text_length: {data['text_length']})")

def test_non_pdf_upload_failure():
    print("Testing POST /api/v1/documents/upload with invalid non-PDF file...")
    files = {
        "file": ("notes.txt", io.BytesIO(b"Plain text content"), "text/plain")
    }
    
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]
    print("[OK] Invalid non-PDF upload correctly rejected with HTTP 400")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING STATLEARN AI PHASE 5 STEP 1 TEST SUITE")
    print("=" * 60)
    test_pdf_upload_success()
    test_non_pdf_upload_failure()
    print("=" * 60)
    print("ALL PHASE 5 STEP 1 UPLOAD TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
