<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import { useEntityWorkspace } from '~/composables/workspace/useEntityWorkspace'
import { consumeListStale } from '~/utils/workspace-list-stale'

const props = defineProps<{
  config: EntityConfig
}>()

const usesExactColumns = computed(() =>
  ['departments', 'companies', 'companyPurposes', 'companySectors', 'officers', 'systemLogs'].includes(props.config.key),
)

const {
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
  exporting,
  kanbanColumns,
  refresh,
  loadMoreStage,
  moveToStage,
  debouncedSearch,
  cellValue,
  openCreate,
  openRow,
  deleteSelected,
  exportData,
} = useEntityWorkspace(props.config)

const toast = useToast()
const { t } = useI18n()
const { confirm } = useConfirm()
const auth = useAuthStore()

onActivated(() => {
  if (consumeListStale(props.config.key)) void refresh()
})

const searchInput = ref(q.value)
const selectedIds = ref<string[]>([])
const deleting = ref(false)
const exportFields = computed(() => props.config.columns
  .filter(column => column.key !== 'rowNumber')
  .map(column => ({ label: t(column.labelKey), value: column.key })))

watch(q, (v) => { searchInput.value = v })
watch(searchInput, (v) => debouncedSearch(v))

const canCreate = computed(() => props.config.canCreate === true
  && !props.config.readOnly
  && auth.canAccessPage(props.config.createPermission || permissionForAction(props.config.permission, 'create')))
const canDelete = computed(() => props.config.canDelete !== false
  && !props.config.readOnly
  && auth.canAccessPage(permissionForAction(props.config.permission, 'delete')))
const canExport = computed(() => auth.canAccessPage(permissionForAction(props.config.permission, 'export')))

