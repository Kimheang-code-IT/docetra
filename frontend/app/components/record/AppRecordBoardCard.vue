<script setup lang="ts">
import type { MeetingHistory, MeetingTopic } from '~/types/docetra/entities'
import { MEETING_BOARD_UNASSIGNED } from '~/composables/meeting/useMeetingTopicBoard'
import { usePointerDrop } from '~/composables/common/usePointerDrop'
import type { WorkflowStage } from '~/types/docetra/common'
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import { useCardFields } from '~/composables/settings/useCardFields'
import { isCardFooterSlot, splitCardSlots } from '~/utils/card-fields'
import {
  computeMeetingTiming,
  isJoinableMeeting,
} from '~/utils/meeting/board'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

/**
 * Single board card for records AND meetings.
 * Pass `row` (+ stages) for record boards; pass `meeting` (+ topics) to enable
 * meeting behaviors: imminent pulse, join, topic assign/reorder, notes.
 */
const props = withDefaults(defineProps<{
  row?: Record<string, unknown>
  meeting?: MeetingHistory | null
  topics?: MeetingTopic[]
  title: string
  stages?: WorkflowStage[]
  dragging?: boolean
  entityKey?: CardDisplayEntityKey
  canMove?: boolean
  canViewLogs?: boolean
  canDelete?: boolean
  /** Meeting-only controls. */
  showTopic?: boolean
  canAssign?: boolean
  canEditNotes?: boolean
}>(), {
  row: () => ({}),
  meeting: null,
  topics: () => [],
  stages: () => [],
  entityKey: 'documents',
  canMove: true,
  canViewLogs: true,
  canDelete: true,
  showTopic: false,
  canAssign: true,
  canEditNotes: true,
})

const emit = defineEmits<{
  open: []
  dragStart: [id: string]
  dragEnd: []
  moveStage: [stage: string]
  logs: []
  delete: []
  openNotes: []
  assign: [topicId: string | null]
  reorderBefore: [beforeId: string | null]
}>()

const { t, te } = useI18n()
const { formatDate, formatDateTime } = useAppLocalization()
const { show, visibleSlots, footerAlign } = useCardFields(() => props.entityKey)

/** True when rendering a meeting-history card. */
const m = computed(() => props.meeting)
const r = computed<Record<string, unknown>>(() => props.row)

function orgName(value: unknown) {
  if (!value || typeof value !== 'object') return ''
  const name = (value as { name?: string }).name
  return name ? String(name) : ''
}

function personName(value: unknown) {
  if (!value || typeof value !== 'object') return ''
  const name = (value as { name?: string }).name
  return name ? String(name) : ''
}

function day(value: unknown) {
  return formatDate(value, '')
}

function listText(value: unknown) {
  return Array.isArray(value)
    ? value.map((item) => {
        if (item && typeof item === 'object' && 'name' in item) return String(item.name || '')
        return String(item || '')
      }).map(item => item.trim()).filter(Boolean).join(', ')
    : (value && typeof value === 'object' && 'name' in value)
        ? String(value.name || '')
        : String(value || '')
}

// --- shared identity fields -------------------------------------------------

const referenceNumber = computed(() => String(r.value.referenceNumber || ''))
const recordTypeLabel = computed(() =>
  String(r.value.recordTypeName || r.value.recordTypeId || ''),
)
const description = computed(() => {
  const raw = String(r.value.recordContent || r.value.description || '').trim()
  if (!raw) return ''
  return raw.length > 90 ? `${raw.slice(0, 90)}…` : raw
})
const recordTime = computed(() =>
  day(props.row?.recordTime)
  || day(props.row?.receivedDate)
  || day(props.row?.sentDate)
  || day(props.row?.createdAt),
)
const tags = computed(() => {
  const source: unknown = props.meeting
    ? (Array.isArray(props.meeting.tags) && props.meeting.tags.length
        ? props.meeting.tags
        : props.meeting.recordTag)
    : (props.row?.tags ?? props.row?.recordTag)
  if (Array.isArray(source)) return source.map(String).filter(Boolean)
  if (typeof source === 'string' && source.trim()) {
    return source.split(/[,;]/).map(s => s.trim()).filter(Boolean)
  }
  return []
})
const sender = computed(() => orgName(r.value.senderOrganization))
const recipient = computed(() => orgName(r.value.recipientOrganization))
const ownerDepartment = computed(() => orgName(r.value.ownerDepartment))
const owner = computed(() => personName(r.value.owner))
const assignee = computed(() => listText(r.value.assignees || r.value.assignee))
const waiting = computed(() => Boolean(r.value.waiting))
const attachmentCount = computed(() => Number(r.value.attachmentCount || 0))
const commentCount = computed(() => Number(r.value.commentCount || 0))

