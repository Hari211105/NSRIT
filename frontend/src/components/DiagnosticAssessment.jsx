import React, { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../services/api'

const DIFFICULTY_LABELS = {
  EASY: { label: 'Easy', weight: '1.0x' },
  MEDIUM: { label: 'Medium', weight: '2.0x' },
  HARD: { label: 'Hard', weight: '3.0x' },
}

const OPTION_LETTERS = ['A', 'B', 'C', 'D']

/**
 * Diagnostic Assessment component.
 *
 * Three states:
 * 1. START — explains what the diagnostic does and has a start button
 * 2. IN_PROGRESS — shows questions one at a time with navigation
 * 3. COMPLETED — shows results with per-competency breakdown
 */
export function DiagnosticAssessment() {
  const [view, setView] = useState('start') // start | in_progress | completed
  const [assessment, setAssessment] = useState(null)
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({})
  const [currentIndex, setCurrentIndex] = useState(0)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState(null)

  const totalQuestions = questions.length
  const answeredCount = questions.filter(
    (q) => answers[q.question_id] !== undefined
  ).length
  const allAnswered = totalQuestions > 0 && answeredCount === totalQuestions

  // Load history on mount
  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      const data = await apiClient.getDiagnosticHistory()
      setHistory(data)
    } catch {
      // Ignore — history is optional
    }
  }

  const startAssessment = useCallback(async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    setAnswers({})
    setCurrentIndex(0)
    try {
      const data = await apiClient.startDiagnostic()
      setAssessment(data)
      setQuestions(data.questions)
      setView('in_progress')
    } catch (err) {
      setError(err.message || 'Could not start the diagnostic assessment.')
    } finally {
      setLoading(false)
    }
  }, [])

  const selectOption = (questionId, optionIndex) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }))
  }

  const handleSubmit = useCallback(async () => {
    if (!allAnswered || !assessment) return
    setSubmitting(true)
    setError(null)
    try {
      const payload = questions.map((q) => ({
        question_id: q.question_id,
        selected_option: answers[q.question_id],
      }))
      const data = await apiClient.submitDiagnostic(assessment.assessment_id, payload)
      setResult(data)
      setView('completed')
      loadHistory()
    } catch (err) {
      setError(err.message || 'Could not submit the assessment.')
    } finally {
      setSubmitting(false)
    }
  }, [allAnswered, assessment, questions, answers])

  return (
    <div className="profile-card">
      <div className="section-header">
        <div>
          <h2 className="learner-name" style={{ marginBottom: '4px' }}>
            Diagnostic Competency Assessment
          </h2>
          <p className="learner-email">
            Assess your competency levels across your role's required areas
          </p>
        </div>
        <span className="demo-badge">Phase 2</span>
      </div>

      {/* ── Error ── */}
      {error && !loading && (
        <div className="quiz-error" role="alert">
          <p className="error-text">⚠ {error}</p>
        </div>
      )}

      {/* ── START VIEW ── */}
      {view === 'start' && !loading && (
        <DiagnosticStart
          onStart={startAssessment}
          loading={loading}
          history={history}
        />
      )}

      {/* ── LOADING ── */}
      {loading && (
        <p className="loading-text" role="status">
          {view === 'start' ? 'Starting diagnostic assessment…' : 'Loading…'}
        </p>
      )}

      {/* ── IN_PROGRESS VIEW ── */}
      {view === 'in_progress' && !loading && (
        <DiagnosticRunner
          questions={questions}
          answers={answers}
          currentIndex={currentIndex}
          answeredCount={answeredCount}
          totalQuestions={totalQuestions}
          allAnswered={allAnswered}
          submitting={submitting}
          onSelect={selectOption}
          onNavigate={setCurrentIndex}
          onSubmit={handleSubmit}
        />
      )}

      {/* ── COMPLETED VIEW ── */}
      {view === 'completed' && result && (
        <DiagnosticResult
          result={result}
          onRetake={() => {
            setView('start')
            setResult(null)
            setAssessment(null)
            setQuestions([])
            setAnswers({})
          }}
        />
      )}

      <p className="phase-note">
        Phase 2: Diagnostic Assessment — difficulty-weighted scoring with
        per-competency evidence and deterministic level updates.
      </p>
    </div>
  )
}


/**
 * START view — explains the assessment and shows a start button.
 */
