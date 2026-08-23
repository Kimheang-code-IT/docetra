export const AUTH_PUBLIC_PATHS = [
  '/auth/login',
  '/auth/forget-password',
  '/auth/verify-code',
  '/auth/reset-password',
  '/login',
  '/forget-password',
] as const

export const PERMITTED_LANDING_ROUTES = [
  ['/', 'dashboard.view'],
  ['/meetings/topics', 'records.meeting_topic.view'],
  ['/meetings/history', 'records.meeting_history.view'],
  ['/records/incoming-documents', 'records.incoming_documents.view'],
  ['/records/outgoing-documents', 'records.outgoing_documents.view'],
  ['/records/documents', 'records.documents.view'],
  ['/records/master-list-requests', 'records.master_list_requests.view'],
  ['/organizations/departments', 'organizations.departments.view'],
  ['/organizations/companies', 'organizations.companies.view'],
  ['/purpose', 'organizations.purposes.view'],
  ['/sector', 'organizations.sectors.view'],
  ['/officers', 'organizations.officers.view'],
  ['/portal/file-upload', 'portal.file_upload.view'],
  ['/user-management/users', 'users.users.view'],
  ['/user-management/roles', 'users.roles.view'],
] as const

export function isAuthPublicPath(path: string): boolean {
  return (AUTH_PUBLIC_PATHS as readonly string[]).includes(path)
}

export function resolvePermittedLandingPath(
  canAccess: (permission: string) => boolean,
): string | null {
  for (const [path, permission] of PERMITTED_LANDING_ROUTES) {
    if (canAccess(permission)) return path
  }
  return null
}

export type AuthRouteDecision =
  | { kind: 'allow' }
  | { kind: 'abort' }
  | { kind: 'deny-and-login' }
  | { kind: 'redirect'; path: string; replace?: boolean }

/** Pure route gate used by auth middleware (no Nuxt types). */
export function resolveAuthRoute(input: {
  isLoggedIn: boolean
  toPath: string
  permission?: string
  canAccessPage: (permission: string) => boolean
  fromMatched: boolean
  fromPath: string
}): AuthRouteDecision {
  const isPublicPage = isAuthPublicPath(input.toPath)
  if (!input.isLoggedIn && !isPublicPage) {
    return { kind: 'redirect', path: '/auth/login' }
  }
  if (input.isLoggedIn && isPublicPage) {
    return { kind: 'redirect', path: '/' }
  }
  const permission = input.permission || ''
  if (input.isLoggedIn && permission && !input.canAccessPage(permission)) {
    if (input.fromMatched && input.fromPath !== input.toPath) return { kind: 'abort' }
    const landing = resolvePermittedLandingPath(input.canAccessPage)
    if (landing) return { kind: 'redirect', path: landing, replace: true }
    return { kind: 'deny-and-login' }
  }
  return { kind: 'allow' }
}
