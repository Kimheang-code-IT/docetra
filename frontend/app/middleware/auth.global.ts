import { useAccessAlert } from '~/composables/common/useAccessAlert'

const PERMITTED_LANDING_ROUTES = [
  ['/', 'dashboard.view'],
  ['/meetings/topics', 'meetings.topics.view'],
  ['/meetings/history', 'meetings.history.view'],
  ['/records/incoming-documents', 'records.incoming_documents.view'],
  ['/records/outgoing-documents', 'records.outgoing_documents.view'],
  ['/records/documents', 'records.documents.view'],
  ['/records/master-list-requests', 'records.master_list_requests.view'],
  ['/organizations/departments', 'organizations.departments.view'],
  ['/organizations/companies', 'organizations.companies.view'],
  ['/portal/file-upload', 'portal.file_upload.view'],
  ['/user-management/users', 'users.users.view'],
  ['/user-management/roles', 'users.roles.view'],
] as const

export default defineNuxtRouteMiddleware((to, from) => {
  const auth = useAuthStore()
  const { showPermissionDenied } = useAccessAlert()

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
    showPermissionDenied({
      requestedPath: to.fullPath,
      permission,
    })

    // Keep the current authorized page when denial happens during navigation.
    if (from.matched.length && from.path !== to.path) return abortNavigation()

    // A direct URL needs an authorized page underneath the global dialog.
    const landing = PERMITTED_LANDING_ROUTES.find(([, required]) => auth.canAccessPage(required))
    if (landing) return navigateTo(landing[0], { replace: true })

    // An account with no usable page returns to sign-in without creating a denial page.
    auth.clearSession()
    return navigateTo('/auth/login', { replace: true })
  }
})
