<script setup lang="ts">
import { usePointerDrop } from '~/composables/common/usePointerDrop'
import type { WorkflowStage } from '~/types/docetra/common'
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import { useCardFields } from '~/composables/settings/useCardFields'
import { isCardFooterSlot, splitCardSlots } from '~/utils/card-fields'

const props = withDefaults(defineProps<{
  row: Record<string, unknown>
  title: string
  statusLabel?: string
  stageLabel?: string
  stages: WorkflowStage[]
  dragging?: boolean
  entityKey?: CardDisplayEntityKey
}>(), {
  entityKey: 'documents',
})

const emit = defineEmits<{
  open: []
  dragStart: [id: string]
  dragEnd: []
  moveStage: [stage: string]
  logs: []
  delete: []
}>()

const { t, te } = useI18n()
const { show, visibleSlots, footerAlign } = useCardFields(() => props.entityKey)

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
  if (value == null || value === '') return ''
  return String(value).slice(0, 10)
}

function listText(value: unknown) {
  return Array.isArray(value)
    ? value.map(String).map(item => item.trim()).filter(Boolean).join(', ')
    : String(value || '')
}

const referenceNumber = computed(() => String(props.row.referenceNumber || ''))
const recordTypeLabel = computed(() =>
  String(props.row.recordTypeName || props.row.recordTypeId || ''),
)
const description = computed(() => {
  const raw = String(props.row.recordContent || props.row.description || '').trim()
  if (!raw) return ''
  return raw.length > 90 ? `${raw.slice(0, 90)}…` : raw
})
const recordTime = computed(() =>
  day(props.row.recordTime)
  || day(props.row.receivedDate)
  || day(props.row.sentDate)
  || day(props.row.createdAt),
)
const tags = computed(() => {
  if (Array.isArray(props.row.tags)) return props.row.tags.map(String).filter(Boolean)
  const raw = props.row.recordTag ?? props.row.tags
  if (typeof raw === 'string' && raw.trim()) {
    return raw.split(/[,;]/).map(s => s.trim()).filter(Boolean)
  }
  return []
})
const sender = computed(() => orgName(props.row.senderOrganization))
const recipient = computed(() => orgName(props.row.recipientOrganization))
const ownerDepartment = computed(() => orgName(props.row.ownerDepartment))
const owner = computed(() => personName(props.row.owner))
const assignee = computed(() => personName(props.row.assignee))
const waiting = computed(() => Boolean(props.row.waiting))
const attachmentCount = computed(() => Number(props.row.attachmentCount || 0))
const commentCount = computed(() => Number(props.row.commentCount || 0))

function bodySlotText(slot: string) {
  const values: Record<string, unknown> = {
    recordFlowCode: props.row.recordFlowCode,
    recordContent: props.row.recordContent || props.row.description,
    documentType: props.row.documentType || props.row.recordTypeName || props.row.recordTypeId,
    letterNumber: props.row.referenceNumber,
    letterSubject: props.row.letterSubject,
    involvedOfficers: listText(props.row.involvedOfficers),
    externalUnits: listText(props.row.externalUnits),
    officeInCharge: props.row.officeInCharge,
    officerInCharge: props.row.officerInCharge,
  }
  return String(values[slot] || '').trim()
}

function footerDate(slot: string) {
  const values: Record<string, unknown> = {
    recordTime: props.row.recordTime,
    receivedDate: props.row.receivedDate,
    sentDate: props.row.sentDate,
    documentDate: props.row.documentDate,
    letterDate: props.row.letterDate,
    directorGeneralDate: props.row.directorGeneralDate,
    directorDate: props.row.directorDate,
    createdAt: props.row.createdAt,
    updatedAt: props.row.updatedAt,
  }
  return day(values[slot])
}

const startDate = computed(() =>
  day(props.row.receivedDate)
  || day(props.row.sentDate)
  || day(props.row.createdAt),
)

