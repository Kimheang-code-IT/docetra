type VersionedRow = { id?: unknown; version?: unknown }

export function concurrencyVersion(source: unknown): number | undefined {
  if (typeof source === 'number' && Number.isFinite(source)) return source
  if (typeof source === 'string' && source.trim() !== '') {
    const parsed = Number(source)
    return Number.isFinite(parsed) ? parsed : undefined
  }
  if (!source || typeof source !== 'object') return undefined
  return concurrencyVersion((source as VersionedRow).version)
}

export function concurrencyHeaders(version: unknown): Record<string, string> {
  const parsed = concurrencyVersion(version)
  if (parsed == null) return {}
  return { 'If-Match': String(parsed) }
}

export function withConcurrencyToken<T extends Record<string, unknown>>(
  payload: T,
  version: unknown,
): T & { version?: number } {
  const parsed = concurrencyVersion(version)
  if (parsed == null) return payload
  return { ...payload, version: parsed }
}

export function versionsById(rows: VersionedRow[], ids: string[]): Record<string, number> {
  const wanted = new Set(ids)
  const out: Record<string, number> = {}
  for (const row of rows) {
    const id = String(row.id || '')
    const version = concurrencyVersion(row)
    if (id && wanted.has(id) && version != null) out[id] = version
  }
  return out
}