const tableRowActions = computed(() => {
  if (props.config.readOnly) {
    return [
      { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
      { key: 'logs', labelKey: 'docetra.rowActions.logs', icon: 'i-lucide-scroll-text' },
    ]
  }
  return undefined
})

async function onMove(id: string, stage: string) {
  try {
    await moveToStage(id, stage)
  }
  catch {
    toast.add({ title: t('docetra.document.moveFailed'), color: 'error' })
  }
}

async function onDeleteSelected(ids = selectedIds.value) {
  if (!ids.length || !canDelete.value) return
  const ok = await confirm({ kind: 'delete', count: ids.length })
  if (!ok) return

  deleting.value = true
  try {
    await deleteSelected(ids)
    selectedIds.value = []
    toast.add({
      title: t('docetra.actions.deletedItems', { n: ids.length }),
      color: 'success',
    })
  }
  catch (e: any) {
    toast.add({
      title: e?.message || t('docetra.actions.deleteFailed'),
      color: 'error',
    })
  }
  finally {
    deleting.value = false
  }
}

function onRowAction(payload: { key: string, row: Record<string, unknown> }) {
  const { key, row } = payload
  if (key === 'detail' || key === 'edit') {
    openRow(row)
    return
  }
  if (key === 'logs') {
    const id = String(row.id || '')
    navigateTo({
      path: '/records/record-logs',
      query: id ? { q: id } : undefined,
    })
    return
  }
  if (key === 'delete') {
    const id = String(row.id || '')
    if (id) onDeleteSelected([id])
  }
}
</script>

<template>
  <WorkspaceAppWorkspacePage
    :title-key="config.titleKey"
    :description-key="config.descriptionKey"
    :icon="config.icon"
    :can-create="canCreate"
    :create-label-key="config.createLabelKey"
    :refreshing="pending"
    :export-fields="canExport ? exportFields : []"
    :selected-count="selectedIds.length"
    :exporting="exporting"
    @create="openCreate"
    @refresh="refresh"
    @export="request => exportData(request, selectedIds)"
  >
    <div
      v-if="view === 'kanban' && config.stages"
      class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default"
    >
      <WorkspaceAppWorkspaceToolbar
        :search="searchInput"
        :filters="config.filters"
        :filter-values="filters"
        :view="view"
        :views="config.views"
        :sort="sort"
        @update:search="searchInput = $event"
        @update:view="view = $event as any"
        @update:sort="sort = $event"
        @set-filter="setFilter"
        @clear-filters="clearFilters"
      />
      <WorkspaceAppKanbanBoard
        class="min-h-0 flex-1 overflow-x-auto overflow-y-auto p-3"
        :stages="config.stages"
        :columns="kanbanColumns"
        :pending="pending"
        :title-field="config.titleField"
        @card-click="openRow"
        @load-more="loadMoreStage"
        @move="onMove"
      />
    </div>

    <div
      v-else-if="view === 'hierarchy'"
      class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default"
    >
      <WorkspaceAppWorkspaceToolbar
        :search="searchInput"
        :filters="config.filters"
        :filter-values="filters"
        :view="view"
        :views="config.views"
        :sort="sort"
        @update:search="searchInput = $event"
        @update:view="view = $event as any"
        @update:sort="sort = $event"
        @set-filter="setFilter"
        @clear-filters="clearFilters"
      />
      <div class="min-h-0 flex-1 overflow-auto p-4">
        <p class="mb-3 text-sm text-muted">{{ $t('docetra.views.hierarchyHint') }}</p>
        <div v-if="pending" class="flex justify-center py-10">
          <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
        </div>
        <ul v-else class="space-y-2">
          <li
            v-for="row in items"
            :key="String(row.id)"
            class="cursor-pointer rounded-md border border-default px-3 py-2 hover:bg-elevated/50"
            :style="{ marginInlineStart: `${row.parentId ? 1.25 : 0}rem` }"
            @click="openRow(row)"
          >
            <span class="font-medium">{{ row.code }} · {{ row.name }}</span>
            <span class="ms-2 text-xs text-muted">{{ row.parentName || $t('docetra.fields.root') }}</span>
          </li>
        </ul>
      </div>
    </div>

    <div
      v-else-if="view === 'timeline'"
      class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default shadow-xs"
    >
      <WorkspaceAppWorkspaceToolbar
        :search="searchInput"
        :filters="config.filters"
        :filter-values="filters"
        :view="view"
        :views="config.views"
        :sort="sort"
        @update:search="searchInput = $event"
        @update:view="view = $event as any"
        @update:sort="sort = $event"
        @set-filter="setFilter"
        @clear-filters="clearFilters"
      />
      <MeetingAppMeetingHistoryTimeline
        :rows="items"
        :total="total"
        :page="page"
        :limit="limit"
        :pending="pending"
        :error="error"
        @update:page="page = $event"
        @update:limit="limit = $event"
        @open="openRow"
        @retry="refresh"
      />
    </div>

    <div
      v-else
      class="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default shadow-xs"
    >
      <WorkspaceAppServerTable
        :columns="config.columns"
        :rows="items"
        :total="total"
        :page="page"
        :limit="limit"
        :pending="pending"
        :error="error"
        :cell-value="cellValue"
        :can-delete="canDelete"
        :selectable="usesExactColumns ? false : canDelete"
        :show-meta="true"
        :row-actions="tableRowActions"
        @update:page="page = $event"
        @update:limit="limit = $event"
        @update:selection="selectedIds = $event"
        @row-click="openRow"
        @row-action="onRowAction"
        @delete-selected="onDeleteSelected"
        @retry="refresh"
      >
        <template #toolbar>
          <WorkspaceAppWorkspaceToolbar
            :search="searchInput"
            :filters="config.filters"
            :filter-values="filters"
            :view="view"
            :views="config.views"
            :sort="sort"
            @update:search="searchInput = $event"
            @update:view="view = $event as any"
            @update:sort="sort = $event"
            @set-filter="setFilter"
            @clear-filters="clearFilters"
          />
        </template>
      </WorkspaceAppServerTable>
    </div>
  </WorkspaceAppWorkspacePage>
</template>
