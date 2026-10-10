"""
UPSKILL AI - Phase 5 Step 2 Document Text Chunking Verification Test Suite

Tests:
1. normalize_extracted_text() joins wrapped single-newline PDF lines
2. normalize_extracted_text() decides genuine paragraph/heading/list boundaries
3. chunk_text() paragraph preference (deterministic, no mid-paragraph splits)
4. chunk_text() oversized-paragraph splitting (no chunk exceeds target_max_words)
5. chunk_text() small / empty / whitespace-only input
6. PDF upload produces genuinely multi-chunk text, persisted in strict order,
   with wrapped lines normalized away
7. GET /api/v1/documents/{document_id}/chunks round-trips the persisted chunks
8. GET /api/v1/documents/{invalid_id}/chunks returns HTTP 404

NOTE: the PDF fixture writes wrapped text via insert_textbox(). Using
insert_text() with one long line clips text off the page, which silently
reduces a "1800 word" fixture to a few dozen words and makes multi-chunk
assertions pass vacuously.
"""

import sys
import os
import io
import re
import pymupdf as fitz  # PyMuPDF
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models import Document, DocumentChunk
from app.routes.documents import chunk_text, normalize_extracted_text
from auth_test_utils import AuthenticatedClient

client = AuthenticatedClient()

TARGET_MAX_WORDS = 1500

# A "\n" that is not part of a "\n\n" paragraph separator, i.e. a leftover
# wrapped line break.
_WRAP_NEWLINE_RE = re.compile(r"(?<!\n)\n(?!\n)")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def words(n: int, prefix: str = "token") -> str:
    return " ".join(f"{prefix}_{i}" for i in range(n))


def build_wrapped_pdf(pages: int = 6, words_per_page: int = 500) -> bytes:
    """Generate a PDF whose text is wrapped inside the page box, so all of it
    survives PyMuPDF text extraction."""
    doc = fitz.open()
    for p in range(pages):
        page = doc.new_page()
        rc = page.insert_textbox(
            fitz.Rect(36, 36, 559, 806), words(words_per_page, f"p{p}"), fontsize=9
        )
        assert rc >= 0, f"fixture paragraph too large for page box (returned {rc})"
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def assert_words_preserved(text: str, chunks) -> None:
    """No chunking strategy may drop or duplicate words, or reorder them."""
    flat = [w for c in chunks for w in c.split()]
    assert flat == text.split(), "chunking dropped, duplicated or reordered words"


def assert_no_wrapped_newlines(text: str) -> None:
    """Normalized text may only contain "\n\n" paragraph separators."""
    assert not _WRAP_NEWLINE_RE.search(text), (
        "text still contains a bare line break, so wrapped PDF lines were not "
        f"re-joined into a paragraph: {text[:120]!r}"
    )


# ------------------------------------------------------------------
# normalize_extracted_text() unit coverage
# ------------------------------------------------------------------

def test_normalization_joins_wrapped_lines():
    print("Testing normalize_extracted_text() joins wrapped lines...")
    raw = (
        "Statistical methods are used\n"
        "across many domains and\n"
        "applied widely.\n"
        "\n"
        "Data quality matters\n"
        "for every analysis."
    )

    normalized = normalize_extracted_text(raw)

    assert normalized == (
        "Statistical methods are used across many domains and applied widely.\n\n"
        "Data quality matters for every analysis."
    ), normalized
    assert_no_wrapped_newlines(normalized)
    assert_words_preserved(raw, [normalized])

    # A document with no blank lines at all collapses into one paragraph
    # rather than one paragraph per wrapped line.
    no_blank_lines = "\n".join(words(40, f"line{i}") for i in range(5))
    collapsed = normalize_extracted_text(no_blank_lines)
    assert collapsed == no_blank_lines.replace("\n", " ")
    assert "\n\n" not in collapsed

    print("[OK] Wrapped lines joined into continuous paragraphs")


def test_normalization_preserves_real_boundaries():
    print("Testing normalize_extracted_text() keeps genuine boundaries...")
    raw = (
        "INTRODUCTION\n"
        "This section describes the methods\n"
        "used in the study.\n"
        "\n"
        "Data Quality\n"
        "- First item\n"
        "- Second item"
    )

    normalized = normalize_extracted_text(raw)

    assert normalized == (
        "INTRODUCTION\n\n"
        "This section describes the methods used in the study.\n\n"
        "Data Quality\n\n"
        "- First item\n\n"
        "- Second item"
    ), normalized
    assert_no_wrapped_newlines(normalized)
    assert_words_preserved(raw, [normalized])

    # Blank lines, CRLF line endings and runs of spaces are all handled.
    assert normalize_extracted_text("") == ""
    assert normalize_extracted_text("   \n\n  \t ") == ""
    assert normalize_extracted_text("alpha\r\nbeta") == "alpha beta"
    assert normalize_extracted_text("spaced   out\ntext   here") == "spaced out text here"

    print("[OK] Headings, list items and blank lines preserved as boundaries")


# ------------------------------------------------------------------
# chunk_text() unit coverage
# ------------------------------------------------------------------

def test_paragraph_preference():
    print("Testing chunk_text() paragraph preference...")
    paragraphs = [words(120, f"para{i}") for i in range(15)]  # 1800 words
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text)

    assert len(chunks) == 2, f"expected 2 chunks, got {len(chunks)}"
    assert [len(c.split()) for c in chunks] == [1440, 360]
    assert_words_preserved(text, chunks)

    # Every chunk must be built from whole paragraphs - never a partial one.
    for chunk in chunks:
        for piece in chunk.split("\n\n"):
            assert piece in paragraphs, "chunk split a paragraph mid-way"

    print(f"[OK] Paragraph preference honored (chunk words: {[len(c.split()) for c in chunks]})")


