import type { ApiResponse, FieldOption } from '~/types/docetra/common'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { useConfigurationRepositories } from '~/repositories'

const OPTIONS_CACHE_TTL_MS = 60_000
const optionsCache = new Map<string, {
  at: number
  data: FieldOption[]
  inflight?: Promise<FieldOption[]>
}>()

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

function endpointParams(endpoint: string) {
  const query = endpoint.includes('?') ? endpoint.slice(endpoint.indexOf('?') + 1) : ''
  return new URLSearchParams(query)
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

function mapDepartmentHierarchy<T extends { id: string, name: string, parentId?: string | null }>(
  rows: T[],
  valueField: 'id' | 'name',
  excludeId?: string,
): FieldOption[] {
  const byParent = new Map<string, T[]>()
  const excluded = new Set<string>()

  if (excludeId) {
    const markExcluded = (id: string) => {
      if (excluded.has(id)) return
      excluded.add(id)
      for (const row of rows) {
        if (row.parentId === id) markExcluded(row.id)
      }
    }
    markExcluded(excludeId)
  }

  const eligible = rows.filter(row => !excluded.has(row.id))
  const eligibleIds = new Set(eligible.map(row => row.id))
  for (const row of eligible) {
    const parentKey = row.parentId && eligibleIds.has(row.parentId) ? row.parentId : ''
    const siblings = byParent.get(parentKey) || []
    siblings.push(row)
    byParent.set(parentKey, siblings)
  }
  for (const siblings of byParent.values()) {
    siblings.sort((a, b) => a.name.localeCompare(b.name))
  }

  const options: FieldOption[] = []
  const visited = new Set<string>()
  const append = (parentId: string, depth: number) => {
    for (const row of byParent.get(parentId) || []) {
      if (visited.has(row.id)) continue
      visited.add(row.id)
      options.push({
        label: `${'- '.repeat(depth)}${row.name}`,
        value: valueField === 'name' ? row.name : row.id,
        meta: { name: row.name, depth, parentId: row.parentId || null },
      })
      append(row.id, depth + 1)
    }
  }
  append('', 0)
  return options
}

export async function loadReferenceOptions(endpoint: string, search = '') {
  const cacheKey = `${endpoint}::${search}`
  // Deduplicate concurrent/identical option loads (forms often share companies).
  if (!search) {
    const cached = optionsCache.get(cacheKey)
    if (cached?.inflight) return cached.inflight
    if (cached && Date.now() - cached.at < OPTIONS_CACHE_TTL_MS) return cached.data
  }

  const inflight = loadReferenceOptionsUncached(endpoint, search)
  if (!search) {
    optionsCache.set(cacheKey, { at: 0, data: [], inflight })
  }

  try {
    const data = await inflight
    if (!search) {
      optionsCache.set(cacheKey, { at: Date.now(), data })
    }
    return data
  }
  catch (error) {
    if (!search) optionsCache.delete(cacheKey)
    throw error
  }
}

async function loadReferenceOptionsUncached(endpoint: string, search = ''): Promise<FieldOption[]> {
  const path = endpointPath(endpoint)
  const params = endpointParams(endpoint)
  const valueField = optionsValueField(endpoint)
  const useMock = useRuntimeConfig().public.useMockData !== false

  if (useMock && path === `${ApiEndpoints.RECORD_TYPES}/options`) {
    const response = await useConfigurationRepositories().recordTypes.list({ q: search || undefined, page: 1, limit: 50, status: 'active' })
    return mapNamedOptions(response.data, valueField)
  }

  if (useMock && path === `${ApiEndpoints.DEPARTMENTS}/options`) {
    const { mockDepartments } = await import('~/mocks/datasets')
    const rows = mockDepartments.filter(department => department.isActive !== false)
    if (params.get('hierarchy') === 'true') {
      return mapDepartmentHierarchy(rows, valueField, params.get('excludeId') || undefined)
    }
    return mapNamedOptions(rows, valueField)
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
    query: {
      q: search || undefined,
      limit: 50,
      status: 'active',
      valueField,
      hierarchy: params.get('hierarchy') || undefined,
      excludeId: params.get('excludeId') || undefined,
    },
    suppressErrorToast: true,
    requestKey: `field-options:${endpoint}`,
    cancelPrevious: true,
  })
  return Array.isArray(response) ? response : response.data
}
