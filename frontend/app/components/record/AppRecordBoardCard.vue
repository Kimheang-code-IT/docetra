<script setup lang="ts">
import type { WorkflowStage } from '~/types/docetra/common'

const props = defineProps<{
  row: Record<string, unknown>
  title: string
  subtitle?: string
  date?: string
  statusLabel?: string
  stageLabel?: string
  stages: WorkflowStage[]
  dragging?: boolean
}>()

const emit = defineEmits<{
  open: []
  dragStart: [id: string]
  dragEnd: []
  moveStage: [stage: string]
  logs: []
  delete: []
}>()

const { t } = useI18n()

const menuItems = computed(() => [
  [{
    label: t('docetra.rowActions.detail'),
    icon: 'i-lucide-eye',
    onSelect: () => emit('open'),
  }, {
    label: t('docetra.rowActions.logs'),
    icon: 'i-lucide-scroll-text',
    onSelect: () => emit('logs'),
  }],
  [{
    label: t('docetra.recordStageBoard.moveToStage'),
    icon: 'i-lucide-layers',
    children: props.stages.map(stage => ({
      label: t(stage.labelKey),
      icon: String(props.row.stage) === stage.code ? 'i-lucide-check' : 'i-lucide-circle',
      onSelect: () => emit('moveStage', stage.code),
    })),
  }],
  [{
    label: t('docetra.rowActions.delete'),
    icon: 'i-lucide-trash-2',
    color: 'error' as const,
    onSelect: () => emit('delete'),
  }],
])

function onDragStart(event: DragEvent) {
  const id = String(props.row.id || '')
  event.dataTransfer?.setData('text/plain', id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
  emit('dragStart', id)
}
</script>

<template>
  <article
    draggable="true"
    class="group relative cursor-grab rounded-lg border border-default bg-default p-3 text-left shadow-xs transition active:cursor-grabbing"
    :class="dragging ? 'opacity-40 ring-2 ring-primary/30' : 'hover:border-primary/35 hover:shadow-sm'"
    tabindex="0"
    role="button"
    @dragstart="onDragStart"
    @dragend="emit('dragEnd')"
    @click="emit('open')"
    @keydown.enter.prevent="emit('open')"
  >
    <div class="flex items-start gap-2">
      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold text-highlighted wrap-break-word">
          {{ title }}
        </p>
        <p v-if="subtitle" class="mt-1 truncate text-xs text-muted">
          {{ subtitle }}
        </p>
      </div>
      <UDropdownMenu :items="menuItems" :content="{ align: 'end' }">
        <UButton
          icon="i-lucide-ellipsis"
          color="neutral"
          variant="ghost"
          size="xs"
          class="shrink-0 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100"
          :aria-label="$t('docetra.actions.more')"
          @click.stop
        />
      </UDropdownMenu>
    </div>

    <div class="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted">
      <span v-if="date" class="inline-flex items-center gap-1">
        <UIcon name="i-lucide-calendar" class="size-3" />
        {{ date }}
      </span>
      <span
        v-if="row.referenceNumber"
        class="inline-flex items-center gap-1"
      >
        <UIcon name="i-lucide-hash" class="size-3" />
        {{ row.referenceNumber }}
      </span>
      <UBadge v-if="statusLabel" size="sm" color="neutral" variant="subtle">
        {{ statusLabel }}
      </UBadge>
      <UBadge v-if="stageLabel" size="sm" color="neutral" variant="outline">
        {{ stageLabel }}
      </UBadge>
    </div>
  </article>
</template>
