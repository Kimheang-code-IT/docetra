<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import type { EntityConfig } from '~/config/entities'
import { getEntityAdapter } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import { useRecordStageBoard } from '~/composables/record/useRecordStageBoard'
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import { consumeListStale } from '~/utils/workspace-list-stale'
import { permissionForAction } from '~/utils/role/access'

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
const adapter = getEntityAdapter(props.config.key)
const cardEntityKey = computed(() => props.config.key as CardDisplayEntityKey)
const mobileStagesOpen = ref(false)
const isSmallScreen = useMediaQuery('(max-width: 1023px)')

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
  toggleLeftPanel,
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

const stagePanelCollapsed = computed(() =>
  isSmallScreen.value ? false : leftCollapsed.value,
)
const showStageDetails = computed(() => !stagePanelCollapsed.value)
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
    path: '/records/record-logs',
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
    if (adapter.delete) await adapter.delete(id)
    else if (adapter.deleteMany) await adapter.deleteMany([id])
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
    <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default">
      <div
        v-if="pending && !filteredItems.length"
        class="absolute inset-0 z-10 flex items-center justify-center bg-default/50"
      >
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <UAlert
        v-if="error"
        class="m-3"
        color="error"
        :title="error"
        :actions="[{ label: $t('docetra.actions.retry'), onClick: refresh }]"
      />

      <UAlert
        v-if="stageConfigurationError"
        class="m-3 mb-0"
        color="warning"
        :title="$t('docetra.recordStageBoard.usingFallbackStages')"
        :description="stageConfigurationError"
        :actions="[{ label: $t('docetra.actions.retry'), onClick: reloadStageConfiguration }]"
      />

      <div class="relative flex min-h-0 flex-1 flex-row overflow-hidden">
        <button
          v-if="isSmallScreen && mobileStagesOpen"
          type="button"
          class="absolute inset-0 z-20 bg-black/25 lg:hidden"
          :aria-label="$t('actions.close')"
          @click="mobileStagesOpen = false"
        />

        <!-- Left: stages — overlay drawer on small screens (no icon rail); collapsible rail on lg+ -->
        <aside
          class="flex h-full min-h-0 shrink-0 flex-col overflow-hidden border-e border-default bg-default transition-[width] duration-200 lg:static lg:z-auto lg:shadow-none"
          :class="isSmallScreen
            ? (mobileStagesOpen
                ? 'absolute inset-y-0 inset-s-0 z-30 w-[min(22rem,calc(100%-3rem))] shadow-xl'
                : 'hidden')
            : ''"
          :style="isSmallScreen
            ? undefined
            : { width: stagePanelCollapsed ? '3.5rem' : 'min(22rem, calc(100% - 3rem))' }"
        >
          <div
            class="shrink-0 space-y-2 border-b border-default"
            :class="showStageDetails ? 'px-3 py-2.5' : 'px-1.5 py-3.5'"
          >
            <div v-if="showStageDetails" class="flex items-center justify-between gap-2">
              <h2 class="min-w-0 truncate text-sm font-semibold text-highlighted">
                {{ $t('docetra.recordStageBoard.stagesTitle') }}
              </h2>
              <UButton
                icon="i-lucide-panel-left-close"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                class="shrink-0 lg:hidden"
                :aria-label="$t('actions.close')"
                @click="mobileStagesOpen = false"
              />
            </div>
            <div v-else class="flex justify-center">
              <UIcon name="i-lucide-layers" class="size-4 text-muted" />
            </div>

            <CommonAppLiveSearch
              v-if="showStageDetails"
              v-model="stageSearch"
              class="w-full"
              :placeholder="$t('docetra.recordStageBoard.searchStages')"
            />

            <UTooltip
              :text="$t('docetra.recordStageBoard.allRecords')"
              :disabled="showStageDetails"
              :content="{ side: 'right', sideOffset: 8 }"
            >
              <button
                type="button"
                class="w-full transition"
                :class="!showStageDetails
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
                <template v-if="!showStageDetails">
                  <UIcon name="i-lucide-layout-grid" class="size-4" />
                </template>
                <template v-else>
                  {{ $t('docetra.recordStageBoard.allRecords') }}
                  <span class="ml-1 tabular-nums text-xs">({{ allCount }})</span>
                </template>
              </button>
            </UTooltip>
          </div>

          <div
            class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden"
            :class="showStageDetails ? 'space-y-2 p-3' : 'space-y-1 p-1.5'"
          >
            <RecordAppRecordStageSideCard
              v-for="stage in filteredStages"
              :key="stage.id"
              :stage="stage"
              :count="stageCounts[stage.code] || 0"
              :selected="selectedStage === stage.code"
              :collapsed="!showStageDetails"
              :drop-active="dropStageCode === stage.code"
              @select="selectStageFromPanel(stage.code)"
              @drag-over="dropStageCode = stage.code"
              @drag-leave="dropStageCode = dropStageCode === stage.code ? null : dropStageCode"
              @drop-record="(id) => onDropRecord(stage.code, id)"
            />

            <p
              v-if="!filteredStages.length && !pending && showStageDetails"
              class="py-8 text-center text-xs text-muted"
            >
              {{ $t('docetra.states.empty') }}
            </p>
          </div>
        </aside>

        <!-- Right: record cards -->
        <section class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div class="flex shrink-0 items-center gap-2 border-b border-default px-3 py-2.5 sm:px-4 sm:py-3.5">
            <div class="flex min-w-0 shrink-0 items-center gap-1.5">
              <UButton
                :icon="mobileStagesOpen ? 'i-lucide-panel-left-close' : 'i-lucide-panel-left-open'"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                class="shrink-0 lg:hidden"
                :aria-label="$t('docetra.recordStageBoard.stagesTitle')"
                :aria-expanded="mobileStagesOpen"
                @click="mobileStagesOpen = !mobileStagesOpen"
              />
              <UButton
                :icon="leftCollapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                class="hidden shrink-0 lg:inline-flex"
                :aria-label="leftCollapsed
                  ? $t('docetra.recordStageBoard.expandStages')
                  : $t('docetra.recordStageBoard.collapseStages')"
                :aria-expanded="!leftCollapsed"
                @click="toggleLeftPanel"
              />
              <h2 class="hidden min-w-0 max-w-40 truncate text-sm font-semibold text-highlighted sm:block">
                {{ selectedStageMeta
                  ? stageLabel(selectedStageMeta.code)
                  : $t('docetra.recordStageBoard.allRecords') }}
              </h2>
            </div>

            <CommonAppLiveSearch
              v-model="recordSearch"
              class="min-w-0 w-full max-w-75 flex-1"
              :placeholder="$t('docetra.recordStageBoard.searchRecords')"
            />
            <CommonAppDateRangeFilter
              v-model:start="dateStart"
              v-model:end="dateEnd"
              class="ms-auto shrink-0"
              size="sm"
            />
          </div>

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
        </section>
      </div>
    </div>
  </WorkspaceAppWorkspacePage>
</template>
