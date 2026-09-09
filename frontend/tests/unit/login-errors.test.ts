import { describe, expect, it } from 'vitest'
import { classifyLoginError, retryAfterMinutes } from '../../app/utils/auth/login-errors'

function fetchErrorWithStatus(status: number, headers?: Record<string, string>, message?: string) {
  return Object.assign(new Error(message ?? `[POST] "/api/v2/auth/login": ${status} Unauthorized`), {
    status,
    response: { status, headers },
  })
}

describe('classifyLoginError', () => {
  it('maps 401 to invalid credentials', () => {
    expect(classifyLoginError(fetchErrorWithStatus(401)).kind).toBe('invalid-credentials')
  })

  it('maps 429 to rate limited and reads Retry-After', () => {
    const result = classifyLoginError(fetchErrorWithStatus(429, { 'Retry-After': '900' }))
    expect(result.kind).toBe('rate-limited')
    expect(result.retryAfterSeconds).toBe(900)
  })

  it('reads Retry-After from Headers instances', () => {
    const headers = new Headers({ 'retry-after': '120' })
    const result = classifyLoginError(fetchErrorWithStatus(429, headers))
    expect(result.retryAfterSeconds).toBe(120)
  })

  it('treats missing status as unreachable network failure', () => {
    expect(classifyLoginError(new TypeError('fetch failed')).kind).toBe('unreachable')
    expect(classifyLoginError(undefined).kind).toBe('unreachable')
  })

  it('maps other API errors to backend and keeps its message', () => {
    const error = Object.assign(new Error('[POST] "/api/v2/auth/login": 500'), {
      status: 500,
      data: { message: 'Internal server error' },
      response: { status: 500 },
    })
    const result = classifyLoginError(error)
    expect(result.kind).toBe('backend')
    expect(result.backendMessage).toBe('Internal server error')
  })

  it('never surfaces raw ofetch status strings as backend messages', () => {
    const result = classifyLoginError(fetchErrorWithStatus(500, undefined, '[POST] "/api/v2/auth/login": 500 Internal Server Error'))
    expect(result.backendMessage).toBeUndefined()
  })
})

describe('retryAfterMinutes', () => {
  it('rounds up to whole minutes with a floor of 1', () => {
    expect(retryAfterMinutes(900)).toBe(15)
    expect(retryAfterMinutes(61)).toBe(2)
    expect(retryAfterMinutes(30)).toBe(1)
  })

  it('returns undefined without a header', () => {
    expect(retryAfterMinutes(undefined)).toBeUndefined()
  })
})
