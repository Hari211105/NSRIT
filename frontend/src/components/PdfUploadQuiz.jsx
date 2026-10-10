import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { QuizRunner, QuizResult } from './DocumentQuiz'

/**
 * PDF upload → MCQ generation → quiz flow.
 *
 * Lets the learner:
 *   1. pick a .pdf from their device,
 *   2. upload it through the backend API (the backend remains the authority on
 *      file type/emptiness — we only give quick client-side feedback),
 *   3. see upload + generation status,
 *   4. take the AI-generated, source-grounded quiz,
 *   5. view the server-scored result (pass/fail + explanations).
 *
 * Where the uploaded document was linked to a competency at upload time, the
 * quiz result also drives the deterministic competency-evidence update. We fork
 * that piece here so the existing DocumentQuiz remains intact.
 */
const OPTION_PDF_TYPES = ['application/pdf']
const MAX_FILE_SIZE_MB = 20 // soft client-side guard; backend is authoritative.

function formatMB(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export function PdfUploadQuiz() {
  // ── Upload state ──
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [documentRecord, setDocumentRecord] = useState(null) // upload response
  const [uploadedDocId, setUploadedDocId] = useState(null)
  const [uploadError, setUploadError] = useState(null)

  // ── Quiz state (shared with the quiz runner) ──
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({})
  const [currentIndex, setCurrentIndex] = useState(0)
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [quizError, setQuizError] = useState(null)

  // Phase 8 (demo readiness): optional competency link. Choosing a competency
  // links the uploaded document so the quiz result records competency evidence
  // (the existing Phase 6A loop). Leaving it on "General" keeps the old
  // behaviour (quiz only, no evidence), exactly as before.
  const [competencyOptions, setCompetencyOptions] = useState([])
  const [competencyId, setCompetencyId] = useState('')

  useEffect(() => {
    let mounted = true
    apiClient
      .getLearnerCompetencies()
      .then((data) => {
        if (mounted) setCompetencyOptions(data?.competencies || [])
      })
      .catch(() => {
        // Optional feature — the upload still works without it.
      })
    return () => {
      mounted = false
    }
  }, [])

  const questions = quiz?.questions ?? []
  const totalQuestions = questions.length
  const answeredCount = questions.filter(
    (q) => answers[q.question_id] !== undefined
  ).length
  const allAnswered = totalQuestions > 0 && answeredCount === totalQuestions

  // ── Step 1: pick + validate the file locally ──
  const handleFileSelect = (event) => {
    const chosen = event.target.files?.[0] ?? null
    setFile(chosen)
    setUploadError(null)
    setUploadedDocId(null)
    setDocumentRecord(null)
    setQuiz(null)
    setResult(null)
    setQuizError(null)

    if (!chosen) return

    const isPdf = chosen.type
      ? OPTION_PDF_TYPES.includes(chosen.type)
      : chosen.name.toLowerCase().endsWith('.pdf')
    if (!isPdf) {
      setUploadError('Invalid file type. Please choose a PDF (.pdf).')
      return
    }
    if (chosen.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setUploadError(
        `File is ${formatMB(chosen.size)} — larger than the ${MAX_FILE_SIZE_MB} MB soft limit. ` +
          'The backend may reject oversized files.'
      )
    }
  }

  // ── Step 2: upload → generate → load quiz ──
  const handleUploadAndGenerate = async () => {
    if (!file) {
      setUploadError('Choose a PDF file first.')
      return
    }
    setUploading(true)
    setUploadError(null)
    setQuizError(null)
    try {
      // Link the document to the selected competency (optional) so the quiz
      // result feeds the competency-evidence loop; null keeps it unlinked.
      const record = await apiClient.uploadDocument(
        file,
        competencyId ? Number(competencyId) : null
      )
      setDocumentRecord(record)
      setUploadedDocId(record.id)

      setGenerating(true)
      try {
        await apiClient.generateDocumentMcqs(record.id)
      } finally {
        setGenerating(false)
      }

      const quizData = await apiClient.getDocumentQuiz(record.id)
      if (!quizData.questions || quizData.questions.length === 0) {
        setQuizError('The document was processed but no quiz questions were generated.')
        return
      }
      setQuiz(quizData)
      setAnswers({})
      setCurrentIndex(0)
      setResult(null)
    } catch (err) {
      setUploadError(
        err?.message || 'Could not upload and process the document. Please try again.'
      )
    } finally {
      setUploading(false)
    }
  }

  // ── Quiz interactions (mirror DocumentQuiz) ──
  const selectOption = (questionId, optionIndex) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }))
  }

  const handleSubmit = async () => {
    if (!allAnswered || uploadedDocId == null) return
    setSubmitting(true)
    setQuizError(null)
    try {
      const payload = questions.map((question) => ({
        question_id: question.question_id,
        selected_option: answers[question.question_id],
      }))
      const scored = await apiClient.submitDocumentQuiz(uploadedDocId, payload)
      setResult(scored)
    } catch (err) {
      setQuizError(err?.message || 'Could not submit the quiz. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const retakeQuiz = () => {
    setResult(null)
    setAnswers({})
    setCurrentIndex(0)
    setQuizError(null)
  }

  const resetAll = () => {
    setFile(null)
    setUploadedDocId(null)
    setDocumentRecord(null)
    setQuiz(null)
    setAnswers({})
    setResult(null)
    setUploadError(null)
    setQuizError(null)
    setCurrentIndex(0)
  }

  const fileName = documentRecord?.filename ?? file?.name ?? ''
  const processing = uploading || generating

  return (
    <div className="profile-card">
      <div className="section-header">
        <div>
          <h2 className="learner-name" style={{ marginBottom: '4px' }}>
            Upload a PDF & Take a Quiz
          </h2>
          <p className="learner-email">
            Direct PDF upload → AI-generated quiz
          </p>
        </div>
        <span className="demo-badge">Learner Quiz</span>
      </div>
      <p className="learner-email">
        Pick a PDF learning material, upload it, and Upskill AI will generate a
        source-grounded quiz you can take immediately. No document ID needed.
      </p>

      {/* ── Upload controls (hidden once a quiz is in progress) ── */}
      {!processing && !quiz && (
        <div className="quiz-picker" style={{ alignItems: 'center' }}>
          <div className="quiz-picker-field" style={{ flex: '1 1 260px' }}>
            <label className="detail-label" htmlFor="pdf-upload-input">
              PDF file
            </label>
            <input
              id="pdf-upload-input"
              type="file"
              accept="application/pdf,.pdf"
              className="quiz-input"
              onChange={handleFileSelect}
              disabled={uploading}
            />
          </div>
          <div className="quiz-picker-field" style={{ flex: '1 1 220px' }}>
            <label className="detail-label" htmlFor="pdf-competency-select">
              Link to competency (optional)
            </label>
            <select
              id="pdf-competency-select"
              className="quiz-input"
              value={competencyId}
              onChange={(e) => setCompetencyId(e.target.value)}
              disabled={uploading}
            >
              <option value="">General (no competency evidence)</option>
              {competencyOptions.map((c) => (
                <option key={c.competency_id} value={c.competency_id}>
                  {c.competency_name}
                </option>
              ))}
            </select>
          </div>
          <button
            className="btn"
            type="button"
            disabled={!file || uploading}
            onClick={handleUploadAndGenerate}
          >
            {uploading ? 'Uploading…' : 'Upload & Generate Quiz'}
          </button>
        </div>
      )}

      {/* ── Upload / generation status ── */}
      {processing && (
        <p className="loading-text" role="status">
          {uploading
            ? `Uploading ${fileName || 'PDF'} and extracting text…`
            : 'Generating AI questions from the document…'}
        </p>
      )}

      {/* ── Upload errors ── */}
      {uploadError && !processing && (
        <div className="quiz-error" role="alert">
          <p className="error-text">⚠ {uploadError}</p>
        </div>
      )}

      {/* ── Uploaded + generated, ready to take ── */}
      {!processing && documentRecord && uploadedDocId != null && (
        <div className="quiz-empty" style={{ textAlign: 'left', marginBottom: '16px' }}>
          <p>
            <strong>{documentRecord.filename}</strong> — uploaded, text extracted
            ({documentRecord.text_length.toLocaleString()} chars),{' '}
            {documentRecord.total_chunks} chunk(s) ready.
          </p>
          {quizError && <p className="error-text">⚠ {quizError}</p>}
        </div>
      )}

      {/* ── Quiz errors ── */}
      {quizError && !processing && (
        <div className="quiz-error" role="alert">
          <p className="error-text">⚠ {quizError}</p>
        </div>
      )}

      {/* ── Quiz runner ── */}
      {!processing && !quizError && quiz && !result && (
        <QuizRunner
          questions={questions}
          answers={answers}
          currentIndex={currentIndex}
          answeredCount={answeredCount}
          allAnswered={allAnswered}
          submitting={submitting}
          onSelect={selectOption}
          onNavigate={setCurrentIndex}
          onSubmit={handleSubmit}
        />
      )}

      {/* ── Results ── */}
      {!processing && result && (
        <>
          <QuizResult result={result} questions={questions} onRetake={retakeQuiz} />
          {result.competency_update && (
            <div className="rec-reason-box" style={{ marginTop: '12px' }}>
              <span className="reason-heading">📊 Competency evidence recorded:</span>
              <p className="reason-text">
                Score {result.percentage}% → evidence level {result.competency_update.evidence_level}.
                Competency level{' '}
                {result.competency_update.level_changed
                  ? `raised: Level ${result.competency_update.previous_level} → ${result.competency_update.new_level} (at most one step per quiz — the prototype rule).`
                  : `unchanged at Level ${result.competency_update.new_level} (a single quiz raises a level by at most one).`}
                {result.competency_update.gap_after !== null &&
                  result.competency_update.gap_after !== undefined &&
                  ` Remaining gap: ${result.competency_update.gap_after} level(s).`}
              </p>
            </div>
          )}
          <div className="quiz-submit-bar">
            <button className="btn btn-secondary" type="button" onClick={resetAll}>
              Upload a different PDF
            </button>
          </div>
        </>
      )}

      <p className="phase-note">
        Phase 5 + 6A: AI-Generated Quiz — questions come from the document&apos;s
        own content and are scored on the server; results feed the deterministic
        competency-evidence loop when the document is linked to a competency.
      </p>
    </div>
  )
}

export default PdfUploadQuiz