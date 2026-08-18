import { useAuthStore } from '~/stores/auth'
import type { AuthUser } from '~/types/auth-user'

/**
 * Thin session facade over the auth Pinia store.
 */
export const useAuthSession = () => {
  const store = useAuthStore()

  const login = (token: string | null | undefined, user: AuthUser) => {
    store.login(token, user)
  }

  const logout = async () => {
    await store.logout()
  }

  const getUser = () => store.user

  return {
    login,
    logout,
    getUser,
    isLoggedIn: computed(() => store.isLoggedIn),
    canAccessPage: store.canAccessPage,
  }
}
