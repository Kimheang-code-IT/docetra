/**
 * Permission catalog for display gating. The backend structured
 * permission-row catalog (GET /api/v2/users/permission-catalog) is the
 * canonical contract; it merges over the static matrix fallback so
 * database-configured RecordTypes appear automatically. `AuthUser.permissions`
 * stays authoritative when present and the backend always enforces — this
 * only powers pickers/hints.
 */
import { usePermissionCatalogRepository } from '~/repositories'
import { ROLE_DOCUMENT_TYPES } from '~/utils/role/permissions'

/** One structured catalog row from GET /users/permission-catalog. */
export interface PermissionCatalogRow {
  id?: string
  documentType: string
  permissionPrefix?: string
  label?: string
  actions: string[]
  onlyIfCreator?: boolean
  level?: number
}

const rowsState = ref<PermissionCatalogRow[] | null>(null)
let inflight: Promise<void> | null = null

type PermissionCatalogRepository = ReturnType<typeof usePermissionCatalogRepository>

async function loadCatalog(repository: PermissionCatalogRepository, force = false): Promise<void> {
  if (!import.meta.client) return
  if (rowsState.value && !force) return
  if (inflight) return inflight

  inflight = (async () => {
    try {
      const response = await repository.list()
      const data = response.data as unknown
      const rows = Array.isArray(data)
        ? (data as PermissionCatalogRow[]).filter(row => row && typeof row.documentType === 'string')
        : []
      if (rows.length) rowsState.value = rows
    }
    catch {
      // Static fallback remains the bootstrapping default; not fully silent:
      console.warn('[permissions] catalog fetch failed; using static matrix fallback')
    }
    finally {
      inflight = null
    }
  })()
  return inflight
}

/** Static fallback rows derived from the role-permission matrix catalog. */
export function staticPermissionCatalogRows(): PermissionCatalogRow[] {
  return ROLE_DOCUMENT_TYPES.map(definition => ({
    documentType: definition.value,
    permissionPrefix: definition.permissionPrefix,
    actions: [...definition.actions],
    onlyIfCreator: false,
    level: 0,
  }))
}

function prefixFor(row: PermissionCatalogRow): string {
  if (row.permissionPrefix) return row.permissionPrefix
  // Legacy rows without a prefix: record types use records.*, others 1:1.
  const known = ROLE_DOCUMENT_TYPES.find(item => item.value === row.documentType)
  return known?.permissionPrefix || (row.documentType ? `records.${row.documentType}` : '')
}

/** Structured rows (server catalog when loaded, else the static fallback). */
export function usePermissionCatalogRows() {
  const repository = usePermissionCatalogRepository()
  const load = (force = false) => loadCatalog(repository, force)
  if (import.meta.client && !rowsState.value && !inflight) {
    void load()
  }
  const rows = computed<PermissionCatalogRow[]>(() => rowsState.value || staticPermissionCatalogRows())
  return {
    rows,
    fromServer: computed(() => rowsState.value != null),
    refresh: () => load(true),
  }
}

export function usePermissionCatalog() {
  const { rows, refresh } = usePermissionCatalogRows()

  /** Flattened `prefix.action` keys for display gating. */
  const permissions = computed<string[]>(() => {
    const keys = new Set<string>()
    for (const row of rows.value) {
      const prefix = prefixFor(row)
      if (!prefix) continue
      for (const action of row.actions) keys.add(`${prefix}.${action}`)
    }
    return [...keys].sort()
  })

  return {
    permissions,
    ready: computed(() => rowsState.value != null),
    refresh,
  }
}
