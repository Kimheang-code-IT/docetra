import { describe, expect, it } from 'vitest'
import {
  fetchErrorStatus,
  shouldClearSessionOn401,
  shouldRefreshSessionOnAuthMeFailure,
  shouldToastConnectionError,
} from '../../app/utils/api/error-policy'
import { csrfRequestHeaders, isMutatingMethod } from '../../app/utils/security/csrf'

describe('error-policy', () => {
  it('toasts connection errors only when there is no HTTP status', () => {
    expect(shouldToastConnectionError({
      fetchErrorName: 'FetchError',
      status: undefined,
    })).toBe(true)

    expect(shouldToastConnectionError({
      fetchErrorName: 'FetchError',
      status: 500,
    })).toBe(false)

    expect(shouldToastConnectionError({
      fetchErrorName: 'FetchError',
      httpErrorToasted: true,
    })).toBe(false)

    expect(shouldToastConnectionError({
      fetchErrorName: 'FetchError',
      handledAccessError: true,
    })).toBe(false)

    expect(shouldToastConnectionError({
      fetchErrorName: 'FetchError',
      suppressErrorToast: true,
    })).toBe(false)
  })

  it('clears session on 401 unless suppressAccessAlert', () => {
    expect(shouldClearSessionOn401({})).toBe(true)
    expect(shouldClearSessionOn401({ suppressAccessAlert: true })).toBe(false)
  })

  it('reads status from fetch-error shapes', () => {
    expect(fetchErrorStatus({ statusCode: 401 })).toBe(401)
    expect(fetchErrorStatus({ status: 500 })).toBe(500)
    expect(fetchErrorStatus({ response: { status: 403 } })).toBe(403)
    expect(fetchErrorStatus(new Error('offline'))).toBeUndefined()
  })

  it('refreshes the session only after /auth/me returns 401', () => {
    expect(shouldRefreshSessionOnAuthMeFailure(401)).toBe(true)
    expect(shouldRefreshSessionOnAuthMeFailure(500)).toBe(false)
    expect(shouldRefreshSessionOnAuthMeFailure(undefined)).toBe(false)
  })
})

describe('csrfRequestHeaders', () => {
  it('detects mutating methods', () => {
    expect(isMutatingMethod('POST')).toBe(true)
    expect(isMutatingMethod('get')).toBe(false)
  })

  it('returns empty headers when cookie missing (jsdom has no document cookie)', () => {
    expect(csrfRequestHeaders('POST', 'XSRF-TOKEN', 'X-CSRF-Token')).toEqual({})
  })
})

describe('ApiEndpoints constants', () => {
  it('exposes critical auth and dashboard paths', async () => {
    const { ApiEndpoints } = await import('../../app/utils/constants/api-endpoints')
    expect(ApiEndpoints.AUTH_LOGIN).toBe('/api/v2/auth/login')
    expect(ApiEndpoints.AUTH_REGISTER).toBe('/api/v2/auth/register')
    expect(ApiEndpoints.AUTH_BOOTSTRAP).toBe('/api/v2/auth/bootstrap')
    expect(ApiEndpoints.AUTH_ME).toBe('/api/v2/auth/me')
    expect(ApiEndpoints.DASHBOARD_SUMMARY).toBe('/api/v2/dashboard/summary')
    expect(ApiEndpoints.DOCUMENTS).toBe('/api/v2/records/document')
  })
})
