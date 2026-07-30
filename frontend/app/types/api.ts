import type { ColumnFiltersState } from '@tanstack/vue-table'

export interface TableQueryParams {
  q?: string
  page: number
  limit: number
  sort?: string
  filters?: ColumnFiltersState
  /** Inclusive range from shared `useGlobalFilter` */
  startDate?: string
  endDate?: string
}

export interface PaginatedResponse<T, S = Record<string, unknown>> {
  items: T[]
  total: number
  page: number
  limit: number
  summary?: S
}
