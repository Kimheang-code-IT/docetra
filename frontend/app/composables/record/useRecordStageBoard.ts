import type { EntityConfig } from '~/config/entities'
import { getEntityAdapter } from '~/config/entities'
import type { WorkflowStage } from '~/types/docetra/common'
import { isWithinDateTimeRange } from '~/utils/date-time-range'

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
  const adapter = getEntityAdapter(config.key)
  const stages = computed(() => config.stages || [])

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
  const stageCounts = ref<Record<string, number>>({})
  const pending = ref(false)
  const error = ref<string | null>(null)
  const draggingId = ref<string | null>(null)
  const dropStageCode = ref<string | null>(null)

  let requestToken = 0

  const filteredStages = computed(() => {
    const q = stageSearch.value.trim().toLowerCase()
    if (!q) return stages.value
    return stages.value.filter((stage) => {
      const label = te(stage.labelKey) ? t(stage.labelKey) : stage.code
      return label.toLowerCase().includes(q) || stage.code.toLowerCase().includes(q)
    })
  })

  const filteredItems = computed(() => {
    let rows = items.value
    if (dateStart.value.trim() || dateEnd.value.trim()) {
      rows = rows.filter(row =>
        isWithinDateTimeRange(
          String(getByPath(row, options.dateField) || ''),
          dateStart.value,
          dateEnd.value,
        ),
      )
    }
    return rows
  })

  async function refreshCounts() {
    const counts: Record<string, number> = {}
    await Promise.all(stages.value.map(async (stage) => {
      const res = await adapter.list({
        stage: stage.code,
        startDate: dateStart.value || undefined,
        endDate: dateEnd.value || undefined,
        page: 1,
        limit: 1,
        q: recordSearch.value || undefined,
      })
      counts[stage.code] = res.meta?.total || 0
    }))
    stageCounts.value = counts
  }

  async function refresh() {
    const token = ++requestToken
    pending.value = true
    error.value = null
    try {
      const [listRes] = await Promise.all([
        adapter.list({
          q: recordSearch.value || undefined,
          stage: selectedStage.value || undefined,
          startDate: dateStart.value || undefined,
          endDate: dateEnd.value || undefined,
          page: 1,
          limit: 100,
          sort: '-updatedAt',
        }),
        refreshCounts(),
      ])
      if (token !== requestToken) return
      items.value = (listRes.data || []) as Record<string, unknown>[]
      total.value = listRes.meta?.total || 0
    }
    catch (e: any) {
      if (token !== requestToken) return
      error.value = e?.message || 'Failed to load'
    }
    finally {
      if (token === requestToken) pending.value = false
    }
  }

  const debouncedRecordSearch = useDebounceFn((value: string) => {
    router.replace({
      query: {
        ...route.query,
        q: value || undefined,
        page: undefined,
      },
    })
    refresh()
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
    refresh()
  })

  watch(selectedStage, () => {
    refresh()
  })

  function selectStage(code: string | null) {
    selectedStage.value = code
  }

  function toggleLeftPanel() {
    leftCollapsed.value = !leftCollapsed.value
  }

  function openCreate() {
    navigateTo(`${config.routeBase}/new`)
  }

  function openRow(row: Record<string, unknown>) {
    navigateTo(`${config.routeBase}/${row.id}`)
  }

  async function moveToStage(id: string, stage: string) {
    if (!adapter.transitionStage) {
      await adapter.update?.(id, { stage } as any)
    }
    else {
      await adapter.transitionStage(id, stage)
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
    return value == null ? '' : String(value).slice(0, 10)
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
    const key = `docetra.stages.${text}`
    return te(key) ? t(key) : text
  }

  const allCount = computed(() =>
    Object.values(stageCounts.value).reduce((sum, n) => sum + n, 0),
  )

  return {
    stages,
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
    stageCounts,
    allCount,
    pending,
    error,
    draggingId,
    dropStageCode,
    refresh,
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
