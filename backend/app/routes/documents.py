"""
UPSKILL AI - Document Upload, Text Extraction & Chunking API (Phase 5)
POST /api/v1/documents/upload
GET  /api/v1/documents/{document_id}
GET  /api/v1/documents/{document_id}/chunks
POST /api/v1/documents/{document_id}/mcqs/generate
GET  /api/v1/documents/{document_id}/mcqs
GET  /api/v1/documents/{document_id}/quiz
POST /api/v1/documents/{document_id}/quiz/submit
"""

import json
import re
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StrictInt
from sqlalchemy.orm import Session
import pymupdf as fitz  # PyMuPDF

from app.database import get_db
from app.models import (
    Competency,
    Document,
    DocumentChunk,
    GeneratedMCQ,
    LearnerCompetency,
    QuizAssessment,
    RoleCompetency,
    User,
)
from app.routes.auth import get_current_user
from app.services import (
    ai_service,
    competency_evidence_service,
    mcq_service,
    quiz_service,
)
from app.services.competency_evidence_service import CompetencyEvidenceError

router = APIRouter(prefix="/documents", tags=["Documents"])


# ------------------------------------------------------------------
# Lightweight, deterministic normalization of PDF-extracted text
# ------------------------------------------------------------------

# A line starting with a bullet or enumerator is its own logical paragraph:
# "- item", "* item", "1. item", "2) item", "a) item", "iv) item".
_MARKER_LINE_RE = re.compile(r"^(?:[-*•‣·]|\(?\d{1,3}[.)]|\(?[a-zA-Z][.)])\s+\S")

# Short lines made only of capitalised/uppercase words are treated as headings
# ("Introduction", "Data Quality", "METHODOLOGY", "Overview:").
_MAX_HEADING_WORDS = 6


def _is_marker_line(line: str) -> bool:
    return bool(_MARKER_LINE_RE.match(line))


def _is_heading_line(line: str) -> bool:
    if line.endswith((".", ",", ";", "-")):
        return False
    line_words = line.split()
    if not line_words or len(line_words) > _MAX_HEADING_WORDS:
        return False
    if line.isupper():
        return True
    # Title Case: every word that starts with a letter starts uppercase.
    return all(w[0].isupper() for w in line_words if w[0].isalpha())


def normalize_extracted_text(text: str) -> str:
    """
    Turn raw PDF-extracted text into blank-line separated logical paragraphs.

    PyMuPDF normally wraps one visual paragraph across many lines joined by a
    single "\n", so feeding extraction output straight into the chunker makes
    every wrapped line look like its own tiny paragraph. This normalizes it
    deterministically, without any AI or layout analysis:

    * blank lines are kept as genuine paragraph boundaries
    * consecutive wrapped lines are joined back into one continuous line
    * list items and short heading-like lines start their own paragraph
    * only the whitespace between words ever changes, so word order,
      and the exact set of words, are always preserved
    """
    if not text:
        return ""

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    paragraphs: List[str] = []
    buffer: List[str] = []

    def flush() -> None:
        if buffer:
            paragraphs.append(" ".join(buffer))
            buffer.clear()

    for raw_line in lines:
        line = " ".join(raw_line.split())
        if not line:
            flush()
            continue

        if _is_heading_line(line):
            # A heading is sealed: the paragraph after it starts fresh.
            flush()
            paragraphs.append(line)
            continue

        if _is_marker_line(line):
            # A list item is its own paragraph, but wrapped continuation lines
            # following it should still join onto the item.
            flush()
            buffer.append(line)
            continue

        buffer.append(line)

    flush()

    return "\n\n".join(paragraphs)


