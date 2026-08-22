import { defineStore } from 'pinia'
import { computed } from 'vue'
import type { AuthUser } from '~/types/auth-user'
import { publishAuthSessionEvent } from '~/utils/auth/session-sync'

const USER_STORAGE_KEY = 'docetra:auth:user'

function readStoredUser(): AuthUser | null {
  if (!import.meta.client) return null
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthUser
    return parsed && typeof parsed === 'object' && parsed.email ? parsed : null
  }
  catch {
    return null
  }
}

function writeStoredUser(value: AuthUser | null) {
  if (!import.meta.client) return
  try {
    if (!value) localStorage.removeItem(USER_STORAGE_KEY)
    else localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(value))
  }
  catch {
    // Quota / private mode — keep in-memory session for this tab only.
  }
}

function unwrapUserPayload(payload: unknown): AuthUser | null {
  if (!payload || typeof payload !== 'object') return null
  const record = payload as Record<string, unknown>
  if (record.email && record.name) return record as unknown as AuthUser
  const nested = record.user
  if (nested && typeof nested === 'object' && (nested as AuthUser).email) {
    return nested as AuthUser
  }
  return null
}

export const useAuthStore = defineStore('auth', () => {
  const config = useRuntimeConfig()
  const usesCookieSession = computed(() => config.public.authMode !== 'bearer')
  // Bearer mode only — keep a small token cookie. User profile is never stored in a cookie
  // (SuperAdmin permissions exceed browser cookie size limits ~4KB).
  const token = useCookie<string | null>('auth_token', {
    default: () => null,
    path: '/',
    sameSite: 'lax',
    secure: import.meta.env.PROD,
  })
  const user = useState<AuthUser | null>('auth-user', () => readStoredUser())
  const sessionChecked = useState('auth-session-checked', () => false)
  const sessionChecking = useState('auth-session-checking', () => false)

  const isLoggedIn = computed(() => usesCookieSession.value ? Boolean(user.value) : Boolean(token.value))

  function login(newToken: string | null | undefined, userData: AuthUser) {
    token.value = usesCookieSession.value ? null : (newToken || null)
    user.value = userData
    writeStoredUser(userData)
    sessionChecked.value = true
    publishAuthSessionEvent('login')
  }

  function clearSession(notify = true) {
    token.value = null
    user.value = null
    writeStoredUser(null)
    sessionChecked.value = true
    if (notify) publishAuthSessionEvent('logout')
  }

  async function logout() {
    try {
      const { logoutSession } = await import('~/adapters/auth')
      await logoutSession()
    }
    catch {
      // Always clear the browser snapshot; the backend session expires independently.
    }
    finally {
      clearSession()
      await navigateTo('/auth/login')
    }
  }

  async function validateSession() {
    if (sessionChecking.value) return isLoggedIn.value
    sessionChecking.value = true
    try {
      const { getCurrentSession, refreshSession } = await import('~/adapters/auth')
      try {
        const response = await getCurrentSession()
        const next = unwrapUserPayload((response as { data?: unknown }).data ?? response)
        if (!next) throw new Error('Invalid session payload')
        user.value = next
        writeStoredUser(next)
        sessionChecked.value = true
        return true
      }
      catch {
        const refreshed = await refreshSession()
        const next = unwrapUserPayload((refreshed as { data?: unknown }).data ?? refreshed)
        if (!next) throw new Error('Invalid refresh payload')
        user.value = next
        writeStoredUser(next)
        sessionChecked.value = true
        return true
      }
    }
    catch {
      clearSession(false)
      return false
    }
    finally {
      sessionChecking.value = false
    }
  }

  /**
   * Frontend-only visibility check. Backend must still enforce authorization.
   * `permissions` is authoritative when present. `pageAccess` remains a
   * backwards-compatible fallback for older sessions.
   */
  function canAccessPage(pageId: string): boolean {
    const currentUser = user.value
    if (!currentUser) return false
    if (currentUser.pageAccess?.includes('ALL_PAGES')) return true

    if (Array.isArray(currentUser.permissions)) {
      if (currentUser.permissions.includes('ALL_PAGES')) return true
      return currentUser.permissions.includes(pageId)
    }

    const access = currentUser.pageAccess
    if (!access?.length) return true
    return access.includes(pageId)
  }

  function updateUser(partial: Partial<AuthUser>) {
    if (!user.value) return
    const next = { ...user.value, ...partial }
    if ('avatar' in partial && partial.avatar == null) {
      delete next.avatar
    }
    user.value = next
    writeStoredUser(next)
  }

  return {
    token,
    user,
    isLoggedIn,
    sessionChecked: readonly(sessionChecked),
    sessionChecking: readonly(sessionChecking),
    login,
    clearSession,
    logout,
    validateSession,
    updateUser,
    canAccessPage,
  }
})
