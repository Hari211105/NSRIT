import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { useAuth } from '../context/AuthContext'

export function CourseStudio() {
  const { user, canAccessTrainer } = useAuth()
  const [courses, setCourses] = useState([])
  const [allCompetencies, setAllCompetencies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [filterStatus, setFilterStatus] = useState('ALL')

  // Selected course for editing
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [activeTab, setActiveTab] = useState('meta') // 'meta' | 'competencies' | 'questions' | 'submit'

  // Questions for selected course
  const [questions, setQuestions] = useState([])
  const [loadingQuestions, setLoadingQuestions] = useState(false)

  // Creation modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [newName, setNewName] = useState('')
  const [newCategory, setNewCategory] = useState('TECHNICAL')
  const [newDescription, setNewDescription] = useState('')
  const [newHours, setNewHours] = useState(20)
  const [newLevelHint, setNewLevelHint] = useState('Beginner')

  // Competency mapping form
  const [mapCompId, setMapCompId] = useState('')
  const [mapLevel, setMapLevel] = useState(3)
  const [mapPriority, setMapPriority] = useState('MEDIUM')

  // Question form
  const [qCompId, setQCompId] = useState('')
  const [qType, setQType] = useState('MCQ')
  const [qText, setQText] = useState('')
  const [qOptions, setQOptions] = useState(['', '', '', ''])
  const [qCorrect, setQCorrect] = useState(0)
  const [qDifficulty, setQDifficulty] = useState('MEDIUM')
  const [qExplanation, setQExplanation] = useState('')

  useEffect(() => {
    loadStudioData()
  }, [])

  async function loadStudioData() {
    try {
      setLoading(true)
      setError(null)
      const [coursesData, compsData] = await Promise.all([
        apiClient.getTrainerCourses(),
        apiClient.getCompetencies().catch(() => []),
      ])
      setCourses(coursesData || [])
      setAllCompetencies(compsData || [])
    } catch (err) {
      setError(err.message || 'Failed to load trainer courses.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSelectCourse(course) {
    try {
      setSelectedCourse(course)
      setActiveTab('meta')
      setSuccessMsg(null)
      setError(null)
      loadCourseQuestions(course.id)
    } catch (err) {
      setError(err.message || 'Failed to select course.')
    }
  }

  async function loadCourseQuestions(courseId) {
    try {
      setLoadingQuestions(true)
      const qList = await apiClient.getCourseQuestions(courseId)
      setQuestions(qList || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingQuestions(false)
    }
  }

  async function handleCreateCourse(e) {
    e.preventDefault()
    if (!newCode.trim() || !newName.trim()) return
    try {
      setError(null)
      const created = await apiClient.createTrainerCourse({
        code: newCode.trim(),
        name: newName.trim(),
        category: newCategory,
        description: newDescription.trim() || undefined,
        estimated_hours: Number(newHours) || 20,
        level_hint: newLevelHint,
      })
      setShowCreateModal(false)
      setNewCode('')
      setNewName('')
      setNewDescription('')
      setSuccessMsg(`Course ${created.code} created in DRAFT status!`)
      await loadStudioData()
      handleSelectCourse(created)
    } catch (err) {
      setError(err.message || 'Failed to create course.')
    }
  }

  async function handleUpdateCourseMeta(e) {
    e.preventDefault()
    if (!selectedCourse) return
    try {
      setError(null)
      const updated = await apiClient.updateTrainerCourse(selectedCourse.id, {
        name: selectedCourse.name,
        category: selectedCourse.category,
        description: selectedCourse.description,
        estimated_hours: Number(selectedCourse.estimated_hours) || 20,
        level_hint: selectedCourse.level_hint,
      })
      setSelectedCourse(updated)
      setSuccessMsg('Course metadata saved successfully.')
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to update course.')
    }
  }

  async function handleMapCompetency(e) {
    e.preventDefault()
    if (!selectedCourse || !mapCompId) return
    try {
      setError(null)
      const updated = await apiClient.mapCourseCompetency(selectedCourse.id, {
        competency_id: Number(mapCompId),
        required_level: Number(mapLevel),
        priority: mapPriority,
      })
      setSelectedCourse(updated)
      setSuccessMsg('Competency mapped to course.')
      setMapCompId('')
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to map competency.')
    }
  }

  async function handleUnmapCompetency(competencyId) {
    if (!selectedCourse) return
    try {
      setError(null)
      const updated = await apiClient.unmapCourseCompetency(selectedCourse.id, competencyId)
      setSelectedCourse(updated)
      setSuccessMsg('Competency unmapped.')
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to unmap competency.')
    }
  }

  async function handleCreateQuestion(e) {
    e.preventDefault()
    if (!selectedCourse || !qCompId || !qText.trim()) return
    try {
      setError(null)
      await apiClient.createCourseQuestion(selectedCourse.id, {
        competency_id: Number(qCompId),
        question_type: qType,
        question: qText.trim(),
        options: qOptions.map((o) => o.trim()),
        correct_option: Number(qCorrect),
        difficulty: qDifficulty,
        explanation: qExplanation.trim() || undefined,
      })
      setSuccessMsg(`Added ${qType} question!`)
      setQText('')
      setQOptions(['', '', '', ''])
      setQExplanation('')
      await loadCourseQuestions(selectedCourse.id)
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to create question.')
    }
  }

  async function handleDeleteQuestion(qId) {
    try {
      setError(null)
      await apiClient.deleteCourseQuestion(qId)
      setSuccessMsg('Question deleted.')
      await loadCourseQuestions(selectedCourse.id)
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to delete question.')
    }
  }

  async function handleSubmitForReview() {
    if (!selectedCourse) return
    try {
      setError(null)
      const updated = await apiClient.submitCourseForReview(selectedCourse.id)
      setSelectedCourse(updated)
      setSuccessMsg('Course submitted for administrative review! Status is now PENDING_REVIEW.')
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to submit course.')
    }
  }

  async function handleArchiveCourse() {
    if (!selectedCourse) return
    try {
      setError(null)
      const updated = await apiClient.archiveTrainerCourse(selectedCourse.id)
      setSelectedCourse(updated)
      setSuccessMsg('Course has been archived.')
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to archive course.')
    }
  }

  if (!canAccessTrainer) {
    return (
      <div className="profile-card error-card">
        <h3>Access Restricted</h3>
        <p>Trainer Studio is reserved for certified Trainers and Platform Administrators.</p>
      </div>
    )
  }

  const filteredCourses = courses.filter((c) => {
    if (filterStatus === 'ALL') return true
    return (c.status || 'DRAFT') === filterStatus
  })

  return (
    <div className="dashboard-content-flow">
      {/* Studio Header */}
      <div className="view-header-strip">
        <div className="view-title-wrap">
          <div className="badge-row">
            <span className="badge-pill bg-purple">TRAINER WORKSPACE</span>
            <span className="badge-pill bg-blue">{user?.account_type || 'TRAINER'}</span>
          </div>
          <h2 className="view-main-heading">Course Studio</h2>
          <p className="view-sub-heading">
            Design learning pathways, define required competencies, author diagnostic questions, and publish official curriculum.
          </p>
        </div>
        <div className="view-action-group">
          {!selectedCourse && (
            <button
              type="button"
              className="action-pill-btn btn-primary"
              onClick={() => setShowCreateModal(true)}
            >
              + Create New Course
            </button>
          )}
          {selectedCourse && (
            <button
              type="button"
              className="action-pill-btn btn-secondary"
              onClick={() => setSelectedCourse(null)}
            >
              ← Back to Course Catalog
            </button>
          )}
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

      {/* Main Studio View */}
      {loading ? (
        <div className="profile-card">
          <p className="loading-text">Loading authoring curriculum...</p>
        </div>
      ) : selectedCourse ? (
        /* COURSE EDITOR VIEW */
        <div className="studio-editor-layout">
          {/* Top Course Meta Banner */}
          <div className="profile-card editor-header-card">
            <div className="editor-badge-line">
              <span className={`status-pill status-${(selectedCourse.status || 'draft').toLowerCase()}`}>
                {selectedCourse.status || 'DRAFT'}
              </span>
              <span className="code-tag">{selectedCourse.code}</span>
              <span className="category-tag">{selectedCourse.category}</span>
              <span className="hours-tag">{selectedCourse.estimated_hours} hrs</span>
            </div>
            <h3 className="editor-title">{selectedCourse.name}</h3>

            {/* Review feedback note if rejected */}
            {selectedCourse.review_note && (
              <div className="review-feedback-alert">
                <strong>Reviewer Feedback / Note:</strong>
                <p>{selectedCourse.review_note}</p>
              </div>
            )}

            {/* Editor Navigation Tabs */}
            <div className="editor-tab-nav">
              <button
                type="button"
                className={`tab-btn ${activeTab === 'meta' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('meta')}
              >
                1. Course Overview
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'competencies' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('competencies')}
              >
                2. Mapped Competencies ({selectedCourse.competencies_count || selectedCourse.competencies?.length || 0})
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'questions' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('questions')}
              >
                3. Question Bank ({questions.length})
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'submit' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('submit')}
              >
                4. Review & Submit
              </button>
            </div>
          </div>

          {/* Tab 1: Meta Editor */}
          {activeTab === 'meta' && (
            <div className="profile-card">
              <h4 className="section-title">Edit Course Metadata</h4>
              <p className="section-subtitle">
                Course details visible to learners upon publication.
                {selectedCourse.status === 'PUBLISHED' && ' (Course is published; unpublish or archive to alter core syllabus).'}
              </p>
              <form onSubmit={handleUpdateCourseMeta} className="studio-form">
                <div className="form-grid">
                  <div className="form-group">
                    <label>Course Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={selectedCourse.name || ''}
                      onChange={(e) => setSelectedCourse({ ...selectedCourse, name: e.target.value })}
                      required
                      disabled={selectedCourse.status === 'PENDING_REVIEW'}
                    />
                  </div>
                  <div className="form-group">
                    <label>Category</label>
                    <select
                      className="form-input"
                      value={selectedCourse.category || 'TECHNICAL'}
                      onChange={(e) => setSelectedCourse({ ...selectedCourse, category: e.target.value })}
                      disabled={selectedCourse.status === 'PENDING_REVIEW'}
                    >
                      <option value="TECHNICAL">TECHNICAL (Data / Stats / AI)</option>
                      <option value="NON_TECHNICAL">NON_TECHNICAL (Governance / Policy / Soft Skills)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Estimated Hours</label>
                    <input
                      type="number"
                      className="form-input"
                      value={selectedCourse.estimated_hours || 20}
                      onChange={(e) => setSelectedCourse({ ...selectedCourse, estimated_hours: e.target.value })}
                      min="1"
                      max="500"
                      disabled={selectedCourse.status === 'PENDING_REVIEW'}
                    />
                  </div>
                  <div className="form-group">
                    <label>Level Hint</label>
                    <select
                      className="form-input"
                      value={selectedCourse.level_hint || 'Beginner'}
                      onChange={(e) => setSelectedCourse({ ...selectedCourse, level_hint: e.target.value })}
                      disabled={selectedCourse.status === 'PENDING_REVIEW'}
                    >
                      <option value="Beginner">Beginner</option>
                      <option value="Intermediate">Intermediate</option>
                      <option value="Advanced">Advanced</option>
                    </select>
                  </div>
                </div>
                <div className="form-group" style={{ marginTop: '1rem' }}>
                  <label>Course Description</label>
                  <textarea
                    rows={4}
                    className="form-input"
                    value={selectedCourse.description || ''}
                    onChange={(e) => setSelectedCourse({ ...selectedCourse, description: e.target.value })}
                    disabled={selectedCourse.status === 'PENDING_REVIEW'}
                  />
                </div>
                {selectedCourse.status !== 'PENDING_REVIEW' && (
                  <button type="submit" className="action-pill-btn btn-primary" style={{ marginTop: '1rem' }}>
                    Save Overview
                  </button>
                )}
              </form>
            </div>
          )}

          {/* Tab 2: Competency Mapping */}
          {activeTab === 'competencies' && (
            <div className="profile-card">
              <h4 className="section-title">Competency Framework Mappings</h4>
              <p className="section-subtitle">
                Align official statistical competencies and target proficiency levels to this course.
              </p>

              {/* Current Mapped List */}
              <div className="mapped-competency-list" style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
                {(!selectedCourse.competencies || selectedCourse.competencies.length === 0) ? (
                  <div className="empty-notice">No competencies mapped yet. Map at least one to enable review submission.</div>
                ) : (
                  <table className="studio-table">
                    <thead>
                      <tr>
                        <th>Competency Name</th>
                        <th>Required Level</th>
                        <th>Priority</th>
                        <th style={{ textAlign: 'right' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedCourse.competencies.map((m) => (
                        <tr key={m.id}>
                          <td><strong>{m.name}</strong></td>
                          <td>Level {m.required_level} / 4</td>
                          <td>
                            <span className={`prio-pill prio-${(m.priority || 'medium').toLowerCase()}`}>
                              {m.priority || 'MEDIUM'}
                            </span>
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            {selectedCourse.status !== 'PENDING_REVIEW' && (
                              <button
                                type="button"
                                className="action-link-danger"
                                onClick={() => handleUnmapCompetency(m.id)}
                              >
                                Remove
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Add / Update Form */}
              {selectedCourse.status !== 'PENDING_REVIEW' && (
                <form onSubmit={handleMapCompetency} className="inline-add-box">
                  <h5 style={{ marginBottom: '0.75rem', fontWeight: 600 }}>+ Map Competency</h5>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Competency</label>
                      <select
                        className="form-input"
                        value={mapCompId}
                        onChange={(e) => setMapCompId(e.target.value)}
                        required
                      >
                        <option value="">-- Choose Competency --</option>
                        {allCompetencies.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Required Level (1-4)</label>
                      <select
                        className="form-input"
                        value={mapLevel}
                        onChange={(e) => setMapLevel(e.target.value)}
                      >
                        <option value={1}>Level 1 - Awareness</option>
                        <option value={2}>Level 2 - Working</option>
                        <option value={3}>Level 3 - Proficient</option>
                        <option value={4}>Level 4 - Advanced</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Priority</label>
                      <select
                        className="form-input"
                        value={mapPriority}
                        onChange={(e) => setMapPriority(e.target.value)}
                      >
                        <option value="HIGH">HIGH</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="LOW">LOW</option>
                      </select>
                    </div>
                  </div>
                  <button type="submit" className="action-pill-btn btn-secondary" style={{ marginTop: '0.75rem' }}>
                    Save Competency Mapping
                  </button>
                </form>
              )}
            </div>
          )}

          {/* Tab 3: Question Bank */}
          {activeTab === 'questions' && (
            <div className="profile-card">
              <h4 className="section-title">Diagnostic Assessment Questions</h4>
              <p className="section-subtitle">
                Author MCQ and SCENARIO questions specific to this course.
              </p>

              {/* Questions List */}
              <div className="questions-stream" style={{ marginTop: '1rem', marginBottom: '2rem' }}>
                {loadingQuestions ? (
                  <p className="loading-text">Loading question bank...</p>
                ) : questions.length === 0 ? (
                  <div className="empty-notice">No questions created yet for this course.</div>
                ) : (
                  questions.map((q, idx) => (
                    <div key={q.id} className="question-item-card">
                      <div className="q-card-header">
                        <span className="q-index-pill">Q{idx + 1}</span>
                        <span className={`q-type-pill q-type-${q.question_type.toLowerCase()}`}>
                          {q.question_type}
                        </span>
                        <span className="q-comp-tag">{q.competency_name || `Competency #${q.competency_id}`}</span>
                        <span className="q-diff-tag">{q.difficulty}</span>
                        {selectedCourse.status !== 'PENDING_REVIEW' && (
                          <button
                            type="button"
                            className="action-link-danger"
                            onClick={() => handleDeleteQuestion(q.id)}
                            style={{ marginLeft: 'auto' }}
                          >
                            Delete
                          </button>
                        )}
                      </div>
                      <p className="q-text-body">{q.question}</p>
                      <div className="q-options-grid">
                        {q.options.map((opt, oIdx) => (
                          <div
                            key={oIdx}
                            className={`q-opt-pill ${oIdx === q.correct_option ? 'q-opt-correct' : ''}`}
                          >
                            <strong>{String.fromCharCode(65 + oIdx)}.</strong> {opt}
                            {oIdx === q.correct_option && ' ✓ (Correct)'}
                          </div>
                        ))}
                      </div>
                      {q.explanation && (
                        <div className="q-explanation">
                          <em>Explanation: {q.explanation}</em>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>

              {/* Add Question Form */}
              {selectedCourse.status !== 'PENDING_REVIEW' && (
                <form onSubmit={handleCreateQuestion} className="inline-add-box">
                  <h5 style={{ marginBottom: '0.75rem', fontWeight: 600 }}>+ Add Diagnostic Question</h5>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Mapped Competency</label>
                      <select
                        className="form-input"
                        value={qCompId}
                        onChange={(e) => setQCompId(e.target.value)}
                        required
                      >
                        <option value="">-- Choose Competency --</option>
                        {selectedCourse.competencies?.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                        {(!selectedCourse.competencies || selectedCourse.competencies.length === 0) &&
                          allCompetencies.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name}
                            </option>
                          ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Question Type</label>
                      <select
                        className="form-input"
                        value={qType}
                        onChange={(e) => setQType(e.target.value)}
                      >
                        <option value="MCQ">MCQ (Knowledge-based)</option>
                        <option value="SCENARIO">SCENARIO (Real-world field situation)</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Difficulty</label>
                      <select
                        className="form-input"
                        value={qDifficulty}
                        onChange={(e) => setQDifficulty(e.target.value)}
                      >
                        <option value="EASY">EASY</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="HARD">HARD</option>
                      </select>
                    </div>
                  </div>

                  <div className="form-group" style={{ marginTop: '0.75rem' }}>
                    <label>Question Prompt</label>
                    <textarea
                      rows={3}
                      className="form-input"
                      value={qText}
                      onChange={(e) => setQText(e.target.value)}
                      placeholder="Enter question scenario or prompt..."
                      required
                    />
                  </div>

                  <div className="options-input-group" style={{ marginTop: '0.75rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
                      Answer Options (Select correct option radio)
                    </label>
                    {[0, 1, 2, 3].map((idx) => (
                      <div key={idx} className="option-row" style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', alignItems: 'center' }}>
                        <input
                          type="radio"
                          name="correct_option"
                          checked={qCorrect === idx}
                          onChange={() => setQCorrect(idx)}
                        />
                        <span style={{ fontWeight: 600 }}>{String.fromCharCode(65 + idx)}:</span>
                        <input
                          type="text"
                          className="form-input"
                          style={{ flex: 1 }}
                          value={qOptions[idx]}
                          onChange={(e) => {
                            const updated = [...qOptions]
                            updated[idx] = e.target.value
                            setQOptions(updated)
                          }}
                          placeholder={`Option ${String.fromCharCode(65 + idx)} text`}
                          required
                        />
                      </div>
                    ))}
                  </div>

                  <div className="form-group" style={{ marginTop: '0.75rem' }}>
                    <label>Explanation / Rationale</label>
                    <input
                      type="text"
                      className="form-input"
                      value={qExplanation}
                      onChange={(e) => setQExplanation(e.target.value)}
                      placeholder="Why is this the correct answer?"
                    />
                  </div>

                  <button type="submit" className="action-pill-btn btn-primary" style={{ marginTop: '1rem' }}>
                    Save Question to Bank
                  </button>
                </form>
              )}
            </div>
          )}

          {/* Tab 4: Review & Submit */}
          {activeTab === 'submit' && (
            <div className="profile-card">
              <h4 className="section-title">Review & Publishing Workflow</h4>
              <p className="section-subtitle">
                Check readiness before submitting for administrative approval.
              </p>

              <div className="readiness-checklist" style={{ marginTop: '1.25rem' }}>
                <div className="checklist-item">
                  <span className={`check-icon ${selectedCourse.name ? 'check-pass' : 'check-fail'}`}>
                    {selectedCourse.name ? '✓' : '✗'}
                  </span>
                  <div>
                    <strong>Course Identity</strong>: {selectedCourse.name} ({selectedCourse.code})
                  </div>
                </div>
                <div className="checklist-item">
                  <span className={`check-icon ${selectedCourse.competencies?.length > 0 ? 'check-pass' : 'check-fail'}`}>
                    {selectedCourse.competencies?.length > 0 ? '✓' : '✗'}
                  </span>
                  <div>
                    <strong>Competency Framework</strong>: {selectedCourse.competencies?.length || 0} mapped competencies
                  </div>
                </div>
                <div className="checklist-item">
                  <span className={`check-icon ${questions.length > 0 ? 'check-pass' : 'check-fail'}`}>
                    {questions.length > 0 ? '✓' : '✗'}
                  </span>
                  <div>
                    <strong>Diagnostic Questions</strong>: {questions.length} questions authored
                  </div>
                </div>
              </div>

              <div className="workflow-actions-box" style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
                {(selectedCourse.status === 'DRAFT' || selectedCourse.status === 'ARCHIVED') && (
                  <button
                    type="button"
                    className="action-pill-btn btn-primary"
                    onClick={handleSubmitForReview}
                    disabled={!selectedCourse.competencies || selectedCourse.competencies.length === 0}
                  >
                    Submit for Admin Approval →
                  </button>
                )}
                {selectedCourse.status === 'PENDING_REVIEW' && (
                  <div className="notice-badge bg-blue" style={{ padding: '0.75rem 1rem' }}>
                    ⏱ This course is currently under review by Platform Administrators.
                  </div>
                )}
                {selectedCourse.status === 'PUBLISHED' && (
                  <div className="notice-badge bg-emerald" style={{ padding: '0.75rem 1rem' }}>
                    ✓ This course is live and accessible to learners.
                  </div>
                )}
                {selectedCourse.status !== 'ARCHIVED' && (
                  <button
                    type="button"
                    className="action-pill-btn btn-danger"
                    onClick={handleArchiveCourse}
                  >
                    Archive Course
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* COURSE LISTING VIEW */
        <div className="studio-courses-view">
          {/* Status Filter Tabs */}
          <div className="status-filter-row">
            {['ALL', 'DRAFT', 'PENDING_REVIEW', 'PUBLISHED', 'ARCHIVED'].map((st) => (
              <button
                key={st}
                type="button"
                className={`filter-tab-pill ${filterStatus === st ? 'filter-tab-active' : ''}`}
                onClick={() => setFilterStatus(st)}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          {filteredCourses.length === 0 ? (
            <div className="profile-card empty-card">
              <p>No courses found matching "{filterStatus}".</p>
              <button
                type="button"
                className="action-pill-btn btn-primary"
                onClick={() => setShowCreateModal(true)}
                style={{ marginTop: '1rem' }}
              >
                Create First Course
              </button>
            </div>
          ) : (
            <div className="studio-course-cards-grid">
              {filteredCourses.map((c) => (
                <div key={c.id} className="studio-course-card">
                  <div className="card-top-line">
                    <span className="code-pill">{c.code}</span>
                    <span className={`status-pill status-${(c.status || 'draft').toLowerCase()}`}>
                      {c.status || 'DRAFT'}
                    </span>
                  </div>
                  <h4 className="card-course-title">{c.name}</h4>
                  <p className="card-course-desc">
                    {c.description ? (c.description.length > 120 ? `${c.description.slice(0, 120)}...` : c.description) : 'No description provided.'}
                  </p>
                  {c.review_note && (
                    <div className="card-feedback-snippet">
                      <em>Feedback: {c.review_note}</em>
                    </div>
                  )}
                  <div className="card-stats-row">
                    <span>📚 {c.competencies_count} Competencies</span>
                    <span>❓ {c.questions_count} Questions</span>
                    <span>⏱ {c.estimated_hours}h</span>
                  </div>
                  <div className="card-btn-footer">
                    <button
                      type="button"
                      className="action-pill-btn btn-secondary full-width"
                      onClick={() => handleSelectCourse(c)}
                    >
                      Manage Course →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Course Modal */}
      {showCreateModal && (
        <div className="modal-backdrop">
          <div className="modal-box">
            <div className="modal-header">
              <h3 style={{ margin: 0 }}>Create New Course</h3>
              <button
                type="button"
                className="close-modal-btn"
                onClick={() => setShowCreateModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleCreateCourse} className="modal-body">
              <div className="form-group">
                <label>Course Code (Unique ID, e.g. STAT_METH_101)</label>
                <input
                  type="text"
                  className="form-input"
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value)}
                  placeholder="e.g. STAT_SAMPLE_301"
                  required
                />
              </div>
              <div className="form-group" style={{ marginTop: '0.75rem' }}>
                <label>Course Title</label>
                <input
                  type="text"
                  className="form-input"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Advanced Sampling Methodology"
                  required
                />
              </div>
              <div className="form-grid" style={{ marginTop: '0.75rem' }}>
                <div className="form-group">
                  <label>Category</label>
                  <select
                    className="form-input"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                  >
                    <option value="TECHNICAL">TECHNICAL</option>
                    <option value="NON_TECHNICAL">NON_TECHNICAL</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Level</label>
                  <select
                    className="form-input"
                    value={newLevelHint}
                    onChange={(e) => setNewLevelHint(e.target.value)}
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                  </select>
                </div>
              </div>
              <div className="form-group" style={{ marginTop: '0.75rem' }}>
                <label>Estimated Hours</label>
                <input
                  type="number"
                  className="form-input"
                  value={newHours}
                  onChange={(e) => setNewHours(e.target.value)}
                  min="1"
                  max="500"
                />
              </div>
              <div className="form-group" style={{ marginTop: '0.75rem' }}>
                <label>Description</label>
                <textarea
                  rows={3}
                  className="form-input"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Course goals and learning objectives..."
                />
              </div>
              <div className="modal-footer" style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  className="action-pill-btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="action-pill-btn btn-primary">
                  Create Course Draft
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
