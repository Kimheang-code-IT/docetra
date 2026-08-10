import type { ApiResponse, FieldOption } from '~/types/docetra/common'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { useConfigurationRepositories } from '~/repositories'

function optionsValueField(endpoint: string): 'id' | 'name' {
  try {
    const query = endpoint.includes('?') ? endpoint.slice(endpoint.indexOf('?') + 1) : ''
    const params = new URLSearchParams(query)
    return params.get('valueField') === 'name' ? 'name' : 'id'
  }
  catch {
    return 'id'
  }
}

function endpointPath(endpoint: string) {
  return endpoint.split('?')[0] || endpoint
}

function mapNamedOptions<T extends { id: string, name: string }>(
  rows: T[],
  valueField: 'id' | 'name',
): FieldOption[] {
  return rows.map(row => ({
    label: row.name,
    value: valueField === 'name' ? row.name : row.id,
  }))
}

export async function loadReferenceOptions(endpoint: string): Promise<FieldOption[]> {
  const path = endpointPath(endpoint)
  const valueField = optionsValueField(endpoint)
  const useMock = useRuntimeConfig().public.useMockData !== false

  if (useMock && path === `${ApiEndpoints.RECORD_TYPES}/options`) {
    const response = await useConfigurationRepositories().recordTypes.list({ page: 1, limit: 100, status: 'active' })
    return mapNamedOptions(response.data, valueField)
  }

  if (useMock && path === `${ApiEndpoints.DEPARTMENTS}/options`) {
    const { mockDepartments } = await import('~/mocks/datasets')
    return mapNamedOptions(
      mockDepartments.filter(department => department.isActive !== false),
      valueField,
    )
  }

  if (useMock && path === `${ApiEndpoints.COMPANIES}/options`) {
    const { mockCompanies } = await import('~/mocks/datasets')
    return mapNamedOptions(
      mockCompanies.filter(company => company.isActive !== false),
      valueField,
    )
  }

  if (useMock && path === `${ApiEndpoints.COMPANY_SECTORS}/options`) {
    const { mockCompanySectors } = await import('~/mocks/datasets')
    return mapNamedOptions(
      mockCompanySectors.filter(sector => sector.status === 'active'),
      valueField,
    )
  }

  if (useMock && path === `${ApiEndpoints.COMPANY_PURPOSES}/options`) {
    const { mockCompanyPurposes } = await import('~/mocks/datasets')
    return mapNamedOptions(
      mockCompanyPurposes.filter(purpose => purpose.status === 'active'),
      valueField,
    )
  }

  if (useMock && path === `${ApiEndpoints.OFFICERS}/options`) {
    const { mockOfficers } = await import('~/mocks/datasets')
    return mapNamedOptions(
      mockOfficers.filter(officer => officer.isActive !== false),
      valueField,
    )
  }

  if (useMock && path === `${ApiEndpoints.ROLES}/options`) {
    const { mockRoles } = await import('~/mocks/datasets')
    return mapNamedOptions(
      mockRoles.filter(role => role.status === 'active'),
      valueField,
    )
  }

  const response = await useApi().get<ApiResponse<FieldOption[]> | FieldOption[]>(path, {
    query: { limit: 100, status: 'active', valueField },
    suppressErrorToast: true,
    requestKey: `field-options:${endpoint}`,
    cancelPrevious: true,
  })
  return Array.isArray(response) ? response : response.data
}
