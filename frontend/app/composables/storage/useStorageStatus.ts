import type { ApiResponse } from '~/types/docetra/common'
import type { StorageStatus } from '~/types/docetra/settings'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { unwrapApiData } from '~/repositories/http/response'

/**
 * Shared, cached storage readiness for portal pages (file upload + Drive sync).
 * Non-admin users may read it; no secret material is returned by the API.
 */
export function useStorageStatus() {
  const status = useState<StorageStatus | null>('storage-status', () => null)
  const pending = useState('storage-status-pending', () => false)
  const loaded = useState('storage-status-loaded', () => false)

  async function load(force = false) {
    if (pending.value) return
    if (loaded.value && !force) return
    pending.value = true
    try {
      const response = await useApi().get<ApiResponse<StorageStatus> | StorageStatus>(ApiEndpoints.STORAGE_STATUS, {
        requestKey: 'storage-status',
        cancelPrevious: false,
        suppressErrorToast: true,
        suppressAccessAlert: true,
      })
      status.value = unwrapApiData(response)
    }
    catch {
      status.value = null
    }
    finally {
      pending.value = false
      loaded.value = true
    }
  }

  return { status, pending, loaded, load }
}
