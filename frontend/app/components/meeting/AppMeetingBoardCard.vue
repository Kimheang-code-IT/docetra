<script setup lang="ts">
import type { MeetingHistory, MeetingTopic } from '~/types/docetra/entities'
import { useCardFields } from '~/composables/settings/useCardFields'
import { splitCardSlots } from '~/utils/card-fields'

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
const { show, visibleSlots, footerAlign } = useCardFields('meetingHistory')

const statusLabel = computed(() => {
  const key = `docetra.status.${props.meeting.status}`
  return te(key) ? t(key) : props.meeting.status
})

const stageLabel = computed(() => {
  if (!props.meeting.stage) return ''
  const key = `docetra.stages.${props.meeting.stage}`
  return te(key) ? t(key) : props.meeting.stage
})

const notesSnippet = computed(() => {
  const html = String(props.meeting.notes || props.meeting.recordContent || '')
  const raw = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
  if (!raw) return ''
  return raw.length > 80 ? `${raw.slice(0, 80)}…` : raw
})

const tags = computed(() => {
  if (Array.isArray(props.meeting.tags) && props.meeting.tags.length) {
    return props.meeting.tags.map(String).filter(Boolean)
  }
  const raw = props.meeting.recordTag
  if (typeof raw === 'string' && raw.trim()) {
    return raw.split(/[,;]/).map(s => s.trim()).filter(Boolean)
  }
  return []
})

const recordTimeLabel = computed(() =>
  day(props.meeting.recordTime) || day(props.meeting.meetingDate),
)

const orderedSlots = computed(() => {
  return visibleSlots.value.filter((slot) => {
    if (slot === 'topicTitle') return Boolean(props.showTopic)
    if (slot === 'status') return Boolean(statusLabel.value)
    if (slot === 'sortOrder') return props.meeting.sortOrder != null
    if (slot === 'stage') return Boolean(stageLabel.value)
    if (slot === 'tags') return tags.value.length > 0
    if (slot === 'meetingDate') return Boolean(props.meeting.meetingDate)
    if (slot === 'recordTime') return Boolean(recordTimeLabel.value)
    if (slot === 'location') return Boolean(props.meeting.location)
    if (slot === 'attendeesCount') return props.meeting.attendeesCount != null
    if (slot === 'notes') return Boolean(notesSnippet.value)
    if (slot === 'createdAt') return Boolean(props.meeting.createdAt)
    if (slot === 'updatedAt') return Boolean(props.meeting.updatedAt)
    return show(slot)
  })
})

const split = computed(() => splitCardSlots('meetingHistory', orderedSlots.value))
const showSortOrder = computed(() => split.value.titleChrome.includes('sortOrder'))
const showStatus = computed(() => split.value.titleChrome.includes('status'))
const bodySlots = computed(() => {
  let slots = split.value.body
  // One status chrome on title — do not also show stage as a second badge
  if (showStatus.value) {
    slots = slots.filter(s => s !== 'stage')
  }
  return slots
})
const footerSlots = computed(() => {
  const slots = split.value.footer
  // Prefer meetingDate when both time slots are enabled
  if (slots.includes('meetingDate') && slots.includes('recordTime')) {
    return slots.filter(s => s !== 'recordTime')
  }
  return slots
})

const footerLeft = computed(() => footerSlots.value.filter(s => footerAlign(s) === 'left'))
const footerRight = computed(() => footerSlots.value.filter(s => footerAlign(s) === 'right'))

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

