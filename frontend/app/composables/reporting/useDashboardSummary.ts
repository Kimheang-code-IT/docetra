import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'

export async function fetchDashboardSummary<T = unknown>() {
  return useApi().get<ApiResponse<T>>(ApiEndpoints.DASHBOARD_SUMMARY, {
    requestKey: 'dashboard-summary',
    cancelPrevious: true,
  })
}

export function useDashboardSummary() {
  return { fetchDashboardSummary }
}
