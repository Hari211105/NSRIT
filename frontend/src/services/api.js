/**
 * UPSKILL AI - API Client Utility
 * Centralizes all backend network requests separate from UI components.
 */

import { getToken } from './tokenStorage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Called when a token-bearing request comes back 401 (missing/invalid/expired
// session). Registered by AuthContext so it can clear the session centrally;
// the login request itself never triggers it (no token is attached yet).
let unauthorizedHandler = null;
export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

function fireUnauthorized() {
  if (typeof unauthorizedHandler === 'function') {
    // Defer so the caller still receives (and can handle) the thrown error.
    setTimeout(() => unauthorizedHandler(), 0);
  }
}

function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function request(path, { method = 'GET', body } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });
  } catch {
    const error = new Error('Could not reach the backend. Make sure it is running.');
    error.status = 0;
    throw error;
  }

  if (!response.ok) {
    // Prefer the backend's own message when it sends one (e.g. quiz errors).
    let detail = '';
    try {
      const payload = await response.json();
      if (payload && typeof payload.detail === 'string') detail = payload.detail;
    } catch {
      // Non-JSON error body — fall back to the generic message below.
    }
    // A token-bearing request rejected with 401 means the session is no longer
    // valid — tell AuthContext to log the user out and return to login.
    if (response.status === 401 && getToken()) {
      fireUnauthorized();
    }
    const error = new Error(
      detail || `Server error: ${response.status} ${response.statusText}`
    );
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export const apiClient = {
  // ── Authentication (Phase 7C & 7D) ──

  /** Register a new account with name/email/password. */
  register: async (name, email, password) => {
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });
    } catch {
      const error = new Error('Could not reach the backend. Make sure it is running.');
      error.status = 0;
      throw error;
    }
    if (!response.ok) {
      let detail = '';
      try {
        const payload = await response.json();
        if (payload && typeof payload.detail === 'string') detail = payload.detail;
      } catch {
        // ignore
      }
      const error = new Error(
        detail || `Registration failed: ${response.status} ${response.statusText}`
      );
      error.status = response.status;
      throw error;
    }
    return response.json();
  },

  /** Log in with email/password; returns { access_token, user }. */
  login: async (email, password) => {
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
    } catch {
      const error = new Error('Could not reach the backend. Make sure it is running.');
      error.status = 0;
      throw error;
    }
    if (!response.ok) {
      let detail = '';
      try {
        const payload = await response.json();
        if (payload && typeof payload.detail === 'string') detail = payload.detail;
      } catch {
        // ignore
      }
      const error = new Error(
        detail || `Login failed: ${response.status} ${response.statusText}`
      );
      error.status = response.status;
      throw error;
    }
    return response.json();
  },

  /** Resolve the current authenticated user from the stored token. */
  getAuthMe: () => request('/auth/me'),
  /** Verify backend health */
  checkHealth: () => request('/health'),

  // ── Onboarding (Phase 8 & 9) ──

  /** Check whether the signed-in user must complete onboarding + list positions and sectors. */
  getOnboardingStatus: () => request('/auth/onboarding-status'),

  /** Persist the selected position/designation and professional profile. */
  completeOnboarding: (payload) =>
    request('/auth/complete-onboarding', { method: 'POST', body: payload }),

  /** Get all sectors */
  getSectors: () => request('/sectors'),

  /** Get roles for a specific sector */
  getSectorRoles: (sectorId) => request(`/sectors/${sectorId}/roles`),

  /** Get all roles */
  getRoles: () => request('/roles'),

  /** Get all competencies */
  getCompetencies: () => request('/competencies'),

  /** Get the authenticated learner's full competency profile */
  getLearnerCompetencies: () => request('/me/competencies'),

  /** Get required competencies for a specific role */
  getRoleCompetencies: (roleId) => request(`/roles/${roleId}/competencies`),

  /** Get the authenticated learner profile */
  getLearnerProfile: () => request('/me'),

  /** Get the authenticated learner's gap analysis */
  getLearnerGaps: () => request('/me/gaps'),

  /** Get all demo learning resources in the catalog */
  getCatalogResources: () => request('/catalog/resources'),

  /** Get personalized recommendations for the demo learner */
  getLearnerRecommendations: () => request('/me/recommendations'),

  /** Get document metadata (filename, chunk count) */
  getDocument: (documentId) => request(`/documents/${documentId}`),

  /** Get the learner-safe quiz questions for a document (no answer key) */
  getDocumentQuiz: (documentId) => request(`/documents/${documentId}/quiz`),

  /** Submit quiz answers to be scored server-side */
  submitDocumentQuiz: (documentId, answers) =>
    request(`/documents/${documentId}/quiz/submit`, {
      method: 'POST',
      body: { answers },
    }),

  /**
   * Upload a PDF learning material (multipart/form-data). Returns the document
   * record with id, filename and chunk totals. The backend remains the
   * authority on file type/emptiness; competencyId (optional) links the
   * document so later quizzes record competency evidence.
   */
  uploadDocument: async (file, competencyId) => {
    const formData = new FormData()
    formData.append('file', file)
    if (competencyId) formData.append('competency_id', String(competencyId))
    let response
    try {
      response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: 'POST',
        headers: authHeaders(),
        body: formData,
      })
    } catch {
      const error = new Error(
        'Could not reach the backend. Make sure it is running.'
      )
      error.status = 0
      throw error
    }
    if (!response.ok) {
      let detail = ''
      try {
        const payload = await response.json()
        if (payload && typeof payload.detail === 'string') detail = payload.detail
      } catch {
        // Non-JSON error body — fall back to the generic message below.
      }
      if (response.status === 401 && getToken()) {
        fireUnauthorized()
      }
      const error = new Error(detail || `Upload failed: ${response.status}`)
      error.status = response.status
      throw error
    }
    return response.json()
  },

  /** Generate five source-grounded MCQs for the next uncovered chunk of a document. */
  generateDocumentMcqs: (documentId) =>
    request(`/documents/${documentId}/mcqs/generate`, { method: 'POST' }),

  // ── Diagnostic Assessment (Phase 2) ──

  /** Start a new diagnostic assessment */
  startDiagnostic: () =>
    request('/diagnostic/start', { method: 'POST' }),

  /** Get diagnostic assessment details */
  getDiagnostic: (assessmentId) =>
    request(`/diagnostic/${assessmentId}`),

  /** Submit diagnostic answers */
  submitDiagnostic: (assessmentId, answers) =>
    request(`/diagnostic/${assessmentId}/submit`, {
      method: 'POST',
      body: { answers },
    }),

  /** Get diagnostic assessment history */
  getDiagnosticHistory: () =>
    request('/diagnostic/history'),
};

export default apiClient;
