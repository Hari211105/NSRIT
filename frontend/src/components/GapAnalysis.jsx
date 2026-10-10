import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'

/**
 * Displays the competency gap analysis for the demo learner.
 * Shows summary counts, then a sorted list of gaps with
 * status badges and a visual gap bar.
 */
export function GapAnalysis() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadGaps() {
      try {
        setLoading(true)
        setError(null)
        const result = await apiClient.getLearnerGaps()
        setData(result)
      } catch (err) {
        setError('Could not load gap data. Make sure the backend is running.')
      } finally {
        setLoading(false)
      }
    }
    loadGaps()
  }, [])

  if (loading) {
    return (
      <div className="profile-card">
        <p className="loading-text">Loading gap analysis...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="profile-card error-card">
        <p className="error-text">⚠ {error}</p>
      </div>
    )
  }

  const { learner, summary, gaps } = data

  return (
    <div className="profile-card">
      {/* Header */}
      <div className="section-header" style={{ marginBottom: '20px' }}>
        <div>
          <h2 className="learner-name" style={{ marginBottom: '4px' }}>
            Competency Gap Analysis
          </h2>
          <p className="learner-email">{learner.name}</p>
        </div>
        <span className="demo-badge">Demo Data</span>
      </div>

      {/* Summary cards */}
      <div className="summary-grid">
        <SummaryCard
          label="Total Competencies"
          value={summary.total_competencies}
          color="neutral"
        />
        <SummaryCard
          label="With Gaps"
          value={summary.competencies_with_gap}
          color="warning"
        />
        <SummaryCard
          label="Major Gaps"
          value={summary.major_gaps}
          color="critical"
        />
        <SummaryCard
          label="Moderate Gaps"
          value={summary.moderate_gaps}
          color="moderate"
        />
        <SummaryCard
          label="Meeting Target"
          value={summary.competencies_meeting_target}
          color="success"
        />
        <SummaryCard
          label="Above Target"
          value={summary.competencies_above_target}
          color="above"
        />
      </div>

      {/* Gap list */}
      <div style={{ marginTop: '24px' }}>
        <h3 className="section-title" style={{ marginBottom: '12px' }}>
          Competency Gaps — Sorted by Priority
        </h3>
        {gaps.length === 0 ? (
          <div className="empty-state">
            <p>
              No gap analysis yet. Complete your competency assessment to
              generate your gap profile.
            </p>
          </div>
        ) : (
          <div className="gap-list">
            {gaps.map((g) => (
              <GapCard key={g.competency_id} gap={g} />
            ))}
          </div>
        )}
      </div>

      <p className="phase-note">
        Phase 3: Gap Analysis Engine — Recommendations coming in Phase 4.
      </p>
    </div>
  )
}

/** One row in the gap list */
function GapCard({ gap }) {
  const gapBarWidth = Math.max(0, Math.min(100, (gap.gap / 3) * 100))

  return (
    <div className={`gap-card gap-card-${gap.status.toLowerCase()}`}>
      <div className="gap-card-top">
        <div className="gap-card-left">
          <span className="comp-name">{gap.competency_name}</span>
          <div className="gap-levels">
            <span className="gap-level-text">
              Current: <strong>Level {gap.current_level} · {gap.current_level_label}</strong>
            </span>
            <span className="gap-sep">→</span>
            <span className="gap-level-text">
              Required: <strong>Level {gap.required_level} · {gap.required_level_label}</strong>
            </span>
          </div>
        </div>
        <div className="gap-card-right">
          <span className={`gap-status-badge status-${gap.status.toLowerCase()}`}>
            {formatStatus(gap.status)}
          </span>
          <span className={`priority-tag priority-${gap.priority.toLowerCase()}`}>
            {gap.priority}
          </span>
        </div>
      </div>

      {/* Visual gap bar — only show for positive gaps */}
      {gap.gap > 0 && (
        <div className="gap-bar-wrapper">
          <div
            className={`gap-bar gap-bar-fill-${gap.status.toLowerCase()}`}
            style={{ width: `${gapBarWidth}%` }}
          />
          <span className="gap-bar-label">
            Gap: {gap.gap} level{gap.gap !== 1 ? 's' : ''}
          </span>
        </div>
      )}

      {gap.gap <= 0 && (
        <div className="gap-bar-wrapper">
          <span className="gap-bar-label" style={{ color: 'var(--success)' }}>
            {gap.gap === 0 ? 'Meets target level' : `${Math.abs(gap.gap)} level(s) above target`}
          </span>
        </div>
      )}
    </div>
  )
}

/** Small stat summary card */
function SummaryCard({ label, value, color }) {
  return (
    <div className={`summary-card summary-card-${color}`}>
      <div className="summary-value">{value}</div>
      <div className="summary-label">{label}</div>
    </div>
  )
}

function formatStatus(status) {
  switch (status) {
    case 'MAJOR_GAP':     return 'Major Gap'
    case 'MODERATE_GAP':  return 'Moderate Gap'
    case 'MEETS_TARGET':  return 'Meets Target'
    case 'ABOVE_TARGET':  return 'Above Target'
    default:              return status
  }
}

export default GapAnalysis
