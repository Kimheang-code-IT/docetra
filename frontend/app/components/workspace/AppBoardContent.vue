<script setup lang="ts">
import type { TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'
import type { BoardViewMode } from '~/composables/common/useBoardViewMode'

type DataRow = Record<string, unknown>

function getByPath(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, key) => {
    if (acc && typeof acc === 'object') return (acc as Record<string, unknown>)[key]
    return undefined
  }, obj)
}

/**
 * Right-pane body for board shells: card grid or server table,
 * shared empty / load-more chrome, optional panel drop for reorder.
 */
const props = withDefaults(defineProps<{
  viewMode: BoardViewMode
  pending?: boolean
  empty?: boolean
  emptyIcon?: string
  emptyLabelKey?: string
  hasMore?: boolean
  loadingMore?: boolean
  columns?: TableColumnDef[]
  rows?: DataRow[]
  total?: number
  page?: number
  limit?: number
  cellValue?: (row: DataRow, key: string) => string
  rowActions?: RowActionItem[] | false
  selectable?: boolean
  showMeta?: boolean
  canDelete?: boolean
  stageColors?: Record<string, string>
  tableError?: string | null
  panelDroppable?: boolean
}>(), {
  pending: false,
  empty: false,
  emptyIcon: 'i-lucide-file-x',
  emptyLabelKey: 'docetra.states.empty',
  hasMore: false,
  loadingMore: false,
  columns: () => [],
  rows: () => [],
  total: 0,
  page: 1,
  limit: 20,
  selectable: false,
  showMeta: true,
  canDelete: false,
  stageColors: () => ({}),
  tableError: null,
  panelDroppable: false,
})

const emit = defineEmits<{
  loadMore: []
  'update:page': [number]
  'update:limit': [number]
  rowClick: [DataRow]
  rowAction: [payload: { key: string, row: DataRow }]
  retry: []
  panelDrop: [DragEvent]
}>()

function defaultCellValue(row: DataRow, key: string) {
  const value = getByPath(row, key)
  if (value == null || value === '') return '—'
  return String(value)
}

const resolveCell = computed(() => props.cellValue || defaultCellValue)

function onPanelDragOver(event: DragEvent) {
  if (!props.panelDroppable) return
  event.preventDefault()
}

function onPanelDrop(event: DragEvent) {
  if (!props.panelDroppable) return
  event.preventDefault()
  emit('panelDrop', event)
}
</script>

<template>
  <div
    class="min-h-0 flex-1"
    :class="viewMode === 'cards'
      ? 'overflow-y-auto p-3'
      : 'flex flex-col overflow-hidden'"
    @dragover="onPanelDragOver"
    @drop="onPanelDrop"
  >
    <template v-if="viewMode === 'cards'">
      <CommonAppCardGrid>
        <slot />
      </CommonAppCardGrid>

      <div v-if="hasMore" class="flex justify-center py-4">
        <UButton
          :loading="loadingMore"
          color="neutral"
          variant="soft"
          icon="i-lucide-chevrons-down"
          @click="emit('loadMore')"
        >
          {{ $t('docetra.actions.loadMore') }}
        </UButton>
      </div>

      <div
        v-if="empty && !pending"
        class="flex flex-col items-center justify-center gap-2 py-16 text-center"
      >
        <UIcon :name="emptyIcon" class="size-8 text-muted" />
        <p class="text-sm text-muted">
          {{ $t(emptyLabelKey) }}
        </p>
      </div>
    </template>

    <WorkspaceAppServerTable
      v-else
      class="min-h-0 flex-1"
      :columns="columns"
      :rows="rows"
      :total="total"
      :page="page"
      :limit="limit"
      :pending="pending"
      :error="tableError"
      :cell-value="resolveCell"
      :can-delete="canDelete"
      :selectable="selectable"
      :show-meta="showMeta"
      :stage-colors="stageColors"
      :row-actions="rowActions"
      @update:page="emit('update:page', $event)"
      @update:limit="emit('update:limit', $event)"
      @row-click="emit('rowClick', $event)"
      @row-action="emit('rowAction', $event)"
      @retry="emit('retry')"
    />

    <div v-if="viewMode === 'table' && hasMore" class="flex justify-center py-4">
      <UButton
        :loading="loadingMore"
        color="neutral"
        variant="soft"
        icon="i-lucide-chevrons-down"
        @click="emit('loadMore')"
      >
        {{ $t('docetra.actions.loadMore') }}
      </UButton>
    </div>
  </div>
</template>