function day(value: unknown) {
  if (value == null || value === '') return ''
  return String(value).slice(0, 10)
}

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
    tabindex="0"
    role="button"
    @dragstart="onDragStart"
    @dragend="emit('dragEnd')"
    @dragover="onDragOver"
    @drop="onDrop"
    @click="emit('open')"
    @keydown.enter.prevent="emit('open')"
  >
    <div class="flex items-start gap-2">
      <span
        v-if="showSortOrder"
        class="mt-0.5 shrink-0 tabular-nums text-[11px] text-muted"
      >
        #{{ (meeting.sortOrder ?? 0) + 1 }}
      </span>
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-1.5">
          <p class="text-sm font-semibold text-highlighted wrap-break-word">
            {{ meeting.title }}
          </p>
          <UBadge
            v-if="showStatus"
            size="sm"
            color="neutral"
            variant="subtle"
          >
            {{ statusLabel }}
          </UBadge>
        </div>
        <p
          v-if="bodySlots.includes('topicTitle')"
          class="mt-1 truncate text-xs text-muted"
        >
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

    <template v-for="slot in bodySlots" :key="slot">
      <p
        v-if="slot === 'notes'"
        class="mt-1.5 line-clamp-2 text-xs text-muted"
      >
        {{ notesSnippet }}
      </p>
      <div v-else-if="slot === 'stage'" class="mt-1.5">
        <UBadge size="sm" color="neutral" variant="outline">{{ stageLabel }}</UBadge>
      </div>
      <div
        v-else-if="slot === 'tags'"
        class="mt-1.5 flex flex-wrap gap-1.5"
      >
        <UBadge
          v-for="tag in tags.slice(0, 2)"
          :key="tag"
          size="sm"
          color="neutral"
          variant="soft"
        >
          {{ tag }}
        </UBadge>
      </div>
    </template>

    <div
      v-if="footerSlots.length"
      class="mt-2 flex items-center justify-between gap-2 border-t border-default pt-2 text-xs text-muted"
    >
      <div class="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
        <template v-for="slot in footerLeft" :key="slot">
          <span
            v-if="slot === 'meetingDate' || slot === 'recordTime'"
            class="inline-flex min-w-0 items-center gap-1 truncate"
          >
            <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
            <span class="truncate">
              {{ slot === 'meetingDate' ? meeting.meetingDate : recordTimeLabel }}
            </span>
          </span>
          <span
            v-else-if="slot === 'location'"
            class="inline-flex min-w-0 items-center gap-1 truncate"
          >
            <UIcon name="i-lucide-map-pin" class="size-3 shrink-0" />
            <span class="truncate">{{ meeting.location }}</span>
          </span>
          <span
            v-else-if="slot === 'attendeesCount'"
            class="inline-flex items-center gap-1"
          >
            <UIcon name="i-lucide-users" class="size-3" />
            {{ meeting.attendeesCount }}
          </span>
          <span
            v-else-if="slot === 'createdAt' || slot === 'updatedAt'"
            class="inline-flex min-w-0 items-center gap-1 truncate"
          >
            <UIcon name="i-lucide-clock" class="size-3 shrink-0" />
            <span class="truncate">{{ day(slot === 'createdAt' ? meeting.createdAt : meeting.updatedAt) }}</span>
          </span>
        </template>
      </div>
      <div class="inline-flex shrink-0 items-center gap-2">
        <template v-for="slot in footerRight" :key="slot">
          <span
            v-if="slot === 'meetingDate' || slot === 'recordTime'"
            class="inline-flex min-w-0 items-center gap-1 truncate"
          >
            <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
            <span class="truncate">
              {{ slot === 'meetingDate' ? meeting.meetingDate : recordTimeLabel }}
            </span>
          </span>
          <span
            v-else-if="slot === 'location'"
            class="inline-flex min-w-0 items-center gap-1 truncate"
          >
            <UIcon name="i-lucide-map-pin" class="size-3 shrink-0" />
            <span class="truncate">{{ meeting.location }}</span>
          </span>
          <span
            v-else-if="slot === 'attendeesCount'"
            class="inline-flex items-center gap-1"
          >
            <UIcon name="i-lucide-users" class="size-3" />
            {{ meeting.attendeesCount }}
          </span>
          <span
            v-else-if="slot === 'createdAt' || slot === 'updatedAt'"
            class="inline-flex min-w-0 items-center gap-1 truncate"
          >
            <UIcon name="i-lucide-clock" class="size-3 shrink-0" />
            <span class="truncate">{{ day(slot === 'createdAt' ? meeting.createdAt : meeting.updatedAt) }}</span>
          </span>
        </template>
      </div>
    </div>
  </article>
</template>