def chunk_text(text: str, target_min_words: int = 1000, target_max_words: int = 1500) -> List[str]:
    """
    Splits text into chunks of approximately 1000-1500 words,
    preferring paragraph boundaries.
    Input is first run through normalize_extracted_text(), so wrapped PDF lines
    are re-joined into paragraphs instead of each line becoming a paragraph.
    If text total word count is small, returns a single chunk.
    Any single paragraph longer than target_max_words is split on word boundaries.
    No words are dropped or duplicated: concatenating the chunks reproduces the input word sequence.
    """
    clean_text = normalize_extracted_text(text)
    if not clean_text:
        return []

    # Separate into paragraphs
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in clean_text.split("\n") if p.strip()]
    if not paragraphs:
        paragraphs = [clean_text]

    chunks = []
    current_paragraphs = []
    current_word_count = 0

    def flush() -> None:
        """Emit the buffered paragraphs as one chunk and reset the buffer."""
        nonlocal current_word_count
        if current_paragraphs:
            chunks.append("\n\n".join(current_paragraphs))
            current_paragraphs.clear()
            current_word_count = 0

    for para in paragraphs:
        para_words = len(para.split())

        # A paragraph that alone exceeds the maximum can never fit in a chunk,
        # so split it on its own regardless of what is already buffered.
        if para_words > target_max_words:
            flush()
            words = para.split()
            for i in range(0, len(words), target_max_words):
                piece = words[i:i + target_max_words]
                if len(piece) == target_max_words:
                    chunks.append(" ".join(piece))
                else:
                    # Short remainder stays buffered so following paragraphs can
                    # merge into it instead of becoming a near-empty chunk.
                    current_paragraphs.append(" ".join(piece))
                    current_word_count = len(piece)
            continue

        if current_word_count >= target_min_words and (current_word_count + para_words > target_max_words):
            flush()

        current_paragraphs.append(para)
        current_word_count += para_words

    flush()

    return chunks


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    competency_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document, extract text, chunk text, and save metadata & chunks to DB.

    `competency_id` is optional. When supplied, the document is explicitly linked
    to that competency so a later quiz on it can record competency evidence
    (Phase 6A). The competency is never inferred from the document text; an
    unknown id is rejected with 400 and an omitted one leaves the document
    unlinked.
    """
    # 1. Validate file extension and content type
    filename = file.filename or "uploaded.pdf"
    if not (filename.lower().endswith(".pdf") or file.content_type == "application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files (.pdf) are supported."
        )

    # 2. Read file bytes
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(e)}"
        )

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded PDF file is empty."
        )

    # Optional explicit competency link - validated, never guessed from the text.
    if competency_id is not None:
        competency = (
            db.query(Competency).filter(Competency.id == competency_id).first()
        )
        if not competency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Competency with ID {competency_id} not found."
            )

    # 3. Extract text using PyMuPDF (fitz)
    extracted_text = ""
    try:
        pdf_doc = fitz.open(stream=contents, filetype="pdf")
        for page_num in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_num)
            text = page.get_text()
            if text:
                extracted_text += text + "\n"
        pdf_doc.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process PDF document: {str(e)}"
        )

    raw_text = extracted_text.strip()
    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unreadable or empty text in uploaded PDF document."
        )

    # Normalize once and persist it: this is the exact text the chunks are cut
    # from, so chunk boundaries stay inspectable next to the raw extraction.
    normalized_text = normalize_extracted_text(raw_text)
    if not normalized_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unreadable or empty text in uploaded PDF document."
        )

    # 4. Save document record to database
    now_iso = datetime.utcnow().isoformat()
    doc_record = Document(
        filename=filename,
        content_type=file.content_type or "application/pdf",
        extracted_text=raw_text,
        normalized_text=normalized_text,
        competency_id=competency_id,
        created_at=now_iso
    )

    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 5. Generate and save document text chunks
    text_chunks = chunk_text(normalized_text)
    chunk_records = []
    for idx, chunk_str in enumerate(text_chunks):
        chunk_rec = DocumentChunk(
            document_id=doc_record.id,
            chunk_index=idx,
            text=chunk_str,
            created_at=now_iso
        )
        db.add(chunk_rec)
        chunk_records.append(chunk_rec)

    db.commit()

    # 6. Return success response
    return {
        "id": doc_record.id,
        "filename": doc_record.filename,
        "content_type": doc_record.content_type,
        "text_length": len(doc_record.extracted_text),
        "normalized_text_length": len(doc_record.normalized_text),
        "total_chunks": len(chunk_records),
        "message": "Document uploaded, text extracted, and chunked successfully."
    }


def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )
    return doc


@router.get("/{document_id}")
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a document's raw extracted text and the normalized text that its
    chunks were cut from. `normalized_text` is null for documents uploaded
    before normalization existed.
    """
    doc = _get_document_or_404(document_id, db)

    total_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .count()
    )

    return {
        "id": doc.id,
        "filename": doc.filename,
        "content_type": doc.content_type,
        "created_at": doc.created_at,
        "text_length": len(doc.extracted_text or ""),
        "normalized_text_length": len(doc.normalized_text or ""),
        "total_chunks": total_chunks,
        "extracted_text": doc.extracted_text,
        "normalized_text": doc.normalized_text,
    }


