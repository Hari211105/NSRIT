import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'

/**
 * Displays the demo learner's competency profile in a clean table.
 * Shows current level vs required level for each competency.
 */
export function CompetencyProfile() {
  const [profile, setProfile] = useState(null)
  const [competencies, setCompetencies] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        setError(null)
        const [profileData, compData] = await Promise.all([
          apiClient.getLearnerProfile(),
          apiClient.getLearnerCompetencies(),
        ])
        setProfile(profileData)
        setCompetencies(compData)
      } catch (err) {
        setError('Could not load competency data. Make sure the backend is running.')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="profile-card">
        <p className="loading-text">Loading competency profile...</p>
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

  return (
    <div className="profile-card">
      {/* Learner header */}
      <div className="learner-header">
        <div className="learner-avatar">
          {profile?.name?.charAt(0) || 'D'}
        </div>
        <div>
          <h2 className="learner-name">{profile?.name}</h2>
          <p className="learner-role">
            <span className="role-tag">Role</span>
            {profile?.role?.name || '—'}
          </p>
          <p className="learner-email">{profile?.email}</p>
        </div>
      </div>

      {/* Section title */}
      <div className="section-header">
        <h3 className="section-title">Competency Profile</h3>
        <span className="demo-badge">Demo Data</span>
      </div>

      {/* Competency table */}
      <div className="table-wrapper">
        <table className="competency-table">
          <thead>
            <tr>
              <th>Competency</th>
              <th>Priority</th>
              <th>Current Level</th>
              <th>Required Level</th>
            </tr>
          </thead>
          <tbody>
            {competencies?.competencies?.map((item) => (
              <tr key={item.competency_id}>
                <td>
                  <span className="comp-name">{item.competency_name}</span>
                </td>
                <td>
                  <span className={`priority-tag priority-${item.priority?.toLowerCase()}`}>
                    {item.priority || '—'}
                  </span>
                </td>
                <td>
                  <LevelBadge level={item.current_level} label={item.current_level_label} type="current" />
                </td>
                <td>
                  <LevelBadge level={item.required_level} label={item.required_level_label} type="required" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="phase-note">
        Phase 2: Competency Profile — See Gap Analysis tab for gap details.
      </p>
    </div>
  )
}

/** Small colored badge to display a competency level */
function LevelBadge({ level, label, type }) {
  if (!level) return <span className="level-none">—</span>
  const cls = `level-badge level-${level} level-${type}`
  return (
    <span className={cls}>
      Level {level} · {label}
    </span>
  )
}

export default CompetencyProfile
