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
