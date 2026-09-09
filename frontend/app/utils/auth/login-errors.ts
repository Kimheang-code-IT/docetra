/**
 * Classifies login-submit failures into user-meaningful buckets so the login
 * page can show a sentence instead of a raw `[POST] /api/v2/auth/login: 401`.
 *
 * Buckets:
 * - invalid-credentials: wrong email/password (401)
 * - rate-limited: too many attempts (429), with optional Retry-After seconds
 * - unreachable: network failure / API down (no HTTP status at all)
 * - backend: API returned another error and may carry its own message
 */
export type LoginErrorKind = 'invalid-credentials' | 'rate-limited' | 'unreachable' | 'backend'

export type ClassifiedLoginError = {
  kind: LoginErrorKind
  /** `Retry-After` response header value in seconds, when the API sent one. */
  retryAfterSeconds?: number
  /** Error message returned by the API, when present. */
  backendMessage?: string
}

type ApiFetchErrorShape = {
  status?: number
  statusCode?: number
  data?: { message?: unknown }
  message?: unknown
  response?: {
    status?: number
    headers?: Headers | Record<string, string>
  }
}

function extractStatus(error: ApiFetchErrorShape): number | undefined {
  return error?.status ?? error?.statusCode ?? error?.response?.status
}

function extractRetryAfter(error: ApiFetchErrorShape): number | undefined {
  const headers = error?.response?.headers
  if (!headers) return undefined
  let raw: string | null | undefined
  if (typeof (headers as Headers).get === 'function') {
    raw = (headers as Headers).get('retry-after')
  }
  else {
    const record = headers as Record<string, string>
    raw = record['retry-after'] ?? record['Retry-After']
  }
  if (!raw) return undefined
  const seconds = Number(raw)
  return Number.isFinite(seconds) && seconds >= 0 ? seconds : undefined
}

function extractBackendMessage(error: ApiFetchErrorShape): string | undefined {
  const fromData = error?.data?.message
  if (typeof fromData === 'string' && fromData.trim()) return fromData
  const fromMessage = error?.message
  // ofetch's own message ("[POST] …: 401 Unauthorized") is raw HTTP noise,
  // not a human sentence — never surface it.
  if (typeof fromMessage === 'string' && !/\[\s*(GET|POST|PUT|PATCH|DELETE)\s*\]/i.test(fromMessage)) {
    return fromMessage
  }
  return undefined
}

export function classifyLoginError(error: unknown): ClassifiedLoginError {
  const apiError = (error || {}) as ApiFetchErrorShape
  const status = extractStatus(apiError)
  const backendMessage = extractBackendMessage(apiError)

  if (status === 401) return { kind: 'invalid-credentials' }
  if (status === 429) {
    return { kind: 'rate-limited', retryAfterSeconds: extractRetryAfter(apiError), backendMessage }
  }
  // No HTTP status at all → the request never reached the API (DNS, refused
  // connection, offline). Timeouts via ofetch also surface without a status.
  if (status == null) return { kind: 'unreachable' }
  return { kind: 'backend', backendMessage }
}

/** Turns a `Retry-After` seconds value into whole minutes (at least 1). */
export function retryAfterMinutes(seconds?: number): number | undefined {
  if (seconds == null) return undefined
  return Math.max(1, Math.ceil(seconds / 60))
}
