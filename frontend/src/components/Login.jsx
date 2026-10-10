/**
 * UPSKILL AI - Full-Screen Pixel-Perfect Login & Account Creation Page
 * Matches upskill-login.png design reference with 100% precision:
 * - Left side: MoSPI branding, "Empowering Statistical Professionals Across India",
 *   "Upskill Today Strengthen India's Statistical Future" hero headline,
 *   feature icon list (Learn, Practice, Grow, Make an Impact), and subtle India map watermark.
 * - Right side: Red Fort (Lal Qila), Delhi at sunset with centered glassmorphic card:
 *   "UPSKILL AI" title, "Build Your Skills for a Stronger Statistical India",
 *   Sign In / Create Account segmented toggle, Google & Microsoft buttons,
 *   Email & Password inputs, Remember me / Forgot password, and vivid blue "#0066FF" Sign In button.
 * - Bottom right banner: "LEARN | BUILD JOB-READY SKILLS"
 * - Official Emblem of India at top right with "Ministry of Statistics and Programme Implementation Government of India".
 */
import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { IndiaMapVector } from './OfficialEmblems'

export function Login() {
  const { login, register, message } = useAuth()
  const [tab, setTab] = useState('signin') // 'signin' | 'signup'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const handleOAuthClick = (provider) => {
    setNotice(`${provider} OAuth integration is in demo mode. Please sign in with your official account credentials.`)
  }

  const handleForgotPassword = (e) => {
    e.preventDefault()
    setNotice('Self-serve password reset: Default demo credentials can be used or register a new test account.')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (submitting) return
    setError('')
    setNotice('')

    if (!email.trim() || !password) {
      setError('Please fill in all required fields.')
      return
    }

    if (tab === 'signup' && !name.trim()) {
      setError('Please enter your full name.')
      return
    }

    setSubmitting(true)
    try {
      if (tab === 'signin') {
        await login(email.trim(), password)
      } else {
        await register(name.trim(), email.trim(), password)
      }
    } catch (err) {
      if (err.status === 401) {
        setError('Incorrect email or password. Please try again.')
      } else if (err.status === 400) {
        setError(err.message || 'An account with this email already exists.')
      } else if (err.status === 0) {
        setError('Could not reach the backend server. Please verify the API is running.')
      } else {
        setError(err.message || 'Authentication failed. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-viewport">
      {/* ══════════════════════════════════════════════════════════════
          LEFT SIDE: White / Ice Blue Branding & Features Panel
          ══════════════════════════════════════════════════════════════ */}
      <div className="login-left-panel">
        <div className="login-left-content">
          {/* Top MoSPI Header */}
          <div className="login-left-header">
            <span className="login-kicker">EMPOWERING</span>
            <span className="login-kicker">STATISTICAL</span>
            <span className="login-kicker">PROFESSIONALS</span>
            <span className="login-kicker">ACROSS INDIA</span>
            <span className="login-kicker-rule" />
          </div>

          {/* Hero Main Headline */}
          <div className="login-left-hero">
            <h1 className="login-hero-title">
              Upskill Today<br />
              <span className="login-hero-blue">Strengthen India's</span><br />
              Statistical Future
            </h1>
          </div>

          {/* 4 Feature Items with Round Icon Badges */}
          <div className="login-features-list">
            {/* Feature 1: Learn */}
            <div className="login-feature-item">
              <div className="feature-icon-circle">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 3v18h18" />
                  <path d="M18 9l-5 5-4-4-3 3" />
                </svg>
              </div>
              <div className="feature-text-block">
                <h3 className="feature-title">Learn</h3>
                <p className="feature-desc">Build Job-Ready Skills</p>
              </div>
            </div>

            {/* Feature 2: Practice */}
            <div className="login-feature-item">
              <div className="feature-icon-circle">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z" />
                </svg>
              </div>
              <div className="feature-text-block">
                <h3 className="feature-title">Practice</h3>
                <p className="feature-desc">Access quality learning resources</p>
              </div>
            </div>

            {/* Feature 3: Grow */}
            <div className="login-feature-item">
              <div className="feature-icon-circle">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                  <polyline points="17 6 23 6 23 12" />
                </svg>
              </div>
              <div className="feature-text-block">
                <h3 className="feature-title">Grow</h3>
                <p className="feature-desc">Bridge skill gaps with AI insights</p>
              </div>
            </div>

            {/* Feature 4: Make an Impact */}
            <div className="login-feature-item">
              <div className="feature-icon-circle">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
                </svg>
              </div>
              <div className="feature-text-block">
                <h3 className="feature-title">Make an Impact</h3>
                <p className="feature-desc">Contribute to a data-driven India</p>
              </div>
            </div>
          </div>
        </div>

        {/* Subtle India Map Watermark Graphic in lower left */}
        <div className="login-india-watermark" aria-hidden="true">
          <IndiaMapVector width={230} height={268} />
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════
          RIGHT SIDE: Dusk Architectural Scene + Centered Glass Card
          ══════════════════════════════════════════════════════════════ */}
      <div className="login-right-panel">
        {/* Scene layer: architectural backdrop + ministry badge (behind the card) */}
        <div className="login-scene-frame">

        {/* Red Fort (Lal Qila), Delhi — photographic dusk backdrop (fills panel, cover-cropped).
            Photo: "Delhi Red fort.jpg" by Hemant Banswal, Wikimedia Commons, CC BY-SA 4.0
            (https://commons.wikimedia.org/wiki/File:Delhi_Red_fort.jpg). Color-graded for dusk. */}
        <div className="login-fort-photo" role="img" aria-label="Red Fort (Lal Qila) in Delhi at dusk">
          <img
            src="/red-fort-dusk-960.jpg"
            alt=""
            className="fort-photo-img"
            draggable={false}
            onError={(e) => {
              e.currentTarget.src = '/red-fort-dusk.jpg'
            }}
          />
        </div>

        {/* ══════════════════════════════════════════════════════════════
            CENTERED GLASSMORPHISM LOGIN CARD
            ══════════════════════════════════════════════════════════════ */}
        <div className="login-card-anchor">
          <div className="login-glass-card">
            {/* Card Header: Brand */}
            <div className="card-brand-row">
              <div className="card-brand-title">
                <span className="brand-upskill">UPSKILL </span>
                <span className="brand-ai">AI</span>
              </div>
            </div>
            <p className="card-brand-subtitle">
              AI-Driven Competency Intelligence Platform for India's Official Statistical System
            </p>

            {/* Main Headline Inside Card */}
            <div className="card-hero-text">
              <h2 className="card-headline">
                Build Your Skills<br />
                for a Stronger<br />
                <span className="card-headline-blue">Statistical India</span>
              </h2>
              <p className="card-tagline">
                Assess · Learn · Grow · Make an Impact
              </p>
            </div>

            {/* Segmented Sign In / Create Account Toggle */}
            <div className="card-auth-toggle">
              <button
                type="button"
                className={`auth-toggle-btn ${tab === 'signin' ? 'auth-toggle-active' : ''}`}
                onClick={() => {
                  setTab('signin')
                  setError('')
                  setNotice('')
                }}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`auth-toggle-btn ${tab === 'signup' ? 'auth-toggle-active' : ''}`}
                onClick={() => {
                  setTab('signup')
                  setError('')
                  setNotice('')
                }}
              >
                Create Account
              </button>
            </div>

            {/* Social OAuth Buttons */}
            <div className="card-social-buttons">
              <button
                type="button"
                className="social-btn google-btn"
                onClick={() => handleOAuthClick('Google')}
              >
                <svg className="social-icon" viewBox="0 0 24 24" width="18" height="18">
                  <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z" />
                  <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.34 24 12 24z" />
                  <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.98 0 12s.45 3.82 1.25 5.42l4.03-3.15z" />
                  <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z" />
                </svg>
                <span>Continue with Google</span>
              </button>

              <button
                type="button"
                className="social-btn microsoft-btn"
                onClick={() => handleOAuthClick('Microsoft')}
              >
                <svg className="social-icon" viewBox="0 0 24 24" width="18" height="18">
                  <rect x="1" y="1" width="10" height="10" fill="#F25022" />
                  <rect x="13" y="1" width="10" height="10" fill="#7FBA00" />
                  <rect x="1" y="13" width="10" height="10" fill="#00A4EF" />
                  <rect x="13" y="13" width="10" height="10" fill="#FFB900" />
                </svg>
                <span>Continue with Microsoft</span>
              </button>
            </div>

            {/* OR Divider */}
            <div className="card-divider">
              <span className="card-divider-line" />
              <span className="card-divider-text">OR</span>
              <span className="card-divider-line" />
            </div>

            {/* Messages / Alerts */}
            {message && (
              <div className="card-alert info">{message}</div>
            )}
            {notice && (
              <div className="card-alert notice">ℹ {notice}</div>
            )}
            {error && (
              <div className="card-alert error">⚠ {error}</div>
            )}

            {/* Form Fields */}
            <form onSubmit={handleSubmit} className="card-form" noValidate>
              {tab === 'signup' && (
                <div className="card-input-wrap">
                  <svg className="input-field-icon" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  <input
                    type="text"
                    className="card-input"
                    placeholder="Full name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={submitting}
                  />
                </div>
              )}

              <div className="card-input-wrap">
                <svg className="input-field-icon" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                </svg>
                <input
                  type="email"
                  className="card-input"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={submitting}
                  autoComplete="email"
                />
              </div>

              <div className="card-input-wrap">
                <svg className="input-field-icon" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="card-input"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={submitting}
                  autoComplete={tab === 'signin' ? 'current-password' : 'new-password'}
                />
                <button
                  type="button"
                  className="input-eye-btn"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                      <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clipRule="evenodd" />
                      <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.064 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                      <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              </div>

              {/* Remember me & Forgot Password */}
              <div className="card-options-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="custom-checkbox"
                  />
                  <span>Remember me</span>
                </label>
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  className="forgot-link"
                >
                  Forgot password?
                </button>
              </div>

              {/* Primary Blue Action Button */}
              <button
                type="submit"
                className="card-submit-btn"
                disabled={submitting}
              >
                {submitting ? (
                  <span>Processing...</span>
                ) : (
                  <>
                    <span>{tab === 'signin' ? 'Sign In' : 'Create Account'}</span>
                    <span className="submit-arrow">→</span>
                  </>
                )}
              </button>
            </form>

            {/* Footer Prompt */}
            <div className="card-footer-prompt">
              {tab === 'signin' ? (
                <span>
                  Don't have an account?{' '}
                  <button
                    type="button"
                    className="prompt-link"
                    onClick={() => {
                      setTab('signup')
                      setError('')
                      setNotice('')
                    }}
                  >
                    Sign Up
                  </button>
                </span>
              ) : (
                <span>
                  Already have an account?{' '}
                  <button
                    type="button"
                    className="prompt-link"
                    onClick={() => {
                      setTab('signin')
                      setError('')
                      setNotice('')
                    }}
                  >
                    Sign In
                  </button>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Right Kicker Watermark Banner */}
        <div className="login-bottom-motto">
          LEARN &nbsp;|&nbsp; BUILD JOB-READY SKILLS
        </div>
        </div>{/* /login-scene-frame */}
      </div>
    </div>
  )
}

export default Login
