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
  rowNumber: { key: 'rowNumber', labelKey: 'docetra.fields.number', priority: 'high' },
  occurredAt: { key: 'occurredAt', labelKey: 'docetra.fields.occurredAt', sortable: true, priority: 'high', cell: 'datetime' },
  action: { key: 'action', labelKey: 'docetra.fields.action', priority: 'high', cell: 'badge' },
  entityType: { key: 'entityType', labelKey: 'docetra.fields.recordType', priority: 'high', cell: 'badge' },
  entityTitle: { key: 'entityTitle', labelKey: 'docetra.fields.title', priority: 'high' },
  recordStage: { key: 'recordStage', labelKey: 'docetra.fields.recordStage', priority: 'high', cell: 'badge' },
  parentRecord: { key: 'parentRecord', labelKey: 'docetra.fields.parentRecord', priority: 'high' },
  updatedAt: { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt', sortable: true, priority: 'high', cell: 'datetime' },
  actor: { key: 'actor.name', labelKey: 'docetra.fields.updater', priority: 'high', cell: 'person' },
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

const recordLogColumns = pickColumns(
  'rowNumber',
  'entityType',
  'entityTitle',
  'recordStage',
  'parentRecord',
  'updatedAt',
  'actor',
)

export const RECORD_LOG_TABS: RecordLogTab[] = [
  {
    id: 'all',
    labelKey: 'docetra.recordLogBoard.tabs.all',
    descriptionKey: 'docetra.recordLogBoard.tabs.allHint',
    icon: 'i-lucide-list',
    columns: recordLogColumns,
  },
  ...[
    ['document', 'i-lucide-file-text'],
    ['file', 'i-lucide-paperclip'],
    ['master_list_request', 'i-lucide-list-checks'],
    ['meeting', 'i-lucide-calendar-days'],
    ['meeting_topic', 'i-lucide-messages-square'],
    ['url', 'i-lucide-link'],
    ['approved_master_list', 'i-lucide-badge-check'],
    ['extension_of_validity', 'i-lucide-clock-3'],
    ['physical_inspection', 'i-lucide-search-check'],
    ['tax_incentive', 'i-lucide-landmark'],
  ].map(([entityType, icon]) => ({
    id: entityType!,
    labelKey: `docetra.entityTypes.${entityType}`,
    icon: icon!,
    filter: { entityType },
    columns: recordLogColumns,
  } satisfies RecordLogTab)),
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
    if (key === 'recordStage') {
      const stageKey = `docetra.stages.${text}`
      return te(stageKey) ? t(stageKey) : text.replaceAll('_', ' ')
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
      pageItems.value = ((res.data || []) as RecordLog[]).map((item, index) => ({
        ...item,
        rowNumber: (page.value - 1) * limit.value + index + 1,
      }))
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