// --- meeting extras ---------------------------------------------------------

const timing = computed(() => {
  if (!m.value) return { imminent: false, inProgress: false }
  if (m.value.imminent != null || m.value.inProgress != null) {
    return {
      imminent: Boolean(m.value.imminent || m.value.inProgress),
      inProgress: Boolean(m.value.inProgress),
    }
  }
  const result = computeMeetingTiming(m.value.meetingDate, m.value.durationMinutes)
  return { imminent: Boolean(result.imminent), inProgress: Boolean(result.inProgress) }
})

const isImminent = computed(() => timing.value.imminent)
const canJoin = computed(() => Boolean(m.value && isJoinableMeeting(m.value.meetingMode, m.value.meetingUrl)))

function joinMeeting() {
  const url = safeExternalUrl(m.value?.meetingUrl)
  if (!url) return
  if (import.meta.client) window.open(url, '_blank', 'noopener,noreferrer')
}

function meetingModeLabel(mode?: string) {
  if (!mode) return ''
  const key = `docetra.meetingMode.${mode}`
  return te(key) ? t(key) : mode
}

// --- slot helpers -----------------------------------------------------------

function bodySlotText(slot: string) {
  const values: Record<string, unknown> = {
    recordFlowCode: r.value.recordFlowCode,
    recordContent: r.value.recordContent || r.value.description,
    documentType: r.value.documentType || r.value.recordTypeName || r.value.recordTypeId,
    letterNumber: r.value.referenceNumber,
    letterSubject: r.value.letterSubject,
    involvedOfficers: listText(r.value.involvedOfficers),
    externalUnits: listText(r.value.externalUnits),
    officeInCharge: listText(r.value.officeInCharge),
    officerInCharge: listText(r.value.officerInCharge),
  }
  return String(values[slot] || '').trim()
}

function footerDate(slot: string) {
  if (m.value) {
    if (slot === 'letterDate') return formatDate(m.value.letterDate, '')
    if (slot === 'meetingDate') return formatDateTime(m.value.meetingDate)
    if (slot === 'recordTime') return formatDateTime(m.value.recordTime || m.value.meetingDate)
    if (slot === 'createdAt') return day(m.value.createdAt)
    if (slot === 'updatedAt') return day(m.value.updatedAt)
    return day(m.value.recordTime) || day(m.value.meetingDate)
  }
  const values: Record<string, unknown> = {
    recordTime: r.value.recordTime,
    receivedDate: r.value.receivedDate,
    sentDate: r.value.sentDate,
    documentDate: r.value.documentDate,
    letterDate: r.value.letterDate,
    directorGeneralDate: r.value.directorGeneralDate,
    directorDate: r.value.directorDate,
    createdAt: r.value.createdAt,
    updatedAt: r.value.updatedAt,
  }
  return day(values[slot])
}

function fieldTone(slot: string) {
  if (slot === 'referenceNumber' || slot === 'letterNumber') return 'app-card-field-highlight--info'
  if (slot === 'recordType' || slot === 'documentType' || slot === 'topicTitle' || slot === 'meetingMode') return 'app-card-field-highlight--secondary'
  if (slot === 'party' || slot === 'externalUnits' || slot === 'durationMinutes') return 'app-card-field-highlight--warning'
  if (slot === 'officeInCharge' || slot === 'internalUnits') return 'app-card-field-highlight--info'
  if (slot === 'owner' || slot === 'assignee' || slot === 'involvedOfficers' || slot === 'officerInCharge' || slot === 'participants') return 'app-card-field-highlight--success'
  if (slot === 'description' || slot === 'recordContent') return 'app-card-field-highlight--neutral'
  return ''
}

function fieldIcon(slot: string) {
  if (slot === 'referenceNumber' || slot === 'letterNumber') return 'i-lucide-hash'
  if (slot === 'recordType' || slot === 'documentType') return 'i-lucide-shapes'
  if (slot === 'description' || slot === 'recordContent' || slot === 'letterSubject') return 'i-lucide-align-left'
  if (slot === 'involvedOfficers' || slot === 'officerInCharge') return 'i-lucide-user-round'
  if (slot === 'externalUnits') return 'i-lucide-landmark'
  if (slot === 'officeInCharge' || slot === 'internalUnits') return 'i-lucide-building-2'
  if (slot === 'topicTitle') return 'i-lucide-messages-square'
  if (slot === 'participants') return 'i-lucide-users'
  if (slot === 'meetingMode') return 'i-lucide-video'
  if (slot === 'durationMinutes') return 'i-lucide-timer'
  return 'i-lucide-file-text'
}

