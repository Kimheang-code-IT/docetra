import type { AdapterKey } from '~/adapters'
import { useConfirm } from '~/composables/common/useConfirm'
import { getEntityAdapter, getEntityConfig } from '~/config/entities'
import type { TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'
import { TABLE_PAGE_SIZES, parsePageLimit } from '~/utils/pagination'
import { isWithinDateTimeRange } from '~/utils/date-time-range'
import { permissionForAction } from '~/utils/role/access'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

export type ArchiveRow = Record<string, unknown> & {
  id: string
  recordId: string
  sourceKey: AdapterKey
  entityType: string
  recordName: string
  status: 'archived' | 'deleted'
  archivedAt: string
}

export const ARCHIVE_SOURCE_KEYS: AdapterKey[] = [
  'meetingTopics',
  'meetingHistory',
  'incomingDocuments',
  'outgoingDocuments',
  'documents',
  'masterListRequests',
]

export const ARCHIVE_COLUMNS: TableColumnDef[] = [
  { key: 'recordName', labelKey: 'docetra.archive.record', priority: 'high' },
  { key: 'entityType', labelKey: 'docetra.archive.type', cell: 'badge' },
  { key: 'status', labelKey: 'docetra.fields.status', cell: 'badge' },
  { key: 'referenceNumber', labelKey: 'docetra.fields.referenceNumber', priority: 'medium' },
  { key: 'archivedAt', labelKey: 'docetra.archive.archivedAt', cell: 'datetime' },
  { key: 'owner.name', labelKey: 'docetra.fields.owner', cell: 'person', priority: 'low' },
]

function displayName(row: Record<string, unknown>, titleField: string) {
  return String(row[titleField] || row.title || row.name || row.fileName || row.referenceNumber || row.id)
}

export function useArchiveWorkspace(sourceKeys: AdapterKey[] = ARCHIVE_SOURCE_KEYS) {
  const { t } = useI18n()
  const { formatDateTime } = useAppLocalization()
  const auth = useAuthStore()
  const toast = useToast()
  const { confirm } = useConfirm()

  const sources = computed(() => sourceKeys
    .map(key => getEntityConfig(key))
    .filter(config => auth.canAccessPage(config.permission)))

  const sourceOptions = computed(() => [
    { label: t('docetra.archive.allTypes'), value: 'all' },
    ...sources.value.map(source => ({ label: t(source.titleKey), value: source.key })),
  ])

  function canRestoreRow(row: ArchiveRow | Record<string, unknown>) {
    const sourceKey = String(row.sourceKey || '') as AdapterKey
    if (!sourceKey) return false
    return auth.canAccessPage(permissionForAction(getEntityConfig(sourceKey).permission, 'restore'))
  }

  function canDeleteRow(row: ArchiveRow | Record<string, unknown>) {
    const sourceKey = String(row.sourceKey || '') as AdapterKey
    if (!sourceKey) return false
    return auth.canAccessPage(permissionForAction(getEntityConfig(sourceKey).permission, 'purge'))
  }

  const canDeleteAny = computed(() => sources.value.some(source =>
    auth.canAccessPage(permissionForAction(source.permission, 'purge')),
  ))

  const rowActions: RowActionItem[] = [
    {
      key: 'restore',
      labelKey: 'docetra.archive.restore',
      icon: 'i-lucide-archive-restore',
      color: 'success',
      hidden: row => !canRestoreRow(row),
    },
    { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
    {
      key: 'delete',
      labelKey: 'docetra.archive.deletePermanently',
      icon: 'i-lucide-trash-2',
      color: 'error',
      hidden: row => !canDeleteRow(row),
    },
  ]

  const allRows = ref<ArchiveRow[]>([])
  const pending = ref(false)
  const error = ref<string | null>(null)
  const search = ref('')
  const sourceFilter = ref<AdapterKey | 'all'>('all')
  const dateStart = ref('')
  const dateEnd = ref('')
  const page = ref(1)
  const limit = ref(10)

  const filteredRows = computed(() => {
    const term = search.value.trim().toLocaleLowerCase()
    return allRows.value.filter((row) => {
      if (sourceFilter.value !== 'all' && row.sourceKey !== sourceFilter.value) return false
      if (!isWithinDateTimeRange(row.archivedAt, dateStart.value, dateEnd.value)) return false
      if (!term) return true
      return [row.recordName, row.referenceNumber, row.entityType]
        .some(value => String(value || '').toLocaleLowerCase().includes(term))
    })
  })

  const visibleRows = computed(() => {
    const start = (page.value - 1) * limit.value
    return filteredRows.value.slice(start, start + limit.value)
  })

  watch([search, sourceFilter, dateStart, dateEnd], () => { page.value = 1 })
  watch(() => filteredRows.value.length, (total) => {
    const lastPage = Math.max(1, Math.ceil(total / limit.value))
    if (page.value > lastPage) page.value = lastPage
  })

  async function loadSource(sourceKey: AdapterKey) {
    const config = getEntityConfig(sourceKey)
    const adapter = getEntityAdapter<Record<string, unknown> & { id: string }>(sourceKey)
    const limit = TABLE_PAGE_SIZES.at(-1) || 100
    const [archivedResponse, deletedResponse] = await Promise.all([
      adapter.list({ status: 'archived', page: 1, limit, sort: '-updatedAt' }),
      adapter.list({ status: 'deleted', page: 1, limit, sort: '-updatedAt' }),
    ])
    return [...(archivedResponse.data || []), ...(deletedResponse.data || [])].map((row): ArchiveRow => ({
      ...row,
      id: `${sourceKey}:${row.id}`,
      recordId: String(row.id),
      sourceKey,
      entityType: t(config.titleKey),
      recordName: displayName(row, config.titleField),
      status: String(row.status) === 'deleted' ? 'deleted' : 'archived',
      archivedAt: String(row.deletedAt || row.archivedAt || row.updatedAt || row.createdAt || ''),
    }))
  }

  async function refresh() {
    pending.value = true
    error.value = null
    try {
      const result = await Promise.all(sources.value.map(source => loadSource(source.key)))
      allRows.value = result.flat().sort((a, b) => b.archivedAt.localeCompare(a.archivedAt))
    }
    catch (cause: any) {
      error.value = cause?.message || t('docetra.archive.loadFailed')
    }
    finally {
      pending.value = false
    }
  }

  function sourceFor(row: ArchiveRow) {
    return getEntityConfig(row.sourceKey)
  }

  function openRow(row: ArchiveRow) {
    navigateTo(`${sourceFor(row).routeBase}/${encodeURIComponent(row.recordId)}`)
  }

  async function restoreRow(row: ArchiveRow) {
    if (!canRestoreRow(row)) return
    const accepted = await confirm({
      kind: 'update',
      titleKey: 'docetra.archive.restoreTitle',
      descriptionKey: 'docetra.archive.restoreDescription',
      confirmLabelKey: 'docetra.archive.restore',
    })
    if (!accepted) return
    try {
      const adapter = getEntityAdapter(row.sourceKey)
      if (adapter.restore) await adapter.restore(row.recordId)
      else await adapter.update(row.recordId, { status: 'active' })
      allRows.value = allRows.value.filter(item => item.id !== row.id)
      toast.add({ title: t('docetra.archive.restored'), color: 'success' })
    }
    catch (cause: any) {
      toast.add({ title: cause?.message || t('docetra.archive.restoreFailed'), color: 'error' })
    }
  }

  async function permanentlyDelete(rows: ArchiveRow[]) {
    const permittedRows = rows.filter(canDeleteRow)
    if (!permittedRows.length) return
    const accepted = await confirm({
      kind: 'delete',
      titleKey: 'docetra.archive.deleteTitle',
      descriptionKey: 'docetra.archive.deleteDescription',
      descriptionParams: { n: permittedRows.length },
      confirmLabelKey: 'docetra.archive.deletePermanently',
    })
    if (!accepted) return
    try {
      await Promise.all(permittedRows.map(async (row) => {
        const adapter = getEntityAdapter(row.sourceKey)
        if (!adapter.purge) throw new Error(t('docetra.archive.deleteUnsupported'))
        await adapter.purge(row.recordId)
      }))
      const deletedIds = new Set(permittedRows.map(row => row.id))
      allRows.value = allRows.value.filter(row => !deletedIds.has(row.id))
      toast.add({ title: t('docetra.archive.deleted', { n: permittedRows.length }), color: 'success' })
    }
    catch (cause: any) {
      toast.add({ title: cause?.message || t('docetra.archive.deleteFailed'), color: 'error' })
      await refresh()
    }
  }

  function onRowAction({ key, row }: { key: string, row: Record<string, unknown> }) {
    const archiveRow = row as ArchiveRow
    if (key === 'restore') void restoreRow(archiveRow)
    else if (key === 'delete') void permanentlyDelete([archiveRow])
    else if (key === 'detail') openRow(archiveRow)
  }

  function onDeleteSelected(ids: string[]) {
    void permanentlyDelete(allRows.value.filter(row => ids.includes(row.id)))
  }

  function cellValue(row: Record<string, unknown>, key: string) {
    const value = key.split('.').reduce<unknown>((current, part) => {
      if (current && typeof current === 'object') return (current as Record<string, unknown>)[part]
      return undefined
    }, row)
    if (key === 'archivedAt' && value) {
      return formatDateTime(value)
    }
    return String(value || '')
  }

  function onLimitChange(value: number) {
    limit.value = parsePageLimit(value, 10)
    page.value = 1
  }

  onMounted(() => void refresh())

  return {
    columns: ARCHIVE_COLUMNS,
    rowActions,
    canDeleteAny,
    canDeleteRow,
    sourceOptions,
    search,
    sourceFilter,
    dateStart,
    dateEnd,
    page,
    limit,
    visibleRows,
    filteredRows,
    pending,
    error,
    refresh,
    openRow,
    onRowAction,
    onDeleteSelected,
    cellValue,
    onLimitChange,
  }
}
