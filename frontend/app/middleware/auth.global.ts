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
})