function footerTone(slot: string) {
  if (slot === 'attachmentCount') return 'app-card-field-highlight--secondary'
  if (slot === 'commentCount') return 'app-card-field-highlight--info'
  if (m.value) {
    if (slot === 'location' || slot === 'durationMinutes') return 'app-card-field-highlight--warning'
    if (slot === 'attendeesCount') return 'app-card-field-highlight--success'
    if (slot === 'meetingMode') return 'app-card-field-highlight--secondary'
    if (slot === 'createdAt' || slot === 'updatedAt') return 'app-card-field-highlight--neutral'
    return 'app-card-field-highlight--info'
  }
  return 'app-card-field-highlight--success'
}

const startDate = computed(() =>
  day(r.value.receivedDate)
  || day(r.value.sentDate)
  || day(r.value.createdAt),
)

const endDate = computed(() => {
  const updated = day(r.value.updatedAt)
  const start = startDate.value
  if (updated && start && updated !== start) return updated
  const received = day(r.value.receivedDate)
  const sent = day(r.value.sentDate)
  if (received && sent && received !== sent) return sent
  return ''
})

const dateLabel = computed(() => {
  if (startDate.value && endDate.value) return `${startDate.value} – ${endDate.value}`
  return startDate.value || endDate.value
})

const partyLabel = computed(() => {
  if (sender.value) return { icon: 'i-lucide-building-2', text: sender.value }
  if (recipient.value) return { icon: 'i-lucide-send', text: recipient.value }
  if (ownerDepartment.value) return { icon: 'i-lucide-building', text: ownerDepartment.value }
  return null
})

// --- slot ordering ----------------------------------------------------------

const orderedSlots = computed(() => {
  return visibleSlots.value.filter((slot) => {
    if (isCardFooterSlot(props.entityKey, slot)) return true
    if (m.value) {
      if (slot === 'topicTitle') return Boolean(props.showTopic)
      if (slot === 'sortOrder') return m.value.sortOrder != null
      if (slot === 'letterNumber') return Boolean(m.value.letterNumber)
      if (slot === 'tags') return tags.value.length > 0
      if (slot === 'participants') return Boolean(listText(m.value.participants))
      if (slot === 'internalUnits') return Boolean(listText(m.value.internalUnits))
      if (slot === 'externalUnits') return Boolean(listText(m.value.externalUnits))
      if (slot === 'letterDate') return Boolean(m.value.letterDate)
      if (slot === 'meetingMode') return Boolean(m.value.meetingMode)
      // Join CTA is a single dedicated button below the body — not a body slot.
      if (slot === 'meetingUrl') return false
      if (slot === 'durationMinutes') return m.value.durationMinutes != null
      return show(slot)
    }
    if (slot === 'referenceNumber') return Boolean(referenceNumber.value)
    if (slot === 'recordType') return Boolean(recordTypeLabel.value)
    if (slot === 'description') return Boolean(description.value)
    if (slot === 'party') return Boolean(partyLabel.value)
    if (slot === 'owner') return Boolean(owner.value)
    if (slot === 'assignee') return Boolean(assignee.value)
    if (slot === 'waiting') return waiting.value
    if (slot === 'tags') return tags.value.length > 0
    if (bodySlotText(slot)) return true
    return show(slot)
  })
})

const split = computed(() => splitCardSlots(props.entityKey, orderedSlots.value))
const showSortOrder = computed(() => m.value != null && split.value.titleChrome.includes('sortOrder'))
const showTopicTitleRow = computed(() =>
  m.value != null && split.value.titleChrome.includes('topicTitle'))
const bodySlots = computed(() => split.value.body)
const footerSlots = computed(() => {
  const slots = split.value.footer
  // Prefer meetingDate when both time slots are enabled (meetings).
  if (m.value && slots.includes('meetingDate') && slots.includes('recordTime')) {
    return slots.filter(s => s !== 'recordTime')
  }
  return slots
})
const footerLeft = computed(() => footerSlots.value.filter(s => footerAlign(s) === 'left'))
const footerRight = computed(() => footerSlots.value.filter(s => footerAlign(s) === 'right'))

