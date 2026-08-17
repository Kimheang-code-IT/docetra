<script setup lang="ts">
import type { MeetingHistory, MeetingTopic } from '~/types/docetra/entities'
import { MEETING_BOARD_UNASSIGNED } from '~/composables/meeting/useMeetingTopicBoard'
import { usePointerDrop } from '~/composables/common/usePointerDrop'
import { useCardFields } from '~/composables/settings/useCardFields'
import { isCardFooterSlot, splitCardSlots } from '~/utils/card-fields'
import {
  computeMeetingTiming,
  formatMeetingDateTime,
  isJoinableMeeting,
} from '~/utils/meeting/board'

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

const timing = computed(() => {
  if (props.meeting.imminent != null || props.meeting.inProgress != null) {
    return {
      imminent: Boolean(props.meeting.imminent || props.meeting.inProgress),
      inProgress: Boolean(props.meeting.inProgress),
    }
  }
  const t = computeMeetingTiming(props.meeting.meetingDate, props.meeting.durationMinutes)
  return { imminent: Boolean(t.imminent), inProgress: Boolean(t.inProgress) }
})

const isImminent = computed(() => timing.value.imminent)
const canJoin = computed(() => isJoinableMeeting(props.meeting.meetingMode, props.meeting.meetingUrl))

const statusLabel = computed(() => {
  const key = `docetra.status.${props.meeting.status}`
  return te(key) ? t(key) : props.meeting.status
})

const stageLabel = computed(() => {
  if (!props.meeting.stage) return ''
  const key = `docetra.stages.${props.meeting.stage}`
  return te(key) ? t(key) : props.meeting.stage
})

const statusColor = computed(() => {
  const status = String(props.meeting.status || '').toLowerCase()
  if (status === 'active' || status === 'completed') return 'success' as const
  if (status === 'pending' || status === 'draft') return 'warning' as const
  if (status === 'disabled' || status === 'failed') return 'error' as const
  return 'info' as const
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

function listText(value: unknown) {
  return Array.isArray(value) ? value.map(String).filter(Boolean).join(', ') : String(value || '')
}

function footerDate(slot: string) {
  if (slot === 'letterDate') return day(props.meeting.letterDate)
  if (slot === 'meetingDate') return formatMeetingDateTime(props.meeting.meetingDate)
  if (slot === 'recordTime') return formatMeetingDateTime(props.meeting.recordTime || props.meeting.meetingDate)
  return recordTimeLabel.value
}

function meetingModeLabel(mode?: string) {
  if (!mode) return ''
  const key = `docetra.meetingMode.${mode}`
  return te(key) ? t(key) : mode
}

function fieldTone(slot: string) {
  if (slot === 'letterNumber') return 'app-card-field-highlight--info'
  if (slot === 'topicTitle' || slot === 'meetingMode') return 'app-card-field-highlight--secondary'
  if (slot === 'participants') return 'app-card-field-highlight--success'
  if (slot === 'internalUnits') return 'app-card-field-highlight--info'
  if (slot === 'externalUnits' || slot === 'durationMinutes') return 'app-card-field-highlight--warning'
  return ''
}

function fieldIcon(slot: string) {
  if (slot === 'letterNumber') return 'i-lucide-hash'
  if (slot === 'topicTitle') return 'i-lucide-messages-square'
  if (slot === 'participants') return 'i-lucide-users'
  if (slot === 'internalUnits') return 'i-lucide-building-2'
  if (slot === 'externalUnits') return 'i-lucide-landmark'
  if (slot === 'meetingMode') return 'i-lucide-video'
  if (slot === 'durationMinutes') return 'i-lucide-timer'
  return 'i-lucide-file-text'
}

function footerTone(slot: string) {
  if (slot === 'location' || slot === 'durationMinutes') return 'app-card-field-highlight--warning'
  if (slot === 'attendeesCount') return 'app-card-field-highlight--success'
  if (slot === 'meetingMode') return 'app-card-field-highlight--secondary'
  if (slot === 'createdAt' || slot === 'updatedAt') return 'app-card-field-highlight--neutral'
  return 'app-card-field-highlight--info'
}

function joinMeeting() {
  const url = safeExternalUrl(props.meeting.meetingUrl)
  if (!url) return
  if (import.meta.client) window.open(url, '_blank', 'noopener,noreferrer')
}

const orderedSlots = computed(() => {
  return visibleSlots.value.filter((slot) => {
    if (isCardFooterSlot('meetingHistory', slot)) return true
    if (slot === 'topicTitle') return Boolean(props.showTopic)
    if (slot === 'status') return Boolean(statusLabel.value)
    if (slot === 'sortOrder') return props.meeting.sortOrder != null
    if (slot === 'letterNumber') return Boolean(props.meeting.letterNumber)
    if (slot === 'stage') return Boolean(stageLabel.value)
    if (slot === 'tags') return tags.value.length > 0
    if (slot === 'participants') return Boolean(listText(props.meeting.participants))
    if (slot === 'internalUnits') return Boolean(listText(props.meeting.internalUnits))
    if (slot === 'externalUnits') return Boolean(listText(props.meeting.externalUnits))
    if (slot === 'letterDate') return Boolean(props.meeting.letterDate)
    if (slot === 'meetingMode') return Boolean(props.meeting.meetingMode)
    if (slot === 'meetingUrl') return Boolean(props.meeting.meetingUrl)
    if (slot === 'durationMinutes') return props.meeting.durationMinutes != null
    return show(slot)
  })
})

const split = computed(() => splitCardSlots('meetingHistory', orderedSlots.value))
const showSortOrder = computed(() => split.value.titleChrome.includes('sortOrder'))
const showStatus = computed(() => split.value.titleChrome.includes('status'))
const bodySlots = computed(() => split.value.body)
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
    },
    ...(canJoin.value
      ? [{
          label: t('docetra.meetingBoard.joinMeeting'),
          icon: 'i-lucide-video',
          onSelect: () => joinMeeting(),
        }]
      : [])],
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

