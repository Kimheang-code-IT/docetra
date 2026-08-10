/** Shared table page-size helpers. `PAGE_SIZE_ALL` = show every matching row. */

export const TABLE_PAGE_SIZES = [10, 20, 50, 100] as const

/** Sentinel: fetch / render all matching rows (URL: `limit=all`). */
export const PAGE_SIZE_ALL = -1

/** Practical upper bound when requesting "all" from the API / mock. */
export const PAGE_SIZE_ALL_FETCH = 10_000

export function isShowAllLimit(limit: number): boolean {
  return limit === PAGE_SIZE_ALL
}

/**
 * Parse `route.query.limit` or a select value into a page size.
 * Accepts `all` / `-1` for show-all; otherwise 10 | 20 | 50 | 100.
 */
export function parsePageLimit(raw: unknown, defaultLimit = 10): number {
  if (raw === 'all' || raw === '-1') return PAGE_SIZE_ALL
  if (typeof raw === 'number' && raw === PAGE_SIZE_ALL) return PAGE_SIZE_ALL

  const n = Number(raw)
  if (!Number.isFinite(n) || n <= 0) return defaultLimit
  if (n === PAGE_SIZE_ALL) return PAGE_SIZE_ALL
  if ((TABLE_PAGE_SIZES as readonly number[]).includes(n)) return n
  if (n > 100) return PAGE_SIZE_ALL
  return Math.min(Math.max(Math.round(n), 10), 100)
}

/** Serialize for URL query — omit when equal to default. */
export function serializePageLimit(limit: number, defaultLimit = 10): string | undefined {
  if (isShowAllLimit(limit)) return 'all'
  if (limit === defaultLimit) return undefined
  return String(limit)
}

/** Limit to send to list APIs / mock pagination. */
export function fetchPageLimit(limit: number): number {
  return isShowAllLimit(limit) ? PAGE_SIZE_ALL_FETCH : limit
}

/** Items-per-page for UPagination when showing all (single page). */
export function paginationItemsPerPage(limit: number, total: number): number {
  if (isShowAllLimit(limit)) return Math.max(total, 1)
  return Math.max(limit, 1)
}
