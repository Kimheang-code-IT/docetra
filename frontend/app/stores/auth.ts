import { defineStore } from 'pinia'
import { computed } from 'vue'
import type { AuthUser } from '~/types/auth-user'
import { publishAuthSessionEvent } from '~/utils/auth/session-sync'

export const useAuthStore = defineStore('auth', () => {
  const config = useRuntimeConfig()
  const usesCookieSession = computed(() =>
    config.public.useMockData === false && config.public.authMode === 'cookie',
  )
  const cookieOptions = {
    default: () => null,
    path: '/',
    sameSite: 'strict' as const,
    secure: import.meta.env.PROD,
  }
  // The access token remains JS-readable until the API supports an HttpOnly session cookie.
  const token = useCookie<string | null>('auth_token', cookieOptions)
  const user = useCookie<AuthUser | null>('auth_user', cookieOptions)
  const sessionChecked = useState('auth-session-checked', () => false)
  const sessionChecking = useState('auth-session-checking', () => false)

  const isLoggedIn = computed(() => usesCookieSession.value ? Boolean(user.value) : Boolean(token.value))

  function login(newToken: string | null | undefined, userData: AuthUser) {
    token.value = usesCookieSession.value ? null : (newToken || null)
    user.value = userData
    sessionChecked.value = true
    publishAuthSessionEvent('login')
  }

  function clearSession(notify = true) {
    token.value = null
    user.value = null
    sessionChecked.value = true
    if (notify) publishAuthSessionEvent('logout')
  }

  async function logout() {
    try {
      if (config.public.useMockData === false) {
        const { logoutSession } = await import('~/adapters/auth')
        await logoutSession()
      }
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
    if (config.public.useMockData !== false) {
      sessionChecked.value = true
      return isLoggedIn.value
    }
    if (sessionChecking.value) return isLoggedIn.value
    sessionChecking.value = true
    try {
      const { getCurrentSession } = await import('~/adapters/auth')
      const response = await getCurrentSession()
      user.value = response.data
      sessionChecked.value = true
      return true
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
