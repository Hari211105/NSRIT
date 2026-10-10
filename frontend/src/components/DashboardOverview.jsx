/**
 * UPSKILL AI - Dashboard Overview Component
 * Matches upskill-dashboard-white.png and upskill-dashboard-black.png with 100% precision:
 * - Top Hero Banner: "Welcome back, Demo Statistical Officer" with India map mesh graphic and "Better Data, Brighter Decisions, Stronger India" motto panel
 * - 5 Metric Cards: Total Competencies (8), With Gaps (6), Major Gaps (2), Meeting Target (1), Above Target (1)
 * - Middle Left: "Your Learning Progress" with circular progress donut (62% Overall Progress) and color legends (Completed 5, In Progress 3, Not Started 4)
 * - Middle Right: "Top Recommendation" with CRITICAL badge, "Statistical Data Management Fundamentals", iGOT Karmayogi · 3 Hours, description, and circular action button
 * - Bottom Row: 4 Quick Actions with precise icons and labels
 *
 * Phase 8 (demo-readiness): a learner who has NOT taken an assessment yet sees
 * an honest empty state instead of the mockup's static numbers. All displayed
 * values come from the backend; the mockup numbers are only used as fallback
 * styling references and are never shown as real data.
 */
import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { IndiaMapVector } from './OfficialEmblems'

