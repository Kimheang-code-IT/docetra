import type { TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'
import { useDebounceFn } from '@vueuse/core'
import { useConfirm } from '~/composables/common/useConfirm'
import { parsePageLimit, serializePageLimit } from '~/utils/pagination'
import type { ExportRequest } from '~/types/docetra/export'
import { createExportJob } from '~/adapters/exports'
import { permissionForAction } from '~/utils/role/access'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

export const CONFIG_ROW_ACTIONS: RowActionItem[] = [
  { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
  { key: 'duplicate', labelKey: 'docetra.rowActions.duplicate', icon: 'i-lucide-copy' },
  {
    key: 'toggleActive',
    labelKey: 'docetra.rowActions.deactivate',
    icon: 'i-lucide-power-off',
    color: 'warning',
    hidden: row => String(row.status) !== 'active',
  },
  {
    key: 'toggleActive',
    labelKey: 'docetra.rowActions.activate',
    icon: 'i-lucide-power',
    color: 'success',
    hidden: row => String(row.status) === 'active',
  },
  { key: 'delete', labelKey: 'docetra.rowActions.delete', icon: 'i-lucide-trash-2', color: 'error' },
]

export function useConfigListPage(options: {
  titleKey: string
  descriptionKey: string
  icon: string
  routeBase: string
  viewPermission: string
  exportResource: string
  columns: TableColumnDef[]
  load: (query: Record<string, unknown>) => Promise<{ data: Record<string, unknown>[], total: number }>
  remove?: (id: string) => Promise<void>
  removeMany?: (ids: string[]) => Promise<void>
  duplicate?: (id: string) => Promise<unknown>
  setActive?: (id: string, active: boolean) => Promise<unknown>
  cellValue?: (row: Record<string, unknown>, key: string) => string
}) {
  const { formatDate, formatDateTime } = useAppLocalization()
  const { t } = useI18n()
  const toast = useToast()
  const router = useRouter()
  const route = useRoute()
  const { confirm, setLoading } = useConfirm()
  const auth = useAuthStore()

  const canCreate = computed(() => auth.canAccessPage(permissionForAction(options.viewPermission, 'create')))
  const canDelete = computed(() => auth.canAccessPage(permissionForAction(options.viewPermission, 'delete')))
  const canExport = computed(() => auth.canAccessPage(permissionForAction(options.viewPermission, 'export')))
  const canConfigure = computed(() => auth.canAccessPage(permissionForAction(options.viewPermission, 'configure')))

  const q = ref(String(route.query.q || ''))
  const page = ref(Math.max(1, Number(route.query.page || 1)))
  const limit = ref(parsePageLimit(route.query.limit, 20))
  const sort = ref(String(route.query.sort || '-updatedAt'))
  const filters = ref<Record<string, string>>(Object.fromEntries(
    Object.entries(route.query)
      .filter(([key, value]) => !['q', 'page', 'limit', 'sort'].includes(key) && typeof value === 'string' && value)
      .map(([key, value]) => [key, String(value)]),
  ))
  const items = ref<Record<string, unknown>[]>([])
  const total = ref(0)
  const pending = ref(false)
  const error = ref<string | null>(null)
  const selectedIds = ref<string[]>([])
  const deleting = ref(false)
  const exporting = ref(false)
  let requestToken = 0

  function syncRoute() {
    void router.replace({
      query: {
        ...filters.value,
        q: q.value || undefined,
        page: page.value > 1 ? String(page.value) : undefined,
        limit: serializePageLimit(limit.value, 20),
        sort: sort.value === '-updatedAt' ? undefined : sort.value,
      },
    })
  }

  async function refresh() {
    const token = ++requestToken
    pending.value = true
    error.value = null
    try {
      const result = await options.load({
        q: q.value || undefined,
        page: page.value,
        limit: limit.value,
        sort: sort.value,
        ...filters.value,
      })
      if (token !== requestToken) return
      items.value = result.data
      total.value = result.total
    }
    catch (e: any) {
      if (token !== requestToken) return
      error.value = e?.message || t('docetra.common.loadFailed')
      items.value = []
      total.value = 0
    }
    finally {
      if (token === requestToken) pending.value = false
    }
  }

  const debouncedSearch = useDebounceFn((value: string) => {
    q.value = value
    page.value = 1
    syncRoute()
    void refresh()
  }, 300)

  function setFilter(key: string, value: string | string[] | undefined) {
    const nextValue = Array.isArray(value)
      ? (value.length ? value.join(',') : undefined)
      : (value || undefined)

    if (!nextValue) {
      const next = { ...filters.value }
      delete next[key]
      filters.value = next
    }
    else {
      filters.value = { ...filters.value, [key]: nextValue }
    }
    page.value = 1
    syncRoute()
    void refresh()
  }

  function clearFilters() {
    filters.value = {}
    page.value = 1
    syncRoute()
    void refresh()
  }

  function openCreate() {
    if (!canCreate.value) return
    void router.push(`${options.routeBase}/new`)
  }

  function openRow(row: Record<string, unknown>) {
    void router.push(`${options.routeBase}/${row.id}`)
  }

  function defaultCellValue(row: Record<string, unknown>, key: string) {
    if (options.cellValue) return options.cellValue(row, key)
    const value = row[key]
    if (value == null) return '—'
    if (typeof value === 'boolean') return value ? t('docetra.common.yes') : t('docetra.common.no')
    if (key.endsWith('At') || key.includes('Date'))
      return String(value).includes('T') ? formatDateTime(value) : formatDate(value)
    return String(value)
  }

  async function requestDelete(ids: string[]) {
    if (!canDelete.value || !options.remove || !ids.length) return
    const ok = await confirm({ kind: 'delete', count: ids.length })
    if (!ok) return

    deleting.value = true
    setLoading(true)
    try {
      if (options.removeMany) await options.removeMany(ids)
      else await Promise.all(ids.map(id => options.remove!(id)))
      toast.add({ title: t('docetra.actions.deletedItems', { n: ids.length }), color: 'success' })
      selectedIds.value = []
      await refresh()
    }
    catch (e: any) {
      toast.add({ title: e?.message || t('docetra.actions.deleteFailed'), color: 'error' })
    }
    finally {
      deleting.value = false
      setLoading(false)
    }
  }

  async function exportData(request: ExportRequest, ids: string[] = selectedIds.value) {
    if (!canExport.value) return
    exporting.value = true
    try {
      return await createExportJob({
        ...request,
        resource: options.exportResource,
        format: 'csv',
        query: { q: q.value || undefined, sort: sort.value, ...filters.value },
        selectedIds: request.scope === 'selected' ? ids : undefined,
      })
    }
    finally { exporting.value = false }
  }

  async function onRowAction(payload: { key: string, row: Record<string, unknown> }) {
    const id = String(payload.row.id || '')
    if (!id) return

    if (payload.key === 'detail' || payload.key === 'edit') {
      openRow(payload.row)
      return
    }
    if (payload.key === 'duplicate' && options.duplicate) {
      if (!canCreate.value) return
      try {
        const created = await options.duplicate(id) as unknown as { id?: string }
        toast.add({ title: t('docetra.common.duplicated'), color: 'success' })
        if (created?.id) void router.push(`${options.routeBase}/${created.id}`)
        else await refresh()
      }
      catch (e: any) {
        toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
      }
      return
    }
    if (payload.key === 'toggleActive' && options.setActive) {
      if (!canConfigure.value) return
      const active = String(payload.row.status) !== 'active'
      try {
        await options.setActive(id, active)
        toast.add({
          title: active ? t('docetra.common.activated') : t('docetra.common.deactivated'),
          color: 'success',
        })
        await refresh()
      }
      catch (e: any) {
        toast.add({ title: e?.message || t('docetra.common.actionFailed'), color: 'error' })
      }
      return
    }
    if (payload.key === 'delete') {
      if (!canDelete.value) return
      requestDelete([id])
    }
  }

  watch([page, limit, sort], () => {
    syncRoute()
    void refresh()
  })

  onMounted(() => void refresh())

  return reactive({
    titleKey: options.titleKey,
    descriptionKey: options.descriptionKey,
    icon: options.icon,
    columns: options.columns,
    rowActions: computed(() => CONFIG_ROW_ACTIONS.filter((action) => {
      if (action.key === 'duplicate') return canCreate.value
      if (action.key === 'toggleActive') return canConfigure.value
      if (action.key === 'delete') return canDelete.value
      return true
    })),
    canCreate,
    canDelete,
    canExport,
    canConfigure,
    q,
    page,
    limit,
    sort,
    filters,
    items,
    total,
    pending,
    error,
    selectedIds,
    deleting,
    exporting,
    refresh,
    debouncedSearch,
    setFilter,
    clearFilters,
    openCreate,
    openRow,
    defaultCellValue,
    requestDelete,
    onRowAction,
    exportData,
  })
}
