import { ref, computed } from 'vue'
import type { SortingState, PaginationState, ColumnFiltersState } from '@tanstack/vue-table'
import type { TableQueryParams } from '~/types/api'
import { useDebounce } from '@vueuse/core'
import { buildSortParam, normalizeColumnFilters } from '~/utils/api/query'
import { PAGINATION_DEFAULTS, clampPageSize, normalizePage } from '~/utils/api/pagination'
import { useGlobalFilter } from '~/composables/useGlobalFilter'

export interface TableQueryOptions {
  initialSorting?: SortingState
  initialPageSize?: number
  initialGlobalFilter?: string
  debounceMs?: number
  /** When false, omit shared global date range from API params (default true). */
  includeGlobalDateRange?: boolean
}

/**
 * Page-local table query state. Merges shared global date range into apiParams
 * so server fetches stay in sync with the header datepicker.
 */
export function useTableQuery(options: TableQueryOptions = {}) {
  const includeGlobalDateRange = options.includeGlobalDateRange !== false
  const { formattedRange } = useGlobalFilter()

  const sorting = ref<SortingState>(options.initialSorting || [])
  const globalFilter = ref(options.initialGlobalFilter || '')
  const debouncedGlobalFilter = useDebounce(globalFilter, options.debounceMs ?? 250)
  const columnFilters = ref<ColumnFiltersState>([])

  const pagination = ref<PaginationState>({
    pageIndex: PAGINATION_DEFAULTS.page - 1,
    pageSize: clampPageSize(options.initialPageSize ?? PAGINATION_DEFAULTS.pageSize),
  })

  const queryState = computed(() => ({
    sorting: sorting.value,
    globalFilter: globalFilter.value,
    columnFilters: columnFilters.value,
    pageIndex: pagination.value.pageIndex,
    pageSize: pagination.value.pageSize,
    startDate: includeGlobalDateRange ? formattedRange.value.start : '',
    endDate: includeGlobalDateRange ? formattedRange.value.end : '',
  }))

  const apiParams = computed<TableQueryParams>(() => {
    const params: TableQueryParams = {
      q: debouncedGlobalFilter.value || undefined,
      page: normalizePage(pagination.value.pageIndex + 1),
      limit: clampPageSize(pagination.value.pageSize),
      sort: buildSortParam(sorting.value),
      filters: normalizeColumnFilters(columnFilters.value),
    }

    if (includeGlobalDateRange) {
      if (formattedRange.value.start) params.startDate = formattedRange.value.start
      if (formattedRange.value.end) params.endDate = formattedRange.value.end
    }

    return params
  })

  function resetQueryState() {
    globalFilter.value = ''
    columnFilters.value = []
    pagination.value.pageIndex = 0
    if (options.initialSorting) {
      sorting.value = [...options.initialSorting]
    }
  }

  return {
    sorting,
    globalFilter,
    debouncedGlobalFilter,
    columnFilters,
    pagination,
    queryState,
    apiParams,
    resetQueryState,
  }
}
