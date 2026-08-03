import type { TableColumnDef } from '~/types/docetra/common'
import type { RecordLog } from '~/types/docetra/entities'
import { getEntityAdapter } from '~/config/entities'

export interface RecordLogTab {
  id: string
  labelKey: string
  descriptionKey?: string
  icon: string
  /** Filter applied when this tab is active. Empty = all logs. */
  filter?: Partial<Pick<RecordLog, 'action' | 'entityType' | 'category' | 'severity'>>
  columns: TableColumnDef[]
}

const baseColumns: Record<string, TableColumnDef> = {
  occurredAt: { key: 'occurredAt', labelKey: 'docetra.fields.occurredAt', sortable: true, priority: 'high', cell: 'datetime' },
  action: { key: 'action', labelKey: 'docetra.fields.action', priority: 'high', cell: 'badge' },
  entityType: { key: 'entityType', labelKey: 'docetra.fields.recordType', priority: 'medium', cell: 'badge' },
  entityTitle: { key: 'entityTitle', labelKey: 'docetra.fields.entity', priority: 'high' },
  actor: { key: 'actor.name', labelKey: 'docetra.fields.actor', priority: 'medium', cell: 'person' },
  organization: { key: 'organization.name', labelKey: 'docetra.fields.organization', priority: 'low' },
  severity: { key: 'severity', labelKey: 'docetra.fields.severity', priority: 'medium', cell: 'badge' },
  summary: { key: 'summary', labelKey: 'docetra.fields.summary', priority: 'high' },
  changes: { key: 'changesSummary', labelKey: 'docetra.fields.changes', priority: 'high' },
  correlationId: { key: 'correlationId', labelKey: 'docetra.fields.correlationId', priority: 'low' },
  category: { key: 'category', labelKey: 'docetra.fields.category', priority: 'medium', cell: 'badge' },
}

export const RECORD_LOG_TABS: RecordLogTab[] = [
  {
    id: 'all',
    labelKey: 'docetra.recordLogBoard.tabs.all',
    descriptionKey: 'docetra.recordLogBoard.tabs.allHint',
    icon: 'i-lucide-list',
    columns: [
      baseColumns.occurredAt,
      baseColumns.action,
      baseColumns.entityType,
      baseColumns.entityTitle,
      baseColumns.actor,
      baseColumns.severity,
      baseColumns.summary,
    ],
  },
  {
    id: 'created',
    labelKey: 'docetra.logActions.created',
    descriptionKey: 'docetra.recordLogBoard.tabs.createdHint',
    icon: 'i-lucide-plus-circle',
    filter: { action: 'created' },
    columns: [
      baseColumns.occurredAt,
      baseColumns.entityType,
      baseColumns.entityTitle,
      baseColumns.actor,
      baseColumns.organization,
      baseColumns.summary,
    ],
  },
  {
    id: 'updated',
    labelKey: 'docetra.logActions.updated',
    descriptionKey: 'docetra.recordLogBoard.tabs.updatedHint',
    icon: 'i-lucide-pencil',
    filter: { action: 'updated' },
    columns: [
      baseColumns.occurredAt,
      baseColumns.entityType,
      baseColumns.entityTitle,
      baseColumns.changes,
      baseColumns.actor,
      baseColumns.summary,
    ],
  },
  {
    id: 'stage_changed',
    labelKey: 'docetra.logActions.stage_changed',
    descriptionKey: 'docetra.recordLogBoard.tabs.stageHint',
    icon: 'i-lucide-git-branch',
    filter: { action: 'stage_changed' },
    columns: [
      baseColumns.occurredAt,
      baseColumns.entityTitle,
      baseColumns.severity,
      baseColumns.actor,
      baseColumns.summary,
      baseColumns.correlationId,
    ],
  },
  {
    id: 'shared',
    labelKey: 'docetra.logActions.shared',
    descriptionKey: 'docetra.recordLogBoard.tabs.sharedHint',
    icon: 'i-lucide-share-2',
    filter: { action: 'shared' },
    columns: [
      baseColumns.occurredAt,
      baseColumns.entityTitle,
      baseColumns.actor,
      baseColumns.organization,
      baseColumns.summary,
      baseColumns.correlationId,
    ],
  },
  {
    id: 'incoming',
    labelKey: 'docetra.entityTypes.incoming_document',
    descriptionKey: 'docetra.recordLogBoard.tabs.incomingHint',
    icon: 'i-lucide-inbox',
    filter: { entityType: 'incoming_document' },
    columns: [
      baseColumns.occurredAt,
      baseColumns.action,
      baseColumns.entityTitle,
      baseColumns.actor,
      baseColumns.severity,
      baseColumns.summary,
    ],
  },
  {
    id: 'outgoing',
    labelKey: 'docetra.entityTypes.outgoing_document',
    descriptionKey: 'docetra.recordLogBoard.tabs.outgoingHint',
    icon: 'i-lucide-send',
    filter: { entityType: 'outgoing_document' },
    columns: [
      baseColumns.occurredAt,
      baseColumns.action,
      baseColumns.entityTitle,
      baseColumns.actor,
      baseColumns.organization,
      baseColumns.summary,
    ],
  },
  {
    id: 'errors',
    labelKey: 'docetra.recordLogBoard.tabs.errors',
    descriptionKey: 'docetra.recordLogBoard.tabs.errorsHint',
    icon: 'i-lucide-triangle-alert',
    filter: { severity: 'error' },
    columns: [
      baseColumns.occurredAt,
      baseColumns.action,
      baseColumns.entityTitle,
      baseColumns.severity,
      baseColumns.summary,
      baseColumns.correlationId,
    ],
  },
]