def test_oversized_paragraph_is_split():
    print("Testing chunk_text() oversized paragraph splitting...")
    # A huge paragraph arriving after buffered text used to bypass the split
    # branch (guarded by `not current_paragraphs`) and emit a 4000-word chunk.
    paragraphs = [words(1000, "small"), words(4000, "huge")]
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text)

    assert [len(c.split()) for c in chunks] == [1000, 1500, 1500, 1000]
    assert all(len(c.split()) <= TARGET_MAX_WORDS for c in chunks), \
        f"chunk exceeded {TARGET_MAX_WORDS} words: {[len(c.split()) for c in chunks]}"
    assert_words_preserved(text, chunks)

    # Same must hold for a lone oversized paragraph.
    lone = chunk_text(words(4000))
    assert [len(c.split()) for c in lone] == [1500, 1500, 1000]
    assert all(len(c.split()) <= TARGET_MAX_WORDS for c in lone)

    print("[OK] Oversized paragraphs split, no chunk exceeds "
          f"{TARGET_MAX_WORDS} words")


def test_small_and_empty_documents():
    print("Testing chunk_text() small / empty input...")
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []

    small = chunk_text(words(50))
    assert len(small) == 1 and len(small[0].split()) == 50

    # Wrapped single-newline input is re-joined, so it yields one paragraph
    # (one chunk) instead of one tiny paragraph per line.
    wrapped = "\n".join(words(40, f"l{i}") for i in range(5))
    joined = chunk_text(wrapped)
    assert len(joined) == 1
    assert joined[0] == wrapped.replace("\n", " ")

    print("[OK] Small documents yield a single chunk, empty input yields none")


# ------------------------------------------------------------------
# Upload + retrieval integration coverage
# ------------------------------------------------------------------

def test_chunk_creation_and_retrieval():
    print("Testing PDF upload with chunk generation and GET /api/v1/documents/{id}/chunks...")
    pdf_bytes = build_wrapped_pdf(pages=6, words_per_page=500)  # ~3000 words

    files = {
        "file": ("statistical_methodology_chunk_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    }

    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 201, f"Expected 201, got {upload_res.status_code}: {upload_res.text}"

    upload_data = upload_res.json()
    doc_id = upload_data["id"]
    assert upload_data["total_chunks"] >= 2, (
        "fixture produced a single chunk, so multi-chunk ordering is not being "
        f"exercised (text_length: {upload_data['text_length']})"
    )

    # Query database directly to verify chunk ordering and persistence
    db = SessionLocal()
    db_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )
    doc_row = db.query(Document).filter(Document.id == doc_id).first()
    extracted_text = doc_row.extracted_text
    db.close()

    # The fixture must really contain wrapped single-newline lines, otherwise
    # the normalization path is not exercised at all.
    assert _WRAP_NEWLINE_RE.search(extracted_text), \
        "fixture produced no wrapped lines, so normalization is not exercised"

    assert len(db_chunks) == upload_data["total_chunks"]
    # Check strict chunk ordering (0, 1, 2, ...)
    for idx, chunk in enumerate(db_chunks):
        assert chunk.chunk_index == idx
        assert len(chunk.text) > 0
        # Wrapped lines must have been re-joined before chunking.
        assert_no_wrapped_newlines(chunk.text)
        assert len(chunk.text.split()) <= TARGET_MAX_WORDS
    assert_words_preserved(extracted_text, [c.text for c in db_chunks])

    # Query GET /api/v1/documents/{document_id}/chunks endpoint
    get_res = client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert get_res.status_code == 200, f"Expected 200, got {get_res.status_code}: {get_res.text}"

    get_data = get_res.json()
    assert get_data["document_id"] == doc_id
    assert get_data["total_chunks"] == len(db_chunks)
    assert len(get_data["chunks"]) == len(db_chunks)

    # Verify retrieved chunk fields, order, and exact text round-trip
    for idx, chunk in enumerate(get_data["chunks"]):
        assert "id" in chunk
        assert chunk["chunk_index"] == idx
        assert "text" in chunk
        assert len(chunk["text"]) > 0
        assert chunk["id"] == db_chunks[idx].id
        assert chunk["text"] == db_chunks[idx].text

    print(f"[OK] Chunk creation, ordering & retrieval passed "
          f"(Doc ID {doc_id}, total_chunks: {get_data['total_chunks']}, "
          f"chunk words: {[len(c['text'].split()) for c in get_data['chunks']]})")


def test_invalid_document_id_chunks():
    print("Testing GET /api/v1/documents/{invalid_id}/chunks...")
    invalid_id = 9999999
    response = client.get(f"/api/v1/documents/{invalid_id}/chunks")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    detail = response.json()["detail"]
    assert "not found" in detail.lower()
    print("[OK] Invalid document ID correctly returns 404 response")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING STATLEARN AI PHASE 5 STEP 2 CHUNKING TEST SUITE")
    print("=" * 60)
    test_normalization_joins_wrapped_lines()
    test_normalization_preserves_real_boundaries()
    test_paragraph_preference()
    test_oversized_paragraph_is_split()
    test_small_and_empty_documents()
    test_chunk_creation_and_retrieval()
    test_invalid_document_id_chunks()
    print("=" * 60)
    print("ALL PHASE 5 STEP 2 CHUNKING TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
