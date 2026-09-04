import type { EntityConfig } from '~/config/entities'
import { getAdapterForConfig } from '~/config/entities'
import type { WorkflowStage } from '~/types/docetra/common'
import type { RecordType } from '~/types/docetra/configuration'
import { useConfigurationRepositories } from '~/repositories'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'
import { provideCardFieldsOverride } from '~/composables/settings/useCardFields'
import { concurrencyVersion } from '~/utils/api/concurrency'

function getByPath(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, key) => {
    if (acc && typeof acc === 'object') return (acc as Record<string, unknown>)[key]
    return undefined
  }, obj)
}

export function useRecordStageBoard(
  config: EntityConfig,
  options: {
    /** Field used for right-pane date filter (e.g. receivedDate, sentDate, updatedAt). */
    dateField: string
    /** Optional secondary line on cards (e.g. senderOrganization.name). */
    subtitleField?: string
    stateKey?: string
  },
) {
  const route = useRoute()
  const router = useRouter()
  const { t, te } = useI18n()
  const { formatDate } = useAppLocalization()
  const adapter = getAdapterForConfig(config)
  const { recordTypes } = useConfigurationRepositories()
  /** Board cards resolve per-type card slots from the loaded type payload. */
  const typePayload = ref<RecordType['payload'] | null>(null)
  provideCardFieldsOverride(() => typePayload.value)
  const runtimeStages = ref<WorkflowStage[]>(
    [...(config.stages || [])].sort((a, b) => a.order - b.order),
  )
  const stages = computed(() => runtimeStages.value)
  const stageConfigurationError = ref<string | null>(null)
  let stageConfigurationLoaded = false

  async function ensureConfiguredStages() {
    if (stageConfigurationLoaded || !config.recordTypeCode) return
    stageConfigurationLoaded = true
    stageConfigurationError.value = null
    try {
      const schema = await recordTypes.getResolvedSchema({ code: config.recordTypeCode })
      const recordType = schema.recordType
      typePayload.value = recordType.payload || null
      if (!recordType.features?.enableWorkflow || !recordType.stages?.length) {
        throw new Error(t('docetra.recordStageBoard.stageConfigEmpty'))
      }
      runtimeStages.value = [...recordType.stages]
        .sort((a, b) => a.order - b.order)
        .map(stage => ({
          id: stage.id,
          code: stage.code,
          label: stage.name,
          labelKey: `docetra.stages.${stage.code}`,
          order: stage.order,
          color: stage.color,
        }))
    }
    catch (cause: any) {
      stageConfigurationError.value = cause?.message || t('docetra.recordStageBoard.stageConfigFailed')
    }
  }

  const stageSearch = ref('')
  const recordSearch = ref(String(route.query.q || ''))
  const dateStart = ref(typeof route.query.startDate === 'string' ? route.query.startDate : '')
  const dateEnd = ref(typeof route.query.endDate === 'string' ? route.query.endDate : '')
  const leftCollapsed = useState(options.stateKey || `record-stage-left-${config.key}`, () => false)

  const selectedStage = computed({
    get: () => {
      const raw = route.query.stage
      return typeof raw === 'string' && raw ? raw : null
    },
    set: (value: string | null) => {
      router.replace({
        query: {
          ...route.query,
          stage: value || undefined,
          page: undefined,
        },
      })
    },
  })

  const selectedStageMeta = computed<WorkflowStage | null>(() =>
    stages.value.find(s => s.code === selectedStage.value) || null,
  )

  const items = ref<Record<string, unknown>[]>([])
  const total = ref(0)
  const page = ref(1)
  const limit = ref(20)
  const stageCounts = ref<Record<string, number>>({})
  const pending = ref(false)
  const error = ref<string | null>(null)

  let requestToken = 0

  const filteredStages = computed(() => {
    const q = stageSearch.value.trim().toLowerCase()
    if (!q) return stages.value
    return stages.value.filter((stage) => {
      const label = (te(stage.labelKey) ? t(stage.labelKey) : stage.label) || stage.code
      return label.toLowerCase().includes(q) || stage.code.toLowerCase().includes(q)
    })
  })

  // Search and date filters are applied by the API. Keeping the browser list
  // bounded avoids scanning a growing local collection on every render.
  const filteredItems = computed(() => items.value)

  async function refreshCounts() {
    if (!adapter.getGroupCounts) return { total: 0, groups: {} as Record<string, number> }
    const response = await adapter.getGroupCounts('stage', {
      startDate: dateStart.value || undefined,
      endDate: dateEnd.value || undefined,
      q: recordSearch.value || undefined,
    })
    return response.data
  }

  async function refresh(options: { resetPage?: boolean } = {}) {
    if (options.resetPage) page.value = 1
    const token = ++requestToken
    pending.value = true
    error.value = null
    try {
      await ensureConfiguredStages()
      const [listRes, counts] = await Promise.all([
        adapter.list({
          q: recordSearch.value || undefined,
          stage: selectedStage.value || undefined,
          startDate: dateStart.value || undefined,
          endDate: dateEnd.value || undefined,
          page: page.value,
          limit: limit.value,
          sort: '-updatedAt',
        }),
        refreshCounts(),
      ])
      if (token !== requestToken) return
      items.value = (listRes.data || []) as Record<string, unknown>[]
      total.value = listRes.meta?.total || 0
      stageCounts.value = counts.groups || {}
      if (!selectedStage.value) total.value = counts.total || total.value
    }
    catch (e: any) {
      if (token !== requestToken) return
      error.value = e?.message || 'Failed to load'
    }
    finally {
      if (token === requestToken) pending.value = false
    }
  }

  function setPage(next: number) {
    if (page.value === next) return
    page.value = next
    void refresh()
  }

  function setLimit(next: number) {
    if (limit.value === next) return
    limit.value = next
    void refresh({ resetPage: true })
  }

  const debouncedRecordSearch = useDebounceFn((value: string) => {
    router.replace({
      query: {
        ...route.query,
        q: value || undefined,
        page: undefined,
      },
    })
    void refresh({ resetPage: true })
  }, 300)

  watch(recordSearch, (value) => {
    debouncedRecordSearch(value)
  })

  watch([dateStart, dateEnd], ([start, end]) => {
    router.replace({
      query: {
        ...route.query,
        startDate: start || undefined,
        endDate: end || undefined,
        page: undefined,
      },
    })
    void refresh({ resetPage: true })
  })

  watch(selectedStage, () => {
    void refresh({ resetPage: true })
  })

  function selectStage(code: string | null) {
    selectedStage.value = code
  }

  function toggleLeftPanel() {
    leftCollapsed.value = !leftCollapsed.value
  }

  function openCreate() {
    return navigateTo(
      `${config.routeBase}/new?returnTo=${encodeURIComponent(config.routeBase)}`,
    )
  }

  function openRow(row: Record<string, unknown>) {
    navigateTo(`${config.routeBase}/${row.id}`)
  }

  async function moveToStage(id: string, stage: string) {
    const row = items.value.find(item => String(item.id) === id)
    const extra = { version: concurrencyVersion(row) }
    if (!adapter.transitionStage) {
      await adapter.update?.(id, { stage, ...extra } as any)
    }
    else {
      await adapter.transitionStage(id, stage, extra)
    }
    await refresh()
  }

  function subtitleOf(row: Record<string, unknown>) {
    if (!options.subtitleField) return ''
    const value = getByPath(row, options.subtitleField)
    return value == null ? '' : String(value)
  }

  function dateOf(row: Record<string, unknown>) {
    const value = getByPath(row, options.dateField)
    return formatDate(value, '')
  }

  function labelOf(row: Record<string, unknown>) {
    const title = row[config.titleField]
    if (title) return String(title)
    if (row.referenceNumber) return String(row.referenceNumber)
    return String(row.id || '')
  }

  function statusLabel(status: unknown) {
    const text = String(status || '')
    if (!text) return ''
    const key = `docetra.status.${text}`
    return te(key) ? t(key) : text
  }

  function stageLabel(stage: unknown) {
    const text = String(stage || '')
    if (!text) return ''
    const configured = stages.value.find(item => item.code === text)
    if (configured?.label) return configured.label
    const key = `docetra.stages.${text}`
    return te(key) ? t(key) : text
  }

  async function reloadStageConfiguration() {
    stageConfigurationLoaded = false
    await refresh()
  }

  const allCount = computed(() => total.value)

  return {
    stages,
    stageConfigurationError,
    filteredStages,
    stageSearch,
    recordSearch,
    dateStart,
    dateEnd,
    leftCollapsed,
    selectedStage,
    selectedStageMeta,
    items,
    filteredItems,
    total,
    page,
    limit,
    stageCounts,
    allCount,
    pending,
    error,
    refresh,
    setPage,
    setLimit,
    reloadStageConfiguration,
    selectStage,
    toggleLeftPanel,
    openCreate,
    openRow,
    moveToStage,
    subtitleOf,
    dateOf,
    labelOf,
    statusLabel,
    stageLabel,
    dateField: options.dateField,
  }
}
