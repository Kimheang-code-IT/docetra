import type { ApiResponse, FieldOption } from '~/types/docetra/common'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { useConfigurationRepositories } from '~/repositories'

export async function loadReferenceOptions(endpoint: string): Promise<FieldOption[]> {
  if (useRuntimeConfig().public.useMockData !== false && endpoint === `${ApiEndpoints.RECORD_TYPES}/options`) {
    const response = await useConfigurationRepositories().recordTypes.list({ page: 1, limit: 100, status: 'active' })
    return response.data.map(row => ({ label: row.name, value: row.id }))
  }

  const response = await useApi().get<ApiResponse<FieldOption[]> | FieldOption[]>(endpoint, {
    query: { limit: 100, status: 'active' },
    suppressErrorToast: true,
    requestKey: `field-options:${endpoint}`,
    cancelPrevious: true,
  })
  return Array.isArray(response) ? response : response.data
}
