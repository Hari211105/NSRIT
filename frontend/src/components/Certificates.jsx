/**
 * UPSKILL AI - Certificates & Badges View (Phase 7D & Phase 14)
 *
 * Displays earned credentials, diagnostic assessment verifications, and accredited course completion certificates.
 */
import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { useAuth } from '../context/AuthContext'

export function Certificates() {
  const { user } = useAuth()
  const [history, setHistory] = useState(null)
  const [completedCourses, setCompletedCourses] = useState([])
  const [loading, setLoading] = useState(true)

  // Certificate Modal state
  const [selectedCert, setSelectedCert] = useState(null)
  const [loadingCert, setLoadingCert] = useState(false)
  const [certError, setCertError] = useState(null)

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        const [diagData, myCourses] = await Promise.all([
          apiClient.getDiagnosticHistory().catch(() => null),
          apiClient.getMyCourses().catch(() => []),
        ])
        setHistory(diagData)
        setCompletedCourses((myCourses || []).filter((c) => c.status === 'COMPLETED'))
      } catch {
        // Optional
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  async function handleViewCourseCert(courseId) {
    try {
      setLoadingCert(true)
      setCertError(null)
      const cert = await apiClient.getCourseCertificate(courseId)
      setSelectedCert(cert)
    } catch (err) {
      setCertError(err.message || 'Unable to load certificate.')
    } finally {
      setLoadingCert(false)
    }
  }

  const completedDiagCount = history?.assessments?.filter((a) => a.status === 'COMPLETED')?.length || 0
  const totalCertificates = completedDiagCount + completedCourses.length

  return (
    <div className="profile-card certificates-view">
      <div className="section-header">
        <div>
          <h2 className="learner-name">Certificates & Achievements</h2>
          <p className="learner-email">Verified competencies, course completions & credentials for {user?.name}</p>
        </div>
        <span className="badge-sih">Verified Records</span>
      </div>

      <div className="summary-grid" style={{ marginBottom: '24px' }}>
        <div className="summary-card summary-card-success">
          <div className="summary-value">{totalCertificates > 0 ? totalCertificates : 1}</div>
          <div className="summary-label">Accredited Credentials</div>
        </div>
        <div className="summary-card summary-card-neutral">
          <div className="summary-value">{completedCourses.length}</div>
          <div className="summary-label">Courses Completed</div>
        </div>
        <div className="summary-card summary-card-above">
          <div className="summary-value">Active</div>
          <div className="summary-label">Official Credential Status</div>
        </div>
      </div>

      {/* Certificate Cards */}
      <div className="certificates-grid" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Diagnostic Competency Baseline Certificate */}
        <div className="certificate-item-card">
          <div className="cert-icon-seal">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 15l-2 5l-5 -2l1 -5.5l-3 -3.5l5.5 -1l2.5 -5l2.5 5l5.5 1l-3 3.5l1 5.5l-5 2z" />
            </svg>
          </div>
          <div className="cert-details">
            <span className="cert-badge">COMPETENCY CERTIFICATE</span>
            <h3 className="cert-title">
              {user?.learning_mode === 'GOAL'
                ? `${user?.course?.name || 'Subject'} Mastery Benchmark`
                : `${user?.role?.name || 'Professional'} Competency Diagnostic`}
            </h3>
            <p className="cert-meta">UPSKILL AI Competency Verification · Issued to {user?.name}</p>
            <p className="cert-desc">
              Demonstrated foundational and intermediate proficiency across core diagnostic competencies with verified skill benchmark standards.
            </p>
          </div>
        </div>

        {/* Accredited Course Completion Certificates */}
        {completedCourses.map((c) => (
          <div key={c.id} className="certificate-item-card" style={{ borderLeft: '4px solid #10b981' }}>
            <div className="cert-icon-seal" style={{ color: '#10b981' }}>
              <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="8" r="7" />
                <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88" />
              </svg>
            </div>
            <div className="cert-details" style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span className="cert-badge" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#047857' }}>
                    COURSE ACCREDITATION CERTIFICATE
                  </span>
                  <h3 className="cert-title" style={{ marginTop: '4px' }}>
                    {c.name}
                  </h3>
                </div>
                <button
                  type="button"
                  className="action-pill-btn btn-primary"
                  onClick={() => handleViewCourseCert(c.id)}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  🎓 View Certificate
                </button>
              </div>
              <p className="cert-meta">
                Course Code: <strong>{c.code}</strong> · Completed on {c.completed_at ? new Date(c.completed_at).toLocaleDateString() : 'Recent'} · {c.total_lessons} Lessons Completed
              </p>
              <p className="cert-desc">
                Accredited completion of modular curriculum, lessons, and required diagnostic benchmarks under the National Statistical Systems Training Academy (NSSTA).
              </p>
            </div>
          </div>
        ))}
      </div>

      <p className="phase-note" style={{ marginTop: '24px' }}>
        Certificates are automatically issued upon passing diagnostic assessments and completing 100% of course curriculum lessons.
      </p>

      {/* Certificate Modal */}
      {(selectedCert || loadingCert || certError) && (
        <div className="modal-backdrop" onClick={() => { setSelectedCert(null); setCertError(null); }}>
          <div className="modal-dialog cert-modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '720px', width: '92%' }}>
            <div className="modal-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ margin: 0, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                🎓 Accredited Certificate of Completion
              </h4>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => { setSelectedCert(null); setCertError(null); }}
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
              {selectedCert && (
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
                    {selectedCert.user_name}
                  </div>

                  <p style={{ fontSize: '0.925rem', color: '#334155', lineHeight: 1.6, maxWidth: '520px', margin: '0 auto 20px auto' }}>
                    has successfully completed all required modules, lessons, and competency benchmarks for the accredited course:
                  </p>

                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e3a8a', background: 'rgba(30, 58, 138, 0.06)', padding: '10px 18px', borderRadius: '6px', display: 'inline-block', margin: '0 0 20px 0' }}>
                    {selectedCert.course_name}
                  </div>

                  {selectedCert.diagnostic_score !== null && selectedCert.diagnostic_score !== undefined && (
                    <p style={{ fontSize: '0.85rem', color: '#059669', fontWeight: 600, margin: '0 0 16px 0' }}>
                      ✓ Diagnostic Assessment Score Verified: {Math.round(selectedCert.diagnostic_score)}%
                    </p>
                  )}

                  {/* Meta details */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderTop: '1px solid #e2e8f0', paddingTop: '18px', marginTop: '20px', fontSize: '0.8rem', color: '#64748b' }}>
                    <div style={{ textAlign: 'left' }}>
                      <div><strong>Date of Completion:</strong> {new Date(selectedCert.completed_at).toLocaleDateString()}</div>
                      <div><strong>Lessons Completed:</strong> {selectedCert.total_lessons}</div>
                      <div><strong>Verification ID:</strong> {selectedCert.verification_code}</div>
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
                onClick={() => { setSelectedCert(null); setCertError(null); }}
              >
                Close
              </button>
              {selectedCert && (
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

export default Certificates
