export const PAGE_SIZE_OPTIONS = [25, 50, 100] as const
export const PAGE_SIZE_ALL = 'All' as const

export const PAGE_SIZE_SELECT_ITEMS = [...PAGE_SIZE_OPTIONS, PAGE_SIZE_ALL] as const

export const PAGINATION_DEFAULTS = {
  page: 1,
  pageSize: PAGE_SIZE_OPTIONS[0],
  maxPageSize: 10_000,
} as const

export function clampPageSize(size: number, maxPageSize: number = PAGINATION_DEFAULTS.maxPageSize): number {
  if (!Number.isFinite(size)) return PAGINATION_DEFAULTS.pageSize
  return Math.min(Math.max(Math.trunc(size), 1), maxPageSize)
}

export function normalizePage(page: number): number {
  if (!Number.isFinite(page)) return PAGINATION_DEFAULTS.page
  return Math.max(Math.trunc(page), PAGINATION_DEFAULTS.page)
}

export function createDefaultPaginationState() {
  return {
    pageIndex: PAGINATION_DEFAULTS.page - 1,
    pageSize: PAGINATION_DEFAULTS.pageSize,
  }
}

export function isAllPageSize(pageSize: number, total: number): boolean {
  return total > 0 && pageSize >= total
}

export function resolvePageSizeSelection(value: number | string, total: number): number {
  if (value === PAGE_SIZE_ALL) return Math.max(total, 1)
  return clampPageSize(Number(value))
}
