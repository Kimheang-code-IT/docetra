import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import type { ApiResponse } from '~/types/docetra/common'
import { resolveRecordSurfaceByParam } from '~/utils/record/surfaces'

type RecordUiSurface = 'meeting' | 'document' | 'system' | string

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

type RecordSurfacesMap = Record<string, RecordSurfaceType[]>

const SURFACES_STORAGE_PREFIX = 'docetra:record-surfaces:v1'
const SURFACES_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000
const surfacesInflightByApp = new WeakMap<object, Promise<RecordSurfacesMap>>()

function isSurfaceMap(value: unknown): value is RecordSurfacesMap {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  return Object.values(value as Record<string, unknown>).every(group => Array.isArray(group))
}

/** Boot catalog: active record types grouped by uiSurface for menus and dynamic routes. */
export function useRecordSurfaces() {
  // Capture the API client while setup context is alive: load() is called
  // delayed (await, onMounted, menu boot) and must not instantiate useApi()
  // after the Nuxt instance is no longer current (Nuxt E1001 otherwise).
  const api = useApi()
  const nuxtApp = useNuxtApp()
  const auth = useAuthStore()
  const surfaces = useState<RecordSurfacesMap | null>('record-surfaces', () => null)
  const loading = useState('record-surfaces-loading', () => false)
  const error = useState<string | null>('record-surfaces-error', () => null)
  const hydrated = useState('record-surfaces-hydrated', () => false)
  const validated = useState('record-surfaces-validated', () => false)
  const hydratedForIdentity = useState<string | null>('record-surfaces-identity', () => null)

  function identity() {
    return String(auth.user?.id || auth.user?.email || 'anonymous')
  }

  function storageKey() {
    return `${SURFACES_STORAGE_PREFIX}:${encodeURIComponent(identity())}`
  }

  function hydrateStoredSurfaces() {
    if (!import.meta.client) return
    if (hydratedForIdentity.value !== identity()) {
      surfaces.value = null
      validated.value = false
      hydrated.value = false
      hydratedForIdentity.value = identity()
    }
    if (hydrated.value) return
    hydrated.value = true
    try {
      const key = storageKey()
      const raw = localStorage.getItem(key)
      if (!raw) return
      const stored = JSON.parse(raw) as { at?: number, data?: unknown }
      if (!stored.at || Date.now() - stored.at > SURFACES_MAX_AGE_MS || !isSurfaceMap(stored.data)) {
        localStorage.removeItem(key)
        return
      }
      if (!surfaces.value) surfaces.value = stored.data
    }
    catch {
      localStorage.removeItem(storageKey())
    }
  }

  function persistSurfaces(data: RecordSurfacesMap) {
    if (!import.meta.client) return
    try {
      localStorage.setItem(storageKey(), JSON.stringify({ at: Date.now(), data }))
    }
    catch {
      // Storage can be unavailable in private/restricted browser contexts.
    }
  }

  function revalidate() {
    const existing = surfacesInflightByApp.get(nuxtApp)
    if (existing) return existing

    loading.value = true
    error.value = null
    const request = (async () => {
      try {
        const res = await api.get<ApiResponse<RecordSurfacesMap>>(ApiEndpoints.RECORD_SURFACES, {
          requestKey: 'record-surfaces',
          cancelPrevious: false,
          suppressAccessAlert: true,
        })
        const fresh = isSurfaceMap(res.data) ? res.data : {}
        surfaces.value = fresh
        validated.value = true
        persistSurfaces(fresh)
        return fresh
      }
      catch (err: any) {
        error.value = err?.message || 'Failed to load record surfaces'
        if (!surfaces.value) surfaces.value = { meeting: [], document: [], system: [] }
        return surfaces.value
      }
      finally {
        loading.value = false
        surfacesInflightByApp.delete(nuxtApp)
      }
    })()
    surfacesInflightByApp.set(nuxtApp, request)
    return request
  }

  async function load(force = false) {
    hydrateStoredSurfaces()
    const current = surfaces.value
    if (!force && validated.value) return current || {}
    const request = revalidate()
    // Stale-while-revalidate: callers can resolve routes/menus from the last-known
    // safe catalog immediately while exactly one boot request refreshes it.
    if (current && !force) return current
    return request
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
