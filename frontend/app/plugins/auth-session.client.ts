import { AUTH_SESSION_EVENT_KEY } from '~/utils/auth/session-sync'

export default defineNuxtPlugin(async () => {
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

  const valid = await auth.validateSession()
  if (!valid && !route.path.startsWith('/auth/')) {
    await navigateTo('/auth/login', { replace: true })
  }
})
