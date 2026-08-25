<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import type { EntityConfig } from '~/config/entities'
import { getAdapterForConfig } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import { useRecordStageBoard } from '~/composables/record/useRecordStageBoard'
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import { consumeListStale } from '~/utils/workspace-list-stale'
import { permissionForAction } from '~/utils/role/access'
import { concurrencyVersion, versionsById } from '~/utils/api/concurrency'

const props = defineProps<{
  config: EntityConfig
  dateField: string
  subtitleField?: string
  stateKey?: string
}>()

const toast = useToast()
const { t } = useI18n()
const { confirm } = useConfirm()
const auth = useAuthStore()
const adapter = getAdapterForConfig(props.config)
const cardEntityKey = computed(() => props.config.key as CardDisplayEntityKey)
const mobileStagesOpen = ref(false)
const isSmallScreen = useMediaQuery('(max-width: 1023px)')
/** Mirrors BoardShell's desktop icon-rail state for pill/item rendering. */
const railCollapsedProxy = computed(() =>
  isSmallScreen.value ? false : leftCollapsed.value,
)

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
  selectedStageMeta,
  filteredItems,
  stageCounts,
  allCount,
  pending,
  loadingMore,
  hasMore,
  error,
  draggingId,
  dropStageCode,
  refresh,
  loadMore,
  selectStage,
  openCreate,
  openRow,
  moveToStage,
  labelOf,
  statusLabel,
  stageLabel,
  stages,
  stageConfigurationError,
  reloadStageConfiguration,
} = useRecordStageBoard(props.config, {
  dateField: props.dateField,
  subtitleField: props.subtitleField,
  stateKey: props.stateKey,
})

function selectStageFromPanel(code: string | null) {
  selectStage(code)
  if (isSmallScreen.value) mobileStagesOpen.value = false
}

onMounted(() => {
  // Always reload when entering the board (including return from /new).
  consumeListStale(props.config.key)
  void refresh()
})

onActivated(() => {
  if (consumeListStale(props.config.key)) void refresh()
})

async function onDropRecord(stageCode: string, id: string) {
  if (!canTransition.value) return
  dropStageCode.value = null
  draggingId.value = null
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
</script>

<template>
  <WorkspaceAppWorkspacePage
    :title-key="config.titleKey"
    :description-key="config.descriptionKey"
    :icon="config.icon"
    :can-create="canCreate"
    :refreshing="pending"
    @create="openCreate"
    @refresh="refresh"
  >
    <WorkspaceAppBoardShell
      v-model:collapsed="leftCollapsed"
      v-model:mobile-open="mobileStagesOpen"
      v-model:rail-search="stageSearch"
      v-model:header-search="recordSearch"
      v-model:date-start="dateStart"
      v-model:date-end="dateEnd"
      rail-title-key="docetra.recordStageBoard.stagesTitle"
      rail-icon="i-lucide-layers"
      expand-label-key="docetra.recordStageBoard.expandStages"
      collapse-label-key="docetra.recordStageBoard.collapseStages"
      rail-search-placeholder-key="docetra.recordStageBoard.searchStages"
      header-search-placeholder-key="docetra.recordStageBoard.searchRecords"
      :header-title="selectedStageMeta
        ? stageLabel(selectedStageMeta.code)
        : $t('docetra.recordStageBoard.allRecords')"
      :pending="pending"
      :show-pending-overlay="pending && !filteredItems.length"
      :error="error || undefined"
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

      <template #rail-pills>
        <UTooltip
          :text="$t('docetra.recordStageBoard.allRecords')"
          :disabled="!railCollapsedProxy"
          :content="{ side: 'right', sideOffset: 8 }"
        >
          <button
            type="button"
            class="w-full transition"
            :class="!railCollapsedProxy
              ? [
                  'flex justify-center rounded-md p-2',
                  selectedStage == null
                    ? 'bg-primary/10 text-primary ring-1 ring-primary/30'
                    : 'text-muted hover:bg-elevated hover:text-highlighted',
                ]
              : [
                  'rounded-lg border px-3 py-2 text-left text-sm',
                  selectedStage == null
                    ? 'border-primary bg-primary/5 font-medium text-highlighted ring-1 ring-primary/25'
                    : 'border-default text-muted hover:border-primary/30',
                ]"
            :aria-label="$t('docetra.recordStageBoard.allRecords')"
            @click="selectStageFromPanel(null)"
          >
            <template v-if="!railCollapsedProxy">
              <UIcon name="i-lucide-layout-grid" class="size-4" />
            </template>
            <template v-else>
              {{ $t('docetra.recordStageBoard.allRecords') }}
              <span class="ml-1 tabular-nums text-xs">({{ allCount }})</span>
            </template>
          </button>
        </UTooltip>
      </template>

      <template #rail-items>
        <RecordAppRecordStageSideCard
          v-for="stage in filteredStages"
          :key="stage.id"
          :stage="stage"
          :count="stageCounts[stage.code] || 0"
          :selected="selectedStage === stage.code"
          :collapsed="railCollapsedProxy"
          :drop-active="dropStageCode === stage.code"
          @select="selectStageFromPanel(stage.code)"
          @drag-over="dropStageCode = stage.code"
          @drag-leave="dropStageCode = dropStageCode === stage.code ? null : dropStageCode"
          @drop-record="(id) => onDropRecord(stage.code, id)"
        />

        <p
          v-if="!filteredStages.length && !pending && !railCollapsedProxy"
          class="py-8 text-center text-xs text-muted"
        >
          {{ $t('docetra.states.empty') }}
        </p>
      </template>

      <div class="min-h-0 flex-1 overflow-y-auto p-3">
        <div
          class="grid items-stretch gap-2"
          style="grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));"
        >
          <RecordAppRecordBoardCard
            v-for="row in filteredItems"
            :key="String(row.id)"
            :row="row"
            :title="labelOf(row)"
            :status-label="statusLabel(row.status)"
            :stage-label="stageLabel(row.stage)"
            :stages="stages"
            :dragging="draggingId === row.id"
            :entity-key="cardEntityKey"
            :can-move="canTransition"
            :can-view-logs="canViewLogs"
            :can-delete="canDelete"
            @open="openRow(row)"
            @drag-start="draggingId = $event"
            @drag-end="draggingId = null; dropStageCode = null"
            @move-stage="(stage) => onMoveStage(String(row.id), stage)"
            @logs="onLogs(row)"
            @delete="onDelete(row)"
          />
        </div>

        <div v-if="hasMore" class="flex justify-center py-4">
          <UButton
            :loading="loadingMore"
            color="neutral"
            variant="soft"
            icon="i-lucide-chevrons-down"
            @click="loadMore"
          >
            {{ $t('docetra.actions.loadMore') }}
          </UButton>
        </div>

        <div
          v-if="!filteredItems.length && !pending"
          class="flex flex-col items-center justify-center gap-2 py-16 text-center"
        >
          <UIcon name="i-lucide-file-x" class="size-8 text-muted" />
          <p class="text-sm text-muted">
            {{ $t('docetra.recordStageBoard.emptyRecords') }}
          </p>
        </div>
      </div>
    </WorkspaceAppBoardShell>
  </WorkspaceAppWorkspacePage>
</template>
