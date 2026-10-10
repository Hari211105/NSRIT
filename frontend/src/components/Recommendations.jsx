import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'

/**
 * Displays personalized learning recommendations for the demo learner.
 * Shows summary cards, followed by ranked recommendation cards matching gaps.
 */
export function Recommendations() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadRecommendations() {
      try {
        setLoading(true)
        setError(null)
        const result = await apiClient.getLearnerRecommendations()
        setData(result)
      } catch (err) {
        setError('Could not load recommendations. Make sure the backend is running.')
      } finally {
        setLoading(false)
      }
    }
    loadRecommendations()
  }, [])

  if (loading) {
    return (
      <div className="profile-card">
        <p className="loading-text">Generating personalized recommendations...</p>
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

  const { learner, summary, recommendations } = data
  const topRec = recommendations.length > 0 ? recommendations[0] : null

  return (
    <div className="profile-card">
      {/* Header */}
      <div className="section-header" style={{ marginBottom: '20px' }}>
        <div>
          <h2 className="learner-name" style={{ marginBottom: '4px' }}>
            Recommended Learning
          </h2>
          <p className="learner-email">
            Personalized training path for {learner.name} {learner.role_name ? `· ${learner.role_name}` : ''}
          </p>
        </div>
        <span className="demo-badge">Demo Catalog</span>
      </div>

      {/* Summary grid */}
      <div className="summary-grid">
        <SummaryCard
          label="Total Recommendations"
          value={summary.total_recommendations}
          color="neutral"
        />
        <SummaryCard
          label="Critical Gap Areas"
          value={summary.critical_gap_competencies}
          color="critical"
        />
        <SummaryCard
          label="Targeted Competencies"
          value={summary.competencies_with_recommendations}
          color="warning"
        />
        <SummaryCard
          label="Top Recommendation"
          value={topRec ? topRec.learning_resource.title : 'None'}
          color="success"
          isText={true}
        />
      </div>

      {/* Recommendations list */}
      <div style={{ marginTop: '28px' }}>
        <h3 className="section-title" style={{ marginBottom: '16px' }}>
          Personalized Learning Pathway — Ranked by Relevance & Priority
        </h3>

        {recommendations.length === 0 ? (
          <div className="empty-state">
            <p>
              No recommendations yet. Complete your competency assessment and
              your personalised learning path will appear here.
            </p>
          </div>
        ) : (
          <div className="recommendation-list">
            {recommendations.map((rec) => (
              <RecommendationCard key={`${rec.rank}-${rec.learning_resource.id}`} recommendation={rec} />
            ))}
          </div>
        )}
      </div>

      <p className="phase-note">
        Phase 4: Personalized Recommendation Engine — Deterministic resource matching based on competency gap and level fit.
      </p>
    </div>
  )
}

/** Individual Recommendation Card */
function RecommendationCard({ recommendation }) {
  const {
    rank,
    competency_name,
    current_level,
    required_level,
    gap,
    priority,
    learning_resource,
    relevance_score,
    reason,
  } = recommendation

  const sourceLabel = formatSourceLabel(learning_resource.source)

  return (
    <div className={`rec-card priority-${priority.toLowerCase()}`}>
      <div className="rec-card-header">
        <div className="rec-title-group">
          <span className="rec-rank-badge">#{rank}</span>
          <h4 className="rec-resource-title">{learning_resource.title}</h4>
        </div>
        <div className="rec-scores-group">
          <span className={`priority-tag priority-${priority.toLowerCase()}`}>
            {priority} PRIORITY
          </span>
          <span className="relevance-badge">
            Relevance: <strong>{relevance_score}/100</strong>
          </span>
        </div>
      </div>

      <div className="rec-source-bar">
        <span className="source-label">Source: <strong>{sourceLabel}</strong></span>
        <span className="type-label">{learning_resource.resource_type} · {learning_resource.duration_hours} Hours</span>
      </div>

      {learning_resource.description && (
        <p className="rec-description">{learning_resource.description}</p>
      )}

      {/* Competency & level breakdown */}
      <div className="rec-details-grid">
        <div className="rec-detail-item">
          <span className="detail-label">Competency</span>
          <span className="detail-value text-accent">{competency_name}</span>
        </div>
        <div className="rec-detail-item">
          <span className="detail-label">Current Level</span>
          <span className="detail-value">Level {current_level}</span>
        </div>
        <div className="rec-detail-item">
          <span className="detail-label">Required Level</span>
          <span className="detail-value">Level {required_level}</span>
        </div>
        <div className="rec-detail-item">
          <span className="detail-label">Competency Gap</span>
          <span className="detail-value text-warning">{gap} level{gap > 1 ? 's' : ''}</span>
        </div>
        <div className="rec-detail-item">
          <span className="detail-label">Resource Level Range</span>
          <span className="detail-value">Level {learning_resource.minimum_level}–{learning_resource.maximum_level}</span>
        </div>
      </div>

      {/* Why recommended explanation */}
      <div className="rec-reason-box">
        <span className="reason-heading">💡 Why Recommended:</span>
        <p className="reason-text">{reason}</p>
      </div>

      {/* Action button */}
      <div className="rec-action-bar">
        {learning_resource.url ? (
          <a
            href={learning_resource.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
          >
            View Resource
          </a>
        ) : (
          <span className="demo-link-pending">
            Demo resource — integration link pending
          </span>
        )}
      </div>
    </div>
  )
}

/** Stat summary card */
function SummaryCard({ label, value, color, isText = false }) {
  return (
    <div className={`summary-card summary-card-${color}`}>
      <div className={`summary-value ${isText ? 'summary-value-text' : ''}`}>
        {value}
      </div>
      <div className="summary-label">{label}</div>
    </div>
  )
}

function formatSourceLabel(source) {
  switch (source) {
    case 'IGOT_DEMO':
      return 'iGOT Karmayogi — Demo Catalog'
    case 'NSSTA_TPAC_DEMO':
      return 'NSSTA / TPAC — Demo Catalog'
    default:
      return source
  }
}

export default Recommendations
