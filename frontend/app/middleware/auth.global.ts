export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()

  // Define public pages
  const isPublicPage = ['/login', '/otp', '/forget-password'].includes(to.path)

  // Redirect if not logged in and trying to access a private page
  if (!auth.isLoggedIn && !isPublicPage) {
    return navigateTo('/login')
  }

  // Redirect if logged in and trying to access login page
  if (auth.isLoggedIn && isPublicPage) {
    return navigateTo('/')
  }
})
