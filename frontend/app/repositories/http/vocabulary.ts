import type { PermissionCatalogRepositoryContract, VocabularyRepositoryContract } from '~/repositories/contracts/vocabulary'
import type { ApiResponse } from '~/types/docetra/common'
import type { VocabularyCatalog, EnumValueOption } from '~/types/docetra/vocabulary'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { unwrapApiData } from './response'

export function createHttpVocabularyRepository(): VocabularyRepositoryContract {
  const api = useApi()

  return {
    getCatalog: () => api.get<ApiResponse<{ groups: VocabularyCatalog }>>(ApiEndpoints.CONFIGURATION_ENUMS, {
      requestKey: 'configuration-enums',
      cancelPrevious: true,
      suppressErrorToast: true,
    }),
    createValue: async (group, input) => unwrapApiData(
      await api.post<EnumValueOption | ApiResponse<EnumValueOption>>(ApiEndpoints.CONFIGURATION_ENUM_GROUP(group), input),
    ),
    updateValue: async (group, code, input) => unwrapApiData(
      await api.patch<EnumValueOption | ApiResponse<EnumValueOption>>(ApiEndpoints.CONFIGURATION_ENUM_VALUE(group, code), input),
    ),
    deleteValue: async (group, code) => {
      await api.delete(ApiEndpoints.CONFIGURATION_ENUM_VALUE(group, code))
    },
  }
}

/** Static permission matrix fallback — server catalog overrides when reachable. */
export const PERMISSION_CATALOG_FALLBACK_PREFIXES = [
  'dashboard',
  'archive',
  'records.incoming_documents',
  'records.outgoing_documents',
  'records.documents',
  'records.master_list_requests',
  'records.meeting_topic',
  'records.meeting_history',
  'organizations.departments',
  'organizations.companies',
  'organizations.purposes',
  'organizations.sectors',
  'organizations.officers',
  'users.users',
  'users.roles',
  'configuration.record_types',
  'configuration.record_attributes',
  'configuration.enums',
  'records.logs',
  'portal.file_upload',
  'portal.google_drive_sync',
  'portal.logs',
  'system.logs',
  'settings.app_config',
  'settings.app_info',
  'settings.storage',
] as const

export function createHttpPermissionCatalogRepository(): PermissionCatalogRepositoryContract {
  const api = useApi()
  return {
    list: () => api.get<ApiResponse<string[]>>(ApiEndpoints.PERMISSION_CATALOG, {
      requestKey: 'permission-catalog',
      cancelPrevious: true,
      suppressErrorToast: true,
      suppressAccessAlert: true,
    }),
  }
}
