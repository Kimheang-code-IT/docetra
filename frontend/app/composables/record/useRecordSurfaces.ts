import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'
import { resolveRecordSurfaceByParam } from '~/utils/record/surfaces'

export type RecordUiSurface = 'meeting' | 'document' | 'system' | string

export interface RecordSurfaceType {
  id: string
  code: string
  name: string
  description?: string | null
  uiSurface: RecordUiSurface
  slug?: string
  icon?: string
  menuOrder?: number
  isCreatable?: boolean
  supportsStages?: boolean
  supportsTopicContainer?: boolean
  apiBase: string
  routeBase: string
}

export type RecordSurfacesMap = Record<string, RecordSurfaceType[]>

/** Boot catalog: active record types grouped by uiSurface for menus and dynamic routes. */
export function useRecordSurfaces() {
  const surfaces = useState<RecordSurfacesMap | null>('record-surfaces', () => null)
  const loading = useState('record-surfaces-loading', () => false)
  const error = useState<string | null>('record-surfaces-error', () => null)

  async function load(force = false) {
    if (surfaces.value && !force) return surfaces.value
    loading.value = true
    error.value = null
    try {
      const res = await useApi().get<ApiResponse<RecordSurfacesMap>>(ApiEndpoints.RECORD_SURFACES, {
        requestKey: 'record-surfaces',
        cancelPrevious: true,
        suppressAccessAlert: true,
      })
      surfaces.value = (res.data || {}) as RecordSurfacesMap
      return surfaces.value
    }
    catch (err: any) {
      error.value = err?.message || 'Failed to load record surfaces'
      if (!surfaces.value) {
        surfaces.value = { meeting: [], document: [], system: [] }
      }
      return surfaces.value
    }
    finally {
      loading.value = false
    }
  }

  const meetingTypes = computed(() => surfaces.value?.meeting || [])
  const documentTypes = computed(() => surfaces.value?.document || [])

  function resolveByParam(surface: 'meeting' | 'document', param: string): RecordSurfaceType | null {
    const list = surface === 'meeting' ? meetingTypes.value : documentTypes.value
    return resolveRecordSurfaceByParam(list, param)
  }

  return {
    surfaces,
    loading,
    error,
    load,
    meetingTypes,
    documentTypes,
    resolveByParam,
  }
}
