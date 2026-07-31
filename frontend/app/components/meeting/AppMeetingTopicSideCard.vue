<script setup lang="ts">
import type { MeetingTopic } from '~/types/docetra/entities'

const props = defineProps<{
  topic: MeetingTopic
  meetingCount: number
  selected?: boolean
  dropActive?: boolean
}>()

const emit = defineEmits<{
  select: []
  open: []
  dropMeeting: [meetingId: string]
  dragOver: []
  dragLeave: []
}>()

const { t, te } = useI18n()

const statusLabel = computed(() => {
  const key = `docetra.status.${props.topic.status}`
  return te(key) ? t(key) : props.topic.status
})

const stageLabel = computed(() => {
  if (!props.topic.stage) return ''
  const key = `docetra.stages.${props.topic.stage}`
  return te(key) ? t(key) : props.topic.stage
})

const menuItems = computed(() => [[
  {
    label: t('docetra.meetingBoard.openTopic'),
    icon: 'i-lucide-external-link',
    onSelect: () => emit('open'),
  },
]])

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  emit('dragOver')
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  const id = event.dataTransfer?.getData('text/plain') || ''
  if (id) emit('dropMeeting', id)
}
</script>

<template>
  <article
    role="button"
    tabindex="0"
    class="group cursor-pointer rounded-lg border p-3 text-left transition"
    :class="[
      selected
        ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
        : 'border-default bg-default hover:border-primary/35',
      dropActive ? 'border-primary bg-primary/10 ring-2 ring-primary/25' : '',
    ]"
    @click="emit('select')"
    @keydown.enter.prevent="emit('select')"
    @dblclick="emit('open')"
    @dragover="onDragOver"
    @dragleave="emit('dragLeave')"
    @drop="onDrop"
  >
    <div class="flex items-start gap-2">
      <div class="min-w-0 flex-1">
        <h3 class="text-sm font-semibold text-highlighted wrap-break-word">
          {{ topic.title }}
        </h3>
        <p class="mt-1.5 truncate text-xs text-muted">
          {{ (topic.owner as any)?.name || statusLabel }}
          <span v-if="topic.meetingDate"> · {{ topic.meetingDate }}</span>
        </p>
      </div>
      <UBadge color="neutral" variant="subtle" size="sm" class="shrink-0 tabular-nums">
        {{ meetingCount }}
      </UBadge>
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
    <div class="mt-2 flex flex-wrap gap-1">
      <UBadge v-if="topic.stage" size="sm" color="neutral" variant="subtle">
        {{ stageLabel }}
      </UBadge>
      <UBadge size="sm" color="neutral" variant="outline">
        {{ statusLabel }}
      </UBadge>
    </div>
  </article>
</template>
