/**
 * UPSKILL AI - Dual Onboarding: Role-Based vs. Goal-Based (Phase 10)
 *
 * 1. Screen 0: "How do you want to learn?"
 *    - "Prepare for a role" (Role path: sector -> role -> profile)
 *    - "Learn a subject" (Goal path: technical/non-technical course -> streamlined profile)
 * 2. Role Path: Sector picker -> Role picker -> Designation & Department (required).
 * 3. Goal Path: Course picker with Technical / Non-Technical tabs -> Short profile (skips employee-only fields).
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
  const [courses, setCourses] = useState([])
  const [loadingStatus, setLoadingStatus] = useState(true)

  // Learning Mode: 'ROLE' | 'GOAL'
  const [learningMode, setLearningMode] = useState('ROLE')
  // Course category filter and search for GOAL mode: 'ALL' | 'TECHNICAL' | 'NON_TECHNICAL'
  const [courseCategoryFilter, setCourseCategoryFilter] = useState('ALL')
  const [courseSearchTerm, setCourseSearchTerm] = useState('')

  // Selections
  const [selectedSectorId, setSelectedSectorId] = useState(null)
  const [selectedRoleId, setSelectedRoleId] = useState(null)
  const [selectedCourseId, setSelectedCourseId] = useState(null)

  // Profile Details
  const [designation, setDesignation] = useState('')
  const [department, setDepartment] = useState('')
  const [assignment, setAssignment] = useState('')
  const [education, setEducation] = useState('')
  const [experience, setExperience] = useState('')
  const [training, setTraining] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Load catalog data from backend
  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const status = await apiClient.getOnboardingStatus()
        if (!mounted) return
        const loadedSectors = status.sectors || []
        const loadedRoles = status.roles || []
        const loadedCourses = status.courses || []
        setSectors(loadedSectors)
        setRoles(loadedRoles)
        setCourses(loadedCourses)

        if (loadedSectors.length > 0) {
          setSelectedSectorId(loadedSectors[0].id)
        }
        if (loadedCourses.length > 0) {
          setSelectedCourseId(loadedCourses[0].id)
        }
      } catch {
        if (mounted) setError('Could not load catalog. Please refresh.')
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

  // Filter courses based on selected category and search term
  const filteredCourses = courses.filter((c) => {
    const matchesCat = courseCategoryFilter === 'ALL' || c.category === courseCategoryFilter
    if (!matchesCat) return false
    if (!courseSearchTerm.trim()) return true
    const term = courseSearchTerm.toLowerCase().trim()
    return (
      (c.name && c.name.toLowerCase().includes(term)) ||
      (c.description && c.description.toLowerCase().includes(term)) ||
      (c.code && c.code.toLowerCase().includes(term))
    )
  })

  const handleSectorSelect = (sectorId) => {
    setSelectedSectorId(sectorId)
    const roleStillValid = roles.some((r) => r.id === selectedRoleId && r.sector_id === sectorId)
    if (!roleStillValid) {
      setSelectedRoleId(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (submitting) return
    setError('')

    if (learningMode === 'ROLE') {
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
    } else {
      // GOAL mode
      if (!selectedCourseId) {
        setError('Please select the subject or course you want to learn.')
        return
      }
    }

    setSubmitting(true)
    try {
      const payload = {
        learning_mode: learningMode,
        role_id: learningMode === 'ROLE' ? selectedRoleId : null,
        course_id: learningMode === 'GOAL' ? selectedCourseId : null,
        designation: designation.trim() || null,
        department: department.trim() || null,
        assignment: assignment.trim() || null,
        education: education.trim() || null,
        work_experience: experience.trim() || null,
        previous_training: training.trim() || null,
      }

      await apiClient.completeOnboarding(payload)
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
            <div className="brand-badge-pill">PERSONALIZED LEARNING PLATFORM</div>
          </div>

          <h2 className="onboarding-title">Welcome, {user?.name || 'Learner'} 👋</h2>
          <p className="onboarding-subtitle">
            Choose your learning pathway: train for a professional role or learn a specific subject at your own pace.
          </p>

          {error && <div className="card-alert error">⚠ {error}</div>}

          {loadingStatus ? (
            <p className="loading-text">Loading competency and course catalog…</p>
          ) : (
            <form onSubmit={handleSubmit} className="card-form" noValidate>
              {/* ── PATHWAY SELECTION: ROLE vs GOAL ── */}
              <div className="onboarding-field-block">
                <div className="step-heading-row">
                  <span className="step-number-tag">STEP 1</span>
                  <span className="detail-label">How do you want to learn? *</span>
                </div>

                <div className="onboarding-mode-grid">
                  <button
                    type="button"
                    className={`mode-select-card ${learningMode === 'ROLE' ? 'mode-select-active' : ''}`}
                    onClick={() => setLearningMode('ROLE')}
                    aria-pressed={learningMode === 'ROLE'}
                  >
                    <div className="mode-card-icon">🎯</div>
                    <div className="mode-card-info">
                      <span className="mode-card-title">Prepare for a Role</span>
                      <span className="mode-card-desc">
                        Select your professional position or career track. Get assessed against industry competency standards with tailored skill gap analysis.
                      </span>
                    </div>
                  </button>

                  <button
                    type="button"
                    className={`mode-select-card ${learningMode === 'GOAL' ? 'mode-select-active' : ''}`}
                    onClick={() => setLearningMode('GOAL')}
                    aria-pressed={learningMode === 'GOAL'}
                  >
                    <div className="mode-card-icon">📚</div>
                    <div className="mode-card-info">
                      <span className="mode-card-title">Learn a Subject</span>
                      <span className="mode-card-desc">
                        Pick a technical or non-technical course to master. Fast-track your learning journey without workplace profile requirements.
                      </span>
                    </div>
                  </button>
                </div>
              </div>

              {/* ════════════════════════════════════════════════════════
                  PATHWAY A: ROLE-BASED ONBOARDING
                  ════════════════════════════════════════════════════════ */}
              {learningMode === 'ROLE' ? (
                <>
                  {/* Step 2: Sector Selection */}
                  <div className="onboarding-field-block">
                    <div className="step-heading-row">
                      <span className="step-number-tag">STEP 2</span>
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

                  {/* Step 3: Role Selection */}
                  <div className="onboarding-field-block">
                    <div className="step-heading-row">
                      <span className="step-number-tag">STEP 3</span>
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
                  </div>

                  {/* Step 4: Professional Profile */}
                  <div className="onboarding-field-block">
                    <div className="step-heading-row">
                      <span className="step-number-tag">STEP 4</span>
                      <span className="detail-label">Professional Details *</span>
                    </div>

                    <div className="onboarding-fields-grid">
                      <div className="onboarding-field">
                        <label className="detail-label" htmlFor="ob-designation">
                          Designation / Job Title *
                        </label>
                        <input
                          id="ob-designation"
                          type="text"
                          className="card-input"
                          placeholder="e.g. Statistical Officer / Software Engineer"
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
                          placeholder="e.g. Directorate of Statistics / Tech Labs"
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
                          placeholder="e.g. Survey compilation / Cloud migration"
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
                          placeholder="e.g. B.Tech / M.Sc. Statistics"
                          value={education}
                          onChange={(e) => setEducation(e.target.value)}
                          disabled={submitting}
                        />
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                /* ════════════════════════════════════════════════════════
                   PATHWAY B: GOAL-BASED (COURSE) ONBOARDING
                   ════════════════════════════════════════════════════════ */
                <>
                  {/* Step 2: Course Picker with Technical/Non-Technical Filter */}
                  <div className="onboarding-field-block">
                    <div className="step-heading-row">
                      <span className="step-number-tag">STEP 2</span>
                      <span className="detail-label">Select Course / Subject *</span>
                    </div>

                    <div className="course-search-filter-wrap">
                      <div className="course-search-input-box">
                        <span className="search-icon">🔍</span>
                        <input
                          type="text"
                          className="course-search-input"
                          placeholder="Search courses by title, topic, or keyword…"
                          value={courseSearchTerm}
                          onChange={(e) => setCourseSearchTerm(e.target.value)}
                        />
                        {courseSearchTerm && (
                          <button
                            type="button"
                            className="search-clear-btn"
                            onClick={() => setCourseSearchTerm('')}
                            aria-label="Clear search"
                          >
                            ✕
                          </button>
                        )}
                      </div>

                      <div className="course-filter-bar">
                        <button
                          type="button"
                          className={`filter-tab-btn ${courseCategoryFilter === 'ALL' ? 'filter-tab-active' : ''}`}
                          onClick={() => setCourseCategoryFilter('ALL')}
                        >
                          All Subjects ({courses.length})
                        </button>
                        <button
                          type="button"
                          className={`filter-tab-btn ${courseCategoryFilter === 'TECHNICAL' ? 'filter-tab-active' : ''}`}
                          onClick={() => setCourseCategoryFilter('TECHNICAL')}
                        >
                          Technical ({courses.filter((c) => c.category === 'TECHNICAL').length})
                        </button>
                        <button
                          type="button"
                          className={`filter-tab-btn ${courseCategoryFilter === 'NON_TECHNICAL' ? 'filter-tab-active' : ''}`}
                          onClick={() => setCourseCategoryFilter('NON_TECHNICAL')}
                        >
                          Non-Technical ({courses.filter((c) => c.category === 'NON_TECHNICAL').length})
                        </button>
                      </div>
                    </div>

                    {filteredCourses.length === 0 ? (
                      <div className="courses-empty-state">
                        <p>No courses match "{courseSearchTerm}". Try clearing filters or searching for another term.</p>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => {
                            setCourseSearchTerm('')
                            setCourseCategoryFilter('ALL')
                          }}
                        >
                          Reset Filters
                        </button>
                      </div>
                    ) : (
                      <div className="onboarding-courses-grid">
                        {filteredCourses.map((crs) => {
                          const isSelected = selectedCourseId === crs.id
                          return (
                            <button
                              key={crs.id}
                              type="button"
                              className={`onboarding-course-card ${isSelected ? 'onboarding-course-selected' : ''}`}
                              onClick={() => setSelectedCourseId(crs.id)}
                              aria-pressed={isSelected}
                            >
                              <div className="course-card-header">
                                <span className={`course-cat-badge ${crs.category === 'TECHNICAL' ? 'cat-tech' : 'cat-non-tech'}`}>
                                  {crs.category === 'TECHNICAL' ? '💻 TECHNICAL' : '💡 NON-TECHNICAL'}
                                </span>
                                <div className="course-meta-tags">
                                  <span className="course-hours-tag">⏱ {crs.estimated_hours || 20} hrs</span>
                                  <span className="course-level-tag">{crs.level_hint || 'All Levels'}</span>
                                </div>
                              </div>
                              <span className="course-card-name">{crs.name}</span>
                              <span className="course-card-desc">{crs.description}</span>
                            </button>
                          )
                        })}
                      </div>
                    )}
                    <span className="onboarding-hint">
                      Your chosen subject maps out targeted competencies, a diagnostic assessment, and structured learning modules.
                    </span>
                  </div>

                  {/* Step 3: Streamlined Profile (No employee fields) */}
                  <div className="onboarding-field-block">
                    <div className="step-heading-row">
                      <span className="step-number-tag">STEP 3</span>
                      <span className="detail-label">Learner Profile (Optional)</span>
                    </div>

                    <div className="onboarding-fields-grid">
                      <div className="onboarding-field">
                        <label className="detail-label" htmlFor="ob-goal-education">
                          Education / Major (Optional)
                        </label>
                        <input
                          id="ob-goal-education"
                          type="text"
                          className="card-input"
                          placeholder="e.g. Student / Graduate / Self-learner"
                          value={education}
                          onChange={(e) => setEducation(e.target.value)}
                          disabled={submitting}
                        />
                      </div>
                      <div className="onboarding-field">
                        <label className="detail-label" htmlFor="ob-goal-training">
                          Prior Courses / Certifications (Optional)
                        </label>
                        <input
                          id="ob-goal-training"
                          type="text"
                          className="card-input"
                          placeholder="e.g. Beginner tutorials / Coursera / NPTEL"
                          value={training}
                          onChange={(e) => setTraining(e.target.value)}
                          disabled={submitting}
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              <button
                type="submit"
                className="card-submit-btn"
                disabled={submitting}
              >
                {submitting ? (
                  <span>Saving Profile…</span>
                ) : (
                  <>
                    <span>{learningMode === 'ROLE' ? 'Save Role Profile & Enter Platform' : 'Enroll in Subject & Start Learning'}</span>
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
