/** Pure helpers for API client error handling (unit-testable without Nuxt). */

export function shouldToastConnectionError(options: {
  fetchErrorName?: string
  handledAccessError?: boolean
  httpErrorToasted?: boolean
  status?: number | null
  suppressErrorToast?: boolean
}): boolean {
  if (options.fetchErrorName !== 'FetchError') return false
  if (options.handledAccessError) return false
  if (options.httpErrorToasted) return false
  if (options.status) return false
  if (options.suppressErrorToast) return false
  return true
}

export function shouldClearSessionOn401(options: {
  suppressAccessAlert?: boolean
}): boolean {
  return !options.suppressAccessAlert
}

export function fetchErrorStatus(error: unknown): number | undefined {
  if (!error || typeof error !== 'object') return undefined
  const err = error as {
    status?: number
    statusCode?: number
    response?: { status?: number }
  }
  const status = err.status ?? err.statusCode ?? err.response?.status
  return typeof status === 'number' && Number.isFinite(status) ? status : undefined
}

/** Refresh the session only when /auth/me says it expired — not on timeouts or 5xx. */
export function shouldRefreshSessionOnAuthMeFailure(status?: number): boolean {
  return status === 401
}
