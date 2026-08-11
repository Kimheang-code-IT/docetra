export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()

  const publicPaths = [
    '/auth/login',
    '/auth/forget-password',
    '/auth/verify-code',
    '/auth/reset-password',
    // Legacy redirects
    '/login',
    '/forget-password',
  ]
  const isPublicPage = publicPaths.includes(to.path)

  if (!auth.isLoggedIn && !isPublicPage) {
    return navigateTo('/auth/login')
  }

  if (auth.isLoggedIn && isPublicPage) {
    return navigateTo('/')
  }

  const permission = typeof to.meta.permission === 'string' ? to.meta.permission : ''
  if (auth.isLoggedIn && permission && !auth.canAccessPage(permission)) {
    // abortNavigation can leave URL on /new while the previous page stays mounted.
    // Redirect to a safe page instead so route and view stay in sync.
    if (to.path.endsWith('/new')) {
      const parent = to.path.slice(0, -'/new'.length) || '/'
      return navigateTo(parent)
    }
    return navigateTo('/')
  }
})
