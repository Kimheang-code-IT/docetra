import type { TableColumnDef } from '~/types/docetra/common'
import type { RecordLog } from '~/types/docetra/entities'
import type { RecordType } from '~/types/docetra/configuration'
import { getEntityAdapter } from '~/config/entities'
import { useConfigurationRepositories } from '~/repositories'
import { toComparableDateTime } from '~/utils/date-time-range'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'
import {
  parsePageLimit,
  serializePageLimit,
} from '~/utils/pagination'

export interface RecordLogTab {
  id: string
  labelKey: string
  /** Literal configured Record Type name. */
  label?: string
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
  recordType: { key: 'recordTypeName', labelKey: 'docetra.fields.recordType', priority: 'high', cell: 'badge' },
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
  'recordType',
  'entityTitle',
  'recordStage',
  'parentRecord',
  'updatedAt',
  'actor',
)

const ALL_RECORD_LOGS_TAB: RecordLogTab = {
  id: 'all',
  labelKey: 'docetra.recordLogBoard.tabs.all',
  descriptionKey: 'docetra.recordLogBoard.tabs.allHint',
  icon: 'i-lucide-list',
  columns: recordLogColumns,
}

function getByPath(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, key) => {
    if (acc && typeof acc === 'object') return (acc as Record<string, unknown>)[key]
    return undefined
  }, obj)
}

export function useRecordLogBoard() {
  const route = useRoute()
  const router = useRouter()
  const { t, te } = useI18n()
  const { formatDateTime } = useAppLocalization()
  const adapter = getEntityAdapter('recordLogs')
  const { recordTypes: recordTypeRepository } = useConfigurationRepositories()

  const pending = ref(false)
  const error = ref<string | null>(null)
  const pageItems = ref<RecordLog[]>([])
  const total = ref(0)
  const tabCounts = ref(new Map<string, number>())
  const search = ref(String(route.query.q || ''))
  const configuredRecordTypes = ref<RecordType[]>([])
  let recordTypesLoaded = false
  const recordTypePage = ref(1)
  const recordTypeTotal = ref(0)
  const loadingMoreRecordTypes = ref(false)
  const hasMoreRecordTypes = computed(() => configuredRecordTypes.value.length < recordTypeTotal.value)
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
          entityId: undefined,
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
    get: () => parsePageLimit(route.query.limit, 20),
    set: (value) => {
      const next = parsePageLimit(value, 20)
      router.replace({
        query: {
          ...route.query,
          limit: serializePageLimit(next, 20),
          page: undefined,
        },
      })
    },
  })

  const entityId = computed(() =>
    typeof route.query.entityId === 'string' ? route.query.entityId : undefined,
  )

  const selectedTab = computed(() =>
    tabs.value.find(tab => tab.id === selectedTabId.value) || ALL_RECORD_LOGS_TAB,
  )

  const recordTypeByCode = computed(() => new Map(
    configuredRecordTypes.value.map(type => [type.code, type]),
  ))

  const tabs = computed<RecordLogTab[]>(() => [
    ALL_RECORD_LOGS_TAB,
    ...configuredRecordTypes.value.map(type => ({
      id: type.code,
      labelKey: `docetra.entityTypes.${type.code}`,
      label: type.name,
      icon: type.icon || 'i-lucide-file-text',
      filter: { entityType: type.code },
      columns: recordLogColumns,
    })),
  ])

  async function ensureRecordTypes() {
    if (recordTypesLoaded) return
    recordTypesLoaded = true
    try {
      const response = await recordTypeRepository.list({ status: 'active', page: 1, limit: 50, sort: 'name' })
      configuredRecordTypes.value = response.data || []
      recordTypePage.value = 1
      recordTypeTotal.value = response.meta?.total || configuredRecordTypes.value.length
      const selectedCode = selectedTabId.value
      if (selectedCode !== 'all' && !configuredRecordTypes.value.some(type => type.code === selectedCode)) {
        try {
          const schema = await recordTypeRepository.getResolvedSchema({ code: selectedCode })
          configuredRecordTypes.value.push(schema.recordType)
        }
        catch { /* inaccessible or deleted type; All remains the safe fallback */ }
      }
    }
    catch {
      configuredRecordTypes.value = []
    }
  }

  async function loadMoreRecordTypes() {
    if (!hasMoreRecordTypes.value || loadingMoreRecordTypes.value) return
    loadingMoreRecordTypes.value = true
    const nextPage = recordTypePage.value + 1
    try {
      const response = await recordTypeRepository.list({ status: 'active', page: nextPage, limit: 50, sort: 'name' })
      const known = new Set(configuredRecordTypes.value.map(type => type.id))
      configuredRecordTypes.value.push(...(response.data || []).filter(type => !known.has(type.id)))
      recordTypePage.value = nextPage
      recordTypeTotal.value = response.meta?.total || recordTypeTotal.value
    }
    finally { loadingMoreRecordTypes.value = false }
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
    if (key === 'recordTypeName') return text
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
      return formatDateTime(text)
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
      await ensureRecordTypes()
      const startDate = toComparableDateTime(dateStart.value, 'start') || undefined
      const endDate = toComparableDateTime(dateEnd.value, 'end') || undefined
      const res = await adapter.list({
        page: page.value,
        limit: limit.value,
        sort: '-occurredAt',
        q: search.value.trim() || undefined,
        startDate,
        endDate,
        entityId: entityId.value,
        ...(selectedTab.value.filter || {}),
      })
      if (token !== requestToken) return
      pageItems.value = ((res.data || []) as RecordLog[]).map((item, index) => {
        const recordType = recordTypeByCode.value.get(item.recordTypeCode || item.entityType)
        return {
          ...item,
          recordTypeId: item.recordTypeId || recordType?.id,
          recordTypeCode: item.recordTypeCode || recordType?.code || item.entityType,
          recordTypeName: item.recordTypeName || recordType?.name || item.entityType.replaceAll('_', ' '),
          rowNumber: (page.value - 1) * limit.value + index + 1,
        }
      })
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
  watch(entityId, () => {
    if (page.value !== 1) page.value = 1
    else void refresh()
  })
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
    tabs,
    selectedTabId,
    selectedTab,
    tabCounts,
    hasMoreRecordTypes,
    loadingMoreRecordTypes,
    loadMoreRecordTypes,
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
