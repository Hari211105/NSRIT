/**
 * UPSKILL AI - Token storage (Phase 7C)
 *
 * Stores the JWT access token in `sessionStorage`, keyed by
 * `upskill_access_token`.
 *
 * SECURITY NOTE (read before choosing to rely on this):
 *   - `sessionStorage` is NOT fully secure: it is readable by any script
 *     running on this origin, so it is exposed to XSS. We accept this for the
 *     MVP and bound the risk with the backend's short access-token lifetime
 *     (JWT_ACCESS_TOKEN_EXPIRE_MINUTES, default 60 minutes) and the absence of a
 *     refresh token — a leaked token self-expires.
 *   - It survives page refreshes within the tab but is cleared when the tab or
 *     window closes (per-tab session, not shared across tabs).
 *   - Production hardening would move the token to an HttpOnly + Secure cookie
 *     with a refresh-token flow. That is out of scope for Phase 7C.
 *
 * Nothing below ever stores a password or logs the token.
 */

const TOKEN_KEY = 'upskill_access_token';

/** Read the current access token, or null when absent / storage unavailable. */
export function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

/** Persist the access token for this tab's session. */
export function setToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage unavailable (e.g. private mode) — session simply won't survive a refresh.
  }
}

/** Remove the stored access token (logout / session clear). */
export function clearToken() {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
}

/** Decode the JWT `exp` claim (epoch seconds) or return null if not decodable. */
export function getTokenExpiry(token) {
  if (!token || typeof token !== 'string') return null;
  const parts = token.split('.');
  if (parts.length < 2) return null;
  let payload;
  try {
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
    payload = JSON.parse(atob(padded));
  } catch {
    return null;
  }
  return typeof payload?.exp === 'number' ? payload.exp : null;
}

export const TOKEN_STORAGE_KEY = TOKEN_KEY;