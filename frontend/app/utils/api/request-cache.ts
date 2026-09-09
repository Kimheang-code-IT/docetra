export function stableRequestValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableRequestValue)
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, entry]) => entry !== undefined)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, entry]) => [key, stableRequestValue(entry)]),
    )
  }
  return value
}

/** Identical GETs share this stable key even when callers construct query objects differently. */
export function requestCacheKey(
  method: string,
  url: string,
  query?: Record<string, unknown>,
  explicitKey?: string,
) {
  if (explicitKey) return explicitKey
  const suffix = query ? `:${JSON.stringify(stableRequestValue(query))}` : ''
  return `${method}:${url}${suffix}`
}
