import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { useAuth } from '../context/AuthContext'

export function MyCourses({ onOpenCourse }) {
  const { user } = useAuth()
  const [enrolledCourses, setEnrolledCourses] = useState([])
  const [catalogCourses, setCatalogCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [enrollingId, setEnrollingId] = useState(null)
  const [error, setError] = useState(null)
  const [infoNotice, setInfoNotice] = useState(null)

  // Certificate Modal state
  const [certData, setCertData] = useState(null)
  const [loadingCert, setLoadingCert] = useState(false)
  const [certError, setCertError] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      setError(null)
      const [myList, catList] = await Promise.all([
        apiClient.getMyCourses().catch(() => []),
        apiClient.getCourses().catch(() => []),
      ])
      setEnrolledCourses(myList || [])
      setCatalogCourses(catList || [])
    } catch (err) {
      setError(err.message || 'Could not load course curriculum.')
    } finally {
      setLoading(false)
    }
  }

  async function handleEnroll(courseId) {
    try {
      setEnrollingId(courseId)
      setError(null)
      setInfoNotice(null)
      const res = await apiClient.enrollCourse(courseId)
      if (res.warning) {
        setInfoNotice(`Enrolled successfully! Notice: ${res.warning}`)
      } else {
        setInfoNotice('Successfully enrolled in course!')
      }
      await loadData()
    } catch (err) {
      setError(err.message || 'Enrollment failed.')
    } finally {
      setEnrollingId(null)
    }
  }

  async function handleViewCertificate(courseId) {
    try {
      setLoadingCert(true)
      setCertError(null)
      const cert = await apiClient.getCourseCertificate(courseId)
      setCertData(cert)
    } catch (err) {
      setCertError(err.message || 'Unable to retrieve course certificate.')
    } finally {
      setLoadingCert(false)
    }
  }

  const enrolledIds = new Set(enrolledCourses.map((c) => c.id))

  if (loading) {
    return (
      <div className="profile-card">
        <p className="loading-text">Loading enrolled courses and curriculum tracks...</p>
      </div>
    )
  }

  return (
    <div className="my-courses-container">
      {/* Header */}
      <div className="section-header" style={{ marginBottom: '20px' }}>
        <div>
          <h2 className="learner-name" style={{ marginBottom: '4px' }}>
            My Courses & Curriculum Tracks
          </h2>
          <p className="learner-email">
            Structured modular learning paths, lesson progression, and accredited certificates for {user?.name}
          </p>
        </div>
        <span className="badge-sih">Accredited Learning</span>
      </div>

      {infoNotice && (
        <div className="info-banner" style={{ marginBottom: '1.25rem', padding: '12px 16px', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid #3b82f6', borderRadius: '8px', color: '#1d4ed8', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>ℹ {infoNotice}</span>
          <button type="button" onClick={() => setInfoNotice(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.1rem', color: '#1d4ed8' }}>×</button>
        </div>
      )}

      {error && (
        <div className="error-banner" style={{ marginBottom: '1.25rem', padding: '12px 16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', color: '#b91c1c' }}>
          ⚠ {error}
        </div>
      )}

      {/* Enrolled Courses Section */}
      <div style={{ marginBottom: '32px' }}>
        <h3 className="section-title" style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          Active Enrollments ({enrolledCourses.length})
        </h3>

        {enrolledCourses.length === 0 ? (
          <div className="profile-card empty-state" style={{ textAlign: 'center', padding: '36px 20px' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📚</div>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '1.1rem' }}>No Active Course Enrollments</h4>
            <p style={{ color: '#64748b', maxWidth: '460px', margin: '0 auto 20px auto' }}>
              You have not enrolled in any structured courses yet. Browse the accredited catalog below to start your statistical and technical training path.
            </p>
          </div>
        ) : (
          <div className="course-cards-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
            {enrolledCourses.map((c) => {
              const isCompleted = c.status === 'COMPLETED'
              const percent = Math.round(c.progress_percent || 0)
              const hasUnmet = c.unmet_prerequisites && c.unmet_prerequisites.length > 0

              return (
                <div key={c.id} className="profile-card course-track-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    {/* Header tags */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <span className="badge-pill bg-blue" style={{ fontSize: '11px', textTransform: 'uppercase' }}>
                        {c.category || 'TECHNICAL'}
                      </span>
                      <span
                        className={`badge-pill ${isCompleted ? 'bg-emerald' : percent > 0 ? 'bg-purple' : 'bg-neutral'}`}
                        style={{ fontSize: '11px' }}
                      >
                        {isCompleted ? 'COMPLETED' : percent > 0 ? 'IN PROGRESS' : 'NOT STARTED'}
                      </span>
                    </div>

                    <h4 style={{ margin: '0 0 6px 0', fontSize: '1.15rem', color: 'var(--text-primary)' }}>
                      {c.name}
                    </h4>
                    <p style={{ fontSize: '0.85rem', color: '#64748b', margin: '0 0 14px 0' }}>
                      Code: <strong>{c.code}</strong> · {c.estimated_hours || 20} Hours · {c.level_hint || 'Beginner'}
                    </p>

                    {c.description && (
                      <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 16px 0' }}>
                        {c.description}
                      </p>
                    )}

                    {/* Prerequisite warning notice */}
                    {hasUnmet && !isCompleted && (
                      <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', borderRadius: '6px', padding: '8px 12px', fontSize: '0.825rem', color: '#b45309', marginBottom: '14px' }}>
                        <strong>⚠️ Advisory:</strong> Recommended prerequisite incomplete:
                        <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                          {c.unmet_prerequisites.map((p) => (
                            <li key={p.course_id}>{p.course_name} ({p.course_code})</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Progress Bar */}
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', marginBottom: '6px' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Curriculum Progress</span>
                        <strong style={{ color: isCompleted ? '#10b981' : 'var(--text-primary)' }}>
                          {c.completed_lessons || 0} / {c.total_lessons || 0} lessons ({percent}%)
                        </strong>
                      </div>
                      <div style={{ height: '8px', background: 'var(--border-color, #e2e8f0)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${percent}%`,
                            background: isCompleted ? '#10b981' : 'var(--accent-color, #2563eb)',
                            borderRadius: '4px',
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '10px', marginTop: '12px', borderTop: '1px solid var(--border-color, #e2e8f0)', paddingTop: '14px' }}>
                    <button
                      type="button"
                      className="action-pill-btn btn-primary"
                      style={{ flex: 1, justifyContent: 'center' }}
                      onClick={() => onOpenCourse && onOpenCourse(c.id)}
                    >
                      {isCompleted ? 'Review Lessons' : percent > 0 ? 'Continue Learning →' : 'Start Course →'}
                    </button>

                    {isCompleted && (
                      <button
                        type="button"
                        className="action-pill-btn btn-secondary"
                        style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                        onClick={() => handleViewCertificate(c.id)}
                        title="View Accredited Certificate"
                      >
                        🎓 Certificate
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Course Catalog (Enrollment) */}
      <div style={{ marginTop: '40px' }}>
        <h3 className="section-title" style={{ marginBottom: '16px' }}>
          Explore More Accredited Courses
        </h3>
        <p className="section-subtitle" style={{ marginBottom: '20px' }}>
          Courses developed by MoSPI trainers aligned to the National Competency Framework.
        </p>

        <div className="course-cards-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
          {catalogCourses.map((c) => {
            const isEnrolled = enrolledIds.has(c.id)
            return (
              <div key={c.id} className="profile-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                    <span className="badge-pill bg-blue" style={{ fontSize: '11px', textTransform: 'uppercase' }}>
                      {c.category || 'TECHNICAL'}
                    </span>
                    <span className="badge-pill bg-neutral" style={{ fontSize: '11px' }}>
                      {c.level_hint || 'Beginner'}
                    </span>
                  </div>

                  <h4 style={{ margin: '0 0 6px 0', fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                    {c.name}
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: '#64748b', margin: '0 0 12px 0' }}>
                    Code: <strong>{c.code}</strong> · {c.estimated_hours || 20} Hours
                  </p>

                  {c.description && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 14px 0' }}>
                      {c.description}
                    </p>
                  )}
                </div>

                <div style={{ borderTop: '1px solid var(--border-color, #e2e8f0)', paddingTop: '12px', marginTop: '12px' }}>
                  {isEnrolled ? (
                    <button
                      type="button"
                      className="action-pill-btn btn-secondary"
                      style={{ width: '100%', justifyContent: 'center' }}
                      onClick={() => onOpenCourse && onOpenCourse(c.id)}
                    >
                      Enrolled ✓ (Open Course)
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="action-pill-btn btn-primary"
                      style={{ width: '100%', justifyContent: 'center' }}
                      disabled={enrollingId === c.id}
                      onClick={() => handleEnroll(c.id)}
                    >
                      {enrollingId === c.id ? 'Enrolling...' : 'Enroll in Course'}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Certificate Modal */}
      {(certData || loadingCert || certError) && (
        <div className="modal-backdrop" onClick={() => { setCertData(null); setCertError(null); }}>
          <div className="modal-dialog cert-modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '720px', width: '92%' }}>
            <div className="modal-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ margin: 0, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                🎓 Accredited Certificate of Completion
              </h4>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => { setCertData(null); setCertError(null); }}
              >
                ×
              </button>
            </div>

            <div className="modal-body" style={{ padding: '24px' }}>
              {loadingCert && <p className="loading-text">Retrieving authenticated certificate...</p>}
              {certError && (
                <div className="error-banner">
                  ⚠ {certError}
                </div>
              )}
              {certData && (
                <div
                  id="printable-certificate"
                  style={{
                    border: '8px double #1e3a8a',
                    padding: '36px 30px',
                    textAlign: 'center',
                    background: '#fafaf9',
                    color: '#1e293b',
                    borderRadius: '4px',
                    position: 'relative',
                  }}
                >
                  {/* Emblem / Header */}
                  <div style={{ marginBottom: '14px' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#1e3a8a' }}>
                      Government of India
                    </div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>
                      Ministry of Statistics and Programme Implementation (MoSPI)
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#475569', letterSpacing: '0.05em' }}>
                      National Statistical Systems Training Academy (NSSTA) & UPSKILL AI
                    </div>
                  </div>

                  <hr style={{ border: 'none', borderTop: '2px solid #cbd5e1', width: '60%', margin: '14px auto' }} />

                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#1e3a8a', letterSpacing: '0.05em', textTransform: 'uppercase', margin: '16px 0 8px 0' }}>
                    Certificate of Course Completion
                  </div>

                  <p style={{ fontSize: '0.9rem', color: '#64748b', margin: '0 0 16px 0' }}>
                    This is to certify that
                  </p>

                  <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#0f172a', margin: '0 0 14px 0', textDecoration: 'underline', textDecorationColor: '#3b82f6' }}>
                    {certData.user_name}
                  </div>

                  <p style={{ fontSize: '0.925rem', color: '#334155', lineHeight: 1.6, maxWidth: '520px', margin: '0 auto 20px auto' }}>
                    has successfully completed all required modules, lessons, and competency benchmarks for the accredited course:
                  </p>

                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e3a8a', background: 'rgba(30, 58, 138, 0.06)', padding: '10px 18px', borderRadius: '6px', display: 'inline-block', margin: '0 0 20px 0' }}>
                    {certData.course_name}
                  </div>

                  {certData.diagnostic_score !== null && certData.diagnostic_score !== undefined && (
                    <p style={{ fontSize: '0.85rem', color: '#059669', fontWeight: 600, margin: '0 0 16px 0' }}>
                      ✓ Diagnostic Assessment Score Verified: {Math.round(certData.diagnostic_score)}%
                    </p>
                  )}

                  {/* Meta details */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderTop: '1px solid #e2e8f0', paddingTop: '18px', marginTop: '20px', fontSize: '0.8rem', color: '#64748b' }}>
                    <div style={{ textAlign: 'left' }}>
                      <div><strong>Date of Completion:</strong> {new Date(certData.completed_at).toLocaleDateString()}</div>
                      <div><strong>Lessons Completed:</strong> {certData.total_lessons}</div>
                      <div><strong>Verification ID:</strong> {certData.verification_code}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ borderBottom: '1px solid #94a3b8', width: '140px', marginBottom: '4px' }}></div>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>Director of Training</div>
                      <div>NSSTA / UPSKILL AI</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', padding: '16px 24px' }}>
              <button
                type="button"
                className="action-pill-btn btn-secondary"
                onClick={() => { setCertData(null); setCertError(null); }}
              >
                Close
              </button>
              {certData && (
                <button
                  type="button"
                  className="action-pill-btn btn-primary"
                  onClick={() => window.print()}
                >
                  🖨 Print / Save PDF
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MyCourses
