import { defineStore } from 'pinia'
import { computed } from 'vue'
import type { AuthUser } from '~/types/auth-user'
import { publishAuthSessionEvent } from '~/utils/auth/session-sync'
import { fetchErrorStatus, shouldRefreshSessionOnAuthMeFailure } from '~/utils/api/error-policy'
import { readStoredUser, unwrapUserPayload, userCanAccessPage, writeStoredUser } from '~/utils/auth/session-user'

export const useAuthStore = defineStore('auth', () => {
  // Capture the Nuxt instance while the store is created from setup/plugin context.
  // Auth API functions call useApi(), so calls made after a dynamic import must be
  // restored to this context (Nuxt E1001 otherwise).
  const nuxtApp = useNuxtApp()
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
      const { logoutSession } = await import('~/composables/auth/useAuthApi')
      await nuxtApp.runWithContext(() => logoutSession())
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
      const { getCurrentSession, refreshSession } = await import('~/composables/auth/useAuthApi')
      try {
        const response = await nuxtApp.runWithContext(() => getCurrentSession())
        const next = unwrapUserPayload((response as { data?: unknown }).data ?? response)
        if (!next) throw new Error('Invalid session payload')
        user.value = next
        writeStoredUser(next)
        sessionChecked.value = true
        return true
      }
      catch (error) {
        const status = fetchErrorStatus(error)
        if (shouldRefreshSessionOnAuthMeFailure(status)) {
          const refreshed = await nuxtApp.runWithContext(() => refreshSession())
          const next = unwrapUserPayload((refreshed as { data?: unknown }).data ?? refreshed)
          if (!next) throw new Error('Invalid refresh payload', { cause: error })
          user.value = next
          writeStoredUser(next)
          sessionChecked.value = true
          return true
        }
        // Timeouts and 5xx must not wipe a working local session.
        if (user.value) {
          sessionChecked.value = true
          return true
        }
        throw error
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

  function canAccessPage(pageId: string): boolean {
    return userCanAccessPage(user.value, pageId)
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
    // A computed view is externally readonly without wrapping the writable
    // useState ref itself (which caused Vue's readonly-set warnings).
    sessionChecked: computed(() => sessionChecked.value),
    sessionChecking: computed(() => sessionChecking.value),
    login,
    clearSession,
    logout,
    validateSession,
    updateUser,
    canAccessPage,
  }
})
