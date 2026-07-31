<script setup lang="ts">
import type { WorkflowStage } from '~/types/docetra/common'

type KanbanColumnData = {
  items: Record<string, unknown>[]
  total: number
  page: number
}

defineProps<{
  stages: WorkflowStage[]
  columns: Record<string, KanbanColumnData>
  pending?: boolean
  titleField?: string
}>()

const emit = defineEmits<{
  cardClick: [Record<string, unknown>]
  loadMore: [stage: string]
  move: [id: string, stage: string]
}>()

const draggingId = ref<string | null>(null)

function onDragStart(id: string) {
  draggingId.value = id
}

function onDragEnd() {
  draggingId.value = null
}

function onDrop(stage: string) {
  if (!draggingId.value) return
  emit('move', draggingId.value, stage)
  draggingId.value = null
}
</script>

<template>
  <div class="relative w-full min-w-0">
    <div
      v-if="pending"
      class="sticky top-0 z-10 flex justify-center bg-default/40 py-16 backdrop-blur-[1px]"
    >
      <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
    </div>

    <!--
      Kanban-only: columns grow with cards; the main board host scrolls on Y
      (and X for stages). Toolbar stays fixed above this scroll area.
    -->
    <div
      class="flex items-start gap-3 pb-1"
      role="list"
      :aria-busy="pending ? 'true' : undefined"
    >
      <WorkspaceAppKanbanColumn
        v-for="stage in stages"
        :key="stage.code"
        role="listitem"
        :stage="stage"
        :stages="stages"
        :column="columns[stage.code]"
        :title-field="titleField"
        :pending="pending"
        :dragging-id="draggingId"
        @card-click="emit('cardClick', $event)"
        @load-more="emit('loadMore', stage.code)"
        @move="(id, next) => emit('move', id, next)"
        @drag-start="onDragStart"
        @drag-end="onDragEnd"
        @drop="onDrop"
      >
        <template v-if="$slots.card" #card="slotProps">
          <slot name="card" v-bind="slotProps" />
        </template>
        <template v-if="$slots['column-header-actions']" #header-actions>
          <slot name="column-header-actions" :stage="stage" />
        </template>
      </WorkspaceAppKanbanColumn>
    </div>
  </div>
</template>
