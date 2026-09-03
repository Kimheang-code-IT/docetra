import type { ApiResponse } from '~/types/docetra/common'

/**
 * Canonical audit DTO (backend contract) + centralized UI mapping.
 *
 * Every log view (record activity, portal logs, system logs) derives its
 * display fields from this single mapper instead of guessing backend fields
 * per page.
 */

/** Canonical audit row returned by the backend audit endpoints. */
export interface CanonicalAuditRow {
  id: string
  summary?: string | null
  action?: string | null
  entityType?: string | null
  occurredAt?: string | null
  status?: string | null
  detail?: Record<string, unknown> | null
  actor?: { id?: string, name?: string } | null
  target?: string | null
  message?: string | null
  statusCode?: string | null
  sourceLog?: string | null
  ipAddress?: string | null
  createdAt?: string | null
  version?: number
  [key: string]: unknown
}

export type AuditLevel = 'info' | 'warn' | 'error'

/** Derive a display level from the canonical status. */
export function auditLevel(row: CanonicalAuditRow): AuditLevel {
  const status = String(row.status || row.statusCode || '').toLowerCase()
  if (status.includes('error') || status.includes('fail')) return 'error'
  if (status.includes('warn') || status.includes('retry')) return 'warn'
  return 'info'
}

/** Record activity feed shape (activity timeline on document pages). */
export function auditToActivityView(row: CanonicalAuditRow) {
  return {
    id: String(row.id),
    entityType: String(row.entityType || ''),
    entityId: String(row.target || row.id),
    action: String(row.action || ''),
    actor: row.actor || undefined,
    summary: String(row.summary || row.message || row.action || ''),
    occurredAt: String(row.occurredAt || row.createdAt || ''),
    metadata: (row.detail as Record<string, unknown> | undefined) || undefined,
  }
}

/** Portal log table shape. */
export function auditToPortalView(row: CanonicalAuditRow) {
  return {
    ...row,
    id: String(row.id),
    action: String(row.action || ''),
    actor: row.actor || undefined,
    'actor.name': row.actor?.name,
    target: String(row.target || row.entityType || ''),
    summary: String(row.summary || row.message || ''),
    occurredAt: String(row.occurredAt || row.createdAt || ''),
  }
}

/** System log table shape (derived centrally from the canonical DTO). */
export function auditToSystemView(row: CanonicalAuditRow, index: number) {
  return {
    ...row,
    id: String(row.id),
    rowNumber: index + 1,
    level: auditLevel(row),
    source: String(row.sourceLog || ''),
    actionCode: String(row.action || ''),
    tableName: String(row.entityType || ''),
    statusCode: row.statusCode,
    sourceLog: String(row.sourceLog || ''),
    ipAddress: String(row.ipAddress || ''),
    message: String(row.summary || row.message || ''),
    occurredAt: String(row.occurredAt || row.createdAt || ''),
    createdAt: String(row.occurredAt || row.createdAt || ''),
    actor: row.actor || undefined,
    'createdBy.name': row.actor?.name,
  }
}

type ListResponse<T> = ApiResponse<T[]>

/** Normalize an audit list response through the canonical mapping. */
export function mapAuditList<T>(
  response: ListResponse<CanonicalAuditRow>,
  view: (row: CanonicalAuditRow, index: number) => T,
): ListResponse<T> {
  const data = (response.data || []).map((row, index) => view(row, index))
  return { ...response, data } as ListResponse<T>
}
