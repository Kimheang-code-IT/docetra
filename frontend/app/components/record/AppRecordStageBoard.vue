<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'
import { getAdapterForConfig } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import { useBoardDragDrop } from '~/composables/common/useBoardDragDrop'
import { useBoardViewMode } from '~/composables/common/useBoardViewMode'
import { useRecordStageBoard } from '~/composables/record/useRecordStageBoard'
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import type { RowActionItem } from '~/types/docetra/row-actions'
import { consumeListStale } from '~/utils/workspace-list-stale'
import { permissionForAction } from '~/utils/role/access'
import { concurrencyVersion, versionsById } from '~/utils/api/concurrency'
import { getByPath } from '~/utils/object-path'

const props = defineProps<{
  config: EntityConfig
  dateField: string
  subtitleField?: string
  stateKey?: string
}>()

const toast = useToast()
const { t, te } = useI18n()
const { confirm } = useConfirm()
const auth = useAuthStore()
const adapter = getAdapterForConfig(props.config)
const cardEntityKey = computed(() => props.config.key as CardDisplayEntityKey)
const viewMode = useBoardViewMode(`record-stage-view-${props.config.key}`, 'cards')
const {
  draggingId,
  dropTargetId,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDragLeave,
  consumeDrop,
} = useBoardDragDrop()

const canCreate = computed(() => props.config.canCreate !== false
  && !props.config.readOnly
  && auth.canAccessPage(
    props.config.createPermission || permissionForAction(props.config.permission, 'create'),
  ))
const canTransition = computed(() => auth.canAccessPage(permissionForAction(props.config.permission, 'transition')))
const canDelete = computed(() => props.config.canDelete !== false
  && auth.canAccessPage(permissionForAction(props.config.permission, 'delete')))
const canViewLogs = computed(() => auth.canAccessPage('records.logs.view'))

const {
  filteredStages,
  stageSearch,
  recordSearch,
  dateStart,
  dateEnd,
  leftCollapsed,
  selectedStage,
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
  selectStage,
  openCreate,
  openRow,
  moveToStage,
  labelOf,
  stageLabel,
  stages,
  stageConfigurationError,
  reloadStageConfiguration,
} = useRecordStageBoard(props.config, {
  dateField: props.dateField,
  subtitleField: props.subtitleField,
  stateKey: props.stateKey,
})

const stageColorMap = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  for (const stage of stages.value) {
    if (stage.code && stage.color) map[stage.code] = stage.color
  }
  return map
})

const tableColumns = computed(() => props.config.columns || [])

