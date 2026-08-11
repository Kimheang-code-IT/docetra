<script setup lang="ts">
import type { WorkflowStage } from '~/types/docetra/common'

const props = defineProps<{
  stage: WorkflowStage
  count: number
  selected?: boolean
  dropActive?: boolean
  collapsed?: boolean
}>()

const { t, te } = useI18n()
const stageName = computed(() =>
  props.stage.label || (te(props.stage.labelKey) ? t(props.stage.labelKey) : props.stage.code),
)

const emit = defineEmits<{
  select: []
  dragOver: []
  dragLeave: []
  dropRecord: [recordId: string]
}>()

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  emit('dragOver')
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  const id = event.dataTransfer?.getData('text/plain') || ''
  if (id) emit('dropRecord', id)
}
</script>

<template>
  <UTooltip
    :text="stageName"
    :disabled="!collapsed"
    :content="{ side: 'right', sideOffset: 8 }"
  >
    <article
      :data-record-stage-drop="stage.code"
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
          ]
        : [
            'rounded-lg border p-3 text-left',
            selected
              ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
              : 'border-default bg-default hover:border-primary/35',
            dropActive ? 'border-primary bg-primary/10 ring-2 ring-primary/25' : '',
          ]"
      :aria-label="stageName"
      :aria-current="selected ? 'page' : undefined"
      @click="emit('select')"
      @keydown.enter.prevent="emit('select')"
      @dragover="onDragOver"
      @dragleave="emit('dragLeave')"
      @drop="onDrop"
    >
      <template v-if="collapsed">
        <UIcon name="i-lucide-layers" class="size-4" />
      </template>
      <template v-else>
        <div class="flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <h3 class="text-sm font-semibold text-highlighted wrap-break-word">
              {{ stageName }}
            </h3>
            <p class="mt-1 truncate text-xs text-muted">
              {{ $t('docetra.recordStageBoard.stageHint') }}
            </p>
          </div>
          <UBadge color="neutral" variant="subtle" size="sm" class="shrink-0 tabular-nums">
            {{ count }}
          </UBadge>
        </div>
        <div class="mt-2 flex flex-wrap gap-1">
          <UBadge size="sm" color="neutral" variant="subtle">
            {{ stageName }}
          </UBadge>
        </div>
      </template>
    </article>
  </UTooltip>
</template>