/** One rendering loop for both footer columns (left wraps, right is fixed). */
const footerColumns = computed(() => [
  { id: 'left', slots: footerLeft.value, columnClass: 'flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1' },
  { id: 'right', slots: footerRight.value, columnClass: 'inline-flex shrink-0 flex-wrap items-center justify-end gap-2' },
])

// --- menus ------------------------------------------------------------------

const menuItems = computed(() => {
  if (m.value) {
    const meeting = m.value
    const topicItems = props.topics.map(topic => ({
      label: topic.title,
      icon: topic.id === meeting.topicId ? 'i-lucide-check' : 'i-lucide-messages-square',
      onSelect: () => emit('assign', topic.id),
    }))
    return [
      [{
        label: t('docetra.meetingBoard.openMeeting'),
        icon: 'i-lucide-external-link',
        onSelect: () => emit('open'),
      }, ...(props.canEditNotes ? [{
        label: t('docetra.meetingBoard.openNotes'),
        icon: 'i-lucide-notebook-pen',
        onSelect: () => emit('openNotes'),
      }] : [])],
      ...(props.canAssign ? [[
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
          disabled: !meeting.topicId,
          onSelect: () => emit('assign', null),
        },
      ]] : []),
      ...(props.canDelete ? [[{
        label: t('docetra.rowActions.delete'),
        icon: 'i-lucide-trash-2',
        color: 'error' as const,
        onSelect: () => emit('delete'),
      }]] : []),
    ]
  }

  return [
    [{
      label: t('docetra.rowActions.detail'),
      icon: 'i-lucide-eye',
      onSelect: () => emit('open'),
    }, ...(props.canViewLogs ? [{
      label: t('docetra.rowActions.logs'),
      icon: 'i-lucide-scroll-text',
      onSelect: () => emit('logs'),
    }] : [])],
    ...(props.canMove ? [[{
      label: t('docetra.recordStageBoard.moveToStage'),
      icon: 'i-lucide-layers',
      children: props.stages.map(stage => ({
        label: stage.label || (te(stage.labelKey) ? t(stage.labelKey) : stage.code),
        icon: String(r.value.stage) === stage.code ? 'i-lucide-check' : 'i-lucide-circle',
        onSelect: () => emit('moveStage', stage.code),
      })),
    }]] : []),
    ...(props.canDelete ? [[{
      label: t('docetra.rowActions.delete'),
      icon: 'i-lucide-trash-2',
      color: 'error' as const,
      onSelect: () => emit('delete'),
    }]] : []),
  ]
})

// --- drag & drop ------------------------------------------------------------

function onDragStart(event: DragEvent) {
  const id = String((m.value ? m.value.id : r.value.id) || '')
  if (m.value) {
    if (!props.canAssign) return
    event.dataTransfer?.setData('text/plain', id)
    event.dataTransfer?.setData('application/x-meeting-id', id)
  }
  else {
    if (!props.canMove) return
    event.dataTransfer?.setData('text/plain', id)
  }
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
  emit('dragStart', id)
}

const pointerDrop = usePointerDrop({
  get selector() {
    return m.value ? '[data-meeting-topic-drop]' : '[data-record-stage-drop]'
  },
  get dataKey() {
    return m.value ? 'meetingTopicDrop' : 'recordStageDrop'
  },
  onDragStart: () => emit('dragStart', String((m.value ? m.value.id : r.value.id) || '')),
  onDrop: (value) => {
    if (m.value) {
      if (props.canAssign) emit('assign', value === MEETING_BOARD_UNASSIGNED ? null : value)
      return
    }
    if (props.canMove) emit('moveStage', value)
  },
  onDragEnd: () => emit('dragEnd'),
})

function onCardClick(event: MouseEvent) {
  if (!pointerDrop.onClick(event)) emit('open')
}

function onDragOver(event: DragEvent) {
  if (!m.value) return
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
}

function onDrop(event: DragEvent) {
  if (!m.value) return
  event.preventDefault()
  event.stopPropagation()
  const id = event.dataTransfer?.getData('text/plain') || ''
  const selfId = String(m.value.id || '')
  if (!id || id === selfId) return
  emit('reorderBefore', selfId)
}
</script>