const tableRowActions = computed<RowActionItem[]>(() => [
  { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
  ...(canViewLogs.value
    ? [{ key: 'logs', labelKey: 'docetra.rowActions.logs', icon: 'i-lucide-scroll-text' } satisfies RowActionItem]
    : []),
  ...(canDelete.value
    ? [{ key: 'delete', labelKey: 'docetra.rowActions.delete', icon: 'i-lucide-trash-2', color: 'error' } satisfies RowActionItem]
    : []),
])

function stageName(stage: { label?: string, labelKey: string, code: string }) {
  return stage.label || (te(stage.labelKey) ? t(stage.labelKey) : stage.code)
}

function cellValue(row: Record<string, unknown>, key: string) {
  const value = getByPath(row, key)
  if (value == null || value === '') return '—'
  const text = String(value)
  if (key === 'stage') return stageLabel(text) || text
  if (key === 'status') {
    const statusKey = `docetra.status.${text}`
    return te(statusKey) ? t(statusKey) : text
  }
  return text
}

onMounted(() => {
  consumeListStale(props.config.key)
  void refresh()
})

onActivated(() => {
  if (consumeListStale(props.config.key)) void refresh()
})

async function onDropRecord(stageCode: string) {
  if (!canTransition.value) return
  const id = consumeDrop()
  if (!id) return
  try {
    await moveToStage(id, stageCode)
    toast.add({
      title: t('docetra.recordStageBoard.moved', { stage: stageLabel(stageCode) }),
      color: 'success',
    })
  }
  catch (e: any) {
    toast.add({
      title: e?.message || t('docetra.recordStageBoard.moveFailed'),
      color: 'error',
    })
  }
}

async function onMoveStage(id: string, stageCode: string) {
  if (!canTransition.value) return
  try {
    await moveToStage(id, stageCode)
    toast.add({
      title: t('docetra.recordStageBoard.moved', { stage: stageLabel(stageCode) }),
      color: 'success',
    })
  }
  catch (e: any) {
    toast.add({
      title: e?.message || t('docetra.recordStageBoard.moveFailed'),
      color: 'error',
    })
  }
}

function onLogs(row: Record<string, unknown>) {
  if (!canViewLogs.value) return
  const id = String(row.id || '')
  const recordTypeCode = props.config.recordTypeCode
  navigateTo({
    path: '/records/logs',
    query: {
      tab: recordTypeCode || undefined,
      entityId: id || undefined,
    },
  })
}

async function onDelete(row: Record<string, unknown>) {
  if (!canDelete.value) return
  const id = String(row.id || '')
  if (!id) return
  const ok = await confirm({ kind: 'delete', count: 1 })
  if (!ok) return
  try {
    if (adapter.delete) await adapter.delete(id, { version: concurrencyVersion(row) })
    else if (adapter.deleteMany) await adapter.deleteMany([id], versionsById([row], [id]))
    toast.add({ title: t('docetra.actions.deletedItems', { n: 1 }), color: 'success' })
    await refresh()
  }
  catch (e: any) {
    toast.add({ title: e?.message || t('docetra.actions.deleteFailed'), color: 'error' })
  }
}

function onRowAction(payload: { key: string, row: Record<string, unknown> }) {
  if (payload.key === 'detail') {
    openRow(payload.row)
    return
  }
  if (payload.key === 'logs') {
    onLogs(payload.row)
    return
  }
  if (payload.key === 'delete') void onDelete(payload.row)
}
</script>

<template>
  <WorkspaceAppWorkspaceBoardPage
    v-model:collapsed="leftCollapsed"
    v-model:rail-search="stageSearch"
    v-model:header-search="recordSearch"
    v-model:date-start="dateStart"
    v-model:date-end="dateEnd"
    v-model:view-mode="viewMode"
    :title-key="config.titleKey"
    :description-key="config.descriptionKey"
    :icon="config.icon"
    :can-create="canCreate"
    rail-title-key="docetra.recordStageBoard.stagesTitle"
    rail-icon="i-lucide-layers"
    expand-label-key="docetra.recordStageBoard.expandStages"
    collapse-label-key="docetra.recordStageBoard.collapseStages"
    rail-search-placeholder-key="docetra.recordStageBoard.searchStages"
    header-search-placeholder-key="docetra.recordStageBoard.searchRecords"
    :pending="pending"
    :show-pending-overlay="pending && !filteredItems.length"
    :error="error"
    @create="openCreate"
    @refresh="refresh"
    @retry="refresh"
  >
    <template #alerts>
      <UAlert
        v-if="stageConfigurationError"
        class="m-3 mb-0"
        color="warning"
        :title="$t('docetra.recordStageBoard.usingFallbackStages')"
        :description="stageConfigurationError"
        :actions="[{ label: $t('docetra.actions.retry'), onClick: reloadStageConfiguration }]"
      />
    </template>

    <template #rail-pills="{ railCollapsed, onRailSelect }">
      <WorkspaceAppBoardRailPill
        :label="$t('docetra.recordStageBoard.allRecords')"
        :count="allCount"
        icon="i-lucide-layout-grid"
        :selected="selectedStage == null"
        :collapsed="railCollapsed"
        @select="onRailSelect(() => selectStage(null))"
      />
    </template>

    <template #rail-items="{ railCollapsed, onRailSelect }">
      <WorkspaceAppBoardRailItem
        v-for="stage in filteredStages"
        :key="stage.id"
        :title="stageName(stage)"
        :count="stageCounts[stage.code] || 0"
        icon="i-lucide-layers"
        :selected="selectedStage === stage.code"
        :collapsed="railCollapsed"
        :drop-active="dropTargetId === stage.code"
        :can-drop="canTransition"
        drop-data-attr="record-stage-drop"
        :drop-value="stage.code"
        @select="onRailSelect(() => selectStage(stage.code))"
        @drag-over="onDragOver(stage.code)"
        @drag-leave="onDragLeave(stage.code)"
        @drop="onDropRecord(stage.code)"
      >
        <template #subtitle>
          <p class="mt-1 truncate text-xs app-card-text">
            {{ $t('docetra.recordStageBoard.stageHint') }}
          </p>
        </template>
      </WorkspaceAppBoardRailItem>

      <p
        v-if="!filteredStages.length && !pending && !railCollapsed"
        class="py-8 text-center text-xs text-muted"
      >
        {{ $t('docetra.states.empty') }}
      </p>
    </template>

    <WorkspaceAppBoardContent
      :view-mode="viewMode"
      :pending="pending"
      :empty="!filteredItems.length"
      empty-icon="i-lucide-file-x"
      empty-label-key="docetra.recordStageBoard.emptyRecords"
      :columns="tableColumns"
      :rows="filteredItems"
      :total="total"
      :page="page"
      :limit="limit"
      :cell-value="cellValue"
      :row-actions="tableRowActions"
      :selectable="false"
      :can-delete="canDelete"
      :show-meta="true"
      :stage-colors="stageColorMap"
      :table-error="error"
      @update:page="setPage"
      @update:limit="setLimit"
      @row-click="openRow"
      @row-action="onRowAction"
      @retry="refresh"
    >
      <RecordAppRecordBoardCard
        v-for="row in filteredItems"
        :key="String(row.id)"
        :row="row"
        :title="labelOf(row)"
        :stages="stages"
        :dragging="draggingId === row.id"
        :entity-key="cardEntityKey"
        :can-move="canTransition"
        :can-view-logs="canViewLogs"
        :can-delete="canDelete"
        @open="openRow(row)"
        @drag-start="onDragStart"
        @drag-end="onDragEnd"
        @move-stage="(stage) => onMoveStage(String(row.id), stage)"
        @logs="onLogs(row)"
        @delete="onDelete(row)"
      />
    </WorkspaceAppBoardContent>
  </WorkspaceAppWorkspaceBoardPage>
</template>
