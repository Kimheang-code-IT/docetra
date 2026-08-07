import type { TableColumnDef } from '~/types/docetra/common'
import type { RecordLog } from '~/types/docetra/entities'
import { getEntityAdapter } from '~/config/entities'
import { toComparableDateTime } from '~/utils/date-time-range'

export interface RecordLogTab {
  id: string
  labelKey: string
  descriptionKey?: string
  icon: string
  /** Filter applied when this tab is active. Empty = all logs. */
  filter?: Partial<Pick<RecordLog, 'action' | 'entityType' | 'category' | 'severity'>>
  columns: TableColumnDef[]
}

const baseColumns = {
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
} satisfies Record<string, TableColumnDef>

function pickColumns(...keys: Array<keyof typeof baseColumns>): TableColumnDef[] {
  return keys.map(key => baseColumns[key])
}

export const RECORD_LOG_TABS: RecordLogTab[] = [
  {
    id: 'all',
    labelKey: 'docetra.recordLogBoard.tabs.all',
    descriptionKey: 'docetra.recordLogBoard.tabs.allHint',
    icon: 'i-lucide-list',
    columns: pickColumns('occurredAt', 'action', 'entityType', 'entityTitle', 'actor', 'severity', 'summary'),
  },
  {
    id: 'created',
    labelKey: 'docetra.logActions.created',
    descriptionKey: 'docetra.recordLogBoard.tabs.createdHint',
    icon: 'i-lucide-plus-circle',
    filter: { action: 'created' },
    columns: pickColumns('occurredAt', 'entityType', 'entityTitle', 'actor', 'organization', 'summary'),
  },
  {
    id: 'updated',
    labelKey: 'docetra.logActions.updated',
    descriptionKey: 'docetra.recordLogBoard.tabs.updatedHint',
    icon: 'i-lucide-pencil',
    filter: { action: 'updated' },
    columns: pickColumns('occurredAt', 'entityType', 'entityTitle', 'changes', 'actor', 'summary'),
  },
  {
    id: 'stage_changed',
    labelKey: 'docetra.logActions.stage_changed',
    descriptionKey: 'docetra.recordLogBoard.tabs.stageHint',
    icon: 'i-lucide-git-branch',
    filter: { action: 'stage_changed' },
    columns: pickColumns('occurredAt', 'entityTitle', 'severity', 'actor', 'summary', 'correlationId'),
  },
  {
    id: 'shared',
    labelKey: 'docetra.logActions.shared',
    descriptionKey: 'docetra.recordLogBoard.tabs.sharedHint',
    icon: 'i-lucide-share-2',
    filter: { action: 'shared' },
    columns: pickColumns('occurredAt', 'entityTitle', 'actor', 'organization', 'summary', 'correlationId'),
  },
  {
    id: 'incoming',
    labelKey: 'docetra.entityTypes.incoming_document',
    descriptionKey: 'docetra.recordLogBoard.tabs.incomingHint',
    icon: 'i-lucide-inbox',
    filter: { entityType: 'incoming_document' },
    columns: pickColumns('occurredAt', 'action', 'entityTitle', 'actor', 'severity', 'summary'),
  },
  {
    id: 'outgoing',
    labelKey: 'docetra.entityTypes.outgoing_document',
    descriptionKey: 'docetra.recordLogBoard.tabs.outgoingHint',
    icon: 'i-lucide-send',
    filter: { entityType: 'outgoing_document' },
    columns: pickColumns('occurredAt', 'action', 'entityTitle', 'actor', 'organization', 'summary'),
  },
  {
    id: 'errors',
    labelKey: 'docetra.recordLogBoard.tabs.errors',
    descriptionKey: 'docetra.recordLogBoard.tabs.errorsHint',
    icon: 'i-lucide-triangle-alert',
    filter: { severity: 'error' },
    columns: pickColumns('occurredAt', 'action', 'entityTitle', 'severity', 'summary', 'correlationId'),
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
  const pageItems = ref<RecordLog[]>([])
  const total = ref(0)
  const tabCounts = ref(new Map<string, number>())
  const search = ref('')
  const dateStart = ref(typeof route.query.startDate === 'string' ? route.query.startDate : '')
  const dateEnd = ref(typeof route.query.endDate === 'string' ? route.query.endDate : '')
  let requestToken = 0

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
    get: () => Math.min(Math.max(Number(route.query.limit || 20) || 20, 10), 100),
    set: (value) => {
      const bounded = Math.min(Math.max(value, 10), 100)
      router.replace({
        query: {
          ...route.query,
          limit: bounded === 20 ? undefined : String(bounded),
          page: undefined,
        },
      })
    },
  })

  const selectedTab = computed(() =>
    RECORD_LOG_TABS.find(tab => tab.id === selectedTabId.value) || RECORD_LOG_TABS[0]!,
  )

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
    const token = ++requestToken
    pending.value = true
    error.value = null
    try {
      const startDate = toComparableDateTime(dateStart.value, 'start') || undefined
      const endDate = toComparableDateTime(dateEnd.value, 'end') || undefined
      const res = await adapter.list({
        page: page.value,
        limit: limit.value,
        sort: '-occurredAt',
        q: search.value.trim() || undefined,
        startDate,
        endDate,
        ...(selectedTab.value.filter || {}),
      })
      if (token !== requestToken) return
      pageItems.value = (res.data || []) as RecordLog[]
      total.value = res.meta?.total || 0

      const counts = (res.meta as (typeof res.meta & { counts?: Record<string, number> }))?.counts
      if (counts) tabCounts.value = new Map(Object.entries(counts))
      else tabCounts.value = new Map([[selectedTab.value.id, total.value]])
    }
    catch (e: any) {
      error.value = e?.message || t('docetra.states.loadFailed')
    }
    finally {
      pending.value = false
    }
  }

  watch([selectedTabId, dateStart, dateEnd], () => {
    router.replace({
      query: {
        ...route.query,
        startDate: dateStart.value || undefined,
        endDate: dateEnd.value || undefined,
        page: undefined,
      },
    })
    if (page.value !== 1) page.value = 1
    else void refresh()
  })
  watch([page, limit], () => { void refresh() }, { immediate: true })
  watch(search, useDebounceFn(() => {
    if (page.value !== 1) page.value = 1
    else void refresh()
  }, 300))

  return {
    pending,
    error,
    search,
    dateStart,
    dateEnd,
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
