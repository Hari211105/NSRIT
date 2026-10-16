import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { useAuth } from '../context/AuthContext'

export function CoursePlayer({ courseId, initialLessonId, onBack, onCompleteCourse }) {
  const { user } = useAuth()
  const [course, setCourse] = useState(null)
  const [modules, setModules] = useState([])
  const [progress, setProgress] = useState(null)
  const [activeLesson, setActiveLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [completing, setCompleting] = useState(false)
  const [error, setError] = useState(null)
  const [completionBanner, setCompletionBanner] = useState(null)

  // Certificate Modal state
  const [certData, setCertData] = useState(null)
  const [loadingCert, setLoadingCert] = useState(false)
  const [certError, setCertError] = useState(null)

  useEffect(() => {
    loadCourseCurriculum()
  }, [courseId])

  async function loadCourseCurriculum() {
    try {
      setLoading(true)
      setError(null)
      const [courseData, modulesData, progData] = await Promise.all([
        apiClient.getCourse(courseId).catch(() => null),
        apiClient.getCourseModules(courseId).catch(() => []),
        apiClient.getCourseProgress(courseId).catch(() => null),
      ])

      setCourse(courseData)
      setModules(modulesData || [])
      setProgress(progData)

      // Find first lesson to select
      let targetLessonId = initialLessonId
      if (!targetLessonId && modulesData && modulesData.length > 0) {
        // Find first incomplete lesson, or default to first lesson
        for (const m of modulesData) {
          const firstIncomplete = (m.lessons || []).find((l) => !l.completed)
          if (firstIncomplete) {
            targetLessonId = firstIncomplete.id
            break
          }
        }
        if (!targetLessonId && modulesData[0].lessons && modulesData[0].lessons.length > 0) {
          targetLessonId = modulesData[0].lessons[0].id
        }
      }

      if (targetLessonId) {
        await loadLesson(targetLessonId)
      }
    } catch (err) {
      setError(err.message || 'Failed to load course player.')
    } finally {
      setLoading(false)
    }
  }

  async function loadLesson(lessonId) {
    try {
      setError(null)
      const lessonDetail = await apiClient.getLesson(lessonId)
      setActiveLesson(lessonDetail)
    } catch (err) {
      setError(err.message || 'Failed to load lesson.')
    }
  }

  async function handleMarkComplete() {
    if (!activeLesson || completing) return
    try {
      setCompleting(true)
      setError(null)
      const res = await apiClient.completeLesson(activeLesson.id)

      // Update active lesson completion state
      setActiveLesson((prev) => ({
        ...prev,
        completed: true,
        completed_at: res.completed_at,
      }))

      // Refresh progress & modules state
      const [updatedModules, updatedProgress] = await Promise.all([
        apiClient.getCourseModules(courseId),
        apiClient.getCourseProgress(courseId),
      ])
      setModules(updatedModules || [])
      setProgress(updatedProgress)

      if (res.certificate_issued) {
        setCompletionBanner({
          title: '🎉 Course Completed!',
          message: 'Congratulations! You have completed all lessons and satisfied all benchmark criteria for this course. Your verified certificate has been issued.',
          readyForCert: true,
        })
      } else if (res.progress_percent >= 100 && !res.certificate_issued) {
        setCompletionBanner({
          title: 'All Lessons Completed!',
          message: updatedProgress?.min_diagnostic_score
            ? `All lessons are complete. A minimum diagnostic assessment score of ${Math.round(updatedProgress.min_diagnostic_score)}% is required to unlock your certificate.`
            : 'All lessons completed.',
          readyForCert: false,
        })
      }

      // Automatically navigate to next lesson if available
      if (activeLesson.next_lesson_id) {
        await loadLesson(activeLesson.next_lesson_id)
      }
    } catch (err) {
      setError(err.message || 'Failed to mark lesson complete.')
    } finally {
      setCompleting(false)
    }
  }

  async function handleOpenCertificate() {
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

  // Format lesson body for TEXT
  function renderLessonBody(body) {
    if (!body) return <p style={{ color: '#94a3b8' }}>No content available for this lesson.</p>

    const paragraphs = body.split('\n\n')
    return (
      <div className="lesson-markdown-body" style={{ lineHeight: 1.7, fontSize: '1rem', color: 'var(--text-primary)' }}>
        {paragraphs.map((p, idx) => {
          const trimmed = p.trim()
          if (trimmed.startsWith('# ')) {
            return <h1 key={idx} style={{ margin: '1.25rem 0 0.75rem 0', fontSize: '1.6rem', color: 'var(--text-primary)' }}>{trimmed.slice(2)}</h1>
          }
          if (trimmed.startsWith('## ')) {
            return <h2 key={idx} style={{ margin: '1.25rem 0 0.5rem 0', fontSize: '1.35rem', color: 'var(--text-primary)' }}>{trimmed.slice(3)}</h2>
          }
          if (trimmed.startsWith('### ')) {
            return <h3 key={idx} style={{ margin: '1rem 0 0.5rem 0', fontSize: '1.15rem', color: 'var(--text-primary)' }}>{trimmed.slice(4)}</h3>
          }
          if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            const items = trimmed.split('\n').map((line) => line.replace(/^[-*]\s+/, ''))
            return (
              <ul key={idx} style={{ margin: '0.75rem 0 0.75rem 1.5rem', padding: 0 }}>
                {items.map((it, iIdx) => (
                  <li key={iIdx} style={{ marginBottom: '6px' }}>{it}</li>
                ))}
              </ul>
            )
          }
          if (trimmed.startsWith('```') && trimmed.endsWith('```')) {
            const codeLines = trimmed.slice(3, -3).replace(/^[a-z]+\n/i, '')
            return (
              <pre
                key={idx}
                style={{
                  background: '#0f172a',
                  color: '#f8fafc',
                  padding: '14px 18px',
                  borderRadius: '8px',
                  overflowX: 'auto',
                  fontFamily: 'monospace',
                  fontSize: '0.9rem',
                  margin: '1rem 0',
                }}
              >
                <code>{codeLines}</code>
              </pre>
            )
          }
          return (
            <p key={idx} style={{ margin: '0.75rem 0' }}>
              {trimmed}
            </p>
          )
        })}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="profile-card">
        <p className="loading-text">Loading course player and lesson curriculum...</p>
      </div>
    )
  }

  const percent = Math.round(progress?.progress_percent || 0)
  const isCompleted = progress?.status === 'COMPLETED'

  return (
    <div className="course-player-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Bar */}
      <div className="profile-card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            type="button"
            className="action-pill-btn btn-secondary"
            onClick={onBack}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            ← Back to Courses
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge-pill bg-blue" style={{ fontSize: '10px' }}>
                {course?.category || 'TECHNICAL'}
              </span>
              <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-primary)' }}>
                {course?.name || 'Accredited Course'}
              </h3>
            </div>
            <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Course Code: <strong>{course?.code}</strong> · {progress?.total_lessons || 0} Total Lessons
            </span>
          </div>
        </div>

        {/* Progress & Certificate trigger */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ textAlign: 'right', minWidth: '160px' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              Progress: <strong>{percent}%</strong> ({progress?.completed_lessons || 0}/{progress?.total_lessons || 0})
            </div>
            <div style={{ height: '8px', width: '100%', background: 'var(--border-color, #e2e8f0)', borderRadius: '4px', overflow: 'hidden' }}>
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

          {(isCompleted || progress?.certificate_issued) && (
            <button
              type="button"
              className="action-pill-btn btn-primary"
              onClick={handleOpenCertificate}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              🎓 Certificate
            </button>
          )}
        </div>
      </div>

      {/* Advisory Banners */}
      {progress?.unmet_prerequisites && progress.unmet_prerequisites.length > 0 && !isCompleted && (
        <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', borderRadius: '8px', padding: '12px 16px', color: '#b45309', fontSize: '0.875rem' }}>
          <strong>⚠️ Prerequisite Advisory:</strong> The following recommended prerequisite courses are not yet completed:
          <span style={{ marginLeft: '6px', fontWeight: 600 }}>
            {progress.unmet_prerequisites.map((p) => `${p.course_name} (${p.course_code})`).join(', ')}
          </span>. You may continue, but foundational knowledge is advised.
        </div>
      )}

      {completionBanner && (
        <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', borderRadius: '8px', padding: '14px 18px', color: '#047857', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong>{completionBanner.title}</strong> {completionBanner.message}
          </div>
          {completionBanner.readyForCert && (
            <button
              type="button"
              className="action-pill-btn btn-primary"
              onClick={handleOpenCertificate}
              style={{ marginLeft: '12px' }}
            >
              View Certificate
            </button>
          )}
        </div>
      )}

      {error && (
        <div className="error-banner" style={{ padding: '12px 16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', color: '#b91c1c' }}>
          ⚠ {error}
        </div>
      )}

      {/* Main 2-Column Workspace: Sidebar Curriculum + Lesson Viewport */}
      <div className="player-layout-grid" style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', alignItems: 'start' }}>
        {/* Left Column: Modules & Lessons Navigation */}
        <div className="profile-card player-curriculum-sidebar" style={{ maxHeight: 'calc(100vh - 220px)', overflowY: 'auto', padding: '16px' }}>
          <h4 style={{ margin: '0 0 14px 0', fontSize: '1rem', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color, #e2e8f0)', paddingBottom: '8px' }}>
            Course Curriculum
          </h4>

          {modules.map((m, mIdx) => (
            <div key={m.id} style={{ marginBottom: '16px' }}>
              <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>Module {mIdx + 1}:</span>
                <span style={{ color: 'var(--text-primary)' }}>{m.title}</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {(m.lessons || []).map((les) => {
                  const isActive = activeLesson?.id === les.id
                  const isDone = les.completed

                  return (
                    <button
                      key={les.id}
                      type="button"
                      onClick={() => loadLesson(les.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: isActive ? '1px solid var(--accent-color, #2563eb)' : '1px solid transparent',
                        background: isActive ? 'rgba(37, 99, 235, 0.1)' : 'transparent',
                        color: isActive ? 'var(--accent-color, #2563eb)' : 'var(--text-primary)',
                        cursor: 'pointer',
                        textAlign: 'left',
                        fontSize: '0.85rem',
                        transition: 'background 0.2s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                        <span style={{ fontSize: '1rem' }}>
                          {isDone ? '✅' : les.lesson_type === 'VIDEO_URL' ? '🎬' : les.lesson_type === 'LINK' ? '🔗' : '📄'}
                        </span>
                        <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                          {les.title}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8', whiteSpace: 'nowrap', marginLeft: '6px' }}>
                        {les.estimated_minutes}m
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Right Column: Active Lesson Content Display */}
        <div className="profile-card player-content-viewport" style={{ padding: '24px' }}>
          {activeLesson ? (
            <div>
              {/* Lesson Meta Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color, #e2e8f0)', paddingBottom: '16px', marginBottom: '20px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span className="badge-pill bg-purple" style={{ fontSize: '10px' }}>
                      {activeLesson.lesson_type}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                      Estimated: {activeLesson.estimated_minutes} min
                    </span>
                    {activeLesson.completed && (
                      <span className="badge-pill bg-emerald" style={{ fontSize: '10px' }}>
                        Completed ✓
                      </span>
                    )}
                  </div>
                  <h2 style={{ margin: 0, fontSize: '1.45rem', color: 'var(--text-primary)' }}>
                    {activeLesson.title}
                  </h2>
                </div>

                {/* Mark as complete button */}
                <button
                  type="button"
                  className={`action-pill-btn ${activeLesson.completed ? 'btn-secondary' : 'btn-primary'}`}
                  disabled={completing}
                  onClick={handleMarkComplete}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {activeLesson.completed ? 'Completed ✓ (Re-complete)' : completing ? 'Saving...' : 'Mark as Complete & Next →'}
                </button>
              </div>

              {/* Lesson Media / Body Presentation */}
              <div style={{ marginBottom: '32px' }}>
                {activeLesson.lesson_type === 'VIDEO_URL' && (
                  <div style={{ marginBottom: '24px' }}>
                    {activeLesson.body && (activeLesson.body.includes('youtube.com') || activeLesson.body.includes('youtu.be')) ? (
                      <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', borderRadius: '8px', background: '#000' }}>
                        <iframe
                          src={activeLesson.body.replace('watch?v=', 'embed/')}
                          title={activeLesson.title}
                          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 0 }}
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                        />
                      </div>
                    ) : (
                      <div style={{ background: 'rgba(37, 99, 235, 0.05)', border: '1px solid #93c5fd', borderRadius: '8px', padding: '20px', textAlign: 'center' }}>
                        <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🎬</div>
                        <h4 style={{ margin: '0 0 8px 0' }}>Video Training Resource</h4>
                        <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '14px' }}>
                          This lesson includes a recorded lecture or tutorial from the MoSPI training archives.
                        </p>
                        <a
                          href={activeLesson.body}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="action-pill-btn btn-primary"
                          style={{ display: 'inline-flex' }}
                        >
                          Watch Video in New Tab ↗
                        </a>
                      </div>
                    )}
                  </div>
                )}

                {activeLesson.lesson_type === 'LINK' && (
                  <div style={{ background: 'rgba(37, 99, 235, 0.05)', border: '1px solid #93c5fd', borderRadius: '8px', padding: '20px', marginBottom: '24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '1.4rem' }}>🔗</span>
                      <h4 style={{ margin: 0, fontSize: '1.1rem' }}>External Accredited Reference Material</h4>
                    </div>
                    <p style={{ color: '#475569', fontSize: '0.9rem', marginBottom: '14px' }}>
                      Access the official external reading, publication or government portal resource below:
                    </p>
                    <a
                      href={activeLesson.body}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="action-pill-btn btn-primary"
                      style={{ display: 'inline-flex' }}
                    >
                      Open Learning Material ({activeLesson.body}) ↗
                    </a>
                  </div>
                )}

                {/* Markdown body for TEXT or supplementary instructions */}
                {activeLesson.lesson_type === 'TEXT' && renderLessonBody(activeLesson.body)}
              </div>

              {/* Bottom Nav Controls */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color, #e2e8f0)', paddingTop: '16px' }}>
                <button
                  type="button"
                  className="action-pill-btn btn-secondary"
                  disabled={!activeLesson.prev_lesson_id}
                  onClick={() => activeLesson.prev_lesson_id && loadLesson(activeLesson.prev_lesson_id)}
                >
                  ← Previous Lesson
                </button>

                <button
                  type="button"
                  className="action-pill-btn btn-primary"
                  disabled={!activeLesson.next_lesson_id}
                  onClick={() => activeLesson.next_lesson_id && loadLesson(activeLesson.next_lesson_id)}
                >
                  Next Lesson →
                </button>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b' }}>
              Select a lesson from the curriculum sidebar on the left to begin learning.
            </div>
          )}
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

export default CoursePlayer