const endDate = computed(() => {
  const updated = day(props.row.updatedAt)
  const start = startDate.value
  if (updated && start && updated !== start) return updated
  const received = day(props.row.receivedDate)
  const sent = day(props.row.sentDate)
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

const orderedSlots = computed(() =>
  visibleSlots.value.filter((slot) => {
    if (isCardFooterSlot(props.entityKey, slot)) return true
    if (slot === 'referenceNumber') return Boolean(referenceNumber.value)
    if (slot === 'recordType') return Boolean(recordTypeLabel.value)
    if (slot === 'description') return Boolean(description.value)
    if (slot === 'party') return Boolean(partyLabel.value)
    if (slot === 'owner') return Boolean(owner.value)
    if (slot === 'assignee') return Boolean(assignee.value)
    if (slot === 'status') return Boolean(props.statusLabel)
    if (slot === 'stage') return Boolean(props.stageLabel)
    if (slot === 'waiting') return waiting.value
    if (slot === 'tags') return tags.value.length > 0
    if (bodySlotText(slot)) return true
    return show(slot)
  }),
)

const split = computed(() => splitCardSlots(props.entityKey, orderedSlots.value))
/** Exactly one status on the title (matches sample card) — never status + stage together. */
const titleStatusText = computed(() => {
  if (split.value.titleChrome.includes('status') && props.statusLabel) {
    return props.statusLabel
  }
  return ''
})
const bodySlots = computed(() => {
  return split.value.body
})
const footerSlots = computed(() => split.value.footer)
const footerLeft = computed(() => footerSlots.value.filter(s => footerAlign(s) === 'left'))
const footerRight = computed(() => footerSlots.value.filter(s => footerAlign(s) === 'right'))

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
      label: te(stage.labelKey) ? t(stage.labelKey) : stage.code,
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

const pointerDrop = usePointerDrop({
  selector: '[data-record-stage-drop]',
  dataKey: 'recordStageDrop',
  onDragStart: () => emit('dragStart', String(props.row.id || '')),
  onDrop: stage => emit('moveStage', stage),
  onDragEnd: () => emit('dragEnd'),
})

function onCardClick(event: MouseEvent) {
  if (!pointerDrop.onClick(event)) emit('open')
}
</script>

<template>
  <article
    draggable="true"
    class="group relative flex h-full min-h-30 cursor-grab touch-pan-y flex-col rounded-lg border border-default bg-default p-3 text-left shadow-xs transition active:cursor-grabbing"
    :class="dragging ? 'opacity-40 ring-2 ring-primary/30' : 'hover:border-primary/35 hover:shadow-sm'"
    tabindex="0"
    role="button"
    @dragstart="onDragStart"
    @dragend="emit('dragEnd')"
    @pointerdown="pointerDrop.onPointerDown"
    @pointermove="pointerDrop.onPointerMove"
    @pointerup="pointerDrop.onPointerUp"
    @pointercancel="pointerDrop.onPointerCancel"
    @click="onCardClick"
    @keydown.enter.prevent="emit('open')"
  >
    <div class="flex items-start gap-2">
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-1.5">
          <p class="text-sm font-semibold text-highlighted wrap-break-word">
            {{ title }}
          </p>
          <UBadge
            v-if="titleStatusText"
            size="sm"
            color="neutral"
            variant="subtle"
          >
            {{ titleStatusText }}
          </UBadge>
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
      <p
        v-if="slot === 'referenceNumber' || slot === 'recordType' || slot === 'description'"
        class="mt-1.5 truncate text-xs text-muted"
      >
        <template v-if="slot === 'referenceNumber'">{{ referenceNumber }}</template>
        <template v-else-if="slot === 'recordType'">{{ recordTypeLabel }}</template>
        <template v-else>{{ description }}</template>
      </p>
      <div
        v-else-if="slot === 'party' && partyLabel"
        class="mt-1.5 flex items-center gap-1.5 truncate text-xs text-muted"
      >
        <UIcon :name="partyLabel.icon" class="size-3 shrink-0" />
        <span class="truncate">{{ partyLabel.text }}</span>
      </div>
      <div
        v-else-if="slot === 'owner'"
        class="mt-1.5 flex items-center gap-1.5 truncate text-xs text-muted"
      >
        <UIcon name="i-lucide-user" class="size-3 shrink-0" />
        <span class="truncate">{{ owner }}</span>
      </div>
      <div
        v-else-if="slot === 'assignee'"
        class="mt-1.5 flex items-center gap-1.5 truncate text-xs text-muted"
      >
        <UIcon name="i-lucide-user-check" class="size-3 shrink-0" />
        <span class="truncate">{{ assignee }}</span>
      </div>
      <div v-else-if="slot === 'stage'" class="mt-1.5">
        <UBadge size="sm" color="neutral" variant="outline">{{ stageLabel }}</UBadge>
      </div>
      <div v-else-if="slot === 'waiting'" class="mt-1.5">
        <UBadge size="sm" color="warning" variant="subtle">{{ $t('docetra.fields.waiting') }}</UBadge>
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
      <div
        v-else-if="bodySlotText(slot)"
        class="mt-1.5 flex min-w-0 items-center gap-1.5 text-xs text-muted"
      >
        <UIcon
          :name="slot === 'involvedOfficers' || slot === 'officerInCharge'
            ? 'i-lucide-user-round'
            : slot === 'externalUnits' || slot === 'officeInCharge'
              ? 'i-lucide-building-2'
              : 'i-lucide-file-text'"
          class="size-3 shrink-0"
        />
        <span class="shrink-0 font-medium text-toned">{{ $t(`docetra.cardSlots.${slot}`) }}:</span>
        <span class="min-w-0 truncate">{{ bodySlotText(slot) }}</span>
      </div>
    </template>
    </div>

    <div
      v-if="footerSlots.length"
      class="mt-auto flex items-center justify-between gap-2 border-t border-default pt-2 text-xs text-muted"
    >
      <div class="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
        <template v-for="slot in footerLeft" :key="`L-${slot}`">
          <span
            v-if="slot === 'attachmentCount'"
            class="inline-flex items-center gap-1"
          >
            <UIcon name="i-lucide-paperclip" class="size-3" />
            {{ attachmentCount }}
          </span>
          <span
            v-else-if="slot === 'commentCount'"
            class="inline-flex items-center gap-1"
          >
            <UIcon name="i-lucide-message-circle" class="size-3" />
            {{ commentCount }}
          </span>
          <span
            v-else
            class="inline-flex min-w-0 items-center gap-1 truncate"
          >
            <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
            <span class="truncate">
              <template v-if="slot === 'recordTime'">{{ recordTime || '—' }}</template>
              <template v-else-if="slot === 'dateRange'">{{ dateLabel || '—' }}</template>
              <template v-else>{{ footerDate(slot) || '—' }}</template>
            </span>
          </span>
        </template>
      </div>
      <div class="inline-flex shrink-0 flex-wrap items-center justify-end gap-2">
        <template v-for="slot in footerRight" :key="`R-${slot}`">
          <span
            v-if="slot === 'attachmentCount'"
            class="inline-flex items-center gap-1"
          >
            <UIcon name="i-lucide-paperclip" class="size-3" />
            {{ attachmentCount }}
          </span>
          <span
            v-else-if="slot === 'commentCount'"
            class="inline-flex items-center gap-1"
          >
            <UIcon name="i-lucide-message-circle" class="size-3" />
            {{ commentCount }}
          </span>
          <span
            v-else
            class="inline-flex min-w-0 items-center gap-1 truncate"
          >
            <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
            <span class="truncate">
              <template v-if="slot === 'recordTime'">{{ recordTime || '—' }}</template>
              <template v-else-if="slot === 'dateRange'">{{ dateLabel || '—' }}</template>
              <template v-else>{{ footerDate(slot) || '—' }}</template>
            </span>
          </span>
        </template>
      </div>
    </div>
  </article>
</template>
