/**
 * UPSKILL AI - System Preferences & Settings View (Phase 7D)
 */
import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export function Settings() {
  const { user } = useAuth()
  const [theme] = useState('dark')
  const [notifications, setNotifications] = useState(true)
  const [emailAlerts, setEmailAlerts] = useState(false)
  const [savedMsg, setSavedMsg] = useState(false)

  const handleSave = (e) => {
    e.preventDefault()
    setSavedMsg(true)
    setTimeout(() => setSavedMsg(false), 3000)
  }

  return (
    <div className="profile-card settings-view">
      <div className="section-header">
        <div>
          <h2 className="learner-name">Platform Settings</h2>
          <p className="learner-email">Personalize interface and competency tracking alerts</p>
        </div>
        <span className="badge-sih">Preferences</span>
      </div>

      <form onSubmit={handleSave} className="settings-form">
        <div className="settings-group">
          <h3 className="settings-group-title">Display & Theme</h3>
          <div className="settings-row">
            <div>
              <div className="settings-item-label">Interface Theme</div>
              <div className="settings-item-sub">Dark charcoal & modern high-contrast statistical UI</div>
            </div>
            <span className="badge badge-connected" style={{ textTransform: 'capitalize' }}>{theme} (Active)</span>
          </div>
        </div>

        <div className="settings-group" style={{ marginTop: '20px' }}>
          <h3 className="settings-group-title">Notifications</h3>
          <div className="settings-row">
            <div>
              <div className="settings-item-label">Assessment Reminders</div>
              <div className="settings-item-sub">Alerts when new competency evaluations or quizzes are available</div>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={notifications}
                onChange={(e) => setNotifications(e.target.checked)}
              />
              <span className="toggle-slider" />
            </label>
          </div>

          <div className="settings-row">
            <div>
              <div className="settings-item-label">Email Gap Summaries</div>
              <div className="settings-item-sub">Receive weekly learning pathway recommendations via official email</div>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.checked)}
              />
              <span className="toggle-slider" />
            </label>
          </div>
        </div>

        <div className="settings-actions" style={{ marginTop: '24px' }}>
          <button type="submit" className="btn btn-primary">
            Save Preferences
          </button>
          {savedMsg && <span className="settings-saved-text">✓ Preferences saved locally.</span>}
        </div>
      </form>
    </div>
  )
}

export default Settings
