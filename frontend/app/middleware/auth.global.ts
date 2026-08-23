import { useAccessAlert } from '~/composables/common/useAccessAlert'
import { resolveAuthRoute } from '~/utils/auth/permission-routing'

export default defineNuxtRouteMiddleware((to, from) => {
  // HttpOnly session cookies are validated in the client plugin (`/auth/me`).
  // Skipping SSR avoids bouncing to login before the browser can send cookies.
  if (import.meta.server) return

  const auth = useAuthStore()
  const { showPermissionDenied } = useAccessAlert()
  const permission = typeof to.meta.permission === 'string' ? to.meta.permission : ''
  const decision = resolveAuthRoute({
    isLoggedIn: auth.isLoggedIn,
    toPath: to.path,
    permission,
    canAccessPage: pageId => auth.canAccessPage(pageId),
    fromMatched: from.matched.length > 0,
    fromPath: from.path,
  })

  if (
    decision.kind !== 'allow'
    && permission
    && auth.isLoggedIn
    && !auth.canAccessPage(permission)
  ) {
    showPermissionDenied({
      requestedPath: to.fullPath,
      permission,
    })
  }

  if (decision.kind === 'allow') return
  if (decision.kind === 'abort') return abortNavigation()
  if (decision.kind === 'deny-and-login') {
    auth.clearSession()
    return navigateTo('/auth/login', { replace: true })
  }
  return navigateTo(decision.path, { replace: decision.replace })
})
