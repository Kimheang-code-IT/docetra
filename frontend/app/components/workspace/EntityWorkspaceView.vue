<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import { useEntityWorkspace } from '~/composables/workspace/useEntityWorkspace'
import type { RowActionItem } from '~/types/docetra/row-actions'
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import { permissionForAction } from '~/utils/role/access'
import { isRowActive, isRowInactive } from '~/utils/row-status'

const props = defineProps<{
  config: EntityConfig
}>()

const usesExactColumns = computed(() =>
  ['departments', 'companies', 'purposes', 'sectors', 'officers', 'systemLogs'].includes(props.config.key),
)

/** Stage colors from the record-type config take precedence over enum/heuristic badge colors. */
const stageColorMap = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  for (const stage of props.config.stages || []) {
    if (stage.code && stage.color) map[stage.code] = stage.color
  }
  return map
})

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
  setRowActive,
  exportData,
} = useEntityWorkspace(props.config)

const toast = useToast()
const { t } = useI18n()
const { confirm } = useConfirm()
const auth = useAuthStore()

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
const canTransition = computed(() =>
  auth.canAccessPage(permissionForAction(props.config.permission, 'transition')),
)
const canDeactivate = computed(() =>
  !props.config.readOnly
  && auth.canAccessPage(permissionForAction(props.config.permission, 'archive')),
)
const canActivate = computed(() =>
  !props.config.readOnly
  && auth.canAccessPage(permissionForAction(props.config.permission, 'restore')),
)
const cardEntityKey = computed(() => props.config.key as CardDisplayEntityKey)

const tableRowActions = computed<RowActionItem[]>(() => [
  { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
  ...(canDeactivate.value
    ? [{
        key: 'deactivate',
        labelKey: 'docetra.rowActions.deactivate',
        icon: 'i-lucide-archive',
        color: 'warning',
        // Only active rows can be deactivated.
        hidden: (row: Record<string, unknown>) => !isRowActive(row),
      } satisfies RowActionItem]
    : []),
  ...(canActivate.value
    ? [{
        key: 'activate',
        labelKey: 'docetra.rowActions.activate',
        icon: 'i-lucide-archive-restore',
        color: 'success',
        // Only inactive rows can be reactivated.
        hidden: (row: Record<string, unknown>) => !isRowInactive(row),
      } satisfies RowActionItem]
    : []),
  ...(canDelete.value
    ? [{
        key: 'delete',
        labelKey: 'docetra.rowActions.delete',
        icon: 'i-lucide-trash-2',
        color: 'error',
        // Delete exists only for inactive rows — deactivate first.
        hidden: (row: Record<string, unknown>) => !isRowInactive(row),
      } satisfies RowActionItem]
    : []),
])

const canDeleteSelected = computed(() =>
  selectedIds.value.length > 0
  && selectedIds.value.every((id) => {
    const row = items.value.find(item => String(item.id) === id)
    return row ? isRowInactive(row) : false
  }),
)

const mutatingRowId = ref<string | null>(null)

async function onToggleRowActive(row: Record<string, unknown>, active: boolean) {
  const id = String(row.id || '')
  if (!id || mutatingRowId.value) return
  mutatingRowId.value = id
  try {
    await setRowActive(row, active)
    toast.add({
      title: t(active ? 'docetra.actions.activated' : 'docetra.actions.deactivated'),
      color: 'success',
    })
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.actions.actionFailed'), color: 'error' })
  }
  finally {
    mutatingRowId.value = null
  }
}

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
  // Deactivate first: refuse rows that are still active.
  const everyInactive = ids.every((id) => {
    const row = items.value.find(item => String(item.id) === id)
    return !row || isRowInactive(row)
  })
  if (!everyInactive) return
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
  if (key === 'deactivate') {
    void onToggleRowActive(row, false)
    return
  }
  if (key === 'activate') {
    void onToggleRowActive(row, true)
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
        :entity-key="cardEntityKey"
        :can-move="canTransition"
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
        <ul class="space-y-2">
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
        :can-delete-selected="canDeleteSelected"
        :selectable="usesExactColumns ? false : canDelete"
        :show-meta="false"
        :row-actions="tableRowActions"
        :stage-colors="stageColorMap"
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
