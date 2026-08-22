import { describe, expect, it } from 'vitest'
import { shouldClearSessionOn401, shouldToastConnectionError } from '../../app/utils/api/error-policy'
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
    expect(ApiEndpoints.AUTH_ME).toBe('/api/v2/auth/me')
    expect(ApiEndpoints.DASHBOARD_SUMMARY).toBe('/api/v2/dashboard/summary')
    expect(ApiEndpoints.DOCUMENTS).toBe('/api/v2/records/document')
  })
})