@router.get("/{document_id}/chunks")
def get_document_chunks(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve document text chunks for a given document_id, together with the
    normalized text they were cut from so the boundaries can be inspected.
    """
    doc = _get_document_or_404(document_id, db)

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )

    return {
        "document_id": doc.id,
        "total_chunks": len(chunks),
        "normalized_text_length": len(doc.normalized_text or ""),
        "normalized_text": doc.normalized_text,
        "chunks": [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text
            }
            for chunk in chunks
        ]
    }


# ------------------------------------------------------------------
# Generated MCQs (Phase 5 Step 4B)
#
# persistence lives here in the route layer, matching the rest of the project;
# all generation and validation is delegated to app.services.mcq_service.
# ------------------------------------------------------------------

def _serialize_mcq(row: GeneratedMCQ) -> dict:
    return {
        "id": row.id,
        "document_id": row.document_id,
        "source_chunk_id": row.source_chunk_id,
        "question": row.question,
        "options": json.loads(row.options),
        "correct_option": row.correct_option,
        "explanation": row.explanation,
        "created_at": row.created_at,
    }


def _stored_mcqs(db: Session, document_id: int) -> List[GeneratedMCQ]:
    return (
        db.query(GeneratedMCQ)
        .filter(GeneratedMCQ.document_id == document_id)
        .order_by(GeneratedMCQ.id.asc())
        .all()
    )


@router.post("/{document_id}/mcqs/generate")
def generate_document_mcqs(
    document_id: int,
    competency_context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate five validated MCQs for one chunk of a document and store them.

    Chunk choice: the lowest-indexed chunk that has no stored questions yet. Once
    every chunk is covered, the first chunk's questions are returned again.
    Questions are never regenerated for a chunk that already has them, so calling
    this endpoint repeatedly neither burns AI calls nor creates duplicates.

    Returns 201 with `generated: true` when new questions were created, or 200
    with `generated: false` when existing questions were reused.

    Errors: 404 unknown document, 400 document has no chunks,
            502 OpenRouter/AI service failure, 422 AI returned invalid MCQs.
    """
    doc = _get_document_or_404(document_id, db)

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Document {document_id} has no text chunks, so no questions can "
                "be generated from it."
            ),
        )

    existing_mcqs = _stored_mcqs(db, document_id)
    covered_chunk_ids = {mcq.source_chunk_id for mcq in existing_mcqs}

    target_chunk = next(
        (chunk for chunk in chunks if chunk.id not in covered_chunk_ids),
        chunks[0],
    )

    existing_for_chunk = [
        mcq for mcq in existing_mcqs if mcq.source_chunk_id == target_chunk.id
    ]
    if existing_for_chunk:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "document_id": doc.id,
                "source_chunk_id": target_chunk.id,
                "generated": False,
                "total_mcqs": len(existing_for_chunk),
                "mcqs": [_serialize_mcq(mcq) for mcq in existing_for_chunk],
            },
        )

    try:
        generated = mcq_service.generate_mcqs(
            target_chunk.text,
            target_chunk.id,
            competency_context=competency_context,
        )
    except mcq_service.MCQGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The AI returned invalid MCQs: {exc}",
        ) from exc
    except ai_service.AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The AI service could not generate MCQs: {exc}",
        ) from exc

    # Only reached once the response has been validated: nothing is persisted
    # for a failed or invalid generation.
    now_iso = datetime.utcnow().isoformat()
    mcq_records = []
    for item in generated:
        mcq_record = GeneratedMCQ(
            document_id=doc.id,
            source_chunk_id=item["source_chunk_id"],
            question=item["question"],
            options=json.dumps(item["options"]),
            correct_option=item["correct_option"],
            explanation=item["explanation"],
            created_at=now_iso,
        )
        db.add(mcq_record)
        mcq_records.append(mcq_record)

    db.commit()
    for mcq_record in mcq_records:
        db.refresh(mcq_record)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "document_id": doc.id,
            "source_chunk_id": target_chunk.id,
            "generated": True,
            "total_mcqs": len(mcq_records),
            "mcqs": [_serialize_mcq(mcq) for mcq in mcq_records],
        },
    )