const pointerDrop = usePointerDrop({
  selector: '[data-meeting-topic-drop]',
  dataKey: 'meetingTopicDrop',
  onDragStart: () => emit('dragStart', props.meeting.id),
  onDrop: topicId => emit('assign', topicId === MEETING_BOARD_UNASSIGNED ? null : topicId),
  onDragEnd: () => emit('dragEnd'),
})

function onCardClick(event: MouseEvent) {
  if (!pointerDrop.onClick(event)) emit('open')
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
    class="group relative flex h-full min-h-30 cursor-grab touch-pan-y flex-col rounded-lg border border-default bg-default p-3 text-left shadow-xs transition active:cursor-grabbing"
    :class="[
      dragging ? 'opacity-40 ring-2 ring-primary/30' : 'hover:border-primary/35 hover:shadow-sm',
      isImminent ? 'meeting-card--imminent border-primary/60' : '',
    ]"
    tabindex="0"
    role="button"
    @dragstart="onDragStart"
    @dragend="emit('dragEnd')"
    @pointerdown="pointerDrop.onPointerDown"
    @pointermove="pointerDrop.onPointerMove"
    @pointerup="pointerDrop.onPointerUp"
    @pointercancel="pointerDrop.onPointerCancel"
    @dragover="onDragOver"
    @drop="onDrop"
    @click="onCardClick"
    @keydown.enter.prevent="emit('open')"
  >
    <span
      v-if="showSortOrder"
      class="pointer-events-none absolute top-1 inset-e-1 z-10 inline-flex size-5 items-center justify-center rounded-full border border-default bg-elevated text-[11px] font-medium tabular-nums text-toned shadow-xs"
    >
      {{ (meeting.sortOrder ?? 0) + 1 }}
    </span>

    <div class="flex items-start gap-2" :class="showSortOrder ? 'pe-6' : ''">
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-1.5">
          <p class="text-sm font-semibold text-highlighted wrap-break-word">
            {{ meeting.title }}
          </p>
          <UBadge
            v-if="showStatus"
            size="sm"
            :color="statusColor"
            variant="subtle"
            icon="i-lucide-circle-dot"
          >
            {{ statusLabel }}
          </UBadge>
          <UBadge
            v-if="isImminent"
            size="sm"
            color="primary"
            variant="soft"
            icon="i-lucide-clock-3"
          >
            {{ timing.inProgress ? $t('docetra.meetingBoard.inProgress') : $t('docetra.meetingBoard.soon') }}
          </UBadge>
        </div>
        <div
          v-if="bodySlots.includes('topicTitle')"
          class="app-card-field-highlight mt-1 flex min-w-0 items-center gap-1.5 text-xs app-card-text"
          :class="fieldTone('topicTitle')"
        >
          <UIcon :name="fieldIcon('topicTitle')" class="size-3 shrink-0" />
          <span class="truncate">{{ meeting.topicTitle || $t('docetra.meetingBoard.unassigned') }}</span>
        </div>
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

    <div class="min-h-0 flex-1">
      <template v-for="slot in bodySlots" :key="slot">
      <div
        v-if="slot === 'letterNumber'"
        class="app-card-field-highlight mt-1.5 flex min-w-0 items-center gap-1.5 text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
        <span class="truncate">{{ meeting.letterNumber }}</span>
      </div>
      <div v-else-if="slot === 'stage'" class="mt-1.5">
        <UBadge size="sm" color="info" variant="soft" icon="i-lucide-git-branch">{{ stageLabel }}</UBadge>
      </div>
      <div
        v-else-if="slot === 'tags'"
        class="mt-1.5 flex flex-wrap gap-1.5"
      >
        <UBadge
          v-for="tag in tags.slice(0, 2)"
          :key="tag"
          size="sm"
          color="secondary"
          variant="soft"
          icon="i-lucide-tag"
        >
          {{ tag }}
        </UBadge>
      </div>
      <div
        v-else-if="slot === 'participants' || slot === 'internalUnits' || slot === 'externalUnits'"
        class="app-card-field-highlight mt-1.5 flex min-w-0 items-center gap-1.5 truncate text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon
          :name="fieldIcon(slot)"
          class="size-3 shrink-0"
        />
        <span class="truncate">
          {{ listText(slot === 'participants'
            ? meeting.participants
            : slot === 'internalUnits'
              ? meeting.internalUnits
              : meeting.externalUnits) }}
        </span>
      </div>
      <div
        v-else-if="slot === 'meetingMode'"
        class="app-card-field-highlight mt-1.5 flex items-center gap-1.5 text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
        <span class="truncate">{{ meetingModeLabel(meeting.meetingMode) }}</span>
      </div>
      <div
        v-else-if="slot === 'meetingUrl' && meeting.meetingUrl"
        class="mt-1.5"
      >
        <UButton
          size="xs"
          color="primary"
          variant="soft"
          icon="i-lucide-video"
          :label="$t('docetra.meetingBoard.joinMeeting')"
          @click.stop="joinMeeting"
        />
      </div>
      <div
        v-else-if="slot === 'durationMinutes' && meeting.durationMinutes != null"
        class="app-card-field-highlight mt-1.5 flex items-center gap-1.5 text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
        <span>{{ $t('docetra.meetingBoard.durationMinutes', { n: meeting.durationMinutes }) }}</span>
      </div>
    </template>
    </div>

    <div v-if="canJoin && !bodySlots.includes('meetingUrl')" class="mt-2 shrink-0">
      <UButton
        size="xs"
        color="primary"
        variant="soft"
        icon="i-lucide-video"
        :label="$t('docetra.meetingBoard.joinMeeting')"
        @click.stop="joinMeeting"
      />
    </div>

    <div
      v-if="footerSlots.length"
      class="mt-auto flex items-center justify-between gap-2 border-t border-default pt-2 text-xs app-card-text"
    >
      <div class="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
        <template v-for="slot in footerLeft" :key="slot">
          <span
            v-if="slot === 'letterDate' || slot === 'meetingDate' || slot === 'recordTime'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
            <span class="truncate">
              {{ footerDate(slot) || '—' }}
            </span>
          </span>
          <span
            v-else-if="slot === 'location'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-map-pin" class="size-3 shrink-0" />
            <span class="truncate">{{ meeting.location || '—' }}</span>
          </span>
          <span
            v-else-if="slot === 'attendeesCount'"
            class="app-card-field-highlight--compact inline-flex items-center gap-1"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-users" class="size-3" />
            {{ meeting.attendeesCount }}
          </span>
          <span
            v-else-if="slot === 'durationMinutes' && meeting.durationMinutes != null"
            class="app-card-field-highlight--compact inline-flex items-center gap-1"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-timer" class="size-3" />
            {{ meeting.durationMinutes }}m
          </span>
          <span
            v-else-if="slot === 'meetingMode'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-video" class="size-3 shrink-0" />
            {{ meetingModeLabel(meeting.meetingMode) }}
          </span>
          <span
            v-else-if="slot === 'createdAt' || slot === 'updatedAt'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-clock" class="size-3 shrink-0" />
            <span class="truncate">{{ day(slot === 'createdAt' ? meeting.createdAt : meeting.updatedAt) || '—' }}</span>
          </span>
        </template>
      </div>
      <div class="inline-flex shrink-0 items-center gap-2">
        <template v-for="slot in footerRight" :key="slot">
          <span
            v-if="slot === 'letterDate' || slot === 'meetingDate' || slot === 'recordTime'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
            <span class="truncate">
              {{ footerDate(slot) || '—' }}
            </span>
          </span>
          <span
            v-else-if="slot === 'location'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-map-pin" class="size-3 shrink-0" />
            <span class="truncate">{{ meeting.location || '—' }}</span>
          </span>
          <span
            v-else-if="slot === 'attendeesCount'"
            class="app-card-field-highlight--compact inline-flex items-center gap-1"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-users" class="size-3" />
            {{ meeting.attendeesCount }}
          </span>
          <span
            v-else-if="slot === 'durationMinutes' && meeting.durationMinutes != null"
            class="app-card-field-highlight--compact inline-flex items-center gap-1"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-timer" class="size-3" />
            {{ meeting.durationMinutes }}m
          </span>
          <span
            v-else-if="slot === 'meetingMode'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-video" class="size-3 shrink-0" />
            {{ meetingModeLabel(meeting.meetingMode) }}
          </span>
          <span
            v-else-if="slot === 'createdAt' || slot === 'updatedAt'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-clock" class="size-3 shrink-0" />
            <span class="truncate">{{ day(slot === 'createdAt' ? meeting.createdAt : meeting.updatedAt) || '—' }}</span>
          </span>
        </template>
      </div>
    </div>
  </article>
</template>

<style scoped>
@keyframes meeting-imminent-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 color-mix(in oklab, var(--ui-primary) 35%, transparent);
  }
  50% {
    box-shadow: 0 0 0 3px color-mix(in oklab, var(--ui-primary) 55%, transparent);
  }
}

.meeting-card--imminent {
  animation: meeting-imminent-pulse 1.6s ease-in-out infinite;
}
</style>
