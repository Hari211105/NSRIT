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
  const [activeTab, setActiveTab] = useState('meta') // 'meta' | 'competencies' | 'curriculum' | 'prerequisites' | 'questions' | 'submit'

  // Questions for selected course
  const [questions, setQuestions] = useState([])
  const [loadingQuestions, setLoadingQuestions] = useState(false)

  // Curriculum for selected course
  const [curriculumModules, setCurriculumModules] = useState([])
  const [loadingCurriculum, setLoadingCurriculum] = useState(false)

  // Prerequisites for selected course
  const [prerequisites, setPrerequisites] = useState([])
  const [loadingPrereqs, setLoadingPrereqs] = useState(false)
  const [selectedPrereqCourseId, setSelectedPrereqCourseId] = useState('')

  // Module Modal state
  const [showModuleModal, setShowModuleModal] = useState(false)
  const [moduleModalEditId, setModuleModalEditId] = useState(null)
  const [modTitle, setModTitle] = useState('')
  const [modDesc, setModDesc] = useState('')

  // Lesson Modal state
  const [showLessonModal, setShowLessonModal] = useState(false)
  const [lessonModalModuleId, setLessonModalModuleId] = useState(null)
  const [lessonModalEditId, setLessonModalEditId] = useState(null)
  const [lesTitle, setLesTitle] = useState('')
  const [lesType, setLesType] = useState('TEXT')
  const [lesBody, setLesBody] = useState('')
  const [lesMinutes, setLesMinutes] = useState(15)

  // Creation modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [newName, setNewName] = useState('')
  const [newCategory, setNewCategory] = useState('TECHNICAL')
  const [newDescription, setNewDescription] = useState('')
  const [newHours, setNewHours] = useState(20)
  const [newLevelHint, setNewLevelHint] = useState('Beginner')
  const [newMinDiagScore, setNewMinDiagScore] = useState('')

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
      loadCourseCurriculum(course.id)
      loadCoursePrerequisites(course.id)
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

  async function loadCourseCurriculum(courseId) {
    try {
      setLoadingCurriculum(true)
      const cur = await apiClient.getTrainerCurriculum(courseId)
      setCurriculumModules(cur || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingCurriculum(false)
    }
  }

  async function loadCoursePrerequisites(courseId) {
    try {
      setLoadingPrereqs(true)
      const pre = await apiClient.getTrainerPrerequisites(courseId)
      setPrerequisites(pre || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingPrereqs(false)
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
        min_diagnostic_score: newMinDiagScore !== '' ? Number(newMinDiagScore) : null,
      })
      setShowCreateModal(false)
      setNewCode('')
      setNewName('')
      setNewDescription('')
      setNewMinDiagScore('')
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
        min_diagnostic_score:
          selectedCourse.min_diagnostic_score !== '' &&
          selectedCourse.min_diagnostic_score !== null &&
          selectedCourse.min_diagnostic_score !== undefined
            ? Number(selectedCourse.min_diagnostic_score)
            : null,
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

  async function handleUnmapCompetency(compRefId) {
    if (!selectedCourse) return
    try {
      setError(null)
      const updated = await apiClient.unmapCourseCompetency(selectedCourse.id, compRefId)
      setSelectedCourse(updated)
      setSuccessMsg('Competency unmapped.')
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to unmap competency.')
    }
  }

  // ── Module & Lesson Handlers ──

  function handleOpenAddModule() {
    setModuleModalEditId(null)
    setModTitle('')
    setModDesc('')
    setShowModuleModal(true)
  }

  function handleOpenEditModule(mod) {
    setModuleModalEditId(mod.id)
    setModTitle(mod.title || '')
    setModDesc(mod.description || '')
    setShowModuleModal(true)
  }

  async function handleSaveModule(e) {
    e.preventDefault()
    if (!modTitle.trim() || !selectedCourse) return
    try {
      setError(null)
      if (moduleModalEditId) {
        await apiClient.updateTrainerModule(moduleModalEditId, {
          title: modTitle.trim(),
          description: modDesc.trim() || undefined,
        })
        setSuccessMsg('Module updated successfully.')
      } else {
        await apiClient.createTrainerModule(selectedCourse.id, {
          title: modTitle.trim(),
          description: modDesc.trim() || undefined,
          order: curriculumModules.length + 1,
        })
        setSuccessMsg('Module added successfully.')
      }
      setShowModuleModal(false)
      await loadCourseCurriculum(selectedCourse.id)
    } catch (err) {
      setError(err.message || 'Failed to save module.')
    }
  }

  async function handleDeleteModule(moduleId) {
    if (!window.confirm('Delete this module and all its lessons?')) return
    try {
      setError(null)
      await apiClient.deleteTrainerModule(moduleId)
      setSuccessMsg('Module deleted.')
      await loadCourseCurriculum(selectedCourse.id)
    } catch (err) {
      setError(err.message || 'Failed to delete module.')
    }
  }

  function handleOpenAddLesson(moduleId) {
    setLessonModalModuleId(moduleId)
    setLessonModalEditId(null)
    setLesTitle('')
    setLesType('TEXT')
    setLesBody('')
    setLesMinutes(15)
    setShowLessonModal(true)
  }

  function handleOpenEditLesson(moduleId, lesson) {
    setLessonModalModuleId(moduleId)
    setLessonModalEditId(lesson.id)
    setLesTitle(lesson.title || '')
    setLesType(lesson.lesson_type || 'TEXT')
    setLesBody(lesson.body || '')
    setLesMinutes(lesson.estimated_minutes || 15)
    setShowLessonModal(true)
  }

  async function handleSaveLesson(e) {
    e.preventDefault()
    if (!lesTitle.trim() || !lessonModalModuleId) return
    try {
      setError(null)
      if (lessonModalEditId) {
        await apiClient.updateTrainerLesson(lessonModalEditId, {
          title: lesTitle.trim(),
          lesson_type: lesType,
          body: lesBody,
          estimated_minutes: Number(lesMinutes) || 15,
        })
        setSuccessMsg('Lesson updated successfully.')
      } else {
        const mod = curriculumModules.find((m) => m.id === lessonModalModuleId)
        const currentCount = mod?.lessons?.length || 0
        await apiClient.createTrainerLesson(lessonModalModuleId, {
          title: lesTitle.trim(),
          lesson_type: lesType,
          body: lesBody,
          estimated_minutes: Number(lesMinutes) || 15,
          order: currentCount + 1,
        })
        setSuccessMsg('Lesson added successfully.')
      }
      setShowLessonModal(false)
      await loadCourseCurriculum(selectedCourse.id)
    } catch (err) {
      setError(err.message || 'Failed to save lesson.')
    }
  }

  async function handleDeleteLesson(lessonId) {
    if (!window.confirm('Delete this lesson?')) return
    try {
      setError(null)
      await apiClient.deleteTrainerLesson(lessonId)
      setSuccessMsg('Lesson deleted.')
      await loadCourseCurriculum(selectedCourse.id)
    } catch (err) {
      setError(err.message || 'Failed to delete lesson.')
    }
  }

  async function handleMoveModule(index, direction) {
    if (!selectedCourse) return
    const newIdx = index + direction
    if (newIdx < 0 || newIdx >= curriculumModules.length) return
    const updated = [...curriculumModules]
    const [moved] = updated.splice(index, 1)
    updated.splice(newIdx, 0, moved)

    const payload = {
      modules: updated.map((m, mIdx) => ({
        id: m.id,
        order: mIdx + 1,
        lessons: (m.lessons || []).map((l, lIdx) => ({
          id: l.id,
          order: lIdx + 1,
        })),
      })),
    }

    try {
      await apiClient.reorderTrainerCurriculum(selectedCourse.id, payload)
      await loadCourseCurriculum(selectedCourse.id)
    } catch (err) {
      setError(err.message || 'Failed to reorder modules.')
    }
  }

  async function handleMoveLesson(moduleIndex, lessonIndex, direction) {
    if (!selectedCourse) return
    const mod = curriculumModules[moduleIndex]
    if (!mod || !mod.lessons) return
    const newIdx = lessonIndex + direction
    if (newIdx < 0 || newIdx >= mod.lessons.length) return

    const updatedModules = [...curriculumModules]
    const updatedLessons = [...mod.lessons]
    const [moved] = updatedLessons.splice(lessonIndex, 1)
    updatedLessons.splice(newIdx, 0, moved)
    updatedModules[moduleIndex] = { ...mod, lessons: updatedLessons }

    const payload = {
      modules: updatedModules.map((m, mIdx) => ({
        id: m.id,
        order: mIdx + 1,
        lessons: (m.lessons || []).map((l, lIdx) => ({
          id: l.id,
          order: lIdx + 1,
        })),
      })),
    }

    try {
      await apiClient.reorderTrainerCurriculum(selectedCourse.id, payload)
      await loadCourseCurriculum(selectedCourse.id)
    } catch (err) {
      setError(err.message || 'Failed to reorder lessons.')
    }
  }

  // ── Prerequisite Handlers ──

  async function handleAddPrerequisite(e) {
    e.preventDefault()
    if (!selectedCourse || !selectedPrereqCourseId) return
    try {
      setError(null)
      await apiClient.addTrainerPrerequisite(selectedCourse.id, Number(selectedPrereqCourseId))
      setSuccessMsg('Prerequisite course linked.')
      setSelectedPrereqCourseId('')
      await loadCoursePrerequisites(selectedCourse.id)
    } catch (err) {
      setError(err.message || 'Failed to add prerequisite.')
    }
  }

  async function handleRemovePrerequisite(prereqId) {
    if (!selectedCourse) return
    try {
      setError(null)
      await apiClient.removeTrainerPrerequisite(selectedCourse.id, prereqId)
      setSuccessMsg('Prerequisite removed.')
      await loadCoursePrerequisites(selectedCourse.id)
    } catch (err) {
      setError(err.message || 'Failed to remove prerequisite.')
    }
  }

  // ── Questions Handlers ──

  async function handleCreateQuestion(e) {
    e.preventDefault()
    if (!selectedCourse || !qText.trim() || !qCompId) return
    try {
      setError(null)
      await apiClient.createCourseQuestion(selectedCourse.id, {
        competency_id: Number(qCompId),
        question_type: qType,
        question_text: qText.trim(),
        options: qOptions,
        correct_option: Number(qCorrect),
        difficulty: qDifficulty,
        explanation: qExplanation.trim() || undefined,
      })
      setSuccessMsg('Diagnostic question added to bank.')
      setQText('')
      setQOptions(['', '', '', ''])
      setQExplanation('')
      await loadCourseQuestions(selectedCourse.id)
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to add question.')
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
      const res = await apiClient.submitCourseForReview(selectedCourse.id)
      setSelectedCourse(res.course)
      setSuccessMsg(res.message || 'Course submitted for admin review.')
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to submit course for review.')
    }
  }

  async function handleArchiveCourse() {
    if (!selectedCourse) return
    try {
      setError(null)
      const res = await apiClient.archiveTrainerCourse(selectedCourse.id)
      setSelectedCourse(res.course)
      setSuccessMsg(res.message || 'Course archived.')
      await loadStudioData()
    } catch (err) {
      setError(err.message || 'Failed to archive course.')
    }
  }

  const filteredCourses = courses.filter((c) => {
    if (filterStatus === 'ALL') return true
    return (c.status || '').toUpperCase() === filterStatus
  })

  const totalLessonsInCurriculum = curriculumModules.reduce(
    (acc, m) => acc + (m.lessons?.length || 0),
    0
  )

  const candidatePrereqCourses = courses.filter(
    (c) =>
      c.id !== selectedCourse?.id &&
      !prerequisites.some((p) => p.prerequisite_course_id === c.id)
  )

  return (
    <div className="trainer-studio-container">
      {/* Header bar */}
      <div className="section-header" style={{ marginBottom: '20px' }}>
        <div>
          <h2 className="learner-name" style={{ marginBottom: '4px' }}>
            Course Authoring Studio
          </h2>
          <p className="learner-email">
            Design accredited curriculum modules, interactive lessons, diagnostic question banks, and competency mappings
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {selectedCourse && (
            <button
              type="button"
              className="action-pill-btn btn-secondary"
              onClick={() => setSelectedCourse(null)}
            >
              ← Back to Course List
            </button>
          )}
          <button
            type="button"
            className="action-pill-btn btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            + Create New Course
          </button>
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
            <div className="editor-tab-nav" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'meta' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('meta')}
              >
                1. Overview & Settings
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
                className={`tab-btn ${activeTab === 'curriculum' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('curriculum')}
              >
                3. Curriculum & Lessons ({totalLessonsInCurriculum})
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'prerequisites' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('prerequisites')}
              >
                4. Prerequisites ({prerequisites.length})
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'questions' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('questions')}
              >
                5. Question Bank ({questions.length})
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'submit' ? 'tab-btn-active' : ''}`}
                onClick={() => setActiveTab('submit')}
              >
                6. Review & Submit
              </button>
            </div>
          </div>

          {/* Tab 1: Meta Editor */}
          {activeTab === 'meta' && (
            <div className="profile-card">
              <h4 className="section-title">Edit Course Metadata & Certification Thresholds</h4>
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
                  <label>Minimum Diagnostic Score for Certificate (%)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="e.g. 70 (Leave blank for none)"
                    value={
                      selectedCourse.min_diagnostic_score !== null &&
                      selectedCourse.min_diagnostic_score !== undefined
                        ? selectedCourse.min_diagnostic_score
                        : ''
                    }
                    onChange={(e) =>
                      setSelectedCourse({
                        ...selectedCourse,
                        min_diagnostic_score: e.target.value === '' ? null : e.target.value,
                      })
                    }
                    min="0"
                    max="100"
                    disabled={selectedCourse.status === 'PENDING_REVIEW'}
                  />
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    Optional prerequisite score threshold learners must achieve on the diagnostic assessment before a completion certificate is issued.
                  </span>
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
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedCourse.competencies.map((c) => (
                        <tr key={c.id}>
                          <td><strong>{c.name}</strong></td>
                          <td>Level {c.required_level || 3}</td>
                          <td>
                            <span className={`priority-tag priority-${(c.priority || 'MEDIUM').toLowerCase()}`}>
                              {c.priority || 'MEDIUM'}
                            </span>
                          </td>
                          <td>
                            {selectedCourse.status !== 'PENDING_REVIEW' && (
                              <button
                                type="button"
                                className="action-link-btn delete-btn"
                                onClick={() => handleUnmapCompetency(c.id)}
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

              {selectedCourse.status !== 'PENDING_REVIEW' && (
                <form onSubmit={handleMapCompetency} className="mapping-form" style={{ borderTop: '1px solid var(--border-color, #e2e8f0)', paddingTop: '1.25rem' }}>
                  <h5 style={{ margin: '0 0 0.75rem 0' }}>Map Another Competency</h5>
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
                        {allCompetencies.map((comp) => (
                          <option key={comp.id} value={comp.id}>
                            {comp.name} ({comp.category || 'Competency'})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Required Level (1-5)</label>
                      <input
                        type="number"
                        className="form-input"
                        value={mapLevel}
                        onChange={(e) => setMapLevel(e.target.value)}
                        min="1"
                        max="5"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Target Priority</label>
                      <select
                        className="form-input"
                        value={mapPriority}
                        onChange={(e) => setMapPriority(e.target.value)}
                      >
                        <option value="CRITICAL">CRITICAL</option>
                        <option value="HIGH">HIGH</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="LOW">LOW</option>
                      </select>
                    </div>
                  </div>
                  <button type="submit" className="action-pill-btn btn-secondary" style={{ marginTop: '1rem' }}>
                    + Map Competency
                  </button>
                </form>
              )}
            </div>
          )}

          {/* Tab 3: Curriculum & Lessons (Phase 14) */}
          {activeTab === 'curriculum' && (
            <div className="profile-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div>
                  <h4 className="section-title" style={{ margin: 0 }}>Course Curriculum & Lessons</h4>
                  <p className="section-subtitle" style={{ margin: '4px 0 0 0' }}>
                    Structured modules and interactive lessons (Text, External Links, Video URLs).
                  </p>
                </div>
                {selectedCourse.status !== 'PENDING_REVIEW' && (
                  <button
                    type="button"
                    className="action-pill-btn btn-primary"
                    onClick={handleOpenAddModule}
                  >
                    + Add New Module
                  </button>
                )}
              </div>

              {loadingCurriculum ? (
                <p className="loading-text">Loading curriculum...</p>
              ) : curriculumModules.length === 0 ? (
                <div className="empty-notice" style={{ padding: '28px', textAlign: 'center' }}>
                  No modules created yet. Click "+ Add New Module" to begin creating your structured syllabus.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '16px' }}>
                  {curriculumModules.map((mod, mIdx) => (
                    <div
                      key={mod.id}
                      style={{
                        border: '1px solid var(--border-color, #e2e8f0)',
                        borderRadius: '8px',
                        padding: '16px 20px',
                        background: 'var(--bg-secondary, #f8fafc)',
                      }}
                    >
                      {/* Module Header */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color, #e2e8f0)', paddingBottom: '12px', marginBottom: '14px' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span className="badge-pill bg-purple" style={{ fontSize: '10px' }}>
                              Module {mIdx + 1}
                            </span>
                            <h4 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                              {mod.title}
                            </h4>
                          </div>
                          {mod.description && (
                            <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#64748b' }}>
                              {mod.description}
                            </p>
                          )}
                        </div>

                        {selectedCourse.status !== 'PENDING_REVIEW' && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <button
                              type="button"
                              className="action-pill-btn btn-secondary"
                              style={{ padding: '2px 8px', fontSize: '11px' }}
                              disabled={mIdx === 0}
                              onClick={() => handleMoveModule(mIdx, -1)}
                              title="Move Module Up"
                            >
                              ▲
                            </button>
                            <button
                              type="button"
                              className="action-pill-btn btn-secondary"
                              style={{ padding: '2px 8px', fontSize: '11px' }}
                              disabled={mIdx === curriculumModules.length - 1}
                              onClick={() => handleMoveModule(mIdx, 1)}
                              title="Move Module Down"
                            >
                              ▼
                            </button>
                            <button
                              type="button"
                              className="action-pill-btn btn-secondary"
                              style={{ padding: '4px 10px', fontSize: '12px' }}
                              onClick={() => handleOpenEditModule(mod)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="action-pill-btn btn-danger"
                              style={{ padding: '4px 10px', fontSize: '12px' }}
                              onClick={() => handleDeleteModule(mod.id)}
                            >
                              Delete
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Lessons in Module */}
                      <div style={{ marginBottom: '12px' }}>
                        {(!mod.lessons || mod.lessons.length === 0) ? (
                          <div style={{ fontSize: '0.85rem', color: '#94a3b8', padding: '8px 0' }}>
                            No lessons in this module yet.
                          </div>
                        ) : (
                          <table className="studio-table" style={{ background: '#fff', borderRadius: '6px' }}>
                            <thead>
                              <tr>
                                <th style={{ width: '40px' }}>#</th>
                                <th>Lesson Title</th>
                                <th>Type</th>
                                <th>Est. Time</th>
                                <th>Actions</th>
                              </tr>
                            </thead>
                            <tbody>
                              {mod.lessons.map((les, lIdx) => (
                                <tr key={les.id}>
                                  <td>{lIdx + 1}</td>
                                  <td>
                                    <strong>{les.title}</strong>
                                    {les.is_demo && (
                                      <span className="badge-pill bg-neutral" style={{ fontSize: '9px', marginLeft: '6px' }}>
                                        DEMO
                                      </span>
                                    )}
                                  </td>
                                  <td>
                                    <span className={`badge-pill ${les.lesson_type === 'VIDEO_URL' ? 'bg-purple' : les.lesson_type === 'LINK' ? 'bg-blue' : 'bg-neutral'}`} style={{ fontSize: '10px' }}>
                                      {les.lesson_type}
                                    </span>
                                  </td>
                                  <td>{les.estimated_minutes} min</td>
                                  <td>
                                    {selectedCourse.status !== 'PENDING_REVIEW' && (
                                      <div style={{ display: 'flex', gap: '6px' }}>
                                        <button
                                          type="button"
                                          className="action-link-btn"
                                          disabled={lIdx === 0}
                                          onClick={() => handleMoveLesson(mIdx, lIdx, -1)}
                                          title="Move Up"
                                        >
                                          ▲
                                        </button>
                                        <button
                                          type="button"
                                          className="action-link-btn"
                                          disabled={lIdx === mod.lessons.length - 1}
                                          onClick={() => handleMoveLesson(mIdx, lIdx, 1)}
                                          title="Move Down"
                                        >
                                          ▼
                                        </button>
                                        <button
                                          type="button"
                                          className="action-link-btn"
                                          onClick={() => handleOpenEditLesson(mod.id, les)}
                                        >
                                          Edit
                                        </button>
                                        <button
                                          type="button"
                                          className="action-link-btn delete-btn"
                                          onClick={() => handleDeleteLesson(les.id)}
                                        >
                                          Delete
                                        </button>
                                      </div>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>

                      {/* Add Lesson button */}
                      {selectedCourse.status !== 'PENDING_REVIEW' && (
                        <button
                          type="button"
                          className="action-pill-btn btn-secondary"
                          style={{ fontSize: '12px', padding: '6px 12px' }}
                          onClick={() => handleOpenAddLesson(mod.id)}
                        >
                          + Add Lesson to Module {mIdx + 1}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 4: Prerequisites (Phase 14) */}
          {activeTab === 'prerequisites' && (
            <div className="profile-card">
              <h4 className="section-title">Course Prerequisites</h4>
              <p className="section-subtitle">
                Specify prerequisite courses learners should complete before taking this course. Prerequisites guide personalized recommendation ranking with non-blocking advisories.
              </p>

              <div style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
                {loadingPrereqs ? (
                  <p className="loading-text">Loading prerequisites...</p>
                ) : prerequisites.length === 0 ? (
                  <div className="empty-notice">No prerequisites configured for this course.</div>
                ) : (
                  <table className="studio-table">
                    <thead>
                      <tr>
                        <th>Prerequisite Course Code</th>
                        <th>Course Title</th>
                        <th>Category</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {prerequisites.map((p) => (
                        <tr key={p.id}>
                          <td><strong>{p.course_code}</strong></td>
                          <td>{p.course_name}</td>
                          <td>
                            <span className="badge-pill bg-blue" style={{ fontSize: '10px' }}>
                              {p.course_category}
                            </span>
                          </td>
                          <td>
                            {selectedCourse.status !== 'PENDING_REVIEW' && (
                              <button
                                type="button"
                                className="action-link-btn delete-btn"
                                onClick={() => handleRemovePrerequisite(p.id)}
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

              {selectedCourse.status !== 'PENDING_REVIEW' && (
                <form onSubmit={handleAddPrerequisite} className="mapping-form" style={{ borderTop: '1px solid var(--border-color, #e2e8f0)', paddingTop: '1.25rem' }}>
                  <h5 style={{ margin: '0 0 0.75rem 0' }}>Add Prerequisite Dependency</h5>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Select Prerequisite Course</label>
                      <select
                        className="form-input"
                        value={selectedPrereqCourseId}
                        onChange={(e) => setSelectedPrereqCourseId(e.target.value)}
                        required
                      >
                        <option value="">-- Choose Course --</option>
                        {candidatePrereqCourses.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.code} — {c.name} ({c.category})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <button type="submit" className="action-pill-btn btn-secondary" style={{ marginTop: '1rem' }} disabled={candidatePrereqCourses.length === 0}>
                    + Link Prerequisite
                  </button>
                </form>
              )}
            </div>
          )}

          {/* Tab 5: Question Bank */}
          {activeTab === 'questions' && (
            <div className="profile-card">
              <h4 className="section-title">Diagnostic Assessment Question Bank</h4>
              <p className="section-subtitle">
                Author multiple-choice or scenario-based questions to evaluate competency proficiency.
              </p>

              <div className="questions-list-preview" style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
                {loadingQuestions ? (
                  <p className="loading-text">Loading question bank...</p>
                ) : questions.length === 0 ? (
                  <div className="empty-notice">No diagnostic questions added yet.</div>
                ) : (
                  <div className="question-cards-stack">
                    {questions.map((q, idx) => (
                      <div key={q.id} className="studio-q-card">
                        <div className="q-card-top">
                          <span className="q-idx">Q{idx + 1}</span>
                          <span className="badge-pill bg-blue">{q.question_type}</span>
                          <span className={`difficulty-pill difficulty-${q.difficulty?.toLowerCase()}`}>
                            {q.difficulty}
                          </span>
                          <span className="q-comp-tag">{q.competency_name}</span>
                          {selectedCourse.status !== 'PENDING_REVIEW' && (
                            <button
                              type="button"
                              className="action-link-btn delete-btn"
                              style={{ marginLeft: 'auto' }}
                              onClick={() => handleDeleteQuestion(q.id)}
                            >
                              Delete
                            </button>
                          )}
                        </div>
                        <p className="q-prompt-text">{q.question_text}</p>
                        <div className="q-options-grid">
                          {q.options?.map((opt, oIdx) => (
                            <div
                              key={oIdx}
                              className={`q-opt-item ${oIdx === q.correct_option ? 'correct-opt' : ''}`}
                            >
                              <span className="opt-letter">{String.fromCharCode(65 + oIdx)}:</span>
                              <span>{opt}</span>
                              {oIdx === q.correct_option && <span className="correct-check">✓</span>}
                            </div>
                          ))}
                        </div>
                        {q.explanation && (
                          <div className="q-explanation-box">
                            <strong>Rationale:</strong> {q.explanation}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Add Question Form */}
              {selectedCourse.status !== 'PENDING_REVIEW' && (
                <form onSubmit={handleCreateQuestion} className="question-builder-form" style={{ borderTop: '1px solid var(--border-color, #e2e8f0)', paddingTop: '1.25rem' }}>
                  <h5 style={{ margin: '0 0 0.75rem 0' }}>Add Diagnostic Question</h5>
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

          {/* Tab 6: Review & Submit */}
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
                  <span className={`check-icon ${totalLessonsInCurriculum > 0 ? 'check-pass' : 'check-fail'}`}>
                    {totalLessonsInCurriculum > 0 ? '✓' : '✗'}
                  </span>
                  <div>
                    <strong>Curriculum Structure</strong>: {totalLessonsInCurriculum} lessons across {curriculumModules.length} modules
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
                    ✓ This course is live and visible to registered learners.
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
        /* COURSE LIST VIEW */
        <div className="studio-courses-view">
          <div className="studio-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div className="filter-pill-group">
              {['ALL', 'DRAFT', 'PENDING_REVIEW', 'PUBLISHED', 'ARCHIVED'].map((st) => (
                <button
                  key={st}
                  type="button"
                  className={`filter-pill ${filterStatus === st ? 'filter-pill-active' : ''}`}
                  onClick={() => setFilterStatus(st)}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>
            <span className="results-count">{filteredCourses.length} courses</span>
          </div>

          {filteredCourses.length === 0 ? (
            <div className="profile-card empty-state" style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
              <p>No courses found in this category.</p>
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
              <div className="form-grid" style={{ marginTop: '0.75rem' }}>
                <div className="form-group">
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
                <div className="form-group">
                  <label>Min Diagnostic Score %</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newMinDiagScore}
                    onChange={(e) => setNewMinDiagScore(e.target.value)}
                    placeholder="Optional (e.g. 70)"
                    min="0"
                    max="100"
                  />
                </div>
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

      {/* Add / Edit Module Modal */}
      {showModuleModal && (
        <div className="modal-backdrop">
          <div className="modal-box">
            <div className="modal-header">
              <h3 style={{ margin: 0 }}>{moduleModalEditId ? 'Edit Module' : 'Add New Module'}</h3>
              <button
                type="button"
                className="close-modal-btn"
                onClick={() => setShowModuleModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSaveModule} className="modal-body">
              <div className="form-group">
                <label>Module Title</label>
                <input
                  type="text"
                  className="form-input"
                  value={modTitle}
                  onChange={(e) => setModTitle(e.target.value)}
                  placeholder="e.g. Module 1: Foundational Concepts"
                  required
                />
              </div>
              <div className="form-group" style={{ marginTop: '0.75rem' }}>
                <label>Description (Optional)</label>
                <textarea
                  rows={3}
                  className="form-input"
                  value={modDesc}
                  onChange={(e) => setModDesc(e.target.value)}
                  placeholder="Module objectives and summary..."
                />
              </div>
              <div className="modal-footer" style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  className="action-pill-btn btn-secondary"
                  onClick={() => setShowModuleModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="action-pill-btn btn-primary">
                  {moduleModalEditId ? 'Save Module' : 'Create Module'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add / Edit Lesson Modal */}
      {showLessonModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: '640px' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0 }}>{lessonModalEditId ? 'Edit Lesson' : 'Add New Lesson'}</h3>
              <button
                type="button"
                className="close-modal-btn"
                onClick={() => setShowLessonModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSaveLesson} className="modal-body">
              <div className="form-group">
                <label>Lesson Title</label>
                <input
                  type="text"
                  className="form-input"
                  value={lesTitle}
                  onChange={(e) => setLesTitle(e.target.value)}
                  placeholder="e.g. Understanding Sample Weights in NSSO Surveys"
                  required
                />
              </div>
              <div className="form-grid" style={{ marginTop: '0.75rem' }}>
                <div className="form-group">
                  <label>Lesson Type</label>
                  <select
                    className="form-input"
                    value={lesType}
                    onChange={(e) => setLesType(e.target.value)}
                  >
                    <option value="TEXT">TEXT (Interactive Markdown Reading)</option>
                    <option value="LINK">LINK (Official External Portal / Reading)</option>
                    <option value="VIDEO_URL">VIDEO_URL (Lecture Video Stream)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Estimated Minutes</label>
                  <input
                    type="number"
                    className="form-input"
                    value={lesMinutes}
                    onChange={(e) => setLesMinutes(e.target.value)}
                    min="1"
                    max="600"
                    required
                  />
                </div>
              </div>
              <div className="form-group" style={{ marginTop: '0.75rem' }}>
                <label>
                  {lesType === 'TEXT'
                    ? 'Lesson Content (Markdown formatted)'
                    : lesType === 'LINK'
                    ? 'External Learning Resource URL'
                    : 'Video Lecture Stream URL (YouTube or MP4)'}
                </label>
                <textarea
                  rows={6}
                  className="form-input"
                  value={lesBody}
                  onChange={(e) => setLesBody(e.target.value)}
                  placeholder={
                    lesType === 'TEXT'
                      ? '# Lesson Heading\n\nExplain key statistical concepts, formulas, or code examples...\n\n```python\nimport pandas as pd\n```'
                      : 'https://example.gov.in/resource'
                  }
                  required
                />
              </div>
              <div className="modal-footer" style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  className="action-pill-btn btn-secondary"
                  onClick={() => setShowLessonModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="action-pill-btn btn-primary">
                  {lessonModalEditId ? 'Save Lesson' : 'Create Lesson'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default CourseStudio
