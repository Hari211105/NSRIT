/**
 * UPSKILL AI - Main Application Component
 * Matches upskill-dashboard-white.png and upskill-dashboard-black.png with 100% precision:
 * - Theme context support (Light mode & Dark mode switchable)
 * - Persistent Sidebar with modern icons, navigation, and signed-in user card with logout
 * - Main Top Bar with Search, Notification Bell, Theme toggle, and MoSPI Ministry Emblem block
 * - Dynamic view rendering (Dashboard Overview, Competency, Skill Gaps, Learning, Assessments, Profile, Settings)
 */
import React, { useState, useEffect } from 'react'
import { useAuth } from './context/AuthContext'
import { useTheme } from './context/ThemeContext'
import { Login } from './components/Login'
import { Onboarding } from './components/Onboarding'
import { DashboardOverview } from './components/DashboardOverview'
import { CompetencyProfile } from './components/CompetencyProfile'
import { GapAnalysis } from './components/GapAnalysis'
import { Recommendations } from './components/Recommendations'
import { DiagnosticAssessment } from './components/DiagnosticAssessment'
import { DocumentQuiz } from './components/DocumentQuiz'
import { PdfUploadQuiz } from './components/PdfUploadQuiz'
import { Certificates } from './components/Certificates'
import { Profile } from './components/Profile'
import { Settings } from './components/Settings'
import { CourseStudio } from './components/CourseStudio'
import { AdminConsole } from './components/AdminConsole'

export const VIEWS = {
  DASHBOARD: 'dashboard',
  COMPETENCY: 'competency',
  GAPS: 'gaps',
  LEARNING: 'learning',
  ASSESSMENTS: 'assessments',
  PROFILE: 'profile',
  SETTINGS: 'settings',
  TRAINER_STUDIO: 'trainer_studio',
  ADMIN_CONSOLE: 'admin_console',
}

export const ASSESSMENT_VIEWS = {
  DIAGNOSTIC: 'diagnostic',
  QUIZ: 'quiz',
}

