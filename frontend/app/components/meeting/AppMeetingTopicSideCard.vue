<script setup lang="ts">
import type { MeetingTopic } from '~/types/docetra/entities'
import { useCardFields } from '~/composables/settings/useCardFields'
import { splitCardSlots } from '~/utils/card-fields'

const props = defineProps<{
  topic: MeetingTopic
  meetingCount: number
  selected?: boolean
  dropActive?: boolean
  collapsed?: boolean
}>()

const emit = defineEmits<{
  select: []
  open: []
  dropMeeting: [meetingId: string]
  dragOver: []
  dragLeave: []
}>()

const { t, te } = useI18n()
const { visibleSlots } = useCardFields('meetingTopics')

const statusLabel = computed(() => {
  const key = `docetra.status.${props.topic.status}`
  return te(key) ? t(key) : props.topic.status
})

const stageLabel = computed(() => {
  if (!props.topic.stage) return ''
  const key = `docetra.stages.${props.topic.stage}`
  return te(key) ? t(key) : props.topic.stage
})

const statusColor = computed(() => {
  const status = String(props.topic.status || '').toLowerCase()
  if (status === 'active' || status === 'completed') return 'success' as const
  if (status === 'pending' || status === 'draft') return 'warning' as const
  if (status === 'disabled' || status === 'failed') return 'error' as const
  return 'info' as const
})

const topicTags = computed(() =>
  Array.isArray(props.topic.tags) ? props.topic.tags.map(String).filter(Boolean) : [],
)

const cardSlots = computed(() => splitCardSlots('meetingTopics', visibleSlots.value))
const showStatus = computed(() => cardSlots.value.titleChrome.includes('status'))
const showStage = computed(() => cardSlots.value.body.includes('stage'))
const showTags = computed(() => cardSlots.value.body.includes('tags'))
const showRecordTime = computed(() => cardSlots.value.footer.includes('recordTime'))

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
    :data-meeting-topic-drop="topic.id"
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
    :aria-label="topic.title"
    :title="collapsed ? topic.title : undefined"
    @click="emit('select')"
    @keydown.enter.prevent="emit('select')"
    @dblclick="emit('open')"
    @dragover="onDragOver"
    @dragleave="emit('dragLeave')"
    @drop="onDrop"
  >
    <UIcon v-if="collapsed" name="i-lucide-message-square" class="size-4" />
    <div v-else class="flex items-start gap-2">
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-1.5">
          <h3 class="text-sm font-semibold text-highlighted wrap-break-word">
            {{ topic.title }}
          </h3>
          <UBadge v-if="showStatus" :color="statusColor" variant="soft" size="sm" icon="i-lucide-circle-dot">
            {{ statusLabel }}
          </UBadge>
        </div>
      </div>
      <UBadge color="neutral" variant="subtle" size="sm" icon="i-lucide-calendar-days" class="shrink-0 tabular-nums">
        {{ meetingCount }}
      </UBadge>
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
    <div v-if="!collapsed && (showStage || showTags)" class="mt-2 flex flex-wrap gap-1">
      <UBadge v-if="showStage && topic.stage" size="sm" color="info" variant="soft" icon="i-lucide-git-branch">
        {{ stageLabel }}
      </UBadge>
      <UBadge v-if="showTags && topicTags.length" size="sm" color="secondary" variant="soft" icon="i-lucide-tag">
        {{ topicTags[0] }}
      </UBadge>
    </div>
    <div
      v-if="!collapsed && showRecordTime"
      class="app-card-field-highlight app-card-field-highlight--info mt-2 flex items-center gap-1 text-xs app-card-text"
    >
      <UIcon name="i-lucide-calendar" class="size-3 shrink-0" />
      <span class="truncate">{{ topic.recordTime || topic.meetingDate || '—' }}</span>
    </div>
  </article>
</template>
