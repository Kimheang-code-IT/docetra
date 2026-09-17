import { describe, expect, it } from 'vitest'
import {
  isAuthPublicPath,
  resolveAuthRoute,
  resolvePermittedLandingPath,
} from '../../app/utils/auth/permission-routing'
import { permissionForAction } from '../../app/utils/role/access'
import {
  auditLevel,
  auditToActivityView,
  auditToPortalView,
  auditToSystemView,
  mapAuditList,
} from '../../app/utils/audit/audit-dto'
import { getByPath, setByPath } from '../../app/utils/object-path'
import { formatSummaryValue } from '../../app/utils/format/summary-value'

describe('auth route gate', () => {
  const allowAll = () => true
  const denyAll = () => false

  it('classifies public auth pages', () => {
    expect(isAuthPublicPath('/auth/login')).toBe(true)
    expect(isAuthPublicPath('/auth/reset-password')).toBe(true)
    expect(isAuthPublicPath('/records/documents')).toBe(false)
  })

  it('redirects anonymous users to login from protected pages', () => {
    expect(resolveAuthRoute({
      isLoggedIn: false,
      toPath: '/records/documents',
      canAccessPage: allowAll,
      fromMatched: false,
      fromPath: '/',
    })).toEqual({ kind: 'redirect', path: '/auth/login' })
  })

  it('sends signed-in users away from public auth pages', () => {
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/auth/login',
      canAccessPage: allowAll,
      fromMatched: false,
      fromPath: '/',
    })).toEqual({ kind: 'redirect', path: '/' })
  })

  it('aborts navigation between two guarded pages when permission is missing', () => {
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/user-management/users',
      permission: 'users.users.view',
      canAccessPage: denyAll,
      fromMatched: true,
      fromPath: '/records/documents',
    })).toEqual({ kind: 'abort' })
  })

  it('redirects to the first permitted landing route when available', () => {
    const decision = resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/user-management/users',
      permission: 'users.users.view',
      canAccessPage: permission => permission === 'records.documents.view',
      fromMatched: false,
      fromPath: '/',
    })
    expect(decision).toEqual({ kind: 'redirect', path: '/records/documents', replace: true })
  })

  it('denies login when the user has no permitted landing route', () => {
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/user-management/users',
      permission: 'users.users.view',
      canAccessPage: denyAll,
      fromMatched: false,
      fromPath: '/',
    })).toEqual({ kind: 'deny-and-login' })
  })

  it('allows access when the permission is granted', () => {
    expect(resolveAuthRoute({
      isLoggedIn: true,
      toPath: '/records/documents',
      permission: 'records.documents.view',
      canAccessPage: allowAll,
      fromMatched: true,
      fromPath: '/',
    })).toEqual({ kind: 'allow' })
  })

  it('resolves landing paths in documented priority order', () => {
    expect(resolvePermittedLandingPath(permission => permission === 'dashboard.view')).toBe('/')
    expect(resolvePermittedLandingPath(permission => permission === 'organizations.officers.view')).toBe('/officers')
    expect(resolvePermittedLandingPath(denyAll)).toBeNull()
  })
})

describe('role action permissions', () => {
  it('derives action permissions from canonical view permissions', () => {
    expect(permissionForAction('records.documents.view', 'edit')).toBe('records.documents.edit')
    expect(permissionForAction('records.documents.view', 'delete')).toBe('records.documents.delete')
    expect(permissionForAction('records.documents.manage', 'edit')).toBe('records.documents.manage')
  })
})

describe('audit DTO mapping', () => {
  const row = {
    id: 'a1',
    action: 'created',
    entityType: 'documents',
    summary: 'Created a document',
    status: 'success',
    sourceLog: 'record',
    actor: { id: 'u1', name: 'Ada' },
    target: 'documents',
    occurredAt: '2026-01-02T03:04:05Z',
    detail: { correlationId: 'a1' },
  }

  it('derives display levels from status', () => {
    expect(auditLevel({ status: 'success' })).toBe('info')
    expect(auditLevel({ statusCode: 'failed' })).toBe('error')
    expect(auditLevel({ status: 'retrying' })).toBe('warn')
  })

  it('maps record activity rows', () => {
    const view = auditToActivityView(row)
    expect(view).toMatchObject({
      id: 'a1',
      action: 'created',
      entityId: 'documents',
      summary: 'Created a document',
    })
    expect(view.actor?.name).toBe('Ada')
    expect(view.metadata).toEqual({ correlationId: 'a1' })
  })

  it('maps portal and system rows with indexed numbering', () => {
    const portal = auditToPortalView(row)
    expect(portal['actor.name']).toBe('Ada')
    expect(portal.target).toBe('documents')

    const system = auditToSystemView(row, 4)
    expect(system.rowNumber).toBe(5)
    expect(system.actionCode).toBe('created')
    expect(system.tableName).toBe('documents')
    expect(system.source).toBe('record')
    expect(system['createdBy.name']).toBe('Ada')
  })

  it('normalizes audit list responses', () => {
    const mapped = mapAuditList({ data: [row] } as never, auditToActivityView)
    expect(mapped.data).toHaveLength(1)
    expect(mapped.data[0]?.id).toBe('a1')
  })
})

describe('object path helpers', () => {
  it('reads nested values safely', () => {
    expect(getByPath({ a: { b: { c: 3 } } }, 'a.b.c')).toBe(3)
    expect(getByPath({ a: 1 }, 'a.b.c')).toBeUndefined()
    expect(getByPath(null, 'a')).toBeUndefined()
    expect(getByPath({ a: 1 }, '')).toBeUndefined()
  })

  it('writes nested values and creates missing objects', () => {
    const target: Record<string, any> = {}
    setByPath(target, 'a.b.c', 5)
    expect(target).toEqual({ a: { b: { c: 5 } } })
    setByPath(target, 'a.b.d', 6)
    expect(target.a.b).toEqual({ c: 5, d: 6 })
    setByPath(target, 'flat', 'x')
    expect(target.flat).toBe('x')
  })
})

describe('summary value formatting', () => {
  it('formats numbers with prefixes, suffixes, and decimals', () => {
    expect(formatSummaryValue(12)).toBe('12')
    expect(formatSummaryValue('12.5', { decimals: 1 })).toBe('12.5')
    expect(formatSummaryValue(1000, { prefix: '$', suffix: ' USD' })).toBe('$1000 USD')
    expect(formatSummaryValue(3.14159, { decimals: 2 })).toBe('3.14')
  })

  it('falls back for non-numeric text and missing values', () => {
    expect(formatSummaryValue('draft')).toBe('draft')
    expect(typeof formatSummaryValue(null)).toBe('string')
    expect(formatSummaryValue(null)).not.toBe('')
    expect(formatSummaryValue(undefined)).not.toBe('')
  })
})