function DiagnosticStart({ onStart, loading, history }) {
  return (
    <div>
      <div className="diagnostic-intro">
        <h3 className="section-title" style={{ marginBottom: '12px' }}>
          What is this assessment?
        </h3>
        <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.6', marginBottom: '16px' }}>
          This diagnostic assessment evaluates your competency levels across all
          areas required for your role. It uses <strong>difficulty-weighted
          scoring</strong> — harder questions carry more weight, ensuring your
          competency levels reflect true proficiency.
        </p>
        <div className="diagnostic-info-grid">
          <div className="diagnostic-info-item">
            <span className="detail-label">Assessment Type</span>
            <span className="detail-value">Diagnostic</span>
          </div>
          <div className="diagnostic-info-item">
            <span className="detail-label">Scoring Method</span>
            <span className="detail-value">Difficulty-Weighted</span>
          </div>
          <div className="diagnostic-info-item">
            <span className="detail-label">Difficulty Levels</span>
            <span className="detail-value">Easy (1x) · Medium (2x) · Hard (3x)</span>
          </div>
          <div className="diagnostic-info-item">
            <span className="detail-label">Pass Threshold</span>
            <span className="detail-value">60%</span>
          </div>
        </div>
        <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '12px' }}>
          Your results will update your competency levels deterministically.
          A single assessment can raise each competency level by at most one step,
          and a poor score never lowers an established level.
        </p>
      </div>

      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button
          className="btn btn-primary"
          onClick={onStart}
          disabled={loading}
          style={{ fontSize: '1rem', padding: '12px 32px' }}
        >
          {loading ? 'Starting…' : 'Start Diagnostic Assessment'}
        </button>
      </div>

      {/* Previous assessments */}
      {history && history.total_assessments > 0 && (
        <div style={{ marginTop: '24px' }}>
          <h3 className="section-title" style={{ marginBottom: '12px' }}>
            Previous Assessments ({history.total_assessments})
          </h3>
          <div className="gap-list">
            {history.assessments.map((a) => (
              <div key={a.id} className="gap-card gap-card-meets_target">
                <div className="gap-card-top">
                  <div className="gap-card-left">
                    <span className="comp-name">
                      {a.assessment_type === 'diagnostic' ? 'Diagnostic' : a.assessment_type}
                    </span>
                    <span className="gap-level-text">
                      Score: <strong>{a.score_percent}%</strong> · {a.total_questions} questions
                    </span>
                  </div>
                  <div className="gap-card-right">
                    <span className={`quiz-review-badge ${a.passed ? 'quiz-review-badge-correct' : 'quiz-review-badge-incorrect'}`}>
                      {a.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}


/**
 * IN_PROGRESS view — shows questions one at a time with navigation.
 */
function DiagnosticRunner({
  questions,
  answers,
  currentIndex,
  answeredCount,
  totalQuestions,
  allAnswered,
  submitting,
  onSelect,
  onNavigate,
  onSubmit,
}) {
  const question = questions[currentIndex]
  const selected = answers[question.question_id]
  const progressPercent = Math.round(((currentIndex + 1) / totalQuestions) * 100)
  const diffInfo = DIFFICULTY_LABELS[question.difficulty] || DIFFICULTY_LABELS.MEDIUM

  // Group questions by competency for the sidebar
  const competencyGroups = {}
  questions.forEach((q, idx) => {
    if (!competencyGroups[q.competency_id]) {
      competencyGroups[q.competency_id] = []
    }
    competencyGroups[q.competency_id].push({ ...q, originalIndex: idx })
  })

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

      {/* Difficulty badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
        <span className={`difficulty-badge difficulty-${question.difficulty?.toLowerCase()}`}>
          {diffInfo.label} · {diffInfo.weight}
        </span>
        <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
          Competency #{question.competency_id}
        </span>
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
          {submitting ? 'Scoring…' : 'Submit Assessment'}
        </button>
      </div>
    </div>
  )
}


/**
 * COMPLETED view — shows results with per-competency breakdown.
 */
function DiagnosticResult({ result, onRetake }) {
  const { overall, competencies } = result

  // Sort competencies by gap (largest first)
  const sortedComps = Object.values(competencies).sort((a, b) => {
    const gapA = a.gap_before ?? 0
    const gapB = b.gap_before ?? 0
    return gapB - gapA
  })

  return (
    <div className="diagnostic-result">
      {/* Verdict */}
      <div className={`quiz-verdict ${overall.passed ? 'quiz-verdict-pass' : 'quiz-verdict-fail'}`}>
        <span className="quiz-verdict-status">
          {overall.passed ? '✓ ASSESSMENT PASSED' : '✕ ASSESSMENT FAILED'}
        </span>
        <span className="quiz-verdict-score">
          Weighted Score: {overall.weighted_percent}% · {overall.total_correct}/{overall.total_questions} correct
        </span>
      </div>

      {/* Summary cards */}
      <div className="summary-grid" style={{ marginTop: '16px' }}>
        <div className="summary-card summary-card-neutral">
          <div className="summary-value">{overall.total_questions}</div>
          <div className="summary-label">Total Questions</div>
        </div>
        <div className="summary-card summary-card-success">
          <div className="summary-value">{overall.total_correct}</div>
          <div className="summary-label">Correct</div>
        </div>
        <div className="summary-card summary-card-above">
          <div className="summary-value">{overall.weighted_percent}%</div>
          <div className="summary-label">Weighted Score</div>
        </div>
        <div className="summary-card summary-card-neutral">
          <div className="summary-value">{overall.total_questions - overall.total_correct}</div>
          <div className="summary-label">Incorrect</div>
        </div>
      </div>

      {/* Pass threshold note */}
      <p className="quiz-threshold-note">
        Pass threshold: {overall.pass_threshold_percent}% — a prototype application
        threshold, not an official government or MoSPI/iGOT standard.
      </p>

      {/* Per-competency results */}
      <h3 className="section-title" style={{ margin: '24px 0 12px' }}>
        Competency Evidence — Deterministic Level Updates
      </h3>

      <div className="gap-list">
        {sortedComps.map((comp) => (
          <CompetencyResultCard key={comp.competency_id} comp={comp} />
        ))}
      </div>

      {/* Action */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <button className="btn btn-primary" type="button" onClick={onRetake}>
          Retake Assessment
        </button>
      </div>
    </div>
  )
}


/**
 * Individual competency result card.
 */
function CompetencyResultCard({ comp }) {
  const levelLabels = { 1: 'Awareness', 2: 'Working', 3: 'Proficient', 4: 'Advanced' }

  return (
    <div className={`gap-card ${comp.level_changed ? 'gap-card-above_target' : 'gap-card-meets_target'}`}>
      <div className="gap-card-top">
        <div className="gap-card-left">
          <span className="comp-name">
            Competency #{comp.competency_id}
            {comp.priority && (
              <span className={`priority-tag priority-${comp.priority?.toLowerCase()}`} style={{ marginLeft: '8px' }}>
                {comp.priority}
              </span>
            )}
          </span>
          <div className="gap-levels">
            <span className="gap-level-text">
              Score: <strong>{comp.weighted_percent}%</strong>
            </span>
            <span className="gap-sep">·</span>
            <span className="gap-level-text">
              Evidence Level: <strong>{comp.evidence_level}</strong>
            </span>
          </div>
        </div>
        <div className="gap-card-right">
          {comp.level_changed ? (
            <span className="quiz-review-badge quiz-review-badge-correct">
              Level ↑ {comp.previous_level} → {comp.new_level}
            </span>
          ) : (
            <span className="quiz-review-badge" style={{ background: 'rgba(100,116,139,0.18)', color: '#94a3b8', border: '1px solid rgba(100,116,139,0.3)' }}>
              Level unchanged ({comp.previous_level})
            </span>
          )}
        </div>
      </div>

      {/* Level details */}
      <div className="rec-details-grid" style={{ marginTop: '10px' }}>
        <div className="rec-detail-item">
          <span className="detail-label">Current Level</span>
          <span className="detail-value">Level {comp.previous_level} · {levelLabels[comp.previous_level] || 'Unknown'}</span>
        </div>
        <div className="rec-detail-item">
          <span className="detail-label">New Level</span>
          <span className="detail-value">Level {comp.new_level} · {levelLabels[comp.new_level] || 'Unknown'}</span>
        </div>
        {comp.required_level && (
          <>
            <div className="rec-detail-item">
              <span className="detail-label">Required Level</span>
              <span className="detail-value">Level {comp.required_level}</span>
            </div>
            <div className="rec-detail-item">
              <span className="detail-label">Gap</span>
              <span className="detail-value text-warning">
                {comp.gap_before !== null ? comp.gap_before : 'N/A'}
                {comp.gap_after !== null && comp.gap_before !== comp.gap_after
                  ? ` → ${comp.gap_after}`
                  : ''}
              </span>
            </div>
          </>
        )}
        <div className="rec-detail-item">
          <span className="detail-label">Questions</span>
          <span className="detail-value">{comp.total_correct}/{comp.total_questions} correct</span>
        </div>
      </div>

      {/* Difficulty breakdown */}
      {comp.difficulty_breakdown && (
        <div style={{ marginTop: '8px', fontSize: '0.78rem', color: '#94a3b8' }}>
          Difficulty: {Object.entries(comp.difficulty_breakdown).map(([d, count]) => (
            <span key={d} style={{ marginRight: '8px' }}>
              {d}: {count}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}


export default DiagnosticAssessment
