/**
 * UPSKILL AI - Authentication Context (Phase 7C)
 *
 * Owns the session state for the whole app:
 *   status  - 'loading' | 'authenticated' | 'unauthenticated'
 *   user    - the authenticated User { id, name, email, role, is_demo }
 *   message - a one-off banner (e.g. "your session has expired")
 *
 * On mount it tries to restore a session from the stored token: if there is no
 * token, or the token is already expired, the user is logged out; otherwise the
 * token is validated against GET /auth/me. An expiring token schedules a
 * automatic logout at its expiry. It also registers the api.js unauthorized
 * handler so any 401 on a token-bearing request clears the session centrally.
 */
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react'
import { apiClient, setUnauthorizedHandler } from '../services/api'
import {
  getToken,
  setToken,
  clearToken,
  getTokenExpiry,
} from '../services/tokenStorage'

const AuthContext = createContext(null)

const SESSION_EXPIRED_MSG = 'Your session has expired. Please log in again.'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading') // loading | authenticated | unauthenticated
  const [message, setMessage] = useState('')
  const expiryTimer = useRef(null)

  const clearSession = useCallback((msg = '') => {
    clearToken()
    setUser(null)
    setStatus('unauthenticated')
    setMessage(msg)
    if (expiryTimer.current) {
      clearTimeout(expiryTimer.current)
      expiryTimer.current = null
    }
  }, [])

  // Central session teardown (logout). Also swallows any in-memory user state.
  const logout = useCallback(() => clearSession(''), [clearSession])

  // Register the api.js unauthorized handler once so any token-bearing 401
  // routes back to login with a clear message.
  useEffect(() => {
    setUnauthorizedHandler(() => clearSession(SESSION_EXPIRED_MSG))
    return () => setUnauthorizedHandler(null)
  }, [clearSession])

  // Schedule an automatic logout when the token reaches its exp claim.
  const scheduleExpiry = useCallback(
    (token) => {
      const exp = getTokenExpiry(token)
      if (!exp) return
      if (Date.now() >= exp * 1000) {
        clearSession(SESSION_EXPIRED_MSG)
        return
      }
      expiryTimer.current = setTimeout(
        () => clearSession(SESSION_EXPIRED_MSG),
        exp * 1000 - Date.now()
      )
    },
    [clearSession]
  )

  // Restore a session on mount.
  useEffect(() => {
    const token = getToken()
    if (!token) {
      setStatus('unauthenticated')
      return
    }

    // Already past its expiry -> no need to hit the backend.
    const exp = getTokenExpiry(token)
    if (exp && Date.now() >= exp * 1000) {
      clearSession(SESSION_EXPIRED_MSG)
      return
    }

    scheduleExpiry(token)

    apiClient
      .getAuthMe()
      .then((me) => {
        setUser(me)
        setStatus('authenticated')
      })
      .catch(() => {
        // Token rejected by the backend -> clear without a scary message.
        clearSession()
      })
  }, [clearSession, scheduleExpiry])

  const login = useCallback(
    async (email, password) => {
      const data = await apiClient.login(email, password)
      setToken(data.access_token)
      scheduleExpiry(data.access_token)
      setUser(data.user)
      setMessage('')
      setStatus('authenticated')
      return data.user
    },
    [scheduleExpiry]
  )

  const register = useCallback(
    async (name, email, password) => {
      await apiClient.register(name, email, password)
      return await login(email, password)
    },
    [login]
  )

  // Phase 8 - re-fetch the user after profile changes (e.g. onboarding) so the
  // whole app sees the updated role/profile fields without a re-login.
  const refreshUser = useCallback(async () => {
    try {
      const me = await apiClient.getAuthMe()
      setUser(me)
      return me
    } catch {
      // Token just expired mid-flow - the 401 handler clears the session.
      return null
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{ user, status, message, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}