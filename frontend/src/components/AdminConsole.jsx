import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { useAuth } from '../context/AuthContext'

export function AdminConsole() {
  const { user, canAccessAdmin } = useAuth()
  const [activeTab, setActiveTab] = useState('stats') // 'stats' | 'review' | 'users' | 'audit'

  // Platform stats
  const [stats, setStats] = useState(null)
  const [loadingStats, setLoadingStats] = useState(false)

  // Pending courses
  const [pendingCourses, setPendingCourses] = useState([])
  const [loadingPending, setLoadingPending] = useState(false)
  const [rejectModalCourse, setRejectModalCourse] = useState(null)
  const [rejectNote, setRejectNote] = useState('')

  // Users management
  const [users, setUsers] = useState([])
  const [userTotal, setUserTotal] = useState(0)
  const [userSearch, setUserSearch] = useState('')
  const [userTypeFilter, setUserTypeFilter] = useState('')
  const [loadingUsers, setLoadingUsers] = useState(false)

  // Audit logs
  const [auditLogs, setAuditLogs] = useState([])
  const [loadingAudit, setLoadingAudit] = useState(false)

  // General banners
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)

  useEffect(() => {
    if (canAccessAdmin) {
      loadStats()
      loadPendingCourses()
      loadUsers()
      loadAuditLogs()
    }
  }, [canAccessAdmin])

  async function loadStats() {
    try {
      setLoadingStats(true)
      const data = await apiClient.getPlatformStats()
      setStats(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingStats(false)
    }
  }

  async function loadPendingCourses() {
    try {
      setLoadingPending(true)
      const data = await apiClient.getPendingCourses()
      setPendingCourses(data || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingPending(false)
    }
  }

  async function loadUsers(search = userSearch, type = userTypeFilter) {
    try {
      setLoadingUsers(true)
      const data = await apiClient.getAdminUsers({ search, account_type: type })
      setUsers(data?.users || [])
      setUserTotal(data?.total || 0)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingUsers(false)
    }
  }

  async function loadAuditLogs() {
    try {
      setLoadingAudit(true)
      const data = await apiClient.getAuditLogs(50, 0)
      setAuditLogs(data || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingAudit(false)
    }
  }

  async function handleApproveCourse(courseId) {
    try {
      setError(null)
      const updated = await apiClient.approveCourse(courseId)
      setSuccessMsg(`Course ${updated.code} has been approved and published to learners!`)
      await loadPendingCourses()
      await loadStats()
      await loadAuditLogs()
    } catch (err) {
      setError(err.message || 'Failed to approve course.')
    }
  }

  async function handleRejectCourse(e) {
    e.preventDefault()
    if (!rejectModalCourse || !rejectNote.trim()) return
    try {
      setError(null)
      const updated = await apiClient.rejectCourse(rejectModalCourse.id, rejectNote.trim())
      setSuccessMsg(`Course ${updated.code} returned to DRAFT with feedback note.`)
      setRejectModalCourse(null)
      setRejectNote('')
      await loadPendingCourses()
      await loadStats()
      await loadAuditLogs()
    } catch (err) {
      setError(err.message || 'Failed to reject course.')
    }
  }

  async function handleRoleChange(userId, newRole) {
    try {
      setError(null)
      const updated = await apiClient.updateUserRole(userId, newRole)
      setSuccessMsg(`Updated role for ${updated.email} to ${newRole}.`)
      await loadUsers()
      await loadStats()
      await loadAuditLogs()
    } catch (err) {
      setError(err.message || 'Failed to update user role.')
    }
  }

  async function handleStatusToggle(userId, currentActive) {
    try {
      setError(null)
      const updated = await apiClient.updateUserStatus(userId, !currentActive)
      const label = updated.is_active ? 'activated' : 'deactivated'
      setSuccessMsg(`Account for ${updated.email} is now ${label}.`)
      await loadUsers()
      await loadStats()
      await loadAuditLogs()
    } catch (err) {
      setError(err.message || 'Failed to change user status.')
    }
  }

  if (!canAccessAdmin) {
    return (
      <div className="profile-card error-card">
        <h3>Access Denied</h3>
        <p>The Admin Console is strictly reserved for platform administrators.</p>
      </div>
    )
  }

  return (
    <div className="dashboard-content-flow">
      {/* Header */}
      <div className="view-header-strip">
        <div className="view-title-wrap">
          <div className="badge-row">
            <span className="badge-pill bg-emerald">GOVERNANCE & AUDIT</span>
            <span className="badge-pill bg-purple">ADMIN CONSOLE</span>
          </div>
          <h2 className="view-main-heading">Platform Administration</h2>
          <p className="view-sub-heading">
            Manage user accounts, review curriculum submissions, inspect system metrics, and audit administrative actions.
          </p>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="notification-banner error-banner">
          <span>⚠ {error}</span>
          <button type="button" onClick={() => setError(null)} className="close-banner-btn">×</button>
        </div>
      )}
      {successMsg && (
        <div className="notification-banner success-banner">
          <span>✓ {successMsg}</span>
          <button type="button" onClick={() => setSuccessMsg(null)} className="close-banner-btn">×</button>
        </div>
      )}

      {/* Tabs */}
      <div className="admin-tab-nav">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'stats' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          📊 Platform Metrics
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'review' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('review')}
        >
          🔍 Review Queue {pendingCourses.length > 0 && <span className="tab-counter-badge">{pendingCourses.length}</span>}
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'users' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 User Directory & Roles ({userTotal})
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'audit' ? 'tab-btn-active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          📜 Audit Trail ({auditLogs.length})
        </button>
      </div>

      {/* TAB 1: PLATFORM STATS */}
      {activeTab === 'stats' && (
        <div className="stats-tab-content">
          {loadingStats ? (
            <div className="profile-card"><p className="loading-text">Computing system statistics...</p></div>
          ) : stats ? (
            <>
              {/* User breakdown cards */}
              <div className="admin-stats-grid">
                <div className="stat-card">
                  <div className="stat-label">TOTAL USERS</div>
                  <div className="stat-number">{stats.total_users}</div>
                  <div className="stat-caption">{stats.active_users} active accounts</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">LEARNERS</div>
                  <div className="stat-number">{stats.learners_count}</div>
                  <div className="stat-caption">Registered trainees</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">TRAINERS</div>
                  <div className="stat-number">{stats.trainers_count}</div>
                  <div className="stat-caption">Curriculum authors</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">ADMINISTRATORS</div>
                  <div className="stat-number">{stats.admins_count}</div>
                  <div className="stat-caption">Platform governors</div>
                </div>
              </div>

              {/* Course breakdown cards */}
              <div className="admin-stats-grid" style={{ marginTop: '1.25rem' }}>
                <div className="stat-card">
                  <div className="stat-label">PUBLISHED COURSES</div>
                  <div className="stat-number color-emerald">{stats.published_courses}</div>
                  <div className="stat-caption">Live in learner catalog</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">PENDING REVIEW</div>
                  <div className="stat-number color-blue">{stats.pending_courses}</div>
                  <div className="stat-caption">Awaiting review action</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">DRAFT COURSES</div>
                  <div className="stat-number color-amber">{stats.draft_courses}</div>
                  <div className="stat-caption">In-progress authoring</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">DIAGNOSTICS TAKEN</div>
                  <div className="stat-number color-purple">{stats.total_diagnostics_taken}</div>
                  <div className="stat-caption">Completed assessments</div>
                </div>
              </div>
            </>
          ) : (
            <p>No statistics available.</p>
          )}
        </div>
      )}

      {/* TAB 2: COURSE REVIEW QUEUE */}
      {activeTab === 'review' && (
        <div className="profile-card">
          <h4 className="section-title">Course Review & Quality Assurance Queue</h4>
          <p className="section-subtitle">
            Verify course competency coverage and questions before approving curriculum into production.
          </p>

          {loadingPending ? (
            <p className="loading-text">Loading pending courses...</p>
          ) : pendingCourses.length === 0 ? (
            <div className="empty-notice" style={{ marginTop: '1rem' }}>
              ✓ All course submissions have been reviewed. No pending courses.
            </div>
          ) : (
            <div className="review-course-list" style={{ marginTop: '1.25rem' }}>
              {pendingCourses.map((c) => (
                <div key={c.id} className="review-course-item-card">
                  <div className="review-item-header">
                    <span className="code-tag">{c.code}</span>
                    <span className="category-tag">{c.category}</span>
                    <span className="hours-tag">{c.estimated_hours}h</span>
                    <span className="status-pill status-pending_review">PENDING REVIEW</span>
                  </div>
                  <h4 style={{ margin: '0.5rem 0', fontSize: '1.15rem' }}>{c.name}</h4>
                  <p style={{ color: 'var(--text-secondary, #64748b)', fontSize: '0.9rem' }}>
                    {c.description || 'No description provided.'}
                  </p>

                  <div className="review-meta-pills" style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem' }}>
                    <span className="prio-pill prio-medium">
                      Mapped Competencies: {c.competencies_count}
                    </span>
                    <span className="prio-pill prio-medium">
                      Diagnostic Questions: {c.questions_count}
                    </span>
                  </div>

                  {c.competencies?.length > 0 && (
                    <div style={{ marginTop: '0.75rem', fontSize: '0.85rem' }}>
                      <strong>Competencies:</strong>{' '}
                      {c.competencies.map((comp) => comp.name).join(', ')}
                    </div>
                  )}

                  <div className="review-actions-line" style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
                    <button
                      type="button"
                      className="action-pill-btn btn-primary"
                      onClick={() => handleApproveCourse(c.id)}
                    >
                      ✓ Approve & Publish
                    </button>
                    <button
                      type="button"
                      className="action-pill-btn btn-secondary"
                      onClick={() => {
                        setRejectModalCourse(c)
                        setRejectNote('')
                      }}
                    >
                      ✗ Reject with Feedback Note
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: USER DIRECTORY & ROLES */}
      {activeTab === 'users' && (
        <div className="profile-card">
          <div className="user-filter-bar" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
            <input
              type="text"
              className="form-input"
              style={{ flex: 1, minWidth: '220px' }}
              placeholder="Search by name or email..."
              value={userSearch}
              onChange={(e) => {
                setUserSearch(e.target.value)
                loadUsers(e.target.value, userTypeFilter)
              }}
            />
            <select
              className="form-input"
              style={{ width: '180px' }}
              value={userTypeFilter}
              onChange={(e) => {
                setUserTypeFilter(e.target.value)
                loadUsers(userSearch, e.target.value)
              }}
            >
              <option value="">All Account Types</option>
              <option value="LEARNER">LEARNER</option>
              <option value="TRAINER">TRAINER</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>

          {loadingUsers ? (
            <p className="loading-text">Loading user directory...</p>
          ) : users.length === 0 ? (
            <div className="empty-notice">No users found.</div>
          ) : (
            <div className="table-responsive">
              <table className="studio-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Email</th>
                    <th>Designation / Dept</th>
                    <th>Account Type</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td>
                        <strong>{u.name}</strong>
                        {u.is_demo && <span className="demo-tag" style={{ marginLeft: '0.5rem' }}>DEMO</span>}
                      </td>
                      <td>{u.email}</td>
                      <td style={{ fontSize: '0.85rem' }}>
                        {u.designation ? `${u.designation} (${u.department || 'MoSPI'})` : '—'}
                      </td>
                      <td>
                        <select
                          className="role-select-box"
                          value={u.account_type || 'LEARNER'}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        >
                          <option value="LEARNER">LEARNER</option>
                          <option value="TRAINER">TRAINER</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>
                      </td>
                      <td>
                        <span className={`status-pill ${u.is_active ? 'status-published' : 'status-archived'}`}>
                          {u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {u.id !== user?.id && (
                          <button
                            type="button"
                            className={u.is_active ? 'action-link-danger' : 'action-link-success'}
                            onClick={() => handleStatusToggle(u.id, u.is_active)}
                          >
                            {u.is_active ? 'Deactivate' : 'Reactivate'}
                          </button>
                        )}
                        {u.id === user?.id && (
                          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>(You)</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div className="profile-card">
          <h4 className="section-title">Administrative Audit Trail</h4>
          <p className="section-subtitle">
            Immutable log of role escalations, course approvals, and user status modifications.
          </p>

          {loadingAudit ? (
            <p className="loading-text">Loading audit logs...</p>
          ) : auditLogs.length === 0 ? (
            <div className="empty-notice">No audit log records yet.</div>
          ) : (
            <div className="table-responsive" style={{ marginTop: '1rem' }}>
              <table className="studio-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Action</th>
                    <th>Administrator</th>
                    <th>Target</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td style={{ fontSize: '0.85rem', whiteSpace: 'nowrap' }}>
                        {log.created_at ? log.created_at.slice(0, 19).replace('T', ' ') : '—'}
                      </td>
                      <td>
                        <span className="badge-pill bg-blue" style={{ fontSize: '0.75rem' }}>
                          {log.action}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.85rem' }}>
                        {log.user_email || `Admin #${log.user_id}`}
                      </td>
                      <td style={{ fontSize: '0.85rem' }}>
                        {log.target_type} #{log.target_id}
                      </td>
                      <td style={{ fontSize: '0.85rem' }}>{log.details}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Rejection Note Modal */}
      {rejectModalCourse && (
        <div className="modal-backdrop">
          <div className="modal-box">
            <div className="modal-header">
              <h3 style={{ margin: 0 }}>Reject Course with Feedback</h3>
              <button
                type="button"
                className="close-modal-btn"
                onClick={() => setRejectModalCourse(null)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleRejectCourse} className="modal-body">
              <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                Course: <strong>{rejectModalCourse.code} — {rejectModalCourse.name}</strong>
              </p>
              <div className="form-group">
                <label>Review Note / Required Corrections</label>
                <textarea
                  rows={4}
                  className="form-input"
                  value={rejectNote}
                  onChange={(e) => setRejectNote(e.target.value)}
                  placeholder="Explain why this course cannot be approved and what changes the trainer needs to make..."
                  required
                />
              </div>
              <div className="modal-footer" style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  className="action-pill-btn btn-secondary"
                  onClick={() => setRejectModalCourse(null)}
                >
                  Cancel
                </button>
                <button type="submit" className="action-pill-btn btn-danger">
                  Reject & Send Feedback
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
