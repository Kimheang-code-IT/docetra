import type { ApiResponse, FieldOption } from '~/types/docetra/common'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { useConfigurationRepositories } from '~/repositories'

export async function loadReferenceOptions(endpoint: string): Promise<FieldOption[]> {
  if (useRuntimeConfig().public.useMockData !== false && endpoint === `${ApiEndpoints.RECORD_TYPES}/options`) {
    const response = await useConfigurationRepositories().recordTypes.list({ page: 1, limit: 100, status: 'active' })
    return response.data.map(row => ({ label: row.name, value: row.id }))
  }

  if (useRuntimeConfig().public.useMockData !== false && endpoint === `${ApiEndpoints.DEPARTMENTS}/options`) {
    const { mockDepartments } = await import('~/mocks/datasets')
    return mockDepartments
      .filter(department => department.isActive !== false)
      .map(department => ({ label: department.name, value: department.id }))
  }

  if (useRuntimeConfig().public.useMockData !== false && endpoint === `${ApiEndpoints.COMPANY_SECTORS}/options`) {
    const { mockCompanySectors } = await import('~/mocks/datasets')
    return mockCompanySectors
      .filter(sector => sector.status === 'active')
      .map(sector => ({ label: sector.name, value: sector.id }))
  }

  if (useRuntimeConfig().public.useMockData !== false && endpoint === `${ApiEndpoints.COMPANY_PURPOSES}/options`) {
    const { mockCompanyPurposes } = await import('~/mocks/datasets')
    return mockCompanyPurposes
      .filter(purpose => purpose.status === 'active')
      .map(purpose => ({ label: purpose.name, value: purpose.id }))
  }

  if (useRuntimeConfig().public.useMockData !== false && endpoint === `${ApiEndpoints.ROLES}/options`) {
    const { mockRoles } = await import('~/mocks/datasets')
    return mockRoles
      .filter(role => role.status === 'active')
      .map(role => ({ label: role.name, value: role.id }))
  }

  const response = await useApi().get<ApiResponse<FieldOption[]> | FieldOption[]>(endpoint, {
    query: { limit: 100, status: 'active' },
    suppressErrorToast: true,
    requestKey: `field-options:${endpoint}`,
    cancelPrevious: true,
  })
  return Array.isArray(response) ? response : response.data
}
