<script setup lang="ts">
/**
 * Shared left-rail list item for stages, topics, log tabs, etc.
 * Collapsed = initial letter; expanded = title (count) + optional slots.
 */
const props = withDefaults(defineProps<{
  title: string
  count?: number
  /** Kept for call-site compatibility; icons are not rendered. */
  icon?: string
  selected?: boolean
  collapsed?: boolean
  dropActive?: boolean
  canDrop?: boolean
  disabled?: boolean
  /** Kept for call-site compatibility; count always renders as "Title (n)". */
  countStyle?: 'highlight' | 'badge'
  dropDataAttr?: 'record-stage-drop' | 'meeting-topic-drop'
  dropValue?: string
}>(), {
  count: undefined,
  selected: false,
  collapsed: false,
  dropActive: false,
  canDrop: false,
  disabled: false,
  countStyle: 'highlight',
})

const emit = defineEmits<{
  select: []
  open: []
  dragOver: []
  dragLeave: []
  drop: [id: string]
}>()

const titleInitial = computed(() => {
  const text = props.title.trim()
  return text ? text.charAt(0).toUpperCase() : '—'
})

const ariaLabel = computed(() =>
  props.count != null ? `${props.title} (${props.count})` : props.title,
)

function onDragOver(event: DragEvent) {
  if (!props.canDrop || props.disabled) return
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.dropEffect = 'move'
  }
  emit('dragOver')
}

function onDrop(event: DragEvent) {
  if (!props.canDrop || props.disabled) return
  event.preventDefault()
  const id = event.dataTransfer?.getData('text/plain') || ''
  if (id) emit('drop', id)
}
</script>

<template>
  <UTooltip
    :text="ariaLabel"
    :disabled="!collapsed"
    :content="{ side: 'right', sideOffset: 8 }"
  >
    <article
      role="button"
      tabindex="0"
      class="group cursor-pointer transition"
      :class="collapsed
        ? [
            'flex justify-center rounded-md p-2',
            selected
              ? 'bg-primary/10 text-primary ring-1 ring-primary/30'
              : 'text-muted hover:bg-elevated hover:text-highlighted',
            dropActive ? 'bg-primary/15 ring-2 ring-primary/25' : '',
            disabled ? 'opacity-55' : '',
          ]
        : [
            'rounded-lg border p-3 text-left',
            selected
              ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
              : 'border-default bg-default hover:border-primary/35',
            dropActive ? 'border-primary bg-primary/10 ring-2 ring-primary/25' : '',
            disabled ? 'opacity-60' : '',
          ]"
      :aria-label="ariaLabel"
      :aria-current="selected ? 'page' : undefined"
      :data-record-stage-drop="canDrop && dropDataAttr === 'record-stage-drop' ? dropValue : undefined"
      :data-meeting-topic-drop="canDrop && dropDataAttr === 'meeting-topic-drop' ? dropValue : undefined"
      @click="emit('select')"
      @keydown.enter.prevent="emit('select')"
      @dblclick="emit('open')"
      @dragover="onDragOver"
      @dragleave="emit('dragLeave')"
      @drop="onDrop"
    >
      <span
        v-if="collapsed"
        class="text-xs font-semibold tabular-nums"
      >
        {{ titleInitial }}
      </span>
      <template v-else>
        <div class="flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <h3
              class="text-sm font-semibold wrap-break-word"
              :class="disabled ? 'text-muted' : 'text-highlighted'"
            >
              {{ title }}
              <span
                v-if="count != null"
                class="font-medium tabular-nums text-muted"
              >
                ({{ count }})
              </span>
            </h3>
            <slot name="subtitle" />
          </div>
          <slot name="actions" />
        </div>
        <slot name="body" />
      </template>
    </article>
  </UTooltip>
</template>