@router.get("/{document_id}/mcqs")
def get_document_mcqs(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return the stored MCQs for a document, oldest first.
    A document with no generated questions yet returns an empty list, not an error.
    """
    doc = _get_document_or_404(document_id, db)
    mcqs = _stored_mcqs(db, document_id)

    return {
        "document_id": doc.id,
        "total_mcqs": len(mcqs),
        "mcqs": [_serialize_mcq(mcq) for mcq in mcqs],
    }


# ------------------------------------------------------------------
# Learner quiz (Phase 5 Step 5A)
#
# These endpoints are learner-facing, so they must never expose correct_option,
# explanation or source_chunk_id. Shaping and scoring both live in
# app.services.quiz_service; the GET /mcqs endpoint above stays the
# inspection endpoint that does return the answer key.
# ------------------------------------------------------------------

class QuizAnswer(BaseModel):
    """One answer in a learner submission. StrictInt rejects bool/float/str."""
    question_id: StrictInt
    selected_option: StrictInt


class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]


def _require_mcqs_or_404(document_id: int, db: Session) -> List[GeneratedMCQ]:
    mcqs = _stored_mcqs(db, document_id)
    if not mcqs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No MCQs have been generated for document {document_id} yet. "
                f"Call POST /api/v1/documents/{document_id}/mcqs/generate first."
            ),
        )
    return mcqs


@router.get("/{document_id}/quiz")
def get_document_quiz(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return the document's MCQs as learner-safe quiz questions.

    Each question exposes only question_id, question and options. The answer key
    (correct_option), the explanation and source_chunk_id are deliberately
    omitted so the learner endpoint cannot leak them.

    Errors: 404 unknown document, 404 no MCQs generated for the document yet.
    """
    doc = _get_document_or_404(document_id, db)
    mcqs = _require_mcqs_or_404(document_id, db)

    questions = quiz_service.build_learner_questions(
        [_serialize_mcq(mcq) for mcq in mcqs]
    )

    return {
        "document_id": doc.id,
        "total_questions": len(questions),
        "questions": questions,
    }


# ------------------------------------------------------------------
# Competency evidence from quiz results (Phase 6A)
#
# The percentage -> evidence level mapping, the at-most-one-level safety rule and
# the gap recalculation (via the existing gap_service) all live in
# app.services.competency_evidence_service. This helper only loads and persists.
# ------------------------------------------------------------------

def _record_quiz_evidence(
    db: Session, doc: Document, score_percent: float, learner: User
) -> dict:
    """
    Persist competency evidence for a completed quiz and apply the bounded level
    rule for the given learner; returns the competency_update payload.

    Evidence is recorded against the authenticate learner (Phase 7B). The
    document must already be linked to a competency: if it is not, the caller
    skips this entirely and returns competency_update = null rather than letting
    a competency be guessed from the document text.
    """
    competency = (
        db.query(Competency).filter(Competency.id == doc.competency_id).first()
    )
    if competency is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Document {doc.id} is linked to competency {doc.competency_id}, "
                "which no longer exists, so competency evidence cannot be recorded."
            ),
        )

    learner_competency = (
        db.query(LearnerCompetency)
        .filter(
            LearnerCompetency.user_id == learner.id,
            LearnerCompetency.competency_id == competency.id,
        )
        .first()
    )
    # 0 means "no level recorded yet" and is never written back as a level.
    existing_level = learner_competency.current_level if learner_competency else 0

    required_level = None
    if learner.role_id is not None:
        mapping = (
            db.query(RoleCompetency)
            .filter(
                RoleCompetency.role_id == learner.role_id,
                RoleCompetency.competency_id == competency.id,
            )
            .first()
        )
        if mapping:
            required_level = mapping.required_level

    update = competency_evidence_service.build_competency_update(
        competency.id, score_percent, existing_level, required_level
    )

    db.add(
        QuizAssessment(
            learner_id=learner.id,
            document_id=doc.id,
            competency_id=competency.id,
            score_percent=float(score_percent),
            evidence_level=update["evidence_level"],
            created_at=datetime.utcnow().isoformat(),
        )
    )

    # The level is only ever raised, and only by the single step the rule allows.
    if update["level_changed"]:
        if learner_competency is None:
            db.add(
                LearnerCompetency(
                    user_id=learner.id,
                    competency_id=competency.id,
                    current_level=update["new_level"],
                )
            )
        else:
            learner_competency.current_level = update["new_level"]

    db.commit()
    return update


