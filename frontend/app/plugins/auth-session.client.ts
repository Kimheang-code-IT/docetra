import { AUTH_SESSION_EVENT_KEY } from '~/utils/auth/session-sync'

export default defineNuxtPlugin(async (nuxtApp): Promise<void> => {
  const auth = useAuthStore()
  const route = useRoute()

  function onStorage(event: StorageEvent) {
    if (event.key !== AUTH_SESSION_EVENT_KEY || !event.newValue) return
    try {
      const payload = JSON.parse(event.newValue) as { kind?: string }
      if (payload.kind === 'logout') auth.clearSession(false)
      if (payload.kind === 'login') window.location.reload()
    }
    catch {
      // Ignore malformed local browser state.
    }
  }

  window.addEventListener('storage', onStorage)
  if (import.meta.hot) import.meta.hot.dispose(() => window.removeEventListener('storage', onStorage))

  async function guardSession() {
    const valid = await auth.validateSession()
    if (!valid && !route.path.startsWith('/auth/')) {
      await navigateTo('/auth/login', { replace: true })
    }
  }

  // Public auth screens must paint immediately. With no local session there is
  // nothing to validate, and calling /auth/me followed by /auth/refresh only
  // delays the login screen and produces expected 401/403 console noise.
  if (!auth.isLoggedIn && window.location.pathname.startsWith('/auth/')) return

  // A stored user is enough to paint the shell. Re-check /auth/me in the background
  // so a slow or down API does not freeze the first page for up to 30s+.
  if (auth.isLoggedIn) {
    void nuxtApp.runWithContext(() => guardSession())
    return
  }
  await nuxtApp.runWithContext(() => guardSession())
})
