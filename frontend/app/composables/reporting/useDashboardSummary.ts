import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'

const DASHBOARD_CACHE_TTL_MS = 30_000
const dashboardInflightByApp = new WeakMap<object, Map<string, Promise<ApiResponse<unknown>>>>()

export function useDashboardSummary() {
  const api = useApi()
  const auth = useAuthStore()
  const nuxtApp = useNuxtApp()
  const cache = useState<Record<string, { at: number, data: unknown }>>('dashboard-summary-cache', () => ({}))
  const appInflight = dashboardInflightByApp.get(nuxtApp) || new Map<string, Promise<ApiResponse<unknown>>>()
  dashboardInflightByApp.set(nuxtApp, appInflight)

  function identityKey() {
    const user = auth.user
    const permissions = Array.isArray(user?.permissions) ? [...user.permissions].sort().join('|') : ''
    return `${user?.id || user?.email || 'anonymous'}:${permissions}`
  }

  function fetchDashboardSummary<T = unknown>(force = false): Promise<ApiResponse<T>> {
    const key = identityKey()
    const cached = cache.value[key]
    if (!force && cached && Date.now() - cached.at < DASHBOARD_CACHE_TTL_MS) {
      return Promise.resolve({ data: cached.data as T })
    }
    const existing = appInflight.get(key)
    if (existing) return existing as Promise<ApiResponse<T>>

    const request = api.get<ApiResponse<T>>(ApiEndpoints.DASHBOARD_SUMMARY, {
      requestKey: `dashboard-summary:${key}`,
      cancelPrevious: false,
    }).then((response) => {
      cache.value = { ...cache.value, [key]: { at: Date.now(), data: response.data } }
      return response
    }).finally(() => {
      if (appInflight.get(key) === request) appInflight.delete(key)
    })
    appInflight.set(key, request as Promise<ApiResponse<unknown>>)
    return request
  }

  return { fetchDashboardSummary }
}
