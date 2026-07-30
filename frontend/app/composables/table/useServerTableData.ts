import { ref, watch, computed } from 'vue'
import type { ComputedRef, Ref } from 'vue'
import type { TableQueryParams } from '~/types/api'
import { useTableApi } from '~/composables/api/useTableApi'
import { ensureMinReloadDuration } from '~/utils/reload-min-duration'

interface UseServerTableDataOptions<T, S> {
  endpoint: string
  apiParams: ComputedRef<TableQueryParams>
  fallbackItems: Ref<T[]>
  extraFilters?: ComputedRef<any[]>
}

export function useServerTableData<T, S = Record<string, unknown>>(
  options: UseServerTableDataOptions<T, S>
) {
  const { fetchPage } = useTableApi()
  const entries = ref<T[]>(options.fallbackItems.value)
  const totalRows = ref(entries.value.length)
  const summary = ref<S | null>(null)
  const apiError = ref<string | null>(null)
  const isRefreshing = ref(false)
  let fetchPromise: Promise<void> | null = null

  const mergedParams = computed<TableQueryParams>(() => ({
    ...options.apiParams.value,
    filters: [
      ...(options.apiParams.value.filters || []),
      ...(options.extraFilters?.value || [])
    ]
  }))

  async function fetchEntries(fetchOptions?: { manual?: boolean }) {
    if (fetchPromise) return fetchPromise

    const manual = fetchOptions?.manual ?? false
    const startedAt = Date.now()
    if (manual) isRefreshing.value = true

    fetchPromise = (async () => {
      try {
        apiError.value = null
        const response = await fetchPage<T, S>(
          options.endpoint,
          mergedParams.value,
          options.fallbackItems
        )
        entries.value = response.items
        totalRows.value = response.total
        summary.value = response.summary || null
      } catch (err: any) {
        if (err?.name === 'AbortError') return
        apiError.value = err?.message || 'Failed to load table data'
      } finally {
        if (manual) {
          await ensureMinReloadDuration(startedAt)
          isRefreshing.value = false
        }
        fetchPromise = null
      }
    })()

    return fetchPromise
  }

  watch(mergedParams, () => {
    fetchEntries().catch(() => undefined)
  }, { deep: true, immediate: true })

  return {
    entries,
    totalRows,
    summary,
    apiError,
    isRefreshing,
    fetchEntries,
    retryFetch: () => fetchEntries({ manual: true }),
  }
}
