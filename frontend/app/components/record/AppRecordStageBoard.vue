<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'
import { getEntityAdapter } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import { useRecordStageBoard } from '~/composables/record/useRecordStageBoard'
import type { CardDisplayEntityKey } from '~/types/docetra/settings'

const props = defineProps<{
  config: EntityConfig
  dateField: string
  subtitleField?: string
  stateKey?: string
}>()

const toast = useToast()
const { t } = useI18n()
const { confirm } = useConfirm()
const adapter = getEntityAdapter(props.config.key)
const cardEntityKey = computed(() => props.config.key as CardDisplayEntityKey)
const mobileStagesOpen = ref(false)

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
  error,
  draggingId,
  dropStageCode,
  refresh,
  selectStage,
  toggleLeftPanel,
  openCreate,
  openRow,
  moveToStage,
  labelOf,
  statusLabel,
  stageLabel,
  stages,
} = useRecordStageBoard(props.config, {
  dateField: props.dateField,
  subtitleField: props.subtitleField,
  stateKey: props.stateKey,
})

const showStageDetails = computed(() => mobileStagesOpen.value || !leftCollapsed.value)
const hasDateFilter = computed(() => Boolean(dateStart.value.trim() || dateEnd.value.trim()))

function selectStageFromPanel(code: string | null) {
  selectStage(code)
  mobileStagesOpen.value = false
}

onMounted(() => {
  refresh()
})

async function onDropRecord(stageCode: string, id: string) {
  dropStageCode.value = null
  draggingId.value = null
  try {
    await moveToStage(id, stageCode)
    toast.add({
      title: t('docetra.recordStageBoard.moved', { stage: t(stages.value.find(s => s.code === stageCode)?.labelKey || stageCode) }),
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
  try {
    await moveToStage(id, stageCode)
    toast.add({
      title: t('docetra.recordStageBoard.moved', { stage: t(stages.value.find(s => s.code === stageCode)?.labelKey || stageCode) }),
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
  const id = String(row.id || '')
  navigateTo({
    path: '/records/record-logs',
    query: id ? { q: id } : undefined,
  })
}

async function onDelete(row: Record<string, unknown>) {
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
    :can-create="config.canCreate !== false && !config.readOnly"
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

      <div class="flex min-h-0 flex-1 flex-row overflow-hidden">
        <button
          v-if="mobileStagesOpen"
          type="button"
          class="absolute inset-0 z-20 bg-black/25 lg:hidden"
          :aria-label="$t('actions.close')"
          @click="mobileStagesOpen = false"
        />

        <!-- Left: stages (topic-style) -->
        <aside
          class="absolute inset-y-0 start-0 z-30 flex h-full min-h-0 w-[min(22rem,calc(100%-3rem))] shrink-0 flex-col overflow-hidden border-e border-default bg-default shadow-xl transition-all duration-200 lg:static lg:z-auto lg:translate-x-0 lg:shadow-none"
          :class="[
            mobileStagesOpen ? 'translate-x-0' : '-translate-x-full rtl:translate-x-full',
            leftCollapsed ? 'lg:w-14' : 'lg:w-[22rem]',
          ]"
        >
          <div
            class="shrink-0 space-y-2 border-b border-default"
            :class="showStageDetails ? 'px-3 py-2.5' : 'px-1.5 py-3.5'"
          >
            <h2
              v-if="showStageDetails"
              class="text-sm font-semibold text-highlighted"
            >
              {{ $t('docetra.recordStageBoard.stagesTitle') }}
            </h2>
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
            <div class="flex min-w-0 flex-1 items-center gap-1.5">
              <UButton
                icon="i-lucide-menu"
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
              <h2 class="min-w-0 truncate text-sm font-semibold text-highlighted">
                {{ selectedStageMeta
                  ? $t(selectedStageMeta.labelKey)
                  : $t('docetra.recordStageBoard.allRecords') }}
              </h2>
            </div>

            <div class="hidden shrink-0 items-center gap-2 lg:flex">
              <CommonAppInputDateRange
                v-model:start="dateStart"
                v-model:end="dateEnd"
                size="sm"
              />
            </div>
            <UPopover class="shrink-0 lg:hidden">
              <UButton
                icon="i-lucide-filter"
                :color="hasDateFilter ? 'primary' : 'neutral'"
                :variant="hasDateFilter ? 'soft' : 'ghost'"
                size="sm"
                square
                :aria-label="$t('docetra.actions.filter')"
              />
              <template #content>
                <div class="max-w-[calc(100vw-2rem)] p-3">
                  <CommonAppInputDateRange
                    v-model:start="dateStart"
                    v-model:end="dateEnd"
                    size="sm"
                  />
                </div>
              </template>
            </UPopover>
            <CommonAppLiveSearch
              v-model="recordSearch"
              class="min-w-0 w-28 shrink sm:w-56"
              :placeholder="$t('docetra.recordStageBoard.searchRecords')"
            />
          </div>

          <div class="min-h-0 flex-1 overflow-y-auto p-3">
            <div class="grid grid-cols-1 items-stretch gap-2 sm:grid-cols-2 xl:grid-cols-3">
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
                @open="openRow(row)"
                @drag-start="draggingId = $event"
                @drag-end="draggingId = null; dropStageCode = null"
                @move-stage="(stage) => onMoveStage(String(row.id), stage)"
                @logs="onLogs(row)"
                @delete="onDelete(row)"
              />
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
