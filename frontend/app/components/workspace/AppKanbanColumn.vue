<script setup lang="ts">
import type { WorkflowStage } from '~/types/docetra/common'

export type KanbanColumnData = {
  items: Record<string, unknown>[]
  total: number
  page: number
}

const props = withDefaults(
  defineProps<{
    stage: WorkflowStage
    column?: KanbanColumnData
    stages: WorkflowStage[]
    titleField?: string
    pending?: boolean
    draggingId?: string | null
  }>(),
  {
    column: () => ({ items: [], total: 0, page: 1 }),
    titleField: 'title',
    pending: false,
    draggingId: null,
  },
)

const emit = defineEmits<{
  cardClick: [Record<string, unknown>]
  loadMore: []
  move: [id: string, stage: string]
  dragStart: [id: string]
  dragEnd: []
  drop: [stage: string]
}>()

const isDropTarget = ref(false)

const items = computed(() => props.column?.items || [])
const total = computed(() => props.column?.total || 0)
const hasMore = computed(() => items.value.length < total.value)

function cardTitle(card: Record<string, unknown>) {
  const key = props.titleField || 'title'
  return String(card[key] || card.name || card.referenceNumber || card.id)
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  isDropTarget.value = true
}

function onDragLeave(event: DragEvent) {
  const next = event.relatedTarget as Node | null
  if (next && (event.currentTarget as HTMLElement).contains(next)) return
  isDropTarget.value = false
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  isDropTarget.value = false
  emit('drop', props.stage.code)
}

function onCardMove(id: string, stage: string) {
  emit('move', id, stage)
}
</script>

<template>
  <section
    class="flex w-72 shrink-0 flex-col rounded-lg border bg-elevated/30 transition-colors"
    :class="isDropTarget
      ? 'border-primary bg-primary/5 ring-1 ring-primary/25'
      : 'border-default'"
    :aria-label="$t(stage.labelKey)"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <header class="sticky top-0 z-1 flex shrink-0 items-center justify-between gap-2 border-b border-default bg-default/95 px-3 py-2 backdrop-blur-sm">
      <div class="flex min-w-0 items-center gap-2">
        <span
          v-if="stage.color"
          class="size-2 shrink-0 rounded-full"
          :style="{ backgroundColor: stage.color }"
        />
        <h3 class="truncate text-sm font-semibold text-highlighted">
          {{ $t(stage.labelKey) }}
        </h3>
        <UBadge color="neutral" variant="subtle" size="sm" class="tabular-nums">
          {{ total }}
        </UBadge>
      </div>
      <slot name="header-actions" />
    </header>

    <div class="flex flex-col gap-2 p-2">
      <slot
        v-for="card in items"
        :key="String(card.id)"
        name="card"
        :card="card"
        :title="cardTitle(card)"
        :stage="stage"
      >
        <WorkspaceAppKanbanCard
          :card="card"
          :title="cardTitle(card)"
          :stages="stages"
          :current-stage="stage.code"
          :dragging="draggingId === String(card.id)"
          @click="emit('cardClick', card)"
          @move="(next) => onCardMove(String(card.id), next)"
          @drag-start="emit('dragStart', $event)"
          @drag-end="emit('dragEnd')"
        />
      </slot>

      <div
        v-if="!items.length && !pending"
        class="flex flex-col items-center justify-center rounded-md border border-dashed border-default px-3 py-8 text-center"
      >
        <UIcon name="i-lucide-inbox" class="mb-2 size-5 text-muted" />
        <p class="text-xs text-muted">
          {{ $t('docetra.states.emptyColumn') }}
        </p>
      </div>

      <UButton
        v-if="hasMore"
        size="xs"
        color="neutral"
        variant="ghost"
        block
        class="shrink-0"
        @click="emit('loadMore')"
      >
        {{ $t('docetra.actions.loadMore') }}
        <span class="text-muted">({{ items.length }}/{{ total }})</span>
      </UButton>
    </div>
  </section>
</template>
