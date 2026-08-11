/** Shared bounded table page-size helpers for server-backed data. */

export const TABLE_PAGE_SIZES = [10, 20, 50, 100] as const

/** Legacy sentinel retained only so old bookmarked URLs can be normalized. */
export const PAGE_SIZE_ALL = -1

export function isShowAllLimit(limit: number): boolean {
  return limit === PAGE_SIZE_ALL
}

/**
 * Parse `route.query.limit` or a select value into a page size.
 * Accepts `all` / `-1` for show-all; otherwise 10 | 20 | 50 | 100.
 */
export function parsePageLimit(raw: unknown, defaultLimit = 10): number {
  if (raw === 'all' || raw === '-1') return defaultLimit
  if (typeof raw === 'number' && raw === PAGE_SIZE_ALL) return defaultLimit

  const n = Number(raw)
  if (!Number.isFinite(n) || n <= 0) return defaultLimit
  if ((TABLE_PAGE_SIZES as readonly number[]).includes(n)) return n
  if (n > 100) return 100
  return Math.min(Math.max(Math.round(n), 10), 100)
}

/** Serialize for URL query — omit when equal to default. */
export function serializePageLimit(limit: number, defaultLimit = 10): string | undefined {
  if (limit === defaultLimit) return undefined
  return String(limit)
}

/** Limit to send to list APIs / mock pagination. */
export function fetchPageLimit(limit: number): number {
  return parsePageLimit(limit)
}

/** Items-per-page for UPagination when showing all (single page). */
export function paginationItemsPerPage(limit: number, total: number): number {
  return Math.max(limit, 1)
}
