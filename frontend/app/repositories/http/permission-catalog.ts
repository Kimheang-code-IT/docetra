import type { PermissionCatalogRepositoryContract } from '~/repositories/contracts/permission-catalog'
import type { ApiResponse } from '~/types/docetra/common'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

export function createHttpPermissionCatalogRepository(): PermissionCatalogRepositoryContract {
  const api = useApi()
  return {
    list: () => api.get<ApiResponse<import('~/composables/config/usePermissionCatalog').PermissionCatalogRow[]>>(ApiEndpoints.PERMISSION_CATALOG, {
      requestKey: 'permission-catalog',
      cancelPrevious: false,
      suppressErrorToast: true,
      suppressAccessAlert: true,
    }),
  }
}