export function App() {
  const { status, user, logout, canAccessTrainer, canAccessAdmin } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [activeView, setActiveView] = useState(VIEWS.DASHBOARD)
  const [activeAssessment, setActiveAssessment] = useState(ASSESSMENT_VIEWS.DIAGNOSTIC)
  const [assessmentsExpanded, setAssessmentsExpanded] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showMobileSidebar, setShowMobileSidebar] = useState(false)

  // Route guard: learners cannot access trainer studio or admin console
  useEffect(() => {
    if (activeView === VIEWS.TRAINER_STUDIO && !canAccessTrainer) {
      setActiveView(VIEWS.DASHBOARD)
    }
    if (activeView === VIEWS.ADMIN_CONSOLE && !canAccessAdmin) {
      setActiveView(VIEWS.DASHBOARD)
    }
  }, [activeView, canAccessTrainer, canAccessAdmin])

  // Handle cross-component navigation
  const handleQuickNavigate = (target) => {
    if (target === 'diagnostic') {
      setActiveView(VIEWS.ASSESSMENTS)
      setActiveAssessment(ASSESSMENT_VIEWS.DIAGNOSTIC)
    } else if (target === 'pdf_quiz') {
      setActiveView(VIEWS.ASSESSMENTS)
      setActiveAssessment(ASSESSMENT_VIEWS.QUIZ)
    } else if (target === 'learning') {
      setActiveView(VIEWS.LEARNING)
    } else if (target === 'gaps') {
      setActiveView(VIEWS.GAPS)
    } else if (target === 'competency') {
      setActiveView(VIEWS.COMPETENCY)
    } else {
      setActiveView(target)
    }
  }

  // If loading session state, show centered loader
  if (status === 'loading') {
    return (
      <div className="auth-loading-screen">
        <div className="loading-spinner-box">
          <div className="spinner-ring" />
          <p className="loading-text">Authenticating official session...</p>
        </div>
      </div>
    )
  }

  // If unauthenticated, show the Login page
  if (status === 'unauthenticated') {
    return <Login />
  }

  // Phase 8: a signed-in user whose profile is incomplete (no position
  // selected yet) must finish onboarding first. Existing users keep
  // profile_completed=true in the database and skip straight to the app.
  if (status === 'authenticated' && user && user.profile_completed === false) {
    return <Onboarding />
  }

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : 'D'

  return (
    <div className={`app-root-shell ${theme === 'dark' ? 'theme-dark' : 'theme-light'}`}>
      {/* ══════════════════════════════════════════════════════════════
          SIDEBAR: Fixed Left Nav
          ══════════════════════════════════════════════════════════════ */}
      <aside className={`main-sidebar ${showMobileSidebar ? 'mobile-visible' : ''}`}>
        {/* Top Logo */}
        <div className="sidebar-brand-block">
          <h1 className="sidebar-brand-title">UPSKILL AI</h1>
        </div>

        {/* Sidebar Navigation */}
        <nav className="sidebar-nav-list" aria-label="Main Navigation">
          {/* Dashboard */}
          <button
            type="button"
            className={`nav-btn ${activeView === VIEWS.DASHBOARD ? 'nav-btn-active' : ''}`}
            onClick={() => {
              setActiveView(VIEWS.DASHBOARD)
              setShowMobileSidebar(false)
            }}
          >
            <div className="nav-btn-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <rect x="3" y="3" width="8" height="8" rx="2" />
                <rect x="13" y="3" width="8" height="8" rx="2" />
                <rect x="3" y="13" width="8" height="8" rx="2" />
                <rect x="13" y="13" width="8" height="8" rx="2" />
              </svg>
            </div>
            <span className="nav-btn-label">Dashboard</span>
          </button>

          {/* My Competency */}
          <button
            type="button"
            className={`nav-btn ${activeView === VIEWS.COMPETENCY ? 'nav-btn-active' : ''}`}
            onClick={() => {
              setActiveView(VIEWS.COMPETENCY)
              setShowMobileSidebar(false)
            }}
          >
            <div className="nav-btn-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a4 4 0 0 1 4 4c0 1.5-.8 2.8-2 3.5v1a2 2 0 0 1-2 2h0a2 2 0 0 1-2-2v-1c-1.2-.7-2-2-2-3.5a4 4 0 0 1 4-4z" />
                <path d="M7 16a5 5 0 0 0 10 0" />
                <circle cx="12" cy="19" r="2" />
              </svg>
            </div>
            <span className="nav-btn-label">My Competency</span>
          </button>

          {/* Skill Gaps */}
          <button
            type="button"
            className={`nav-btn ${activeView === VIEWS.GAPS ? 'nav-btn-active' : ''}`}
            onClick={() => {
              setActiveView(VIEWS.GAPS)
              setShowMobileSidebar(false)
            }}
          >
            <div className="nav-btn-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                <line x1="12" y1="22.08" x2="12" y2="12" />
              </svg>
            </div>
            <span className="nav-btn-label">Skill Gaps</span>
          </button>

          {/* My Learning */}
          <button
            type="button"
            className={`nav-btn ${activeView === VIEWS.LEARNING ? 'nav-btn-active' : ''}`}
            onClick={() => {
              setActiveView(VIEWS.LEARNING)
              setShowMobileSidebar(false)
            }}
          >
            <div className="nav-btn-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </div>
            <span className="nav-btn-label">My Learning</span>
          </button>

          {/* Assessments with Dropdown Toggle */}
          <div className="nav-item-dropdown-wrap">
            <button
              type="button"
              className={`nav-btn ${activeView === VIEWS.ASSESSMENTS ? 'nav-btn-active' : ''}`}
              onClick={() => {
                setActiveView(VIEWS.ASSESSMENTS)
                setAssessmentsExpanded(!assessmentsExpanded)
                setShowMobileSidebar(false)
              }}
            >
              <div className="nav-btn-icon">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
              </div>
              <span className="nav-btn-label">Assessments</span>
              <span className={`dropdown-chevron ${assessmentsExpanded ? 'chevron-rotated' : ''}`}>
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </span>
            </button>
          </div>

          {/* Profile */}
          <button
            type="button"
            className={`nav-btn ${activeView === VIEWS.PROFILE ? 'nav-btn-active' : ''}`}
            onClick={() => {
              setActiveView(VIEWS.PROFILE)
              setShowMobileSidebar(false)
            }}
          >
            <div className="nav-btn-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <span className="nav-btn-label">Profile</span>
          </button>

          {/* Course Studio (Trainer & Admin) */}
          {canAccessTrainer && (
            <button
              type="button"
              className={`nav-btn ${activeView === VIEWS.TRAINER_STUDIO ? 'nav-btn-active' : ''}`}
              onClick={() => {
                setActiveView(VIEWS.TRAINER_STUDIO)
                setShowMobileSidebar(false)
              }}
            >
              <div className="nav-btn-icon">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                  <line x1="12" y1="6" x2="16" y2="6" />
                  <line x1="12" y1="10" x2="16" y2="10" />
                </svg>
              </div>
              <span className="nav-btn-label">Course Studio</span>
            </button>
          )}

          {/* Admin Console (Admin Only) */}
          {canAccessAdmin && (
            <button
              type="button"
              className={`nav-btn ${activeView === VIEWS.ADMIN_CONSOLE ? 'nav-btn-active' : ''}`}
              onClick={() => {
                setActiveView(VIEWS.ADMIN_CONSOLE)
                setShowMobileSidebar(false)
              }}
            >
              <div className="nav-btn-icon">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                  <line x1="8" y1="21" x2="16" y2="21" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
              </div>
              <span className="nav-btn-label">Admin Console</span>
            </button>
          )}

          {/* Settings */}
          <button
            type="button"
            className={`nav-btn ${activeView === VIEWS.SETTINGS ? 'nav-btn-active' : ''}`}
            onClick={() => {
              setActiveView(VIEWS.SETTINGS)
              setShowMobileSidebar(false)
            }}
          >
            <div className="nav-btn-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </div>
            <span className="nav-btn-label">Settings</span>
          </button>
        </nav>

        {/* Sidebar Footer: Signed-in User Card & Sign Out */}
        <div className="sidebar-footer-user">
          <div className="user-avatar-badge">{userInitial}</div>
          <div className="user-text-meta">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="user-name-text">{user?.name || 'Demo Officer'}</span>
              <span
                className={`badge-pill ${user?.account_type === 'ADMIN' ? 'bg-emerald' : user?.account_type === 'TRAINER' ? 'bg-purple' : 'bg-blue'}`}
                style={{ fontSize: '10px', padding: '1px 6px', lineHeight: '14px' }}
              >
                {user?.account_type || 'LEARNER'}
              </span>
            </div>
            <span className="user-email-text">{user?.email || 'demo@statslearn.in'}</span>
          </div>
          <button
            type="button"
            className="sidebar-logout-icon-btn"
            onClick={logout}
            title="Sign Out"
            aria-label="Sign Out"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </aside>

      {/* ══════════════════════════════════════════════════════════════
          MAIN CONTENT VIEW AREA
          ══════════════════════════════════════════════════════════════ */}
      <div className="main-viewport-wrapper">
        {/* Top Header Bar */}
        <header className="top-header-bar">
          {/* Mobile hamburger */}
          <button
            type="button"
            className="hamburger-menu-btn"
            onClick={() => setShowMobileSidebar(!showMobileSidebar)}
            aria-label="Toggle Navigation"
          >
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>

          {/* Search Pill Input */}
          <div className="top-search-pill">
            <svg className="search-lens-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              className="search-text-input"
              placeholder="Search courses, competencies, or learning paths..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Right Header: Theme Toggle, Notifications, Government Header */}
          <div className="top-header-right">
            {/* Theme Toggle (Light / Dark) */}
            <button
              type="button"
              className="theme-switch-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
              aria-label="Toggle Theme"
            >
              {theme === 'dark' ? (
                /* Sun Icon */
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              ) : (
                /* Moon Icon */
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
            </button>

            {/* Notification Bell with Red Indicator Dot */}
            <button
              type="button"
              className="notification-bell-btn"
              title="Notifications"
              aria-label="Notifications"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
              <span className="bell-red-dot" />
            </button>

            <span
              className={`badge-pill ${user?.account_type === 'ADMIN' ? 'bg-emerald' : user?.account_type === 'TRAINER' ? 'bg-purple' : 'bg-blue'}`}
              style={{ fontSize: '11px', padding: '3px 8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}
            >
              {user?.account_type || 'LEARNER'}
            </span>
          </div>
        </header>

        {/* Dashboard Main Workspace */}
        <main className="dashboard-main-area">
          {activeView === VIEWS.DASHBOARD && (
            <DashboardOverview onNavigate={handleQuickNavigate} />
          )}

          {activeView === VIEWS.COMPETENCY && <CompetencyProfile />}

          {activeView === VIEWS.GAPS && <GapAnalysis />}

          {activeView === VIEWS.LEARNING && <Recommendations />}

          {activeView === VIEWS.ASSESSMENTS && (
            <AssessmentsSection
              activeAssessment={activeAssessment}
              setActiveAssessment={setActiveAssessment}
            />
          )}

          {activeView === VIEWS.PROFILE && <Profile />}

          {activeView === VIEWS.SETTINGS && <Settings />}

          {activeView === VIEWS.TRAINER_STUDIO && canAccessTrainer && <CourseStudio />}

          {activeView === VIEWS.ADMIN_CONSOLE && canAccessAdmin && <AdminConsole />}
        </main>
      </div>
    </div>
  )
}

function AssessmentsSection({ activeAssessment, setActiveAssessment }) {
  return (
    <div className="assessments-wrapper">
      <div className="assessment-tabs-row">
        <button
          type="button"
          className={`tab-pill-btn ${activeAssessment === ASSESSMENT_VIEWS.DIAGNOSTIC ? 'tab-pill-active' : ''}`}
          onClick={() => setActiveAssessment(ASSESSMENT_VIEWS.DIAGNOSTIC)}
        >
          Diagnostic Assessment
        </button>
        <button
          type="button"
          className={`tab-pill-btn ${activeAssessment === ASSESSMENT_VIEWS.QUIZ ? 'tab-pill-active' : ''}`}
          onClick={() => setActiveAssessment(ASSESSMENT_VIEWS.QUIZ)}
        >
          Document Quiz & Upload
        </button>
      </div>

      {activeAssessment === ASSESSMENT_VIEWS.DIAGNOSTIC && <DiagnosticAssessment />}
      {activeAssessment === ASSESSMENT_VIEWS.QUIZ && <DocumentQuizFlow />}
    </div>
  )
}

function DocumentQuizFlow() {
  const [mode, setMode] = useState('upload')

  return (
    <div>
      <div className="assessment-tabs-row" style={{ marginTop: '12px', marginBottom: '16px' }}>
        <button
          type="button"
          className={`tab-pill-btn ${mode === 'upload' ? 'tab-pill-active' : ''}`}
          onClick={() => setMode('upload')}
        >
          Upload a PDF
        </button>
        <button
          type="button"
          className={`tab-pill-btn ${mode === 'manual' ? 'tab-pill-active' : ''}`}
          onClick={() => setMode('manual')}
        >
          Enter Document ID
        </button>
      </div>
      {mode === 'upload' ? <PdfUploadQuiz /> : <DocumentQuiz />}
    </div>
  )
}

export default App
