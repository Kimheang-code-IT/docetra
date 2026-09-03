<script setup lang="ts">
/**
 * Compact rail pill for All / Unassigned / similar filter buttons.
 * Supports collapsed icon-rail and optional drop targets.
 */
const props = withDefaults(defineProps<{
  label: string
  count?: number
  icon?: string
  selected?: boolean
  collapsed?: boolean
  dropActive?: boolean
  droppable?: boolean
  /** Sets data-record-stage-drop or data-meeting-topic-drop for pointer drop. */
  dropDataAttr?: 'record-stage-drop' | 'meeting-topic-drop'
  dropValue?: string
  /** When false, pills share a row (meeting All + Unassigned). */
  stacked?: boolean
}>(), {
  count: undefined,
  icon: 'i-lucide-layout-grid',
  selected: false,
  collapsed: false,
  dropActive: false,
  droppable: false,
  stacked: true,
})

const emit = defineEmits<{
  select: []
  dragOver: []
  dragLeave: []
  drop: [id: string]
}>()

function onDragOver(event: DragEvent) {
  if (!props.droppable) return
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  emit('dragOver')
}

function onDrop(event: DragEvent) {
  if (!props.droppable) return
  event.preventDefault()
  const id = event.dataTransfer?.getData('text/plain') || ''
  if (id) emit('drop', id)
}

const expandedSelected = computed(() =>
  props.selected
    ? 'border-primary bg-primary/5 font-medium text-highlighted ring-1 ring-primary/25'
    : 'border-default text-muted hover:border-primary/30',
)

const collapsedSelected = computed(() =>
  props.selected
    ? 'bg-primary/10 text-primary ring-1 ring-primary/30'
    : 'text-muted hover:bg-elevated hover:text-highlighted',
)
</script>

<template>
  <UTooltip
    :text="label"
    :disabled="!collapsed"
    :content="{ side: 'right', sideOffset: 8 }"
  >
    <button
      type="button"
      class="w-full transition"
      :class="[
        collapsed
          ? ['flex items-center justify-center rounded-md p-2', collapsedSelected]
          : [
              'inline-flex min-w-0 items-center gap-1 whitespace-nowrap rounded-lg border px-2.5 py-2 text-sm',
              stacked ? 'justify-start text-left px-3' : 'justify-center',
              expandedSelected,
            ],
        dropActive ? 'ring-2 ring-primary/40' : '',
      ]"
      :aria-label="label"
      :aria-current="selected ? 'page' : undefined"
      :data-record-stage-drop="dropDataAttr === 'record-stage-drop' ? dropValue : undefined"
      :data-meeting-topic-drop="dropDataAttr === 'meeting-topic-drop' ? dropValue : undefined"
      @click="emit('select')"
      @dragover="onDragOver"
      @dragleave="emit('dragLeave')"
      @drop="onDrop"
    >
      <UIcon v-if="collapsed" :name="icon" class="size-4 shrink-0" />
      <template v-else>
        <span class="min-w-0 truncate">{{ label }}</span>
        <span v-if="count != null" class="shrink-0 tabular-nums text-xs">({{ count }})</span>
      </template>
    </button>
  </UTooltip>
</template>
