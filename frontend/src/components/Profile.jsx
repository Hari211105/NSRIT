/**
 * UPSKILL AI - Learner Profile & Official Details View (Phase 7D)
 */
import React from 'react'
import { useAuth } from '../context/AuthContext'

export function Profile() {
  const { user } = useAuth()

  return (
    <div className="profile-card profile-details-view">
      <div className="section-header">
        <div>
          <h2 className="learner-name">Learner Profile</h2>
          <p className="learner-email">Official identity & role parameters</p>
        </div>
        <span className="badge-sih">Cadre Record</span>
      </div>

      <div className="learner-header" style={{ marginBottom: '24px' }}>
        <div className="learner-avatar">
          {user?.name?.charAt(0) || 'D'}
        </div>
        <div>
          <h2 className="learner-name">{user?.name}</h2>
          <p className="learner-role">
            <span className="role-tag">Designation</span>
            {user?.role?.name || 'Statistical Officer'}
          </p>
          <p className="learner-email">{user?.email}</p>
        </div>
      </div>

      <div className="profile-fields-grid">
        <div className="profile-field-item">
          <span className="field-label">Official Email</span>
          <span className="field-value">{user?.email}</span>
        </div>
        <div className="profile-field-item">
          <span className="field-label">Assigned Role</span>
          <span className="field-value">{user?.role?.name || 'Statistical Officer'}</span>
        </div>
        <div className="profile-field-item">
          <span className="field-label">Account Category</span>
          <span className="field-value">{user?.is_demo ? 'Official Demonstration Account' : 'Standard Cadre Account'}</span>
        </div>
        <div className="profile-field-item">
          <span className="field-label">Department / Organization</span>
          <span className="field-value">{user?.department || 'Ministry of Statistics & Programme Implementation (MoSPI)'}</span>
        </div>
        {user?.assignment && (
          <div className="profile-field-item">
            <span className="field-label">Current Assignment</span>
            <span className="field-value">{user.assignment}</span>
          </div>
        )}
        {user?.education && (
          <div className="profile-field-item">
            <span className="field-label">Education</span>
            <span className="field-value">{user.education}</span>
          </div>
        )}
        {user?.work_experience && (
          <div className="profile-field-item">
            <span className="field-label">Work Experience</span>
            <span className="field-value">{user.work_experience}</span>
          </div>
        )}
        {user?.previous_training && (
          <div className="profile-field-item">
            <span className="field-label">Previous Training</span>
            <span className="field-value">{user.previous_training}</span>
          </div>
        )}
      </div>

      <p className="phase-note" style={{ marginTop: '24px' }}>
        Role competencies and required target levels are managed centrally by the statistical system administrator.
      </p>
    </div>
  )
}

export default Profile
