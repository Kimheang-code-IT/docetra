<script setup lang="ts">
import type { PersonSummary, WorkflowStage } from '~/types/docetra/common'

const props = withDefaults(
  defineProps<{
    card: Record<string, unknown>
    title: string
    stages: WorkflowStage[]
    currentStage: string
    dragging?: boolean
    dropTarget?: boolean
  }>(),
  {
    dragging: false,
    dropTarget: false,
  },
)

const emit = defineEmits<{
  click: []
  move: [stage: string]
  dragStart: [id: string]
  dragEnd: []
}>()

const { t, te } = useI18n()

const person = computed((): PersonSummary | null => {
  const assignee = props.card.assignee as PersonSummary | undefined
  const owner = props.card.owner as PersonSummary | undefined
  return assignee || owner || null
})

const statusLabel = computed(() => {
  const status = props.card.status
  if (!status) return ''
  const key = `docetra.status.${status}`
  return te(key) ? t(key) : String(status)
})

const attachmentCount = computed(() => Number(props.card.attachmentCount || 0))
const commentCount = computed(() => Number(props.card.commentCount || 0))
const waiting = computed(() => Boolean(props.card.waiting))

const moveItems = computed(() => [
  props.stages
    .filter(s => s.code !== props.currentStage)
    .map(s => ({
      label: t('docetra.actions.moveTo', { stage: t(s.labelKey) }),
      icon: 'i-lucide-arrow-right',
      onSelect: () => emit('move', s.code),
    })),
])

function onDragStart(event: DragEvent) {
  const id = String(props.card.id)
  event.dataTransfer?.setData('text/plain', id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
  emit('dragStart', id)
}

function onDragEnd() {
  emit('dragEnd')
}
</script>

<template>
  <article
    draggable="true"
    class="group relative cursor-grab rounded-md border border-default bg-default p-2.5 text-left shadow-xs transition-all active:cursor-grabbing"
    :class="[
      dragging ? 'opacity-40 scale-[0.98] ring-2 ring-primary/30' : 'hover:border-primary/35 hover:shadow-sm',
      dropTarget ? 'ring-2 ring-primary/40' : '',
    ]"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @click="emit('click')"
    @keydown.enter.prevent="emit('click')"
    tabindex="0"
    role="button"
    :aria-label="title"
  >
    <div class="flex items-start gap-2">
      <div class="min-w-0 flex-1">
        <slot>
          <p class="text-sm font-medium leading-snug text-highlighted wrap-break-word">
            {{ title }}
          </p>
        </slot>
      </div>

      <UDropdownMenu v-if="moveItems[0]?.length" :items="moveItems" :content="{ align: 'end' }">
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

    <slot name="meta">
      <div v-if="person || statusLabel" class="mt-2 flex items-center gap-2 min-w-0">
        <UAvatar
          v-if="person"
          :src="person.avatarUrl"
          :alt="person.name"
          size="xs"
          :text="person.name.slice(0, 1)"
        />
        <p class="truncate text-xs app-card-text">
          {{ person?.name || statusLabel }}
        </p>
      </div>
    </slot>

    <div
      v-if="waiting || statusLabel || attachmentCount || commentCount || $slots.footer"
      class="mt-2 flex flex-wrap items-center gap-1.5"
    >
      <slot name="footer">
        <UBadge v-if="waiting" size="sm" color="warning" variant="subtle">
          {{ $t('docetra.fields.waiting') }}
        </UBadge>
        <UBadge v-else-if="statusLabel" size="sm" color="neutral" variant="subtle">
          {{ statusLabel }}
        </UBadge>
        <span
          v-if="attachmentCount"
          class="inline-flex items-center gap-0.5 text-[11px] app-card-text"
          :title="$t('docetra.fields.attachments')"
        >
          <UIcon name="i-lucide-paperclip" class="size-3" />
          {{ attachmentCount }}
        </span>
        <span
          v-if="commentCount"
          class="inline-flex items-center gap-0.5 text-[11px] app-card-text"
          :title="$t('docetra.comments.title')"
        >
          <UIcon name="i-lucide-message-square" class="size-3" />
          {{ commentCount }}
        </span>
      </slot>
    </div>
  </article>
</template>
