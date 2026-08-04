<script setup lang="ts">
import type { WorkflowStage } from '~/types/docetra/common'

const props = defineProps<{
  row: Record<string, unknown>
  title: string
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

const { t, te } = useI18n()

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

const referenceNumber = computed(() => String(props.row.referenceNumber || ''))
const recordTypeLabel = computed(() =>
  String(props.row.recordTypeName || props.row.recordTypeId || ''),
)
const sender = computed(() => orgName(props.row.senderOrganization))
const recipient = computed(() => orgName(props.row.recipientOrganization))
const ownerDepartment = computed(() => orgName(props.row.ownerDepartment))
const owner = computed(() => personName(props.row.owner))
const assignee = computed(() => personName(props.row.assignee))
const waiting = computed(() => Boolean(props.row.waiting))
const attachmentCount = computed(() => Number(props.row.attachmentCount || 0))
const commentCount = computed(() => Number(props.row.commentCount || 0))
const tags = computed(() =>
  Array.isArray(props.row.tags) ? props.row.tags.map(String).filter(Boolean) : [],
)

const startDate = computed(() =>
  day(props.row.receivedDate)
  || day(props.row.sentDate)
  || day(props.row.createdAt),
)

const endDate = computed(() => {
  const updated = day(props.row.updatedAt)
  const start = startDate.value
  if (updated && start && updated !== start) return updated
  // Prefer the other operational date when both exist.
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
  if (sender.value) return { icon: 'i-lucide-building-2', text: sender.value, key: 'sender' }
  if (recipient.value) return { icon: 'i-lucide-send', text: recipient.value, key: 'recipient' }
  if (ownerDepartment.value) return { icon: 'i-lucide-building', text: ownerDepartment.value, key: 'dept' }
  return null
})

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
        <p
          v-if="referenceNumber || recordTypeLabel"
          class="mt-1 truncate text-xs text-muted"
        >
          <span v-if="referenceNumber">{{ referenceNumber }}</span>
          <span v-if="referenceNumber && recordTypeLabel"> · </span>
          <span v-if="recordTypeLabel">{{ recordTypeLabel }}</span>
        </p>
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

    <div
      v-if="partyLabel"
      class="mt-2 flex items-center gap-1.5 truncate text-xs text-muted"
    >
      <UIcon :name="partyLabel.icon" class="size-3 shrink-0" />
      <span class="truncate">{{ partyLabel.text }}</span>
    </div>

    <div
      v-if="owner || assignee"
      class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted"
    >
      <span v-if="owner" class="inline-flex min-w-0 items-center gap-1 truncate">
        <UIcon name="i-lucide-user" class="size-3 shrink-0" />
        <span class="truncate">{{ owner }}</span>
      </span>
      <span v-if="assignee" class="inline-flex min-w-0 items-center gap-1 truncate">
        <UIcon name="i-lucide-user-check" class="size-3 shrink-0" />
        <span class="truncate">{{ assignee }}</span>
      </span>
    </div>

    <div
      v-if="statusLabel || stageLabel || waiting"
      class="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted"
    >
      <UBadge v-if="statusLabel" size="sm" color="neutral" variant="subtle">
        {{ statusLabel }}
      </UBadge>
      <UBadge v-if="stageLabel" size="sm" color="neutral" variant="outline">
        {{ stageLabel }}
      </UBadge>
      <UBadge
        v-if="waiting"
        size="sm"
        color="warning"
        variant="subtle"
      >
        {{ $t('docetra.fields.waiting') }}
      </UBadge>
    </div>

    <div
      v-if="tags.length"
      class="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted"
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
      v-if="dateLabel || attachmentCount || commentCount"
      class="mt-2 flex items-center justify-between gap-2 border-t border-default pt-2 text-xs text-muted"
    >
      <span v-if="dateLabel" class="inline-flex min-w-0 items-center gap-1 truncate">
        <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
        <span class="truncate">{{ dateLabel }}</span>
      </span>
      <span v-else />
      <span
        v-if="attachmentCount || commentCount"
        class="inline-flex shrink-0 items-center gap-2"
      >
        <span v-if="attachmentCount" class="inline-flex items-center gap-1">
          <UIcon name="i-lucide-paperclip" class="size-3" />
          {{ attachmentCount }}
        </span>
        <span v-if="commentCount" class="inline-flex items-center gap-1">
          <UIcon name="i-lucide-message-circle" class="size-3" />
          {{ commentCount }}
        </span>
      </span>
    </div>
  </article>
</template>
