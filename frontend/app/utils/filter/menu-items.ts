export type MenuRow = {
  label: string
  value: string | number | boolean
  icon?: string
  disabled?: boolean
  [key: string]: unknown
}

/**
 * Normalize mixed filter option shapes into USelectMenu `{ label, value }` rows.
 */
export function normalizeToMenuRows(items: unknown[]): MenuRow[] {
  const rows: MenuRow[] = []

  for (const item of items ?? []) {
    if (item == null) continue

    if (typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean') {
      rows.push({ label: String(item), value: item })
      continue
    }

    if (typeof item !== 'object') continue

    const row = item as Record<string, unknown>
    const value = row.value ?? row.id ?? row.key
    if (value == null || (typeof value !== 'string' && typeof value !== 'number' && typeof value !== 'boolean')) {
      continue
    }

    const labelSource = row.label ?? row.name ?? row.title ?? value
    rows.push({
      ...row,
      label: String(labelSource),
      value,
      icon: typeof row.icon === 'string' ? row.icon : undefined,
      disabled: Boolean(row.disabled),
    })
  }

  return rows
}
