import { describe, expect, it } from 'vitest'
import {
  concurrencyHeaders,
  concurrencyVersion,
  versionsById,
  withConcurrencyToken,
} from '../../app/utils/api/concurrency'
import { unwrapUserPayload, userCanAccessPage } from '../../app/utils/auth/session-user'
import {
  isAuthPublicPath,
  resolveAuthRoute,
  resolvePermittedLandingPath,
} from '../../app/utils/auth/permission-routing'
import { createLoginSchema, createSetupSchema } from '../../app/utils/auth/login-schema'
import { readRememberMe, writeRememberMe } from '../../app/utils/auth/remember-me'
import { AUTH_SESSION_EVENT_KEY } from '../../app/utils/auth/session-sync'
import { permissionForAction } from '../../app/utils/role/access'
import { parsePageLimit } from '../../app/utils/pagination'
import { getByPath, setByPath } from '../../app/utils/object-path'
import { formatSummaryValue } from '../../app/utils/format/summary-value'
import { groupUserPermissions, resolveUserPermissionKeys } from '../../app/utils/auth/user-permissions'

describe('auth store helpers', () => {
  it('unwraps nested and flat session payloads', () => {
    expect(unwrapUserPayload({ email: 'a@b.c', name: 'A' })?.email).toBe('a@b.c')
    expect(unwrapUserPayload({ user: { email: 'a@b.c', name: 'A' } })?.name).toBe('A')
    expect(unwrapUserPayload({})).toBeNull()
  })

  it('checks page access from permissions first', () => {
    expect(userCanAccessPage(null, 'dashboard.view')).toBe(false)
    expect(userCanAccessPage({ name: 'A', email: 'a@b.c', pageAccess: ['ALL_PAGES'] }, 'dashboard.view')).toBe(true)
    expect(userCanAccessPage({
      name: 'A',
      email: 'a@b.c',
      permissions: ['records.documents.view'],
    }, 'dashboard.view')).toBe(false)
    expect(userCanAccessPage({
      name: 'A',
      email: 'a@b.c',
      permissions: ['records.documents.view'],
    }, 'records.documents.view')).toBe(true)
    expect(userCanAccessPage({ name: 'A', email: 'a@b.c' }, 'dashboard.view')).toBe(true)
  })
})

describe('permission routing', () => {
  it('treats auth screens as public', () => {
    expect(isAuthPublicPath('/auth/login')).toBe(true)
    expect(isAuthPublicPath('/records/documents')).toBe(false)
  })

  it('picks the first permitted landing route', () => {
    expect(resolvePermittedLandingPath(permission => permission === 'records.documents.view')).toBe('/records/documents')
    expect(resolvePermittedLandingPath(() => false)).toBeNull()
  })

  it('gates login, public pages, abort, landing, and empty-access logout', () => {
    const allow = (permission: string) => permission === 'records.documents.view'
    expect(resolveAuthRoute({
      isLoggedIn: false,
      toPath: '/records/documents',
      canAccessPage: allow,
      fromMatched: false,
      fromPath: '/',
    })).toEqual({ kind: 'redirect', path: '/auth/login' })
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/auth/login',
      canAccessPage: allow,
      fromMatched: false,
      fromPath: '/',
    })).toEqual({ kind: 'redirect', path: '/' })
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/records/documents',
      permission: 'records.documents.view',
      canAccessPage: allow,
      fromMatched: false,
      fromPath: '/',
    })).toEqual({ kind: 'allow' })
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/user-management/users',
      permission: 'users.users.view',
      canAccessPage: allow,
      fromMatched: true,
      fromPath: '/records/documents',
    })).toEqual({ kind: 'abort' })
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/user-management/users',
      permission: 'users.users.view',
      canAccessPage: allow,
      fromMatched: false,
      fromPath: '/user-management/users',
    })).toEqual({ kind: 'redirect', path: '/records/documents', replace: true })
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/user-management/users',
      permission: 'users.users.view',
      canAccessPage: () => false,
      fromMatched: false,
      fromPath: '/user-management/users',
    })).toEqual({ kind: 'deny-and-login' })
  })
})