@router.post("/{document_id}/quiz/submit")
def submit_document_quiz(
    document_id: int,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Score a learner's answers server-side against the stored correct options.

    Answers are validated (known question ids for this document, no duplicates,
    selected_option 0-3) and scored on the server; the client is never asked to
    grade itself. Results cover only the answered questions and still never
    include correct_option, and unanswered questions are not revealed at all.

    `passed` uses PASS_THRESHOLD_PERCENT, a PROTOTYPE threshold for this MVP -
    it is not an official government or MoSPI/iGOT standard.

    Phase 6A: after a successful score the result is recorded as competency
    evidence and the learner's competency level is recalculated with the bounded
    prototype rule in competency_evidence_service (at most +1 per quiz, never a
    decrease), recalculating the gap with the existing gap_service. The existing
    quiz response fields are unchanged; `competency_update` is added, and is null
    when the document is not linked to a competency.

    Errors: 404 unknown document, 404 no MCQs, 400 invalid submission
    (unknown/duplicate question id, out-of-range option, empty answers),
    422 malformed request body.
    """
    doc = _get_document_or_404(document_id, db)
    mcqs = _require_mcqs_or_404(document_id, db)

    try:
        result = quiz_service.score_submission(
            [_serialize_mcq(mcq) for mcq in mcqs],
            [answer.model_dump() for answer in submission.answers],
        )
    except quiz_service.QuizValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid quiz submission: {exc}",
        ) from exc

    # No competency association -> no guess, no evidence, null update. Scoring
    # above still succeeds, so the existing response contract is unaffected.
    competency_update = None
    if doc.competency_id is not None:
        try:
            competency_update = _record_quiz_evidence(
                db, doc, result["percentage"], current_user
            )
        except CompetencyEvidenceError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Competency evidence could not be recorded: {exc}",
            ) from exc

    return {
        "document_id": doc.id,
        **result,
        "competency_update": competency_update,
    }