function getByPath(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, key) => {
    if (acc && typeof acc === 'object') return (acc as Record<string, unknown>)[key]
    return undefined
  }, obj)
}

export function useRecordLogBoard() {
  const route = useRoute()
  const router = useRouter()
  const { t, te, locale } = useI18n()
  const adapter = getEntityAdapter('recordLogs')

  const pending = ref(false)
  const error = ref<string | null>(null)
  const allItems = ref<RecordLog[]>([])
  const search = ref('')
  const dateFilter = ref('')

  const selectedTabId = computed({
    get: () => String(route.query.tab || 'all'),
    set: (value) => {
      router.replace({
        query: {
          ...route.query,
          tab: value === 'all' ? undefined : value,
          page: undefined,
        },
      })
    },
  })

  const page = computed({
    get: () => Number(route.query.page || 1),
    set: (value) => {
      router.replace({
        query: { ...route.query, page: value > 1 ? String(value) : undefined },
      })
    },
  })

  const limit = computed({
    get: () => Number(route.query.limit || 20),
    set: (value) => {
      router.replace({
        query: {
          ...route.query,
          limit: value === 20 ? undefined : String(value),
          page: undefined,
        },
      })
    },
  })

  const selectedTab = computed(() =>
    RECORD_LOG_TABS.find(tab => tab.id === selectedTabId.value) || RECORD_LOG_TABS[0]!,
  )

  const tabCounts = computed(() => {
    const counts = new Map<string, number>()
    for (const tab of RECORD_LOG_TABS) {
      if (!tab.filter || !Object.keys(tab.filter).length) {
        counts.set(tab.id, allItems.value.length)
        continue
      }
      counts.set(
        tab.id,
        allItems.value.filter(item => matchesFilter(item, tab.filter!)).length,
      )
    }
    return counts
  })

  const filteredItems = computed(() => {
    let rows = [...allItems.value]
    const filter = selectedTab.value.filter
    if (filter) rows = rows.filter(item => matchesFilter(item, filter))

    if (dateFilter.value) {
      const day = dateFilter.value.slice(0, 10)
      rows = rows.filter(item => String(item.occurredAt || '').slice(0, 10) === day)
    }

    const q = search.value.trim().toLowerCase()
    if (q) {
      rows = rows.filter(item =>
        [item.summary, item.entityTitle, item.action, item.entityType, item.correlationId, item.actor?.name]
          .filter(Boolean)
          .some(value => String(value).toLowerCase().includes(q)),
      )
    }

    rows.sort((a, b) => String(b.occurredAt).localeCompare(String(a.occurredAt)))
    return rows
  })

  const total = computed(() => filteredItems.value.length)

  const pageItems = computed(() => {
    const start = (page.value - 1) * limit.value
    return filteredItems.value.slice(start, start + limit.value)
  })

  function matchesFilter(
    item: RecordLog,
    filter: NonNullable<RecordLogTab['filter']>,
  ) {
    return Object.entries(filter).every(([key, value]) =>
      String((item as Record<string, unknown>)[key] ?? '') === String(value),
    )
  }

  function selectTab(id: string) {
    selectedTabId.value = id
  }

  function cellValue(row: Record<string, unknown>, key: string) {
    const value = getByPath(row, key)
    if (value == null || value === '') return '—'
    const text = String(value)

    if (key === 'action') {
      const actionKey = `docetra.logActions.${text}`
      return te(actionKey) ? t(actionKey) : text.replaceAll('_', ' ')
    }
    if (key === 'entityType') {
      const typeKey = `docetra.entityTypes.${text}`
      return te(typeKey) ? t(typeKey) : text.replaceAll('_', ' ')
    }
    if (key === 'severity') {
      const severityKey = `docetra.severity.${text}`
      return te(severityKey) ? t(severityKey) : text
    }
    if (key === 'category') {
      const categoryKey = `docetra.logCategories.${text}`
      return te(categoryKey) ? t(categoryKey) : text
    }
    if (key.endsWith('At') || key === 'occurredAt') {
      const date = new Date(text)
      if (!Number.isNaN(date.getTime())) {
        return date.toLocaleString(locale.value === 'km' ? 'km-KH' : 'en-US', {
          dateStyle: 'medium',
          timeStyle: 'short',
        })
      }
    }
    return text
  }

  function openRow(row: Record<string, unknown>) {
    navigateTo(`/records/record-logs/${row.id}`)
  }

  async function refresh() {
    pending.value = true
    error.value = null
    try {
      const res = await adapter.list({ page: 1, limit: 9999, sort: '-occurredAt' })
      allItems.value = (res.data || []) as RecordLog[]
    }
    catch (e: any) {
      error.value = e?.message || t('docetra.states.loadFailed')
    }
    finally {
      pending.value = false
    }
  }

  watch(selectedTabId, () => {
    if (page.value !== 1) page.value = 1
  })

  watch([search, dateFilter], () => {
    if (page.value !== 1) page.value = 1
  })

  return {
    pending,
    error,
    search,
    dateFilter,
    tabs: RECORD_LOG_TABS,
    selectedTabId,
    selectedTab,
    tabCounts,
    page,
    limit,
    total,
    pageItems,
    columns: computed(() => selectedTab.value.columns),
    cellValue,
    selectTab,
    openRow,
    refresh,
  }
}