describe('login form schema', () => {
  it('rejects invalid credentials', () => {
    const schema = createLoginSchema('email required', 'password required')
    expect(schema.safeParse({ email: 'not-an-email', password: '123456' }).success).toBe(false)
    expect(schema.safeParse({ email: 'a@b.c', password: '123' }).success).toBe(false)
    expect(schema.safeParse({ email: 'admin@example.com', password: '123456' }).success).toBe(true)
  })

  it('requires a matching password for first-admin setup', () => {
    const schema = createSetupSchema({
      emailRequired: 'email required',
      nameRequired: 'name required',
      passwordTooShort: 'too short',
      passwordMismatch: 'mismatch',
    })
    expect(schema.safeParse({
      name: 'Admin',
      email: 'admin@example.com',
      password: '1234567',
      passwordConfirmation: '1234567',
    }).success).toBe(false)
    expect(schema.safeParse({
      name: 'Admin',
      email: 'admin@example.com',
      password: '12345678',
      passwordConfirmation: '87654321',
    }).success).toBe(false)
    expect(schema.safeParse({
      name: 'Admin',
      email: 'admin@example.com',
      password: '12345678',
      passwordConfirmation: '12345678',
    }).success).toBe(true)
  })
})

describe('remember-me', () => {
  it('round-trips enabled email through localStorage', () => {
    const store = new Map<string, string>()
    const original = globalThis.localStorage
    const mock = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => { store.set(key, value) },
      removeItem: (key: string) => { store.delete(key) },
    } as Storage
    Object.defineProperty(globalThis, 'localStorage', { value: mock, configurable: true })
    Object.defineProperty(globalThis, 'window', { value: globalThis, configurable: true })

    writeRememberMe({ enabled: true, email: 'keep@example.com' })
    expect(readRememberMe()).toEqual({ enabled: true, email: 'keep@example.com' })
    writeRememberMe({ enabled: false, email: '' })
    expect(readRememberMe()).toEqual({ enabled: false, email: '' })

    if (original) Object.defineProperty(globalThis, 'localStorage', { value: original, configurable: true })
  })
})

describe('session-sync', () => {
  it('exposes a stable storage key', () => {
    expect(AUTH_SESSION_EVENT_KEY).toBe('docetra:auth:session-event')
  })
})

describe('concurrency tokens', () => {
  it('parses versions and attaches If-Match', () => {
    expect(concurrencyVersion({ version: 3 })).toBe(3)
    expect(concurrencyHeaders(7)).toEqual({ 'If-Match': '7' })
    expect(withConcurrencyToken({ title: 'x' }, 2)).toEqual({ title: 'x', version: 2 })
    expect(versionsById([{ id: 'a', version: 1 }, { id: 'b', version: 4 }], ['b'])).toEqual({ b: 4 })
  })
})

describe('forms and workspace helpers', () => {
  it('derives action permissions from view keys', () => {
    expect(permissionForAction('records.documents.view', 'delete')).toBe('records.documents.delete')
  })

  it('parses bounded page limits', () => {
    expect(parsePageLimit('20')).toBe(20)
    expect(parsePageLimit('all')).toBe(20)
    expect(parsePageLimit(500)).toBe(100)
  })

  it('reads and writes nested object paths', () => {
    const target: Record<string, unknown> = {}
    setByPath(target, 'owner.name', 'Ada')
    expect(getByPath(target, 'owner.name')).toBe('Ada')
  })
})

describe('summary card formatting', () => {
  it('formats numeric metrics used by AppSummaryCard', () => {
    expect(formatSummaryValue(12, { prefix: '$', suffix: 'k' })).toBe('$12k')
    expect(formatSummaryValue(null)).toBe('—')
    expect(formatSummaryValue('pending')).toBe('pending')
  })
})

describe('user permissions grouping', () => {
  it('resolves keys for unrestricted pageAccess', () => {
    const keys = resolveUserPermissionKeys({
      name: 'Admin',
      email: 'admin@example.com',
      pageAccess: ['ALL_PAGES'],
    })
    expect(keys.length).toBeGreaterThan(10)
    expect(groupUserPermissions(keys).some(group => group.documentType === 'document')).toBe(true)
  })
})