export function DashboardOverview({ onNavigate }) {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)

  // Phase 8: null until real data arrives. `hasProfile` is true only when the
  // backend returns at least one competency row for the learner.
  const [hasProfile, setHasProfile] = useState(false)
  const [assessmentCount, setAssessmentCount] = useState(null)

  const [metrics, setMetrics] = useState(null)
  const [progressData, setProgressData] = useState(null)
  const [topRec, setTopRec] = useState(null)

  useEffect(() => {
    let isMounted = true

    async function loadDashboardData() {
      setLoading(true)
      const [gapsRes, recsRes, compsRes, historyRes] = await Promise.allSettled([
        apiClient.getLearnerGaps(),
        apiClient.getLearnerRecommendations(),
        apiClient.getLearnerCompetencies(),
        apiClient.getDiagnosticHistory(),
      ])

      if (!isMounted) return

      // Profile exists only if the learner has competency rows in the DB.
      const competencies =
        compsRes.status === 'fulfilled' ? compsRes.value?.competencies || [] : []
      setHasProfile(competencies.length > 0)

      if (historyRes.status === 'fulfilled') {
        setAssessmentCount(historyRes.value?.total_assessments ?? 0)
      }

      if (
        competencies.length > 0 &&
        gapsRes.status === 'fulfilled' &&
        gapsRes.value?.summary
      ) {
        const s = gapsRes.value.summary
        const total = s.total_competencies || 0
        const withGaps = s.competencies_with_gap ?? 0
        const major = s.major_gaps ?? 0
        const meeting = s.competencies_meeting_target ?? 0
        const above = s.competencies_above_target ?? 0

        setMetrics({
          totalCompetencies: total,
          withGaps,
          majorGaps: major,
          meetingTarget: meeting,
          aboveTarget: above,
        })

        const atOrAboveTarget = meeting + above
        const pct = total > 0 ? Math.round((atOrAboveTarget / total) * 100) : 0
        setProgressData({
          percentage: pct,
          completed: atOrAboveTarget,
          inProgress: s.moderate_gaps ?? 0,
          notStarted: major,
        })
      }

      if (
        recsRes.status === 'fulfilled' &&
        recsRes.value?.recommendations?.length > 0
      ) {
        const r = recsRes.value.recommendations[0]
        setTopRec({
          title: r.learning_resource?.title,
          source:
            r.learning_resource?.source === 'IGOT_DEMO'
              ? 'iGOT Karmayogi — Demo Catalog'
              : r.learning_resource?.source === 'NSSTA_TPAC_DEMO'
                ? 'NSSTA / TPAC — Demo Catalog'
                : r.learning_resource?.source || '',
          duration: r.learning_resource?.duration_hours
            ? `${r.learning_resource.duration_hours} Hours`
            : '',
          priority: r.priority || '',
          description: r.learning_resource?.description || '',
        })
      }

      if (isMounted) setLoading(false)
    }

    loadDashboardData()
    return () => {
      isMounted = false
    }
  }, [])

  // Circumference for multi-segment or single progress donut (radius 48)
  const radius = 48
  const circumference = 2 * Math.PI * radius
  // Segment lengths derived from REAL data (0 when absent).
  const greenStroke = ((progressData?.percentage ?? 0) / 100) * circumference
  const yellowStroke = ((progressData?.inProgress ?? 0) / 100) * circumference
  const redStroke = ((progressData?.notStarted ?? 0) / 100) * circumference

  return (
    <div className="dashboard-content-grid">
      {/* ══════════════════════════════════════════════════════════════
          1. HERO BANNER: Welcome Back & Motto Card
          ══════════════════════════════════════════════════════════════ */}
      <section className="hero-banner-card">
        <div className="hero-banner-main">
          <p className="hero-greeting">Welcome to UPSKILL AI,</p>
          <h1 className="hero-name">
            {user?.name || 'Officer'}
          </h1>
          <p className="hero-subtext">
            Continue your learning journey and strengthen India's Official Statistical System.
          </p>
        </div>

        {/* Center Decorative India Map Graphic */}
        <div className="hero-map-graphic" aria-hidden="true">
          <IndiaMapVector width={125} height={146} />
        </div>

        {/* Right Motto Card */}
        <div className="hero-motto-card">
          <div className="motto-row">Better Data</div>
          <div className="motto-row">Brighter Decisions</div>
          <div className="motto-row">Stronger India</div>
          <div className="motto-bar" />
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════
          2. NEW-USER EMPTY STATE (Phase 8): no fake scores before the
             first assessment. Honest CTA instead of mockup numbers.
          ══════════════════════════════════════════════════════════════ */}
      {!loading && !hasProfile && (
        <section className="profile-card dashboard-new-user-card">
          <div className="section-header">
            <div>
              <h2 className="learner-name" style={{ marginBottom: '4px' }}>
                Welcome to UPSKILL AI
              </h2>
              <p className="learner-email">
                {user?.role?.name
                  ? `Position mapped: ${user.role.name}`
                  : 'Your professional profile is ready.'}
              </p>
            </div>
            <span className="demo-badge">
              {assessmentCount ? 'Assessment in progress' : 'Getting started'}
            </span>
          </div>

          <div className="empty-state" style={{ marginTop: '16px' }}>
            <p style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '6px' }}>
              Complete your competency assessment to discover your strengths and skill gaps.
            </p>
            <p style={{ fontSize: '0.85rem' }}>
              Your {user?.role?.name ? `${user.role.name} ` : ''}competency
              framework, personalised gap analysis and learning recommendations
              unlock right after the assessment.
            </p>
          </div>

          <div style={{ marginTop: '18px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-primary"
              style={{ fontSize: '0.95rem', padding: '12px 28px' }}
              onClick={() => onNavigate('diagnostic')}
            >
              Start Assessment →
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onNavigate('learning')}
            >
              Browse the demo learning catalog
            </button>
          </div>

          <p className="phase-note">
            Your dashboard fills with your real competency scores, gaps and
            recommendations as soon as you complete the diagnostic assessment.
          </p>
        </section>
      )}

      {/* ══════════════════════════════════════════════════════════════
          2b. METRICS ROW: 5 Clean Indicator Cards (real data only)
          ══════════════════════════════════════════════════════════════ */}
      {!loading && hasProfile && metrics && (
        <section className="metrics-row-container">
          {/* Metric 1: Total Competencies */}
          <div className="metric-box">
            <div className="metric-icon-wrap icon-teal-book">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </div>
            <div className="metric-value">{metrics.totalCompetencies}</div>
            <div className="metric-title">Total Competencies</div>
          </div>

          {/* Metric 2: With Gaps */}
          <div className="metric-box">
            <div className="metric-icon-wrap icon-amber-target">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2">
                <circle cx="12" cy="12" r="10" />
                <circle cx="12" cy="12" r="6" />
                <circle cx="12" cy="12" r="2" fill="currentColor" />
              </svg>
            </div>
            <div className="metric-value">{metrics.withGaps}</div>
            <div className="metric-title">With Gaps</div>
          </div>

          {/* Metric 3: Major Gaps */}
          <div className="metric-box">
            <div className="metric-icon-wrap icon-red-alert">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
                <path d="M12 2L1 21h22L12 2zm0 3.5l8.5 14.5H3.5L12 5.5zM11 10h2v4h-2zm0 6h2v2h-2z" />
              </svg>
            </div>
            <div className="metric-value">{metrics.majorGaps}</div>
            <div className="metric-title">Major Gaps</div>
          </div>

          {/* Metric 4: Meeting Target */}
          <div className="metric-box">
            <div className="metric-icon-wrap icon-green-bars">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            </div>
            <div className="metric-value">{metrics.meetingTarget}</div>
            <div className="metric-title">Meeting Target</div>
          </div>

          {/* Metric 5: Above Target */}
          <div className="metric-box">
            <div className="metric-icon-wrap icon-brightgreen-star">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
            </div>
            <div className="metric-value">{metrics.aboveTarget}</div>
            <div className="metric-title">Above Target</div>
          </div>
        </section>
      )}

      {/* ══════════════════════════════════════════════════════════════
          3. MAIN CONTENT SPLIT: Learning Progress & Top Recommendation
          ══════════════════════════════════════════════════════════════ */}
      {!loading && hasProfile && (
        <section className="main-split-grid">
          {/* Left: Your Learning Progress */}
          <div className="progress-panel-card">
            <h2 className="panel-card-title">Your Learning Progress</h2>
            <div className="progress-panel-body">
              {/* Custom Multi-Color Circular Progress Meter */}
              <div className="donut-meter-container">
                <svg viewBox="0 0 130 130" className="progress-donut-svg">
                  {/* Dark Base Ring */}
                  <circle
                    cx="65"
                    cy="65"
                    r={radius}
                    className="donut-track-ring"
                  />
                  {/* Red Segment (Not Started) */}
                  <circle
                    cx="65"
                    cy="65"
                    r={radius}
                    className="donut-segment-red"
                    style={{
                      strokeDasharray: `${redStroke} ${circumference - redStroke}`,
                      strokeDashoffset: 0,
                    }}
                  />
                  {/* Yellow / Amber Segment (In Progress) */}
                  <circle
                    cx="65"
                    cy="65"
                    r={radius}
                    className="donut-segment-yellow"
                    style={{
                      strokeDasharray: `${yellowStroke} ${circumference - yellowStroke}`,
                      strokeDashoffset: -redStroke,
                    }}
                  />
                  {/* Green Segment (Completed / Target Met) */}
                  <circle
                    cx="65"
                    cy="65"
                    r={radius}
                    className="donut-segment-green"
                    style={{
                      strokeDasharray: `${greenStroke} ${circumference - greenStroke}`,
                      strokeDashoffset: -(redStroke + yellowStroke),
                    }}
                  />
                </svg>
                <div className="donut-center-info">
                  <span className="donut-headline-pct">{progressData?.percentage ?? 0}%</span>
                  <span className="donut-sublabel">Overall Progress</span>
                </div>
              </div>

              {/* Legend Counts */}
              <div className="progress-legend-column">
                <div className="legend-entry">
                  <div className="legend-left">
                    <span className="legend-dot dot-green" />
                    <span className="legend-name">Completed</span>
                  </div>
                  <span className="legend-number">{progressData?.completed ?? 0}</span>
                </div>
                <div className="legend-entry">
                  <div className="legend-left">
                    <span className="legend-dot dot-yellow" />
                    <span className="legend-name">In Progress</span>
                  </div>
                  <span className="legend-number">{progressData?.inProgress ?? 0}</span>
                </div>
                <div className="legend-entry">
                  <div className="legend-left">
                    <span className="legend-dot dot-red" />
                    <span className="legend-name">Not Started</span>
                  </div>
                  <span className="legend-number">{progressData?.notStarted ?? 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Top Recommendation */}
          <div className="recommendation-panel-card">
            <div className="rec-panel-header">
              <h2 className="panel-card-title">Top Recommendation</h2>
              <button
                type="button"
                className="view-all-button"
                onClick={() => onNavigate('learning')}
              >
                <span>View All</span>
                <span className="arrow-icon">→</span>
              </button>
            </div>

            {topRec ? (
              <div className="rec-panel-body">
                {/* Left Icon Square */}
                <div className="rec-icon-square">
                  <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                  </svg>
                </div>

                {/* Center Course Details */}
                <div className="rec-details-column">
                  <div className="rec-badge-wrap">
                    {topRec.priority && (
                      <span className="critical-tag-badge">{topRec.priority}</span>
                    )}
                  </div>
                  <h3 className="rec-course-title">
                    {topRec.title}
                  </h3>
                  <p className="rec-source-meta">
                    {topRec.source} {topRec.duration ? `• ${topRec.duration}` : ''}
                  </p>
                  <p className="rec-description-text">
                    {topRec.description}
                  </p>
                </div>

                {/* Right Action Arrow Button */}
                <button
                  type="button"
                  className="rec-circle-arrow-btn"
                  onClick={() => onNavigate('learning')}
                  title="Start Recommendation"
                  aria-label="Start course"
                >
                  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
              </div>
            ) : (
              <div className="empty-state" style={{ margin: '12px 16px 16px' }}>
                <p>🎉 No active competency gaps — all target levels met so far.</p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* ══════════════════════════════════════════════════════════════
          4. QUICK ACTIONS ROW: 4 Bottom Action Cards
          ══════════════════════════════════════════════════════════════ */}
      <section className="quick-actions-container">
        <h2 className="quick-actions-header-title">Quick Actions</h2>
        <div className="quick-actions-4col-grid">
          {/* Card 1: Diagnostic */}
          <button
            type="button"
            className="qa-card"
            onClick={() => onNavigate('diagnostic')}
          >
            <div className="qa-icon-header">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <div className="qa-text-body">
              <h4 className="qa-main-label">
                {hasProfile ? 'Take Diagnostic Assessment' : 'Start Competency Assessment'}
              </h4>
              <p className="qa-sub-label">Assess your current level</p>
            </div>
            <div className="qa-arrow-corner">
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </button>

          {/* Card 2: Learning Paths */}
          <button
            type="button"
            className="qa-card"
            onClick={() => onNavigate('learning')}
          >
            <div className="qa-icon-header">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </div>
            <div className="qa-text-body">
              <h4 className="qa-main-label">Explore Learning Paths</h4>
              <p className="qa-sub-label">Personalized for you</p>
            </div>
            <div className="qa-arrow-corner">
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </button>

          {/* Card 3: Course Catalog */}
          <button
            type="button"
            className="qa-card"
            onClick={() => onNavigate('learning')}
          >
            <div className="qa-icon-header">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            <div className="qa-text-body">
              <h4 className="qa-main-label">Browse Course Catalog</h4>
              <p className="qa-sub-label">iGOT & NSSTA-TPAC (demo catalog)</p>
            </div>
            <div className="qa-arrow-corner">
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </button>

          {/* Card 4: Upload PDF for Quiz */}
          <button
            type="button"
            className="qa-card"
            onClick={() => onNavigate('pdf_quiz')}
          >
            <div className="qa-icon-header">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <div className="qa-text-body">
              <h4 className="qa-main-label">Upload PDF for Quiz</h4>
              <p className="qa-sub-label">Generate MCQs from content</p>
            </div>
            <div className="qa-arrow-corner">
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </button>
        </div>
      </section>
    </div>
  )
}

export default DashboardOverview
