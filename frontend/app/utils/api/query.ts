import type { ColumnFiltersState, SortingState } from '@tanstack/vue-table'

export function buildSortParam(sorting: SortingState): string | undefined {
  if (!sorting.length) return undefined
  return sorting.map((item) => `${item.id}:${item.desc ? 'desc' : 'asc'}`).join(',')
}

export function normalizeColumnFilters(filters: ColumnFiltersState): ColumnFiltersState | undefined {
  const normalized = filters.filter((filter) => {
    const value = filter.value
    if (value === null || value === undefined) return false
    if (typeof value === 'string') return value.trim().length > 0
    if (Array.isArray(value)) return value.length > 0
    return true
  })

  return normalized.length ? normalized : undefined
}

export function compactQuery<T extends Record<string, any>>(query: T | undefined): Partial<T> | undefined {
  if (!query) return undefined

  const compacted = Object.fromEntries(
    Object.entries(query).filter(([, value]) => {
      if (value === null || value === undefined) return false
      if (typeof value === 'string') return value.trim().length > 0
      if (Array.isArray(value)) return value.length > 0
      return true
    })
  ) as Partial<T>

  return Object.keys(compacted).length ? compacted : undefined
}
