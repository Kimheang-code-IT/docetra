/**
 * Permission catalog for display gating. Server catalog
 * (GET /api/v2/users/permission-catalog) merges over the static matrix
 * fallback; `AuthUser.permissions` stays authoritative when present and the
 * backend always enforces — this only powers pickers/hints.
 */
import { usePermissionCatalogRepository } from '~/repositories'
import { ROLE_DOCUMENT_TYPES } from '~/utils/role/permissions'

const catalogState = useState<string[] | null>('permission-catalog', () => null)
let inflight: Promise<void> | null = null

async function loadCatalog(): Promise<void> {
  if (!import.meta.client) return
  if (catalogState.value) return
  if (inflight) return inflight

  inflight = (async () => {
    try {
      const response = await usePermissionCatalogRepository().list()
      const keys = Array.isArray(response.data) ? response.data : []
      if (keys.length) catalogState.value = keys
    }
    catch {
      // Static fallback remains.
    }
    finally {
      inflight = null
    }
  })()
  return inflight
}

/** Static fallback keys derived from the role-permission matrix catalog. */
export function staticPermissionCatalog(): string[] {
  const actionsByPrefix = ROLE_DOCUMENT_TYPES.flatMap(definition =>
    definition.actions.map(action => `${definition.permissionPrefix}.${action}`),
  )
  return [...new Set(actionsByPrefix)].sort()
}

export function usePermissionCatalog() {
  if (import.meta.client && !catalogState.value && !inflight) {
    void loadCatalog()
  }

  /** Server catalog when loaded, else the static matrix-derived fallback. */
  const permissions = computed<string[]>(() => catalogState.value || staticPermissionCatalog())

  return {
    permissions,
    ready: computed(() => catalogState.value != null),
    refresh: loadCatalog,
  }
}
