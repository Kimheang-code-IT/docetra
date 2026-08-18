export const AUTH_SESSION_EVENT_KEY = 'docetra:auth:session-event'

export type AuthSessionEvent = 'login' | 'logout'

export function publishAuthSessionEvent(kind: AuthSessionEvent) {
  if (!import.meta.client) return
  localStorage.setItem(AUTH_SESSION_EVENT_KEY, JSON.stringify({ kind, at: Date.now() }))
}
