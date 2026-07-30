import type { Ref } from 'vue'
import type { TableQueryParams, PaginatedResponse } from '~/types/api'
import { clampPageSize, normalizePage } from '~/utils/api/pagination'

export function useTableApi() {
  const api = useApi()

  async function fetchPage<T, S = Record<string, unknown>>(
    endpoint: string,
    params: TableQueryParams,
    fallbackItems: Ref<T[]>,
    fallbackSummary?: () => S
  ): Promise<PaginatedResponse<T, S>> {
    const safeParams: TableQueryParams = {
      ...params,
      page: normalizePage(params.page),
      limit: clampPageSize(params.limit)
    }

    if (api.useMockData) {
      return {
        items: fallbackItems.value,
        total: fallbackItems.value.length,
        page: safeParams.page,
        limit: safeParams.limit,
        summary: fallbackSummary ? fallbackSummary() : undefined
      }
    }

    return api.get<PaginatedResponse<T, S>>(endpoint, {
      query: safeParams,
      requestKey: `table:${endpoint}`,
      cancelPrevious: true,
      suppressErrorToast: true
    })
  }

  return { fetchPage }
}
