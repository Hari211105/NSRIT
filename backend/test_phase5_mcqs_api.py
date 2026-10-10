"""
UPSKILL AI - Phase 5 Step 4B MCQ Persistence & API Verification Test Suite

MCQ generation is replaced with an injected fake, so no OpenRouter request is
ever made and no API key is read or used.

Tests:
1. POST /{id}/mcqs/generate persists 5 validated MCQs and returns them with ids
2. Repeating generation for the same chunk reuses stored MCQs (no duplicates)
3. A multi-chunk document advances to the next uncovered chunk, then reuses
4. GET /{id}/mcqs returns stored MCQs, and an empty list when there are none
5. Unknown document returns 404 on both endpoints
6. A document with no chunks returns 400 from generate (and empty from GET)
7. AI service failure -> 502, invalid AI output -> 422, nothing persisted
"""

import sys
import os
import io
import contextlib
import pymupdf as fitz  # PyMuPDF
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models import Document, GeneratedMCQ
from app.services import ai_service, mcq_service
from auth_test_utils import AuthenticatedClient

client = AuthenticatedClient()

MCQ_COUNT = 5


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def build_wrapped_pdf(pages: int = 1, words_per_page: int = 50) -> bytes:
    """PDF whose text wraps inside the page box, so extraction keeps it all."""
    doc = fitz.open()
    for p in range(pages):
        page = doc.new_page()
        text = " ".join(f"p{p}_token{i}" for i in range(words_per_page))
        rc = page.insert_textbox(fitz.Rect(36, 36, 559, 806), text, fontsize=9)
        assert rc >= 0, f"fixture text too large for one page (returned {rc})"
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def upload_document(name: str, pages: int = 1, words_per_page: int = 50) -> int:
    files = {"file": (name, io.BytesIO(build_wrapped_pdf(pages, words_per_page)),
                      "application/pdf")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201, f"upload failed: {response.status_code} {response.text}"
    return response.json()["id"]


def build_question(index: int, chunk_id: int) -> dict:
    return {
        "question": f"Question {index + 1} for chunk {chunk_id}?",
        "options": [f"Chunk{chunk_id} choice {index + 1}{letter}" for letter in "ABCD"],
        "correct_option": index % 4,
        "explanation": f"Explanation {index + 1} grounded in chunk {chunk_id}.",
        "source_chunk_id": chunk_id,
    }


@contextlib.contextmanager
def fake_generation(error=None):
    """
    Replace mcq_service.generate_mcqs for the duration of the block.
    Records each call and returns a valid 5-question payload echoing the
    chunk id it was given, exactly as the real service would.
    """
    calls = []

    def fake_generate(chunk_text, source_chunk_id, **kwargs):
        calls.append({
            "chunk_text": chunk_text,
            "source_chunk_id": source_chunk_id,
            "kwargs": kwargs,
        })
        if error is not None:
            raise error
        return [
            build_question(index, source_chunk_id) for index in range(MCQ_COUNT)
        ]

    original = mcq_service.generate_mcqs
    mcq_service.generate_mcqs = fake_generate
    try:
        yield calls
    finally:
        mcq_service.generate_mcqs = original


def stored_mcqs(document_id: int):
    db = SessionLocal()
    try:
        rows = (
            db.query(GeneratedMCQ)
            .filter(GeneratedMCQ.document_id == document_id)
            .order_by(GeneratedMCQ.id.asc())
            .all()
        )
        return [
            {
                "id": row.id,
                "source_chunk_id": row.source_chunk_id,
                "question": row.question,
                "options": row.options,
                "correct_option": row.correct_option,
                "explanation": row.explanation,
            }
            for row in rows
        ]
    finally:
        db.close()


# ------------------------------------------------------------------
# 1. Generation and persistence
# ------------------------------------------------------------------

def test_generate_and_persist():
    print("Testing successful generation and persistence...")
    doc_id = upload_document("mcq_single_chunk.pdf")

    with fake_generation() as calls:
        response = client.post(
            f"/api/v1/documents/{doc_id}/mcqs/generate",
            params={"competency_context": "Survey Methodology"},
        )

    assert response.status_code == 201, f"{response.status_code}: {response.text}"
    data = response.json()
    assert data["document_id"] == doc_id
    assert data["generated"] is True
    assert data["total_mcqs"] == MCQ_COUNT
    assert len(data["mcqs"]) == MCQ_COUNT

    chunk_ids = {mcq["source_chunk_id"] for mcq in data["mcqs"]}
    assert len(chunk_ids) == 1, "all questions must come from one chunk"
    assert chunk_ids == {data["source_chunk_id"]}

    for mcq in data["mcqs"]:
        assert isinstance(mcq["id"], int), "each MCQ must be returned with an id"
        assert mcq["question"]
        assert len(mcq["options"]) == 4, "options must survive the JSON round-trip"
        assert mcq["correct_option"] in (0, 1, 2, 3)
        assert mcq["explanation"]
        assert mcq["created_at"]

    # Exactly one AI call, made through mcq_service with the chunk's text.
    assert len(calls) == 1, f"expected 1 generation call, got {len(calls)}"
    assert calls[0]["source_chunk_id"] == data["source_chunk_id"]
    assert calls[0]["chunk_text"].strip(), "chunk text must be passed to the service"
    assert calls[0]["kwargs"].get("competency_context") == "Survey Methodology"

    # Rows really are in the database, with options stored as JSON.
    rows = stored_mcqs(doc_id)
    assert len(rows) == MCQ_COUNT, f"expected {MCQ_COUNT} stored rows, got {len(rows)}"
    for row in rows:
        assert row["options"].startswith("["), "options must be stored as JSON"
        assert row["question"]

    print(f"[OK] {MCQ_COUNT} MCQs generated once, persisted and returned with ids")


# ------------------------------------------------------------------
# 2-3. Idempotency across repeated calls
# ------------------------------------------------------------------

def test_repeated_generation_reuses_existing():
    print("Testing repeated generation for the same chunk...")
    doc_id = upload_document("mcq_repeat.pdf")

    with fake_generation() as calls:
        first = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")
        second = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")
        third = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")

    assert first.status_code == 201, first.text
    assert second.status_code == 200, f"reuse must not be a 201: {second.text}"
    assert third.status_code == 200, third.text

    assert len(calls) == 1, f"expected the AI to be called once, got {len(calls)}"
    assert second.json()["generated"] is False
    assert third.json()["generated"] is False

    first_ids = [mcq["id"] for mcq in first.json()["mcqs"]]
    assert [mcq["id"] for mcq in second.json()["mcqs"]] == first_ids
    assert [mcq["id"] for mcq in third.json()["mcqs"]] == first_ids

    assert len(stored_mcqs(doc_id)) == MCQ_COUNT, "repeated calls duplicated rows"
    print("[OK] Repeated calls reused stored MCQs without duplicates or extra AI calls")


def test_multi_chunk_progression():
    print("Testing multi-chunk progression...")
    doc_id = upload_document("mcq_multi_chunk.pdf", pages=6, words_per_page=500)

    with fake_generation() as calls:
        first = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")
        second = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")
        third = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")

    assert first.status_code == 201 and second.status_code == 201, "each new chunk generates"
    assert third.status_code == 200, "all chunks covered, so questions are reused"

    chunk_ids = [first.json()["source_chunk_id"], second.json()["source_chunk_id"]]
    assert chunk_ids[0] != chunk_ids[1], "the second call must use a different chunk"
    assert len(calls) == 2, f"expected 2 AI calls (one per chunk), got {len(calls)}"

    rows = stored_mcqs(doc_id)
    assert len(rows) == 2 * MCQ_COUNT, f"expected {2 * MCQ_COUNT} rows, got {len(rows)}"
    assert len({row["id"] for row in rows}) == len(rows), "duplicate rows created"
    assert third.json()["generated"] is False
    assert len(stored_mcqs(doc_id)) == 2 * MCQ_COUNT, "the reuse call added rows"
    assert third.json()["source_chunk_id"] == first.json()["source_chunk_id"]

    print("[OK] One chunk per call, then reuse once every chunk is covered")


# ------------------------------------------------------------------
# 4-5. Retrieval and unknown documents
# ------------------------------------------------------------------

def test_get_stored_mcqs():
    print("Testing GET /api/v1/documents/{id}/mcqs...")
    doc_id = upload_document("mcq_get.pdf")

    # Before generating: empty list, not an error.
    empty = client.get(f"/api/v1/documents/{doc_id}/mcqs")
    assert empty.status_code == 200, empty.text
    assert empty.json()["total_mcqs"] == 0
    assert empty.json()["mcqs"] == []

    with fake_generation():
        created = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")

    response = client.get(f"/api/v1/documents/{doc_id}/mcqs")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["document_id"] == doc_id
    assert data["total_mcqs"] == MCQ_COUNT
    assert [mcq["id"] for mcq in data["mcqs"]] == \
        [mcq["id"] for mcq in created.json()["mcqs"]], "GET must return the same rows, in order"
    for mcq in data["mcqs"]:
        assert mcq["document_id"] == doc_id
        assert len(mcq["options"]) == 4
        assert mcq["correct_option"] in (0, 1, 2, 3)
        assert mcq["explanation"]

    print("[OK] Stored MCQs retrieved (and empty list for a document with none)")


def test_document_not_found():
    print("Testing unknown documents...")
    missing = 9999999

    with fake_generation() as calls:
        generate = client.post(f"/api/v1/documents/{missing}/mcqs/generate")
        fetch = client.get(f"/api/v1/documents/{missing}/mcqs")

    assert generate.status_code == 404, f"expected 404, got {generate.status_code}"
    assert fetch.status_code == 404, f"expected 404, got {fetch.status_code}"
    assert "not found" in generate.json()["detail"].lower()
    assert "not found" in fetch.json()["detail"].lower()
    assert calls == [], "the AI must not be called for an unknown document"

    print("[OK] Unknown document returns 404 on both endpoints")


# ------------------------------------------------------------------
# 6. Document without chunks
# ------------------------------------------------------------------

def test_document_without_chunks():
    print("Testing a document with no chunks...")
    db = SessionLocal()
    try:
        doc = Document(
            filename="no_chunks.pdf",
            content_type="application/pdf",
            extracted_text="Text that was never chunked.",
            normalized_text="Text that was never chunked.",
            created_at="2026-01-01T00:00:00",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id
    finally:
        db.close()

    with fake_generation() as calls:
        response = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")

    assert response.status_code == 400, f"expected 400, got {response.status_code}"
    assert "no text chunks" in response.json()["detail"]
    assert calls == [], "the AI must not be called when there are no chunks"
    assert stored_mcqs(doc_id) == [], "nothing may be persisted without chunks"

    fetch = client.get(f"/api/v1/documents/{doc_id}/mcqs")
    assert fetch.status_code == 200 and fetch.json()["total_mcqs"] == 0

    print("[OK] No chunks returns 400 from generate, empty list from GET")


# ------------------------------------------------------------------
# 7. Failure handling
# ------------------------------------------------------------------

def test_generation_failures_are_reported_and_nothing_is_persisted():
    print("Testing generation failures...")
    doc_id = upload_document("mcq_failures.pdf")

    # AI/service failure -> 502
    with fake_generation(error=ai_service.AIServiceError("OpenRouter returned HTTP 401: bad key")):
        upstream = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")

    assert upstream.status_code == 502, f"expected 502, got {upstream.status_code}"
    assert "AI service" in upstream.json()["detail"]
    assert stored_mcqs(doc_id) == [], "nothing may be persisted after an AI failure"

    # Invalid AI output -> 422
    with fake_generation(error=mcq_service.MCQGenerationError("Expected exactly 5 questions, got 4.")):
        invalid = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")

    assert invalid.status_code == 422, f"expected 422, got {invalid.status_code}"
    assert "invalid MCQs" in invalid.json()["detail"]
    assert stored_mcqs(doc_id) == [], "nothing may be persisted after invalid output"

    # Recovery: a later successful call still works on the same document.
    with fake_generation():
        recovered = client.post(f"/api/v1/documents/{doc_id}/mcqs/generate")

    assert recovered.status_code == 201, recovered.text
    assert len(stored_mcqs(doc_id)) == MCQ_COUNT
    assert len(recovered.json()["mcqs"]) == MCQ_COUNT

    print("[OK] AI failure -> 502 and invalid output -> 422, nothing persisted before recovery")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING STATLEARN AI PHASE 5 STEP 4B MCQ API TEST SUITE")
    print("=" * 60)
    test_generate_and_persist()
    test_repeated_generation_reuses_existing()
    test_multi_chunk_progression()
    test_get_stored_mcqs()
    test_document_not_found()
    test_document_without_chunks()
    test_generation_failures_are_reported_and_nothing_is_persisted()
    print("=" * 60)
    print("ALL PHASE 5 STEP 4B MCQ API TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
