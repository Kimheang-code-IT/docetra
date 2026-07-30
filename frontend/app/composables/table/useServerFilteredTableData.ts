import { computed, type ComputedRef, type Ref } from 'vue'
import type { ColumnFiltersState } from '@tanstack/vue-table'
import type { TableQueryParams } from '~/types/api'
import { useServerTableData } from '~/composables/table/useServerTableData'

interface UseServerFilteredTableDataOptions<T> {
  endpoint: string
  apiParams: ComputedRef<TableQueryParams>
  fallbackItems: Ref<T[]>
  /** Single-field filter (legacy) */
  filterField?: string
  selectedValues?: Ref<string[]> | ComputedRef<string[]>
  /** Multi-field filters sent to the API as `filters` */
  extraFilters?: ComputedRef<ColumnFiltersState>
}

export function useServerFilteredTableData<T>(
  options: UseServerFilteredTableDataOptions<T>
) {
  const extraFilters = computed<ColumnFiltersState>(() => {
    if (options.extraFilters) return options.extraFilters.value
    const values = options.selectedValues?.value ?? []
    if (options.filterField && values.length) {
      return [{ id: options.filterField, value: values }]
    }
    return []
  })

  const serverData = useServerTableData<T>({
    endpoint: options.endpoint,
    apiParams: options.apiParams,
    fallbackItems: options.fallbackItems,
    extraFilters
  })

  return {
    entries: serverData.entries,
    totalRows: serverData.totalRows,
    summary: serverData.summary,
    apiError: serverData.apiError,
    isReloading: serverData.isRefreshing,
    retryFetch: serverData.retryFetch,
  }
}
