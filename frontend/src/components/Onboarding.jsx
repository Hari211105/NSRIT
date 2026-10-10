/**
 * UPSKILL AI - Multi-Sector User Onboarding (Phases 8 & 9)
 *
 * Shown when the signed-in user's profile is incomplete (no position/sector selected).
 * Allows the user to select:
 * 1. Sector (IT & Tech, Healthcare, Finance, Agriculture, Education, Governance)
 * 2. Position / Role within that sector
 * 3. Profile details (Designation, Department/Org, Education, Experience, etc.)
 */
import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { useAuth } from '../context/AuthContext'

const SECTOR_ICONS = {
  landmark: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 21h18M3 10h18M5 10v11M9 10v11M15 10v11M19 10v11M12 2L2 7h20L12 2z" />
    </svg>
  ),
  cpu: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <rect x="9" y="9" width="6" height="6" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3" />
    </svg>
  ),
  activity: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  ),
  'trending-up': (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
    </svg>
  ),
  sun: (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="5" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </svg>
  ),
  'book-open': (
    <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  ),
}

export function Onboarding() {
  const { user, refreshUser } = useAuth()
  const [sectors, setSectors] = useState([])
  const [roles, setRoles] = useState([])
  const [loadingStatus, setLoadingStatus] = useState(true)

  const [selectedSectorId, setSelectedSectorId] = useState(null)
  const [selectedRoleId, setSelectedRoleId] = useState(null)

  const [designation, setDesignation] = useState('')
  const [department, setDepartment] = useState('')
  const [assignment, setAssignment] = useState('')
  const [education, setEducation] = useState('')
  const [experience, setExperience] = useState('')
  const [training, setTraining] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Load sectors & roles from backend
  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const status = await apiClient.getOnboardingStatus()
        if (!mounted) return
        const loadedSectors = status.sectors || []
        const loadedRoles = status.roles || []
        setSectors(loadedSectors)
        setRoles(loadedRoles)

        // Select the first sector by default if available
        if (loadedSectors.length > 0) {
          setSelectedSectorId(loadedSectors[0].id)
        }
      } catch {
        if (mounted) setError('Could not load sector catalog. Please refresh.')
      } finally {
        if (mounted) setLoadingStatus(false)
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  // Filter roles based on selected sector
  const filteredRoles = roles.filter((r) => {
    if (!selectedSectorId) return true
    return r.sector_id === selectedSectorId
  })

  const handleSectorSelect = (sectorId) => {
    setSelectedSectorId(sectorId)
    // If the currently selected role doesn't belong to the new sector, reset it
    const roleStillValid = roles.some((r) => r.id === selectedRoleId && r.sector_id === sectorId)
    if (!roleStillValid) {
      setSelectedRoleId(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (submitting) return
    setError('')

    if (!selectedRoleId) {
      setError('Please select your specific position / role.')
      return
    }
    if (!designation.trim() || designation.trim().length < 2) {
      setError('Please enter your designation or job title.')
      return
    }
    if (!department.trim() || department.trim().length < 2) {
      setError('Please enter your department, college, or organization.')
      return
    }

    setSubmitting(true)
    try {
      await apiClient.completeOnboarding({
        role_id: selectedRoleId,
        designation: designation.trim(),
        department: department.trim(),
        assignment: assignment.trim() || null,
        education: education.trim() || null,
        work_experience: experience.trim() || null,
        previous_training: training.trim() || null,
      })
      await refreshUser()
    } catch (err) {
      setError(err?.message || 'Could not save your profile. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const currentSector = sectors.find((s) => s.id === selectedSectorId)

  return (
    <div className="onboarding-viewport">
      <div className="onboarding-scene">
        <div className="onboarding-glass-card">
          <div className="card-brand-row">
            <div className="card-brand-title">
              <span className="brand-upskill">UPSKILL </span>
              <span className="brand-ai">AI</span>
            </div>
            <div className="brand-badge-pill">MULTI-SECTOR PLATFORM</div>
          </div>

          <h2 className="onboarding-title">Welcome, {user?.name || 'Learner'} 👋</h2>
          <p className="onboarding-subtitle">
            Choose your sector and position to personalize your AI diagnostic assessment,
            competency map, and tailored upskilling curriculum.
          </p>

          {error && <div className="card-alert error">⚠ {error}</div>}

          {loadingStatus ? (
            <p className="loading-text">Loading competency catalog…</p>
          ) : (
            <form onSubmit={handleSubmit} className="card-form" noValidate>
              {/* ── STEP 1: SELECT SECTOR ── */}
              <div className="onboarding-field-block">
                <div className="step-heading-row">
                  <span className="step-number-tag">STEP 1</span>
                  <span className="detail-label">Select Your Domain / Sector *</span>
                </div>

                <div className="onboarding-sectors-grid">
                  {sectors.map((sec) => {
                    const isSelected = selectedSectorId === sec.id
                    return (
                      <button
                        key={sec.id}
                        type="button"
                        className={`onboarding-sector-card ${isSelected ? 'onboarding-sector-selected' : ''}`}
                        onClick={() => handleSectorSelect(sec.id)}
                        aria-pressed={isSelected}
                      >
                        <div className="sector-card-icon">
                          {SECTOR_ICONS[sec.icon] || SECTOR_ICONS.landmark}
                        </div>
                        <div className="sector-card-content">
                          <span className="sector-card-name">{sec.name}</span>
                          <span className="sector-card-desc">{sec.description}</span>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* ── STEP 2: SELECT POSITION / ROLE ── */}
              <div className="onboarding-field-block">
                <div className="step-heading-row">
                  <span className="step-number-tag">STEP 2</span>
                  <span className="detail-label">
                    Select Your Position ({currentSector ? currentSector.name : 'All'}) *
                  </span>
                </div>

                {filteredRoles.length === 0 ? (
                  <p className="no-roles-notice">No positions found for this sector.</p>
                ) : (
                  <div className="onboarding-roles-grid">
                    {filteredRoles.map((role) => (
                      <button
                        key={role.id}
                        type="button"
                        className={`onboarding-role-card ${selectedRoleId === role.id ? 'onboarding-role-selected' : ''}`}
                        onClick={() => setSelectedRoleId(role.id)}
                        aria-pressed={selectedRoleId === role.id}
                        title={role.description || ''}
                      >
                        <span className="onboarding-role-name">{role.name}</span>
                        {role.description && (
                          <span className="onboarding-role-desc">{role.description}</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
                <span className="onboarding-hint">
                  Your selected role customizes your diagnostic questions, required competency levels,
                  and automated skill gap matrix.
                </span>
              </div>

              {/* ── STEP 3: PROFILE DETAILS ── */}
              <div className="onboarding-field-block">
                <div className="step-heading-row">
                  <span className="step-number-tag">STEP 3</span>
                  <span className="detail-label">Professional Details *</span>
                </div>

                <div className="onboarding-fields-grid">
                  <div className="onboarding-field">
                    <label className="detail-label" htmlFor="ob-designation">
                      Designation / Title *
                    </label>
                    <input
                      id="ob-designation"
                      type="text"
                      className="card-input"
                      placeholder="e.g. Senior Software Engineer / Statistical Officer"
                      value={designation}
                      onChange={(e) => setDesignation(e.target.value)}
                      disabled={submitting}
                    />
                  </div>
                  <div className="onboarding-field">
                    <label className="detail-label" htmlFor="ob-department">
                      Organization / Department / College *
                    </label>
                    <input
                      id="ob-department"
                      type="text"
                      className="card-input"
                      placeholder="e.g. Technology Solutions / Directorate of Statistics"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      disabled={submitting}
                    />
                  </div>
                  <div className="onboarding-field">
                    <label className="detail-label" htmlFor="ob-assignment">
                      Current Project / Key Responsibility
                    </label>
                    <input
                      id="ob-assignment"
                      type="text"
                      className="card-input"
                      placeholder="e.g. Cloud migration / Survey enumeration"
                      value={assignment}
                      onChange={(e) => setAssignment(e.target.value)}
                      disabled={submitting}
                    />
                  </div>
                  <div className="onboarding-field">
                    <label className="detail-label" htmlFor="ob-education">
                      Highest Qualification
                    </label>
                    <input
                      id="ob-education"
                      type="text"
                      className="card-input"
                      placeholder="e.g. B.Tech Computer Science / M.Sc. Statistics"
                      value={education}
                      onChange={(e) => setEducation(e.target.value)}
                      disabled={submitting}
                    />
                  </div>
                  <div className="onboarding-field">
                    <label className="detail-label" htmlFor="ob-experience">
                      Work Experience
                    </label>
                    <input
                      id="ob-experience"
                      type="text"
                      className="card-input"
                      placeholder="e.g. 3 years in full-stack development"
                      value={experience}
                      onChange={(e) => setExperience(e.target.value)}
                      disabled={submitting}
                    />
                  </div>
                  <div className="onboarding-field">
                    <label className="detail-label" htmlFor="ob-training">
                      Previous Certifications / Courses
                    </label>
                    <input
                      id="ob-training"
                      type="text"
                      className="card-input"
                      placeholder="e.g. NPTEL / AWS / SWAYAM certifications"
                      value={training}
                      onChange={(e) => setTraining(e.target.value)}
                      disabled={submitting}
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                className="card-submit-btn"
                disabled={submitting}
              >
                {submitting ? (
                  <span>Saving Profile…</span>
                ) : (
                  <>
                    <span>Complete Onboarding & Enter Platform</span>
                    <span className="submit-arrow">→</span>
                  </>
                )}
              </button>
            </form>
          )}
        </div>

        <div className="login-bottom-motto">
          ASSESS &nbsp;|&nbsp; MAP &nbsp;|&nbsp; UPSKILL
        </div>
      </div>
    </div>
  )
}

export default Onboarding
