import type { AuthUser } from '~/types/auth-user'

export const AUTH_USER_STORAGE_KEY = 'docetra:auth:user'

export function readStoredUser(): AuthUser | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(AUTH_USER_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthUser
    return parsed && typeof parsed === 'object' && parsed.email ? parsed : null
  }
  catch {
    return null
  }
}

export function writeStoredUser(value: AuthUser | null) {
  if (typeof window === 'undefined') return
  try {
    if (!value) localStorage.removeItem(AUTH_USER_STORAGE_KEY)
    else localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(value))
  }
  catch {
    // Quota / private mode — keep in-memory session for this tab only.
  }
}

export function unwrapUserPayload(payload: unknown): AuthUser | null {
  if (!payload || typeof payload !== 'object') return null
  const record = payload as Record<string, unknown>
  if (record.email && record.name) return record as unknown as AuthUser
  const nested = record.user
  if (nested && typeof nested === 'object' && (nested as AuthUser).email) {
    return nested as AuthUser
  }
  return null
}

/**
 * Frontend-only visibility check. Backend must still enforce authorization.
 * `permissions` is authoritative when present. `pageAccess` remains a
 * backwards-compatible fallback for older sessions.
 */
export function userCanAccessPage(user: AuthUser | null | undefined, pageId: string): boolean {
  if (!user) return false
  if (user.pageAccess?.includes('ALL_PAGES')) return true

  if (Array.isArray(user.permissions)) {
    if (user.permissions.includes('ALL_PAGES')) return true
    return user.permissions.includes(pageId)
  }

  const access = user.pageAccess
  if (!access?.length) return true
  return access.includes(pageId)
}
