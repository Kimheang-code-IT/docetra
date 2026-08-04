<script setup lang="ts">
import type { MeetingHistory, MeetingTopic } from '~/types/docetra/entities'

const props = defineProps<{
  meeting: MeetingHistory
  topics: MeetingTopic[]
  dragging?: boolean
  showTopic?: boolean
}>()

const emit = defineEmits<{
  open: []
  openNotes: []
  dragStart: [id: string]
  dragEnd: []
  assign: [topicId: string | null]
  reorderBefore: [beforeId: string | null]
}>()

const { t, te } = useI18n()

const statusLabel = computed(() => {
  const key = `docetra.status.${props.meeting.status}`
  return te(key) ? t(key) : props.meeting.status
})

const assignItems = computed(() => {
  const topicItems = props.topics.map(topic => ({
    label: topic.title,
    icon: topic.id === props.meeting.topicId ? 'i-lucide-check' : 'i-lucide-messages-square',
    onSelect: () => emit('assign', topic.id),
  }))
  return [
    [{
      label: t('docetra.meetingBoard.openMeeting'),
      icon: 'i-lucide-external-link',
      onSelect: () => emit('open'),
    }, {
      label: t('docetra.meetingBoard.openNotes'),
      icon: 'i-lucide-notebook-pen',
      onSelect: () => emit('openNotes'),
    }],
    [
      {
        label: t('docetra.meetingBoard.assignToTopic'),
        icon: 'i-lucide-link',
        children: topicItems.length
          ? topicItems
          : [{ label: t('docetra.states.empty'), disabled: true }],
      },
      {
        label: t('docetra.meetingBoard.unassignFromTopic'),
        icon: 'i-lucide-unlink',
        disabled: !props.meeting.topicId,
        onSelect: () => emit('assign', null),
      },
    ],
  ]
})

function onDragStart(event: DragEvent) {
  event.dataTransfer?.setData('text/plain', props.meeting.id)
  event.dataTransfer?.setData('application/x-meeting-id', props.meeting.id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
  emit('dragStart', props.meeting.id)
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  event.stopPropagation()
  const id = event.dataTransfer?.getData('text/plain') || ''
  if (!id || id === props.meeting.id) return
  emit('reorderBefore', props.meeting.id)
}
</script>

<template>
  <article
    draggable="true"
    class="group relative cursor-grab rounded-lg border border-default bg-default p-3 text-left shadow-xs transition active:cursor-grabbing"
    :class="dragging ? 'opacity-40 ring-2 ring-primary/30' : 'hover:border-primary/35 hover:shadow-sm'"
    @dragstart="onDragStart"
    @dragend="emit('dragEnd')"
    @dragover="onDragOver"
    @drop="onDrop"
    @click="emit('open')"
    @keydown.enter.prevent="emit('open')"
    tabindex="0"
    role="button"
  >
    <div class="flex items-start gap-2">
      <div class="min-w-0 flex-1">
        <p class="text-sm font-semibold text-highlighted wrap-break-word">
          {{ meeting.title }}
        </p>
        <p v-if="showTopic" class="mt-1 truncate text-xs text-muted">
          {{ meeting.topicTitle || $t('docetra.meetingBoard.unassigned') }}
        </p>
      </div>
      <UDropdownMenu :items="assignItems" :content="{ align: 'end' }">
        <UButton
          icon="i-lucide-ellipsis"
          color="neutral"
          variant="ghost"
          size="xs"
          class="shrink-0"
          :aria-label="$t('docetra.actions.more')"
          @click.stop
        />
      </UDropdownMenu>
    </div>

    <div
      v-if="statusLabel || meeting.sortOrder != null"
      class="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted"
    >
      <UBadge size="sm" color="neutral" variant="subtle">{{ statusLabel }}</UBadge>
      <span v-if="meeting.sortOrder != null" class="tabular-nums text-[11px]">
        #{{ meeting.sortOrder + 1 }}
      </span>
    </div>

    <div
      v-if="meeting.meetingDate || meeting.location"
      class="mt-2 flex items-center justify-between gap-2 border-t border-default pt-2 text-xs text-muted"
    >
      <span v-if="meeting.meetingDate" class="inline-flex min-w-0 items-center gap-1 truncate">
        <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
        <span class="truncate">{{ meeting.meetingDate }}</span>
      </span>
      <span v-else />
      <span v-if="meeting.location" class="inline-flex min-w-0 items-center gap-1 truncate">
        <UIcon name="i-lucide-map-pin" class="size-3 shrink-0" />
        <span class="truncate">{{ meeting.location }}</span>
      </span>
    </div>
  </article>
</template>
