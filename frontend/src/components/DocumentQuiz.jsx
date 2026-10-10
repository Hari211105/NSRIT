import React, { useState } from 'react'
import { apiClient } from '../services/api'

/**
 * Learner quiz for a document's AI-generated MCQs.
 *
 * Loads learner-safe questions from GET /documents/{id}/quiz, which never
 * returns the answer key — this component cannot and must not know the correct
 * answers. Scoring happens server-side on submit, and only then are the
 * per-question results and explanations shown.
 */
const OPTION_LETTERS = ['A', 'B', 'C', 'D']

export function DocumentQuiz() {
  const [documentIdInput, setDocumentIdInput] = useState('')
  const [documentId, setDocumentId] = useState(null)
  const [documentInfo, setDocumentInfo] = useState(null)
  const [quiz, setQuiz] = useState(null)
  const [answers, setAnswers] = useState({}) // question_id -> selected option index
  const [currentIndex, setCurrentIndex] = useState(0)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const questions = quiz?.questions ?? []
  const totalQuestions = questions.length
  const answeredCount = questions.filter(
    (q) => answers[q.question_id] !== undefined
  ).length
  const allAnswered = totalQuestions > 0 && answeredCount === totalQuestions

  const loadQuiz = async (rawId) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setAnswers({})
    setCurrentIndex(0)
    setDocumentInfo(null)

    try {
      const quizData = await apiClient.getDocumentQuiz(rawId)
      if (!quizData.questions || quizData.questions.length === 0) {
        setQuiz(null)
        setDocumentId(null)
        setError('This document has no quiz questions available yet.')
        return
      }

      setQuiz(quizData)
      setDocumentId(rawId)

      // Best effort only: the filename makes a nicer title, but the quiz works
      // without it.
      try {
        setDocumentInfo(await apiClient.getDocument(rawId))
      } catch {
        setDocumentInfo(null)
      }
    } catch (err) {
      setQuiz(null)
      setDocumentId(null)
      setError(
        err?.message ||
          'Could not load the quiz. Make sure the backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleLoad = (event) => {
    event.preventDefault()
    const parsed = Number(documentIdInput)
    if (!Number.isInteger(parsed) || parsed < 1) {
      setError('Enter a positive document ID to load its quiz.')
      return
    }
    loadQuiz(parsed)
  }

  const selectOption = (questionId, optionIndex) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }))
  }

  const handleSubmit = async () => {
    if (!allAnswered) return

    setSubmitting(true)
    setError(null)
    try {
      const payload = questions.map((question) => ({
        question_id: question.question_id,
        selected_option: answers[question.question_id],
      }))
      const scored = await apiClient.submitDocumentQuiz(documentId, payload)
      setResult(scored)
    } catch (err) {
      setError(
        err?.message || 'Could not submit the quiz. Please try again.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  const retakeQuiz = () => {
    setResult(null)
    setAnswers({})
    setCurrentIndex(0)
    setError(null)
  }

  const quizTitle = quiz
    ? documentInfo?.filename
      ? `Quiz: ${documentInfo.filename}`
      : `Quiz: Document #${documentId}`
    : 'Document Quiz'

  const quizSubtitle = quiz
    ? `Document #${documentId} · ${totalQuestions} questions`
    : 'Enter a document ID to take the quiz generated from its content.'

  return (
    <div className="profile-card">
      <div className="section-header">
        <div>
          <h2 className="learner-name" style={{ marginBottom: '4px' }}>
            {quizTitle}
          </h2>
          <p className="learner-email">{quizSubtitle}</p>
        </div>
        <span className="demo-badge">Learner Quiz</span>
      </div>

      {/* ── Document picker ── */}
      <form className="quiz-picker" onSubmit={handleLoad}>
        <div className="quiz-picker-field">
          <label className="detail-label" htmlFor="quiz-document-id">
            Document ID
          </label>
          <input
            id="quiz-document-id"
            className="quiz-input"
            type="number"
            min="1"
            step="1"
            inputMode="numeric"
            placeholder="e.g. 1"
            value={documentIdInput}
            onChange={(event) => setDocumentIdInput(event.target.value)}
            disabled={loading || submitting}
          />
        </div>
        <button className="btn" type="submit" disabled={loading || submitting}>
          {loading ? 'Loading…' : 'Load Quiz'}
        </button>
      </form>

      {/* ── Loading ── */}
      {loading && (
        <p className="loading-text" role="status">
          Loading quiz questions…
        </p>
      )}

      {/* ── Error ── */}
      {error && !loading && (
        <div className="quiz-error" role="alert">
          <p className="error-text">⚠ {error}</p>
        </div>
      )}

      {/* ── Empty ── */}
      {!loading && !error && !quiz && !result && (
        <div className="quiz-empty">
          <p>🔍 No quiz loaded yet — enter a document ID above to begin.</p>
        </div>
      )}

      {/* ── Answering ── */}
      {!loading && !error && quiz && !result && (
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
      {!loading && result && (
        <QuizResult
          result={result}
          questions={questions}
          onRetake={retakeQuiz}
        />
      )}

      <p className="phase-note">
        Phase 5: AI-Generated Quiz — questions generated from the document&apos;s
        own content, scored on the server.
      </p>
    </div>
  )
}

/** One question at a time, with Previous / Next and a gated submit button. */
export function QuizRunner({
  questions,
  answers,
  currentIndex,
  answeredCount,
  allAnswered,
  submitting,
  onSelect,
  onNavigate,
  onSubmit,
}) {
  const totalQuestions = questions.length
  const question = questions[currentIndex]
  const selected = answers[question.question_id]
  const progressPercent = Math.round(((currentIndex + 1) / totalQuestions) * 100)

  return (
    <div className="quiz-runner">
      {/* Progress */}
      <div className="quiz-progress-row">
        <span className="quiz-progress-label">
          Question {currentIndex + 1} of {totalQuestions}
        </span>
        <span className="quiz-answered-count">
          {answeredCount} of {totalQuestions} answered
        </span>
      </div>
      <div className="quiz-progress-bar">
        <div
          className="quiz-progress-fill"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Question */}
      <p className="quiz-question-text">{question.question}</p>

      {/* Options */}
      <div className="quiz-options" role="group" aria-label="Answer options">
        {question.options.map((option, optionIndex) => {
          const isSelected = selected === optionIndex
          return (
            <button
              key={optionIndex}
              type="button"
              className={`quiz-option ${isSelected ? 'quiz-option-selected' : ''}`}
              aria-pressed={isSelected}
              onClick={() => onSelect(question.question_id, optionIndex)}
            >
              <span className="quiz-option-letter">
                {OPTION_LETTERS[optionIndex] ?? optionIndex + 1}
              </span>
              <span className="quiz-option-text">{option}</span>
            </button>
          )
        })}
      </div>

      {/* Navigation */}
      <div className="quiz-nav">
        <button
          className="btn btn-secondary"
          type="button"
          disabled={currentIndex === 0}
          onClick={() => onNavigate(currentIndex - 1)}
        >
          ← Previous
        </button>
        <button
          className="btn btn-secondary"
          type="button"
          disabled={currentIndex >= totalQuestions - 1}
          onClick={() => onNavigate(currentIndex + 1)}
        >
          Next →
        </button>
      </div>

      {/* Submit */}
      <div className="quiz-submit-bar">
        {!allAnswered && (
          <p className="quiz-hint">
            Answer all {totalQuestions} questions before submitting (
            {totalQuestions - answeredCount} remaining).
          </p>
        )}
        <button
          className="btn btn-primary"
          type="button"
          disabled={!allAnswered || submitting}
          onClick={onSubmit}
        >
          {submitting ? 'Scoring…' : 'Submit Quiz'}
        </button>
      </div>
    </div>
  )
}

/** Server-scored result: score, percentage, pass status and explanations. */
export function QuizResult({ result, questions, onRetake }) {
  const questionById = Object.fromEntries(
    questions.map((question) => [question.question_id, question])
  )
  const {
    score,
    total_questions: totalQuestions,
    answered_questions: answeredQuestions,
    unanswered_questions: unansweredQuestions,
    percentage,
    passed,
    pass_threshold_percent: passThreshold,
    results,
  } = result

  return (
    <div className="quiz-result">
      <div className={`quiz-verdict ${passed ? 'quiz-verdict-pass' : 'quiz-verdict-fail'}`}>
        <span className="quiz-verdict-status">
          {passed ? '✓ PASSED' : '✕ FAILED'}
        </span>
        <span className="quiz-verdict-score">
          Score: {score} / {totalQuestions} · {percentage}%
        </span>
      </div>

      <div className="summary-grid" style={{ marginTop: '16px' }}>
        <div className="summary-card summary-card-neutral">
          <div className="summary-value">{score}</div>
          <div className="summary-label">Correct</div>
        </div>
        <div className="summary-card summary-card-above">
          <div className="summary-value">{percentage}%</div>
          <div className="summary-label">Percentage</div>
        </div>
        <div className="summary-card summary-card-success">
          <div className="summary-value">{answeredQuestions}</div>
          <div className="summary-label">Answered</div>
        </div>
        <div className="summary-card summary-card-warning">
          <div className="summary-value">{unansweredQuestions}</div>
          <div className="summary-label">Unanswered</div>
        </div>
      </div>

      <p className="quiz-threshold-note">
        Pass threshold: {passThreshold}% — a prototype application threshold for
        this MVP, not an official government or MoSPI/iGOT standard.
      </p>

      <h3 className="section-title" style={{ margin: '24px 0 12px' }}>
        Your Answers — {results.length} of {totalQuestions} questions reviewed
      </h3>

      <div className="quiz-review-list">
        {results.map((item, index) => {
          const question = questionById[item.question_id]
          const selectedText =
            question?.options?.[item.selected_option] ?? 'No answer submitted'

          return (
            <div
              key={item.question_id}
              className={`quiz-review-item ${
                item.is_correct ? 'quiz-review-correct' : 'quiz-review-incorrect'
              }`}
            >
              <div className="quiz-review-top">
                <span className="quiz-review-question">
                  {index + 1}. {question?.question ?? `Question #${item.question_id}`}
                </span>
                <span
                  className={`quiz-review-badge ${
                    item.is_correct
                      ? 'quiz-review-badge-correct'
                      : 'quiz-review-badge-incorrect'
                  }`}
                >
                  {item.is_correct ? 'Correct' : 'Incorrect'}
                </span>
              </div>

              <div className="quiz-review-answer">
                <span className="detail-label">Your answer</span>
                <span className="detail-value">{selectedText}</span>
              </div>

              {item.explanation && (
                <div className="quiz-review-explanation">
                  <span className="reason-heading">💡 Explanation</span>
                  <p className="reason-text">{item.explanation}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="quiz-submit-bar">
        <button className="btn btn-primary" type="button" onClick={onRetake}>
          Retake Quiz
        </button>
      </div>
    </div>
  )
}

export default DocumentQuiz
