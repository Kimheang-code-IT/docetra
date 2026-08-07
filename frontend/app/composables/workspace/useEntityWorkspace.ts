import type { ListQuery } from '~/types/docetra/common'
import type { EntityConfig } from '~/config/entities'
import { getEntityAdapter } from '~/config/entities'

function getByPath(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, key) => {
    if (acc && typeof acc === 'object') return (acc as Record<string, unknown>)[key]
    return undefined
  }, obj)
}

export function useEntityWorkspace(config: EntityConfig) {
  const route = useRoute()
  const router = useRouter()
  const { t, te, locale } = useI18n()
  const adapter = getEntityAdapter(config.key)

  const view = computed({
    get: () => {
      const requested = String(route.query.view || config.defaultView) as 'table' | 'kanban' | 'hierarchy'
      return config.views.includes(requested) ? requested : config.defaultView
    },
    set: (value) => {
      router.replace({ query: { ...route.query, view: value === config.defaultView ? undefined : value } })
    },
  })

  const q = computed({
    get: () => String(route.query.q || ''),
    set: (value) => {
      router.replace({ query: { ...route.query, q: value || undefined, page: undefined } })
    },
  })

  const page = computed({
    get: () => Number(route.query.page || 1),
    set: (value) => {
      router.replace({ query: { ...route.query, page: value > 1 ? String(value) : undefined } })
    },
  })

  const limit = computed({
    get: () => Math.min(Math.max(Number(route.query.limit || 10) || 10, 10), 100),
    set: (value) => {
      const bounded = Math.min(Math.max(value, 10), 100)
      router.replace({ query: { ...route.query, limit: bounded === 10 ? undefined : String(bounded), page: undefined } })
    },
  })

  const sort = computed({
    get: () => String(route.query.sort || '-updatedAt'),
    set: (value) => {
      router.replace({ query: { ...route.query, sort: value || undefined } })
    },
  })

  const filters = computed(() => {
    const result: Record<string, string> = {}
    for (const filter of config.filters) {
      if (filter.type === 'daterange') {
        const startKey = filter.startKey || 'startDate'
        const endKey = filter.endKey || 'endDate'
        const start = route.query[startKey] || route.query.startDate || route.query[`${filter.key}Start`]
        const end = route.query[endKey] || route.query.endDate || route.query[`${filter.key}End`]
        if (typeof start === 'string' && start) result[startKey] = start
        if (typeof end === 'string' && end) result[endKey] = end
      }
      else {
        const value = route.query[filter.key]
        if (Array.isArray(value)) {
          const joined = value.filter((v): v is string => typeof v === 'string' && Boolean(v)).join(',')
          if (joined) result[filter.key] = joined
        }
        else if (typeof value === 'string' && value) {
          result[filter.key] = value
        }
      }
    }
    return result
  })

  function setFilter(key: string, value: string | string[] | undefined) {
    const next = Array.isArray(value)
      ? (value.length ? value.join(',') : undefined)
      : (value || undefined)

    router.replace({
      query: {
        ...route.query,
        [key]: next,
        page: undefined,
      },
    })
  }

  function clearFilters() {
    const next = { ...route.query }
    for (const filter of config.filters) {
      delete next[filter.key]
      if (filter.type === 'daterange') {
        const startKey = filter.startKey || 'startDate'
        const endKey = filter.endKey || 'endDate'
        delete next[startKey]
        delete next[endKey]
        delete next.startDate
        delete next.endDate
        delete next[`${filter.key}Start`]
        delete next[`${filter.key}End`]
      }
    }
    delete next.q
    delete next.page
    router.replace({ query: next })
  }

  const items = ref<Record<string, unknown>[]>([])
  const total = ref(0)
  const pending = ref(false)
  const error = ref<string | null>(null)
  const kanbanColumns = ref<Record<string, { items: Record<string, unknown>[]; total: number; page: number }>>({})

  let requestToken = 0

  const listQuery = computed<ListQuery>(() => ({
    q: q.value || undefined,
    page: page.value,
    limit: limit.value,
    sort: sort.value,
    view: view.value,
    ...filters.value,
  }))

  async function refresh() {
    const token = ++requestToken
    pending.value = true
    error.value = null
    try {
      if (view.value === 'kanban' && config.stages?.length) {
        const columns: typeof kanbanColumns.value = {}
        await Promise.all(config.stages.map(async (stage) => {
          const res = await adapter.listByStage?.(stage.code, {
            ...listQuery.value,
            page: 1,
            limit: 8,
            stage: undefined,
          }) || await adapter.list({ ...listQuery.value, stage: stage.code, page: 1, limit: 8 })
          columns[stage.code] = {
            items: (res.data || []) as Record<string, unknown>[],
            total: res.meta?.total || 0,
            page: 1,
          }
        }))
        if (token !== requestToken) return
        kanbanColumns.value = columns
        items.value = Object.values(columns).flatMap(c => c.items)
        total.value = Object.values(columns).reduce((sum, c) => sum + c.total, 0)
      }
      else {
        const res = await adapter.list(listQuery.value)
        if (token !== requestToken) return
        items.value = (res.data || []) as Record<string, unknown>[]
        total.value = res.meta?.total || 0
      }
    }
    catch (e: any) {
      if (token !== requestToken) return
      error.value = e?.message || 'Failed to load'
    }
    finally {
      if (token === requestToken) pending.value = false
    }
  }

  async function loadMoreStage(stage: string) {
    const current = kanbanColumns.value[stage]
    if (!current) return
    const nextPage = current.page + 1
    const res = await adapter.listByStage?.(stage, {
      ...listQuery.value,
      page: nextPage,
      limit: 8,
      stage: undefined,
    }) || await adapter.list({ ...listQuery.value, stage, page: nextPage, limit: 8 })
    kanbanColumns.value = {
      ...kanbanColumns.value,
      [stage]: {
        items: [...current.items, ...((res.data || []) as Record<string, unknown>[])],
        total: res.meta?.total || current.total,
        page: nextPage,
      },
    }
  }

  async function moveToStage(id: string, stage: string) {
    if (!adapter.transitionStage) return
    const snapshot = JSON.parse(JSON.stringify(kanbanColumns.value))
    // optimistic
    for (const [code, col] of Object.entries(kanbanColumns.value)) {
      const idx = col.items.findIndex(i => i.id === id)
      if (idx >= 0) {
        const [card] = col.items.splice(idx, 1)
        if (card) {
          card.stage = stage
          kanbanColumns.value[stage]?.items.unshift(card)
        }
        break
      }
    }
    try {
      await adapter.transitionStage(id, stage)
    }
    catch (e) {
      kanbanColumns.value = snapshot
      throw e
    }
  }

  watch([listQuery, view], () => {
    refresh()
  }, { deep: true, immediate: true })

  const debouncedSearch = useDebounceFn((value: string) => {
    q.value = value
  }, 300)

  function cellValue(row: Record<string, unknown>, key: string) {
    const value = getByPath(row, key)

    if (typeof value === 'boolean') {
      return value ? t('docetra.status.active') : t('docetra.status.disabled')
    }
    if (value == null || value === '') return '—'

    const text = String(value)

    if (key === 'status' || key === 'stage' || key === 'level') {
      const statusKey = `docetra.status.${text}`
      const stageKey = `docetra.stages.${text}`
      if (te(statusKey)) return t(statusKey)
      if (te(stageKey)) return t(stageKey)
      return text
    }

    if (key === 'action') {
      const actionKey = `docetra.logActions.${text}`
      if (te(actionKey)) return t(actionKey)
      return text.replaceAll('_', ' ')
    }

    if (key === 'entityType') {
      const typeKey = `docetra.entityTypes.${text}`
      if (te(typeKey)) return t(typeKey)
      return text.replaceAll('_', ' ')
    }

    if (key === 'recordTypeId') {
      return String(row.recordTypeName || text)
    }

    if (key === 'severity') {
      const severityKey = `docetra.severity.${text}`
      if (te(severityKey)) return t(severityKey)
      return text
    }

    if (key === 'category') {
      const categoryKey = `docetra.logCategories.${text}`
      if (te(categoryKey)) return t(categoryKey)
      return text
    }

    if (
      key.endsWith('At')
      || key.endsWith('Date')
      || key === 'occurredAt'
      || key === 'lastLoginAt'
      || key === 'lastSyncAt'
      || key === 'uploadedAt'
    ) {
      const date = new Date(text)
      if (!Number.isNaN(date.getTime())) {
        const hasTime = text.includes('T')
        return date.toLocaleString(locale.value === 'km' ? 'km-KH' : 'en-US', {
          dateStyle: 'medium',
          ...(hasTime ? { timeStyle: 'short' as const } : {}),
        })
      }
    }

    return text
  }

  function openCreate() {
    navigateTo(`${config.routeBase}/new`)
  }

  function openRow(row: Record<string, unknown>) {
    navigateTo(`${config.routeBase}/${row.id}`)
  }

  async function deleteSelected(ids: string[]) {
    if (!ids.length || config.readOnly || config.canDelete === false) return
    if (adapter.deleteMany) {
      await adapter.deleteMany(ids)
    }
    else if (adapter.delete) {
      await Promise.all(ids.map(id => adapter.delete!(id)))
    }
    else {
      throw createError({ statusCode: 501, statusMessage: 'Delete not supported' })
    }
    await refresh()
  }

  return {
    view,
    q,
    page,
    limit,
    sort,
    filters,
    setFilter,
    clearFilters,
    items,
    total,
    pending,
    error,
    kanbanColumns,
    refresh,
    loadMoreStage,
    moveToStage,
    debouncedSearch,
    cellValue,
    openCreate,
    openRow,
    deleteSelected,
    listQuery,
  }
}
