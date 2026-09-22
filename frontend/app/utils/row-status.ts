/**
 * Row activation state from either a lifecycle `status` string (roles, users,
 * records, ...) or an `isActive` boolean (organizations, purposes, ...).
 * Deactivate first, then delete — the table only offers Delete for inactive rows.
 */
export function rowActivity(
  row: Record<string, unknown> | null | undefined,
): 'active' | 'inactive' | null {
  const status = row?.status
  if (typeof status === 'string' && status !== '') {
    return status === 'active' ? 'active' : 'inactive'
  }
  if (typeof row?.isActive === 'boolean') return row.isActive ? 'active' : 'inactive'
  return null
}

export function isRowInactive(row: Record<string, unknown> | null | undefined): boolean {
  return rowActivity(row) === 'inactive'
}

export function isRowActive(row: Record<string, unknown> | null | undefined): boolean {
  return rowActivity(row) === 'active'
}
