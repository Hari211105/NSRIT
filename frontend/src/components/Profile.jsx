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
          <p className="learner-email">Identity &amp; learning pathway parameters</p>
        </div>
        <span className="badge-sih">{user?.learning_mode === 'GOAL' ? 'Goal Pathway' : 'Professional Record'}</span>
      </div>

      <div className="learner-header" style={{ marginBottom: '24px' }}>
        <div className="learner-avatar">
          {user?.name?.charAt(0) || 'L'}
        </div>
        <div>
          <h2 className="learner-name">{user?.name}</h2>
          <p className="learner-role">
            <span className="role-tag">{user?.learning_mode === 'GOAL' ? 'Enrolled Course' : 'Role'}</span>
            {user?.learning_mode === 'GOAL' ? (user?.course?.name || 'Selected Course') : (user?.role?.name || 'Professional Role')}
          </p>
          <p className="learner-email">{user?.email}</p>
        </div>
      </div>

      <div className="profile-fields-grid">
        <div className="profile-field-item">
          <span className="field-label">Email Address</span>
          <span className="field-value">{user?.email}</span>
        </div>
        <div className="profile-field-item">
          <span className="field-label">{user?.learning_mode === 'GOAL' ? 'Target Course' : 'Assigned Role'}</span>
          <span className="field-value">
            {user?.learning_mode === 'GOAL'
              ? (user?.course?.name || 'General Learning Track')
              : (user?.role?.name || 'Professional Role')}
          </span>
        </div>
        <div className="profile-field-item">
          <span className="field-label">Learning Pathway</span>
          <span className="field-value">
            {user?.learning_mode === 'GOAL' ? 'Subject & Skill Mastery (Self-paced)' : 'Role Competency Development'}
          </span>
        </div>
        <div className="profile-field-item">
          <span className="field-label">Department / Organization</span>
          <span className="field-value">{user?.department || (user?.learning_mode === 'GOAL' ? 'Independent Learner' : 'Organization Member')}</span>
        </div>
        {user?.assignment && (
          <div className="profile-field-item">
            <span className="field-label">Current Focus / Assignment</span>
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
            <span className="field-label">Experience</span>
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
        Target competency benchmarks and required levels are dynamically calibrated to accelerate your personalized mastery.
      </p>
    </div>
  )
}

export default Profile