<template>
  <article
    :draggable="m ? canAssign : canMove"
    class="group relative flex h-full min-h-30 min-w-0 w-full touch-pan-y flex-col overflow-hidden rounded-lg border border-default bg-default p-3 text-left shadow-xs transition"
    :class="[
      (m ? canAssign : canMove) ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer',
      dragging ? 'opacity-40 ring-2 ring-primary/30' : 'hover:border-primary/35 hover:shadow-sm',
      isImminent ? 'meeting-card--imminent border-primary/60' : '',
    ]"
    tabindex="0"
    role="button"
    @dragstart="onDragStart"
    @dragend="emit('dragEnd')"
    @pointerdown="(m ? canAssign : canMove) && pointerDrop.onPointerDown($event)"
    @pointermove="(m ? canAssign : canMove) && pointerDrop.onPointerMove($event)"
    @pointerup="(m ? canAssign : canMove) && pointerDrop.onPointerUp($event)"
    @pointercancel="(m ? canAssign : canMove) && pointerDrop.onPointerCancel($event)"
    @dragover="onDragOver"
    @drop="onDrop"
    @click="onCardClick"
    @keydown.enter.prevent="emit('open')"
  >
    <span
      v-if="showSortOrder"
      class="pointer-events-none absolute top-1 inset-e-1 z-10 inline-flex size-5 items-center justify-center rounded-full border border-default bg-elevated text-[11px] font-medium tabular-nums text-toned shadow-xs"
    >
      {{ ((m?.sortOrder ?? 0) as number) + 1 }}
    </span>

    <div class="flex min-w-0 items-start gap-2" :class="showSortOrder ? 'pe-6' : ''">
      <div class="min-w-0 flex-1 overflow-hidden">
        <div class="flex min-w-0 flex-wrap items-center gap-1.5">
          <p class="min-w-0 max-w-full line-clamp-2 text-sm font-semibold text-highlighted wrap-break-word">
            {{ title }}
          </p>
          <span
            v-if="isImminent"
            class="app-card-field-highlight app-card-field-highlight--secondary text-xs"
          >
            <UIcon name="i-lucide-clock-3" class="size-3 shrink-0" />
            <span class="truncate">
              {{ timing.inProgress ? $t('docetra.meetingBoard.inProgress') : $t('docetra.meetingBoard.soon') }}
            </span>
          </span>
        </div>
        <div
          v-if="showTopicTitleRow"
          class="app-card-field-highlight mt-1 flex min-w-0 items-center gap-1.5 text-xs app-card-text"
          :class="fieldTone('topicTitle')"
        >
          <UIcon :name="fieldIcon('topicTitle')" class="size-3 shrink-0" />
          <span class="truncate">{{ m?.topicTitle || $t('docetra.meetingBoard.unassigned') }}</span>
        </div>
      </div>
      <UDropdownMenu :items="menuItems" :content="{ align: 'end' }">
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
        v-if="slot === 'referenceNumber' || slot === 'recordType' || slot === 'description'"
        class="app-card-field-highlight mt-1.5 truncate text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <span class="flex min-w-0 items-center gap-1.5">
          <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
          <span class="truncate">
            <template v-if="slot === 'referenceNumber'">{{ referenceNumber }}</template>
            <template v-else-if="slot === 'recordType'">{{ recordTypeLabel }}</template>
            <template v-else>{{ description }}</template>
          </span>
        </span>
      </div>
      <div
        v-else-if="slot === 'letterNumber'"
        class="app-card-field-highlight mt-1.5 flex min-w-0 items-center gap-1.5 text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
        <span class="truncate">{{ m?.letterNumber }}</span>
      </div>
      <div
        v-else-if="slot === 'party' && partyLabel"
        class="app-card-field-highlight mt-1.5 flex items-center gap-1.5 truncate text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="partyLabel.icon" class="size-3 shrink-0" />
        <span class="truncate">{{ partyLabel.text }}</span>
      </div>
      <div
        v-else-if="slot === 'owner'"
        class="app-card-field-highlight mt-1.5 flex items-center gap-1.5 truncate text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon name="i-lucide-user" class="size-3 shrink-0" />
        <span class="truncate">{{ owner }}</span>
      </div>
      <div
        v-else-if="slot === 'assignee'"
        class="app-card-field-highlight mt-1.5 flex items-center gap-1.5 truncate text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon name="i-lucide-user-check" class="size-3 shrink-0" />
        <span class="truncate">{{ assignee }}</span>
      </div>
      <div
        v-else-if="slot === 'waiting'"
        class="app-card-field-highlight app-card-field-highlight--warning mt-1.5 text-xs"
      >
        <UIcon name="i-lucide-clock-3" class="size-3 shrink-0" />
        <span class="truncate">{{ $t('docetra.fields.waiting') }}</span>
      </div>
      <div
        v-else-if="slot === 'tags'"
        class="mt-1.5 flex min-w-0 flex-wrap gap-x-2 gap-y-1"
      >
        <span
          v-for="tag in tags.slice(0, 2)"
          :key="tag"
          class="app-card-field-highlight app-card-field-highlight--secondary text-xs"
        >
          <UIcon name="i-lucide-tag" class="size-3 shrink-0" />
          <span class="truncate">{{ tag }}</span>
        </span>
      </div>
      <div
        v-else-if="slot === 'participants' || slot === 'internalUnits' || slot === 'externalUnits'"
        class="app-card-field-highlight mt-1.5 flex min-w-0 items-center gap-1.5 truncate text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
        <span class="truncate">
          {{ listText(slot === 'participants'
            ? m?.participants
            : slot === 'internalUnits'
              ? m?.internalUnits
              : m?.externalUnits) }}
        </span>
      </div>
      <div
        v-else-if="slot === 'meetingMode'"
        class="app-card-field-highlight mt-1.5 flex items-center gap-1.5 text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
        <span class="truncate">{{ meetingModeLabel(m?.meetingMode) }}</span>
      </div>
      <div
        v-else-if="slot === 'durationMinutes' && m?.durationMinutes != null"
        class="app-card-field-highlight mt-1.5 flex items-center gap-1.5 text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
        <span>{{ $t('docetra.meetingBoard.durationMinutes', { n: m.durationMinutes }) }}</span>
      </div>
      <div
        v-else-if="['involvedOfficers', 'externalUnits', 'officeInCharge', 'officerInCharge'].includes(slot) && bodySlotText(slot)"
        class="app-card-field-highlight mt-1.5 flex min-w-0 items-center gap-1.5 text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon :name="fieldIcon(slot)" class="size-3 shrink-0" />
        <span class="min-w-0 truncate">{{ bodySlotText(slot) }}</span>
      </div>
      <div
        v-else-if="bodySlotText(slot)"
        class="app-card-field-highlight mt-1.5 flex min-w-0 items-center gap-1.5 text-xs app-card-text"
        :class="fieldTone(slot)"
      >
        <UIcon
          :name="fieldIcon(slot)"
          class="size-3 shrink-0"
        />
        <span class="shrink-0 font-medium app-card-text">{{ $t(`docetra.cardSlots.${slot}`) }}:</span>
        <span class="min-w-0 truncate">{{ bodySlotText(slot) }}</span>
      </div>
    </template>
    </div>

    <div v-if="canJoin" class="mt-2 shrink-0">
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
      <div v-for="column in footerColumns" :key="column.id" :class="column.columnClass">
        <template v-for="slot in column.slots" :key="`${column.id}-${slot}`">
          <span
            v-if="slot === 'attachmentCount'"
            class="app-card-field-highlight--compact inline-flex items-center gap-1"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-paperclip" class="size-3" />
            {{ attachmentCount }}
          </span>
          <span
            v-else-if="slot === 'commentCount'"
            class="app-card-field-highlight--compact inline-flex items-center gap-1"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-message-circle" class="size-3" />
            {{ commentCount }}
          </span>
          <span
            v-else-if="slot === 'location'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-map-pin" class="size-3 shrink-0" />
            <span class="truncate">{{ m?.location || '—' }}</span>
          </span>
          <span
            v-else-if="slot === 'attendeesCount'"
            class="app-card-field-highlight--compact inline-flex items-center gap-1"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-users" class="size-3" />
            {{ m?.attendeesCount }}
          </span>
          <span
            v-else-if="slot === 'durationMinutes'"
            class="app-card-field-highlight--compact inline-flex items-center gap-1"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-timer" class="size-3" />
            {{ m?.durationMinutes }}m
          </span>
          <span
            v-else-if="slot === 'meetingMode'"
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-video" class="size-3 shrink-0" />
            {{ meetingModeLabel(m?.meetingMode) }}
          </span>
          <span
            v-else
            class="app-card-field-highlight--compact inline-flex min-w-0 items-center gap-1 truncate"
            :class="footerTone(slot)"
          >
            <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
            <span class="truncate">
              <template v-if="!m && slot === 'recordTime'">{{ recordTime || '—' }}</template>
              <template v-else-if="!m && slot === 'dateRange'">{{ dateLabel || '—' }}</template>
              <template v-else>{{ footerDate(slot) || '—' }}</template>
            </span>
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
