/**
 * Normalize filter / record timestamps for string comparison at minute precision.
 * Date-only values use start-of-day or end-of-day depending on the bound.
 */
export function toComparableDateTime(
  value: string | null | undefined,
  bound: 'start' | 'end' | 'value' = 'value',
): string {
  const raw = String(value || '').trim()
  if (!raw) return ''

  if (raw.includes('T')) {
    return raw.slice(0, 16)
  }

  const day = raw.slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return ''

  if (bound === 'start') return `${day}T00:00`
  if (bound === 'end') return `${day}T23:59`
  return `${day}T00:00`
}

/** Inclusive range check using minute-precision datetimes. */
export function isWithinDateTimeRange(
  value: string | null | undefined,
  start: string | null | undefined,
  end: string | null | undefined,
): boolean {
  const startBound = toComparableDateTime(start, 'start')
  const endBound = toComparableDateTime(end, 'end')
  if (!startBound && !endBound) return true

  const point = toComparableDateTime(value, 'value')
  if (!point) return false
  if (startBound && point < startBound) return false
  if (endBound && point > endBound) return false
  return true
}

/**
 * Single-picker filter: same calendar day as `filter`.
 * If `filter` includes a non-midnight time, also require value >= filter.
 */
export function matchesDateTimeDayFilter(
  value: string | null | undefined,
  filter: string | null | undefined,
): boolean {
  const bound = toComparableDateTime(filter, 'start')
  if (!bound) return true

  const point = toComparableDateTime(value, 'value')
  if (!point) return false
  if (point.slice(0, 10) !== bound.slice(0, 10)) return false

  const raw = String(filter || '').trim()
  const timePart = raw.includes('T') ? raw.slice(11, 16) : ''
  if (timePart && timePart !== '00:00' && point < bound) return false
  return true
}
