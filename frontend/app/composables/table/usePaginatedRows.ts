import { computed, type ComputedRef, type Ref } from 'vue'
import type { PaginationState } from '@tanstack/vue-table'
import { slicePage } from '~/utils/table/paginate-rows'

/** Paginate filtered rows in mock mode; pass through in API mode (server already paginated). */
export function usePaginatedRows<T>(
  rows: ComputedRef<T[]>,
  pagination: Ref<PaginationState>,
) {
  const { useMockData } = useApi()

  return computed(() =>
    slicePage(
      rows.value,
      pagination.value.pageIndex,
      pagination.value.pageSize,
      useMockData,
    ),
  )
}

/** Total displayed by the paginator: filtered total in mock mode, backend total in API mode. */
export function useDisplayRowTotal<T>(
  rows: ComputedRef<T[]>,
  serverTotal: Ref<number>,
) {
  const { useMockData } = useApi()

  return computed(() => useMockData ? rows.value.length : serverTotal.value)
}
