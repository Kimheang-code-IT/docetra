import type { TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'
import { useDebounceFn } from '@vueuse/core'

export const CONFIG_ROW_ACTIONS: RowActionItem[] = [
  { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
  { key: 'duplicate', labelKey: 'docetra.rowActions.duplicate', icon: 'i-lucide-copy' },
  { key: 'toggleActive', labelKey: 'docetra.rowActions.toggleActive', icon: 'i-lucide-power' },
  { key: 'delete', labelKey: 'docetra.rowActions.delete', icon: 'i-lucide-trash-2', color: 'error' },
]

export function useConfigListPage(options: {
  titleKey: string
  descriptionKey: string
  icon: string
  routeBase: string
  columns: TableColumnDef[]
  load: (query: Record<string, unknown>) => Promise<{ data: Record<string, unknown>[], total: number }>
  remove?: (id: string) => Promise<void>
  duplicate?: (id: string) => Promise<unknown>
  setActive?: (id: string, active: boolean) => Promise<unknown>
  cellValue?: (row: Record<string, unknown>, key: string) => string
}) {
  const { t } = useI18n()
  const toast = useToast()
  const router = useRouter()

  const q = ref('')
  const page = ref(1)
  const limit = ref(20)
  const sort = ref('-updatedAt')
  const filters = ref<Record<string, string>>({})
  const items = ref<Record<string, unknown>[]>([])
  const total = ref(0)
  const pending = ref(false)
  const error = ref<string | null>(null)
  const selectedIds = ref<string[]>([])
  const confirmOpen = ref(false)
  const pendingDeleteIds = ref<string[]>([])
  const deleting = ref(false)

  async function refresh() {
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
      items.value = result.data
      total.value = result.total
    }
    catch (e: any) {
      error.value = e?.message || t('docetra.common.loadFailed')
      items.value = []
      total.value = 0
    }
    finally {
      pending.value = false
    }
  }

  const debouncedSearch = useDebounceFn((value: string) => {
    q.value = value
    page.value = 1
    void refresh()
  }, 300)

  function setFilter(key: string, value: string) {
    if (!value) {
      const next = { ...filters.value }
      delete next[key]
      filters.value = next
    }
    else {
      filters.value = { ...filters.value, [key]: value }
    }
    page.value = 1
    void refresh()
  }

  function clearFilters() {
    filters.value = {}
    page.value = 1
    void refresh()
  }

  function openCreate() {
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
    if (key.endsWith('At') || key.includes('Date')) {
      try {
        return new Date(String(value)).toLocaleString()
      }
      catch {
        return String(value)
      }
    }
    return String(value)
  }

  function requestDelete(ids: string[]) {
    pendingDeleteIds.value = ids
    confirmOpen.value = true
  }

  async function confirmDelete() {
    if (!options.remove || !pendingDeleteIds.value.length) {
      confirmOpen.value = false
      return
    }
    deleting.value = true
    try {
      for (const id of pendingDeleteIds.value) {
        await options.remove(id)
      }
      toast.add({ title: t('docetra.actions.deletedItems', { n: pendingDeleteIds.value.length }), color: 'success' })
      selectedIds.value = []
      confirmOpen.value = false
      pendingDeleteIds.value = []
      await refresh()
    }
    catch (e: any) {
      toast.add({ title: e?.message || t('docetra.actions.deleteFailed'), color: 'error' })
    }
    finally {
      deleting.value = false
    }
  }

  async function onRowAction(payload: { key: string, row: Record<string, unknown> }) {
    const id = String(payload.row.id || '')
    if (!id) return

    if (payload.key === 'detail' || payload.key === 'edit') {
      openRow(payload.row)
      return
    }
    if (payload.key === 'duplicate' && options.duplicate) {
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
      requestDelete([id])
    }
  }

  watch([page, limit, sort], () => void refresh())

  onMounted(() => void refresh())

  return reactive({
    titleKey: options.titleKey,
    descriptionKey: options.descriptionKey,
    icon: options.icon,
    columns: options.columns,
    rowActions: CONFIG_ROW_ACTIONS,
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
    confirmOpen,
    deleting,
    refresh,
    debouncedSearch,
    setFilter,
    clearFilters,
    openCreate,
    openRow,
    defaultCellValue,
    requestDelete,
    confirmDelete,
    onRowAction,
  })
}
