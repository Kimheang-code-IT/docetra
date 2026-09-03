import type { ApiResponse } from '~/types/docetra/common'

export interface PermissionCatalogRepositoryContract {
  list: () => Promise<ApiResponse<import('~/composables/config/usePermissionCatalog').PermissionCatalogRow[]>>
}
