import { defineStore } from 'pinia'
import { computed } from 'vue'
import type { AuthUser } from '~/types/auth-user'

export const useAuthStore = defineStore('auth', () => {
  const token = useCookie<string | null>('auth_token', { default: () => null })
  const user = useCookie<AuthUser | null>('auth_user', { default: () => null })

  const isLoggedIn = computed(() => Boolean(token.value))

  function login(newToken: string, userData: AuthUser) {
    token.value = newToken
    user.value = userData
  }

  function logout() {
    token.value = null
    user.value = null
    return navigateTo('/login')
  }

  /**
   * Frontend-only visibility check. Backend must still enforce authorization.
   * When `pageAccess` is missing or includes `ALL_PAGES`, access is allowed.
   */
  function canAccessPage(pageId: string): boolean {
    const access = user.value?.pageAccess
    if (!access?.length) return true
    if (access.includes('ALL_PAGES')) return true
    return access.includes(pageId)
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    logout,
    canAccessPage,
  }
})
